import discord
from discord.ext import commands, tasks
import logging
import os
import config
import importlib
import asyncio
import random
import aiohttp
import json
from datetime import datetime, timedelta
import re
import pytz
import traceback
from shared.api import api  # Import the API singleton

# Define BOT_DIR as the current working directory
BOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.typing = True
intents.dm_messages = True
intents.guilds = True
intents.members = True

class SplinterTreeBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_messages = set()
        self.api_client = api
        self.loaded_cogs = []
        self.message_history = {}
        self.last_used_cogs = {}
        self.start_time = None
        self.last_interaction = {
            'user': None,
            'time': None
        }
        self.cogs_loaded = False  # Flag to prevent multiple cog setups
        self.last_status_check = 0  # Track last status check time
        self.current_status = None  # Track current custom status

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    def get_uptime_enabled(self):
        """Get uptime status toggle state"""
        try:
            with open('bot_config.json', 'r') as f:
                config_data = json.load(f)
                return config_data.get('uptime_enabled', True)
        except:
            return True

    async def check_status_file(self):
        """Check if there's a new status to set"""
        try:
            if not os.path.exists('bot_status.txt'):
                return
            
            # Check file modification time
            mod_time = os.path.getmtime('bot_status.txt')
            if mod_time <= self.last_status_check:
                return
            
            # Read and update status
            with open('bot_status.txt', 'r') as f:
                status = f.read().strip()
            
            if status:
                self.current_status = status
                await self.change_presence(activity=discord.Game(name=status))
                self.last_status_check = mod_time
                
                # Clear the file
                with open('bot_status.txt', 'w') as f:
                    f.write('')
                
        except Exception as e:
            logging.error(f"Error checking status file: {e}")

