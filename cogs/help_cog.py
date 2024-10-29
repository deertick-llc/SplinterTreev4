import discord
from discord.ext import commands

class ContactButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="Contact Card", 
            url="https://sydney.gwyn.tel/contactcard"
        ))

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='contact')
    async def show_contact(self, ctx):
        """Show contact information with button"""
        embed = discord.Embed(
            title="Contact Information",
            description="Click the button below to view my contact card",
            color=discord.Color.blue()
        )
        view = ContactButton()
        await ctx.send(embed=embed, view=view)

    @commands.command(name='splintertree_help')
    async def splintertree_help(self, ctx, mode: str = "channel"):
        """Comprehensive help command showing all features, models, and commands
        
        Parameters:
        mode: str - Where to send help info: "channel" or "dm" (default: channel)
        """
        embeds = []

        # Main Features Embed
        main_embed = discord.Embed(
            title="🌳 Splintertree Help",
            description="Complete guide to Splintertree's features and capabilities",
            color=discord.Color.green()
        )

        # Add Administrative Commands section
        admin_commands = """
        `!splintertree_help [channel|dm]` - Show this help message (in channel or DM)
        `!setcontext <size>` - Set context window size for the channel
        `!getcontext` - Show current context window size
        `!resetcontext` - Reset context window to default
        `!clearcontext [hours]` - Clear conversation history (optionally specify hours)
        `!contact` - Show contact information
        """
        main_embed.add_field(name="👑 Administrative Commands", value=admin_commands.strip(), inline=False)

        # Add Core Features section
        features = """
        • **Shared Context Database** - Persistent conversation history shared between agents
        • **Image Processing** - Automatic image description using vision models
        • **File Handling** - Support for text files and images
        • **Response Reroll** - Button to generate alternative responses
        • **Emotion Analysis** - Reactions based on message sentiment
        • **Status Updates** - Rotating status showing uptime, last interaction, and current model
        """
        main_embed.add_field(name="✨ Core Features", value=features.strip(), inline=False)

        # Add Basic Usage section
        usage = """
        • **Direct Mention** - @Splintertree for random model response
        • **Keyword Trigger** - Use "splintertree" in message for random model
        • **Model Selection** - Use specific model triggers (listed below)
        • **Image Analysis** - Simply attach an image with your message
        • **File Processing** - Attach .txt or .md files with your message
        • **Context Management** - Use context commands to control conversation history
        """
        main_embed.add_field(name="📝 Basic Usage", value=usage.strip(), inline=False)
        embeds.append(main_embed)

        # Models Embed
        models_embed = discord.Embed(
            title="🤖 Available Models",
            description="List of all available AI models and their trigger words",
            color=discord.Color.blue()
        )

        # Get all available models and their capabilities
        models_info = {}
        vision_models = []
        
        for cog in self.bot.cogs.values():
            if hasattr(cog, 'name') and hasattr(cog, 'provider') and hasattr(cog, 'trigger_words'):
                provider = "OpenRouter" if cog.provider == "openrouter" else "OpenPipe"
                capabilities = []
                
                if hasattr(cog, 'supports_vision') and cog.supports_vision:
                    capabilities.append("Vision")
                    vision_models.append(cog.name)
                
                capabilities.append(provider)
                capabilities_str = " | ".join(capabilities)
                
                trigger_words = [f"`{word}`" for word in cog.trigger_words]
                trigger_str = ", ".join(trigger_words)
                
                models_info[cog.name] = f"**Capabilities:** {capabilities_str}\n**Triggers:** {trigger_str}"

        # Sort models by name and add to embed
        for name in sorted(models_info.keys()):
            models_embed.add_field(name=name, value=models_info[name], inline=False)

        embeds.append(models_embed)

        # Special Features Embed
        special_embed = discord.Embed(
            title="🎯 Special Features",
            description="Detailed information about special features and capabilities",
            color=discord.Color.gold()
        )

        # Add Vision Processing section
        vision_info = f"""
        The following models support direct image analysis:
        {', '.join(vision_models)}
        
        Other models will receive text descriptions of images processed by Llama.
        Simply attach an image to your message or reference a recent image.
        """
        special_embed.add_field(name="👁️ Vision Processing", value=vision_info.strip(), inline=False)

        # Add Context Management section
        context_info = """
        • **Persistent Storage**: SQLite database for reliable context storage
        • **Shared Context**: All models can see and reference each other's responses
        • **Flexible Management**: Adjustable context window per channel
        • **History Control**: Clear old context with customizable timeframe
        • **Cross-Session**: Context persists between bot restarts
        """
        special_embed.add_field(name="🧠 Context Management", value=context_info.strip(), inline=False)

        # Add File Processing section
        file_info = """
        • Supports .txt and .md files
        • Automatic content extraction
        • Can be combined with image processing
        • Content included in model context
        """
        special_embed.add_field(name="📄 File Processing", value=file_info.strip(), inline=False)

        embeds.append(special_embed)

        try:
            if mode.lower() == "dm":
                # Try to send via DM
                try:
                    for embed in embeds:
                        await ctx.author.send(embed=embed)
                    await ctx.message.add_reaction('✅')
                except discord.Forbidden:
                    await ctx.send("❌ I couldn't send you a DM. Please check your DM settings or use `!splintertree_help channel` instead.")
            else:
                # Send in channel
                for embed in embeds:
                    await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ An error occurred while sending help information: {str(e)}")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
