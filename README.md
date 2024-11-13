# 🌳 Splintertree v4

A powerful Discord bot that provides access to multiple AI language models with advanced features like shared conversation context, image processing, and dynamic prompting.

## ✨ Features

### Core Features
- **Multi-Model Support**: Access to various AI models through OpenRouter, OpenPipe, and Groq.
- **Direct Message Support**: Full support for private messaging with the bot, with automatic model routing.
- **Web Dashboard**: Real-time statistics and activity monitoring through a web interface.
- **Streaming Responses**: Real-time response streaming with 1-3 sentence chunks for a more natural conversation flow.
- **Shared Context Database**: SQLite-based persistent conversation history shared between all models.
- **Universal Image Processing**: Automatic image description and analysis for all models, regardless of native vision support.
- **File Handling**: Support for text files and images.
- **Response Reroll**: Button to generate alternative responses.
- **Emotion Analysis**: Reactions based on message sentiment.
- **Status Updates**: Rotating status showing uptime, last interaction, and current model.
- **Dynamic System Prompts**: Customizable per-channel system prompts with variable support.
- **Agent Cloning**: Create custom variants of existing agents with unique system prompts.
- **PST Timezone Preference**: All time-related operations use Pacific Standard Time (PST) by default.
- **User ID Resolution**: Automatically resolves Discord user IDs to usernames in messages.
- **Default Model Configuration**: Prioritizes the default model when the bot is mentioned or specific keywords are used.
- **Attachment-Only Processing**: Handles messages containing only attachments (images, text files) without additional text.
- **Automatic Database Initialization**: Schema is automatically applied on bot startup.
- **Improved Error Handling and Logging**: Enhanced error reporting for better troubleshooting and maintenance.
- **OpenPipe Request Reporting**: Automatic logging of each message processed by context cogs to OpenPipe for analysis and potential model improvement.
- **Message ID Tracking**: Prevents duplicate messages by tracking processed message IDs.
- **Extended Model List**: Support for additional models and providers.
- **Context Management Enhancements**: Improved context handling with commands to manage context size and history.

### Special Capabilities
- **Enhanced Vision Processing**: All models can now process and respond to images, with descriptions provided for non-vision models.
- **Context Management**: Per-channel message history with configurable window size.
- **Cross-Model Context**: Models can see and reference each other's responses.
- **File Processing**: Automatic content extraction from text files.
- **Dynamic Prompting**: Customizable system prompts per channel/server.
- **Model Cloning**: Ability to clone existing models with custom prompts and settings.
- **Router Mode**: Ability to make the Router respond to all messages in a channel.

## 🌐 Web Dashboard

The bot includes a real-time web dashboard that provides:
- Total message statistics
- Active channel count
- Daily message metrics
- Most active model tracking
- Recent activity feed
- Auto-refreshing interface

Access the dashboard at your Heroku app URL (e.g., https://your-app-name.herokuapp.com).

## 🤖 Available Models

[Previous models section remains unchanged...]

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- Discord Bot Token
- OpenRouter API Key
- OpenPipe API Key
- SQLite3

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SplinterTreev4.git
   cd SplinterTreev4
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   - Copy `.env.example` to `.env`
   - Add your API keys and configuration
4. Run the bot:
   ```bash
   python bot.py
   ```

For Heroku deployment:
1. Create a new Heroku app
2. Set your environment variables in Heroku settings
3. Deploy using Git or GitHub integration
4. Ensure both web and worker dynos are enabled:
   ```bash
   heroku ps:scale web=1 worker=1
   ```

## ⚙️ Configuration

### Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENPIPE_API_KEY`: OpenPipe API key
- `OPENPIPE_API_URL`: OpenPipe API URL (ensure this is set correctly)
- `PORT`: Port for web dashboard (set automatically by Heroku)

### Configuration Files
- `config.py`: Main configuration settings
- `temperatures.json`: Model temperature settings
- `dynamic_prompts.json`: Custom prompts per channel
- `databases/interaction_logs.db`: SQLite database for conversation history

## 📝 Usage

### Core Commands
- `!listmodels` - Show all available models.
- `!uptime` - Shows how long the bot has been running.
- `!set_system_prompt <agent> <prompt>` - Set a custom system prompt for an AI agent.
- `!reset_system_prompt <agent>` - Reset an AI agent's system prompt to default.
- `!clone_agent <agent> <new_name> <system_prompt>` - Create a new agent based on an existing one (Admin only).
- `!setcontext <size>` - Set the number of previous messages to include in context (Admin only).
- `!getcontext` - View current context window size.
- `!resetcontext` - Reset context window to default size.
- `!clearcontext [hours]` - Clear conversation history, optionally specify hours (Admin only).
- `!help` - Display the help message with available commands and models.

### Router Commands
- `!router_activate` - Make Router respond to all messages in the current channel (Admin only).
- `!router_deactivate` - Stop Router from responding to all messages in the current channel (Admin only).

### System Prompt Variables
When setting custom system prompts, you can use these variables:
- `{MODEL_ID}`: The AI model's name.
- `{USERNAME}`: The user's Discord display name.
- `{DISCORD_USER_ID}`: The user's Discord ID.
- `{TIME}`: Current local time (in PST).
- `{TZ}`: Local timezone (PST).
- `{SERVER_NAME}`: Current Discord server name.
- `{CHANNEL_NAME}`: Current channel name.

### Triggering Models
- **Default Model (Router)**: By default, the bot routes messages to the most appropriate model. Mention the bot or use general keywords.
- **Specific Model**: Use model-specific triggers (e.g., "claude3haiku", "gemini", "nemotron", etc.).
- **FreeRouter Model**: For unrestricted responses, use the **"freerouter"** trigger.
- **Image Analysis**: Simply attach an image to your message (works with all models).
- **File Processing**: Attach `.txt` or `.md` files.
- **Attachment-Only Processing**: Send a message with only attachments (images, text files) without any text.
- **Direct Messages**: Send a message to the bot in DMs— all DMs are automatically handled by the router.
- **Router Mode**: Use `!router_activate` in a channel to make the Router respond to all messages.

[Rest of the README remains unchanged...]