async def load_context_settings():
    """Load saved context window settings"""
    try:
        settings_file = os.path.join(BOT_DIR, 'context_windows.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                config.CONTEXT_WINDOWS.update(settings)
                logging.info("Loaded context window settings")
    except Exception as e:
        logging.error(f"Error loading context settings: {str(e)}")

async def setup_cogs(bot: SplinterTreeBot):
    """Load all cogs"""
    if bot.cogs_loaded:
        logging.info("Cogs have already been loaded. Skipping setup.")
        return

    bot.loaded_cogs = []  # Reset loaded cogs list

    # Load context settings
    await load_context_settings()

    # First load core cogs
    core_cogs = ['context_cog', 'management_cog', 'webhook_cog']
    for cog in core_cogs:
        try:
            await bot.load_extension(f'cogs.{cog}')
            logging.info(f"Loaded core cog: {cog}")
        except Exception as e:
            logging.error(f"Failed to load core cog {cog}: {str(e)}")
            logging.error(traceback.format_exc())

    # Then load all model cogs
    cogs_dir = os.path.join(BOT_DIR, 'cogs')
    for filename in os.listdir(cogs_dir):
        if filename.endswith('_cog.py') and filename not in ['base_cog.py', 'help_cog.py', 'sorcerer_cog.py']:
            module_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{module_name}')
                logging.debug(f"Attempting to load cog: {module_name}")
                
                # Dynamically derive the cog class name from the module name
                class_name = ''.join(word.capitalize() for word in module_name.split('_'))
                
                cog_instance = bot.get_cog(class_name)
                if cog_instance and hasattr(cog_instance, 'handle_message'):
                    bot.loaded_cogs.append(cog_instance)
                    logging.info(f"Loaded cog: {cog_instance.name}")
                
            except commands.errors.ExtensionAlreadyLoaded:
                logging.info(f"Extension 'cogs.{module_name}' is already loaded, skipping.")
            except Exception as e:
                logging.error(f"Failed to load cog {filename}: {str(e)}")
                logging.error(traceback.format_exc())

    # Finally load help cog after all other cogs are loaded
    try:
        await bot.load_extension('cogs.help_cog')
        logging.info("Loaded help cog")
        
        # Ensure help command is accessible
        help_cog = bot.get_cog('HelpCog')
        if help_cog:
            logging.info("Help cog loaded successfully")
        else:
            logging.error("Failed to find HelpCog after loading")
    except Exception as e:
        logging.error(f"Failed to load help cog: {str(e)}")
        logging.error(traceback.format_exc())

    logging.info(f"Total loaded cogs with handle_message: {len(bot.loaded_cogs)}")
    for cog in bot.loaded_cogs:
        logging.debug(f"Available cog: {cog.name} (Vision: {getattr(cog, 'supports_vision', False)})")
    logging.info(f"Loaded extensions: {list(bot.extensions.keys())}")

    bot.cogs_loaded = True  # Set the flag to indicate cogs have been loaded

# Initialize bot with a default command prefix
bot = SplinterTreeBot(command_prefix='!', intents=intents, help_command=None)

# File to persist processed messages
PROCESSED_MESSAGES_FILE = os.path.join(BOT_DIR, 'processed_messages.json')

def load_processed_messages():
    """Load processed messages from file"""
    if os.path.exists(PROCESSED_MESSAGES_FILE):
        try:
            with open(PROCESSED_MESSAGES_FILE, 'r') as f:
                bot.processed_messages = set(json.load(f))
            logging.info(f"Loaded {len(bot.processed_messages)} processed messages from file")
        except Exception as e:
            logging.error(f"Error loading processed messages: {str(e)}")

def save_processed_messages():
    """Save processed messages to file"""
    try:
        with open(PROCESSED_MESSAGES_FILE, 'w') as f:
            json.dump(list(bot.processed_messages), f)
        logging.info(f"Saved {len(bot.processed_messages)} processed messages to file")
    except Exception as e:
        logging.error(f"Error saving processed messages: {str(e)}")

def get_history_file(channel_id: str) -> str:
    """Get the history file path for a channel"""
    history_dir = os.path.join(BOT_DIR, 'history')
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
    return os.path.join(history_dir, f'history_{channel_id}.json')

def get_uptime():
    """Get bot uptime as a formatted string"""
    if bot.start_time is None:
        return "Unknown"
    pst = pytz.timezone('US/Pacific')
    current_time = datetime.now(pst)
    uptime = current_time - bot.start_time.astimezone(pst)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)

@tasks.loop(seconds=30)
async def update_status():
    """Update bot status"""
    try:
        # Check for status updates from web UI
        await bot.check_status_file()
        
        # If no custom status and uptime is enabled, show uptime
        if not bot.current_status and bot.get_uptime_enabled():
            await bot.change_presence(activity=discord.Game(name=f"Up for {get_uptime()}"))
        elif bot.current_status:
            # Ensure custom status stays set
            await bot.change_presence(activity=discord.Game(name=bot.current_status))
    except Exception as e:
        logging.error(f"Error updating status: {str(e)}")

async def setup_cogs_task():
    """Load all cogs"""
    await setup_cogs(bot)

@bot.event
async def on_ready():
    pst = pytz.timezone('US/Pacific')
    bot.start_time = datetime.now(pst)
    logging.info(f"Bot is ready! Logged in as {bot.user.name}")
    
    # Set initial "Booting..." status
    await bot.change_presence(activity=discord.Game(name="Booting..."))
    
    await setup_cogs_task()
    
    # Start the status update task
    if not update_status.is_running():
        update_status.start()

async def resolve_user_id(user_id):
    """Resolve a user ID to a username"""
    try:
        user = await bot.fetch_user(user_id)
        return user.name if user else str(user_id)
    except Exception as e:
        logging.error(f"Error resolving user ID {user_id}: {e}")
        return str(user_id)

