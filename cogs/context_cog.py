import discord
from discord.ext import commands
from config import CONTEXT_WINDOWS, DEFAULT_CONTEXT_WINDOW, MAX_CONTEXT_WINDOW, OPENPIPE_API_KEY, OPENPIPE_API_URL
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Optional
import textwrap
from openai import OpenAI

class ContextCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'databases/interaction_logs.db'
        self._setup_database()
        self.summary_chunk_hours = 24  # Summarize every 24 hours of chat
        self.last_summary_check = {}  # Track last summary generation per channel
        self.openai_client = OpenAI(
            base_url=OPENPIPE_API_URL,
            api_key=OPENPIPE_API_KEY
        )
        # Track last message per role to prevent duplicates
        self.last_messages = {}  # Format: {channel_id: {'user': msg, 'assistant': msg}}

    def _setup_database(self):
        """Initialize the SQLite database for interaction logs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create messages table if not exists
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    guild_id TEXT,
                    user_id TEXT,
                    content TEXT,
                    is_assistant BOOLEAN,
                    persona_name TEXT,
                    emotion TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Create index on channel_id and timestamp for faster queries
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_channel_timestamp 
                ON messages(channel_id, timestamp DESC)
                ''')
                
                # Create context_windows table if not exists
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_windows (
                    channel_id TEXT PRIMARY KEY,
                    window_size INTEGER
                )
                ''')
                
                conn.commit()
                logging.info("Database setup completed successfully")
        except Exception as e:
            logging.error(f"Failed to set up database: {str(e)}")

    async def get_context_messages(self, channel_id: str, limit: int = None, exclude_message_id: str = None) -> List[Dict]:
        """Get previous messages from the context database for all users and cogs in the channel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Always get 50 messages for API context
                window_size = 50
                if limit is not None:
                    window_size = min(window_size, limit)
                
                # Query to get messages from all users and cogs in chronological order
                query = '''
                SELECT 
                    m.id,
                    m.user_id,
                    m.content,
                    m.is_assistant,
                    m.persona_name,
                    m.emotion,
                    m.timestamp
                FROM messages m
                WHERE m.channel_id = ?
                AND (? IS NULL OR m.id != ?)
                AND m.content IS NOT NULL
                AND m.content != ''
                ORDER BY m.timestamp DESC
                LIMIT ?
                '''
                
                cursor.execute(query, (
                    channel_id,
                    exclude_message_id,
                    exclude_message_id,
                    window_size
                ))
                
                messages = []
                seen_contents = set()  # Track seen message contents
                
                for row in cursor.fetchall():
                    content = row[2]
                    
                    # Skip empty or None content
                    if not content or content.isspace():
                        continue
                        
                    # Skip if we've seen this exact content before
                    if content in seen_contents:
                        continue
                    
                    # Skip if content is too similar to recent messages
                    skip = False
                    for prev_content in list(seen_contents)[-3:]:
                        if self._similarity_score(content, prev_content) > 0.9:
                            skip = True
                            break
                    if skip:
                        continue
                    
                    seen_contents.add(content)
                    messages.append({
                        'id': row[0],
                        'user_id': row[1],
                        'content': content,
                        'is_assistant': bool(row[3]),
                        'persona_name': row[4],
                        'emotion': row[5],
                        'timestamp': row[6]
                    })
                
                # Reverse to maintain chronological order
                messages.reverse()
                return messages
                
        except Exception as e:
            logging.error(f"Failed to get context messages: {str(e)}")
            return []

    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple length-based comparison for performance
        if abs(len(str1) - len(str2)) / max(len(str1), len(str2)) > 0.3:
            return 0.0
        
        # Convert to sets of words for comparison
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    async def add_message_to_context(self, message_id, channel_id, guild_id, user_id, content, is_assistant, persona_name=None, emotion=None):
        """Add a message to the interaction logs"""
        try:
            # Skip empty or whitespace-only content
            if not content or content.isspace():
                return

            # Check for duplicate content
            last_msg = self.last_messages.get(channel_id, {}).get('assistant' if is_assistant else 'user')
            if last_msg and last_msg['content'] == content:
                logging.debug(f"Skipping duplicate message content in channel {channel_id}")
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if this message already exists
                cursor.execute('''
                SELECT content FROM messages WHERE id = ?
                ''', (str(message_id),))
                
                existing = cursor.fetchone()
                if existing:
                    logging.debug(f"Message {message_id} already exists in context")
                    return
                
                cursor.execute('''
                INSERT OR REPLACE INTO messages 
                (id, channel_id, guild_id, user_id, content, is_assistant, persona_name, emotion, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(message_id), 
                    str(channel_id), 
                    str(guild_id) if guild_id else None, 
                    str(user_id), 
                    content, 
                    is_assistant, 
                    persona_name, 
                    emotion, 
                    datetime.now().isoformat()
                ))
                
                conn.commit()

            # Update last message tracking
            if channel_id not in self.last_messages:
                self.last_messages[channel_id] = {}
            self.last_messages[channel_id]['assistant' if is_assistant else 'user'] = {
                'content': content,
                'timestamp': datetime.now()
            }

            logging.debug(f"Added message to context: {message_id} in channel {channel_id}")
        except Exception as e:
            logging.error(f"Failed to add message to context: {str(e)}")

    @commands.command(name='st_setcontext')
    @commands.has_permissions(manage_messages=True)
    async def st_set_context(self, ctx, size: int):
        """Set the number of previous messages to include in context"""
        try:
            # Validate size
            if size < 1 or size > MAX_CONTEXT_WINDOW:
                await ctx.reply(f"❌ Context size must be between 1 and {MAX_CONTEXT_WINDOW}")
                return

            # Update context window for this channel
            channel_id = str(ctx.channel.id)
            CONTEXT_WINDOWS[channel_id] = size

            # Optionally, save to a persistent configuration file
            try:
                with open('config.py', 'r') as f:
                    config_content = f.read()
                
                # Update or add the CONTEXT_WINDOWS dictionary
                import re
                config_content = re.sub(
                    r'CONTEXT_WINDOWS\s*=\s*{[^}]*}', 
                    f'CONTEXT_WINDOWS = {json.dumps(CONTEXT_WINDOWS)}', 
                    config_content
                )
                
                with open('config.py', 'w') as f:
                    f.write(config_content)
            except Exception as e:
                logging.warning(f"Could not update config.py: {str(e)}")

            await ctx.reply(f"✅ Context window set to {size} messages for this channel")
        except Exception as e:
            logging.error(f"Failed to set context: {str(e)}")
            await ctx.reply("❌ Failed to set context window")

    @commands.command(name='st_getcontext')
    async def st_get_context(self, ctx):
        """View current context window size"""
        try:
            channel_id = str(ctx.channel.id)
            context_size = CONTEXT_WINDOWS.get(channel_id, DEFAULT_CONTEXT_WINDOW)
            await ctx.reply(f"📋 Current context window: {context_size} messages")
        except Exception as e:
            logging.error(f"Failed to get context: {str(e)}")
            await ctx.reply("❌ Failed to retrieve context window size")

    @commands.command(name='st_resetcontext')
    @commands.has_permissions(manage_messages=True)
    async def st_reset_context(self, ctx):
        """Reset context window to default size"""
        try:
            channel_id = str(ctx.channel.id)
            
            # Remove channel-specific context setting
            if channel_id in CONTEXT_WINDOWS:
                del CONTEXT_WINDOWS[channel_id]

            # Update config.py
            try:
                with open('config.py', 'r') as f:
                    config_content = f.read()
                
                # Update or add the CONTEXT_WINDOWS dictionary
                import re
                config_content = re.sub(
                    r'CONTEXT_WINDOWS\s*=\s*{[^}]*}', 
                    f'CONTEXT_WINDOWS = {json.dumps(CONTEXT_WINDOWS)}', 
                    config_content
                )
                
                with open('config.py', 'w') as f:
                    f.write(config_content)
            except Exception as e:
                logging.warning(f"Could not update config.py: {str(e)}")

            await ctx.reply(f"🔄 Context window reset to default ({DEFAULT_CONTEXT_WINDOW} messages)")
        except Exception as e:
            logging.error(f"Failed to reset context: {str(e)}")
            await ctx.reply("❌ Failed to reset context window")

    @commands.command(name='st_clearcontext')
    @commands.has_permissions(manage_messages=True)
    async def st_clear_context(self, ctx, hours: Optional[int] = None):
        """Clear conversation history, optionally specify hours"""
        try:
            channel_id = str(ctx.channel.id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if hours:
                    # Delete messages older than specified hours
                    cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                    cursor.execute("""
                        DELETE FROM messages
                        WHERE channel_id = ? AND timestamp < ?
                    """, (channel_id, cutoff_time))
                else:
                    # Delete all messages for this channel
                    cursor.execute("""
                        DELETE FROM messages
                        WHERE channel_id = ?
                    """, (channel_id,))
                
                conn.commit()

            # Clear last messages tracking for this channel
            if channel_id in self.last_messages:
                del self.last_messages[channel_id]

            await ctx.reply(f"🗑️ Cleared conversation history{f' older than {hours} hours' if hours else ''}")
        except Exception as e:
            logging.error(f"Failed to clear context: {str(e)}")
            await ctx.reply("❌ Failed to clear conversation history")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and add them to context"""
        try:
            # Skip bot messages
            if message.author.bot and not message.content.lower().startswith('[summary]'):
                return

            # Skip command messages
            if message.content.startswith('!'):
                return

            # Add message to context
            guild_id = str(message.guild.id) if message.guild else None
            await self.add_message_to_context(
                message.id,
                str(message.channel.id),
                guild_id,
                str(message.author.id),
                message.content,
                False,  # is_assistant
                None,   # persona_name
                None    # emotion
            )
        except Exception as e:
            logging.error(f"Error in on_message: {e}")

async def setup(bot):
    await bot.add_cog(ContextCog(bot))
