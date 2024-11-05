import discord
from discord.ext import commands
import logging
from .base_cog import BaseCog
import json

class MysteryMergeNemoCog(BaseCog):
    def __init__(self, bot):
        super().__init__(
            bot=bot,
            name="Mystery Merge Nemo",
            nickname="MysteryNemo",
            trigger_words=['nemo'],
            model="openpipe:AutoMeta/PygTesting/mystery-merge-nemo",
            provider="openpipe",
            prompt_file="None",
            supports_vision=False
        )
        logging.debug(f"[Mystery Merge Nemo] Initialized with raw_prompt: {self.raw_prompt}")
        logging.debug(f"[Mystery Merge Nemo] Using provider: {self.provider}")
        logging.debug(f"[Mystery Merge Nemo] Vision support: {self.supports_vision}")

        # Load temperature settings
        try:
            with open('temperatures.json', 'r') as f:
                self.temperatures = json.load(f)
        except Exception as e:
            logging.error(f"[Mystery Merge Nemo] Failed to load temperatures.json: {e}")
            self.temperatures = {}

    @property
    def qualified_name(self):
        """Override qualified_name to match the expected cog name"""
        return "Mystery Merge Nemo"

    def get_temperature(self):
        """Get temperature setting for this agent"""
        return self.temperatures.get(self.name.lower(), 0.7)

    async def generate_response(self, message):
        """Generate a response using openpipe"""
        try:
            # Format system prompt
            formatted_prompt = self.format_prompt(message)
            messages = [{"role": "system", "content": formatted_prompt}]

            # Get last 50 messages from database
            channel_id = str(message.channel.id)
            history_messages = await self.context_cog.get_context_messages(channel_id, limit=50)
            
            # Format history messages with proper roles
            for msg in history_messages:
                role = "assistant" if msg['is_assistant'] else "user"
                content = msg['content']
                
                # Handle system summaries
                if msg['user_id'] == 'SYSTEM' and content.startswith('[SUMMARY]'):
                    role = "system"
                    content = content[9:].strip()  # Remove [SUMMARY] prefix
                
                messages.append({
                    "role": role,
                    "content": content
                })

            # Process current message and any images
            content = message.content
            image_descriptions = []

            # Get descriptions for any image attachments
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    description = await self.get_image_description(attachment.url)
                    if description:
                        image_descriptions.append(description)  # Append the description directly

            # Get descriptions for image URLs in embeds
            for embed in message.embeds:
                if embed.image and embed.image.url:
                    description = await self.get_image_description(embed.image.url)
                    if description:
                        image_descriptions.append(description)  # Append the description directly
                if embed.thumbnail and embed.thumbnail.url:
                    description = await self.get_image_description(embed.thumbnail.url)
                    if description:
                        image_descriptions.append(description)  # Append the description directly

            # Combine message content with image descriptions
            if image_descriptions:
                content += '\n\n' + '\n\n'.join(image_descriptions)

            messages.append({
                "role": "user",
                "content": content
            })

            logging.debug(f"[Mystery Merge Nemo] Sending {len(messages)} messages to API")
            logging.debug(f"[Mystery Merge Nemo] Formatted prompt: {formatted_prompt}")

            # Get temperature for this agent
            temperature = self.get_temperature()
            logging.debug(f"[Mystery Merge Nemo] Using temperature: {temperature}")

            # Call API and return the stream directly
            response_stream = await self.api_client.call_openpipe(
                messages=messages,
                model=self.model,
                temperature=temperature,
                stream=True
            )

            return response_stream

        except Exception as e:
            logging.error(f"Error processing message for Mystery Merge Nemo: {e}")
            return None

async def setup(bot):
    # Register the cog with its proper name
    try:
        cog = MysteryMergeNemoCog(bot)
        await bot.add_cog(cog)
        logging.info(f"[Mystery Merge Nemo] Registered cog with qualified_name: {cog.qualified_name}")
        return cog
    except Exception as e:
        logging.error(f"[Mystery Merge Nemo] Failed to register cog: {e}", exc_info=True)
        raise