async def process_attachment(attachment):
    """Process a single attachment and return its content"""
    try:
        if attachment.filename.endswith(('.txt', '.md')):
            content = await attachment.read()
            return content.decode('utf-8')
        elif attachment.content_type and attachment.content_type.startswith('image/'):
            return f"[Image: {attachment.filename}]"
        else:
            return f"[Attachment: {attachment.filename}]"
    except Exception as e:
        logging.error(f"Error processing attachment {attachment.filename}: {e}")
        return f"[Attachment: {attachment.filename}]"

def get_cog_by_name(name):
    """Get a cog by name or class name"""
    for cog in bot.cogs.values():
        if (hasattr(cog, 'name') and cog.name.lower() == name.lower()) or \
           cog.__class__.__name__.lower() == f"{name.lower()}cog":
            return cog
    return None

def get_model_from_message(content):
    """Extract model name from message content"""
    if content.startswith('[') and ']' in content:
        return content[1:content.index(']')]
    return None

@bot.event
async def on_message(message):
    # Process commands first
    await bot.process_commands(message)

    # Update last interaction
    bot.last_interaction['user'] = message.author.display_name
    bot.last_interaction['time'] = datetime.now(pytz.timezone('US/Pacific'))

    # Skip if message is from this bot
    if message.author == bot.user:
        return

    # Process attachments
    attachment_contents = []
    for attachment in message.attachments:
        attachment_content = await process_attachment(attachment)
        attachment_contents.append(attachment_content)

    # Combine message content and attachment contents
    full_content = message.content
    if attachment_contents:
        full_content += "\n" + "\n".join(attachment_contents)

    # Debug logging for message content and attachments
    logging.debug(f"Received message in channel {message.channel.id}: {full_content}")

    # Check if message is a reply to a bot message
    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                # Extract model name from the replied message
                model_name = get_model_from_message(replied_msg.content)
                if model_name:
                    # Get corresponding cog
                    cog = get_cog_by_name(model_name)
                    if cog and hasattr(cog, 'handle_message'):
                        logging.debug(f"Using {model_name} cog to handle reply")
                        await cog.handle_message(message, full_content)
                        return
        except Exception as e:
            logging.error(f"Error handling reply: {str(e)}")

    # Pass the message to all cogs' on_message methods
    for cog in bot.cogs.values():
        if hasattr(cog, 'on_message'):
            try:
                await cog.on_message(message)
            except Exception as e:
                logging.error(f"Error in {cog.__class__.__name__}.on_message: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Ignore command not found errors
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.")
    else:
        logging.error(f"Command error: {str(error)}")
        logging.error(traceback.format_exc())
        await ctx.reply("❌ An error occurred while executing the command.")

def load_processed_messages():
    """Load processed messages from file"""
    if os.path.exists(PROCESSED_MESSAGES_FILE):
        try:
            with open(PROCESSED_MESSAGES_FILE, 'r') as f:
                bot.processed_messages = set(json.load(f))
            logging.info(f"Loaded {len(bot.processed_messages)} processed messages from file")
        except Exception as e:
            logging.error(f"Error loading processed messages: {str(e)}")

def save_processed_messages():
    """Save processed messages to file"""
    try:
        with open(PROCESSED_MESSAGES_FILE, 'w') as f:
            json.dump(list(bot.processed_messages), f)
        logging.info(f"Saved {len(bot.processed_messages)} processed messages to file")
    except Exception as e:
        logging.error(f"Error saving processed messages: {str(e)}")

def get_history_file(channel_id: str) -> str:
    """Get the history file path for a channel"""
    history_dir = os.path.join(BOT_DIR, 'history')
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
    return os.path.join(history_dir, f'history_{channel_id}.json')

def get_uptime():
    """Get bot uptime as a formatted string"""
    if bot.start_time is None:
        return "Unknown"
    pst = pytz.timezone('US/Pacific')
    current_time = datetime.now(pst)
    uptime = current_time - bot.start_time.astimezone(pst)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)

# Run bot
if __name__ == "__main__":
    logging.debug("Starting bot...")
    load_processed_messages()  # Load processed messages on startup
    bot.run(TOKEN)
