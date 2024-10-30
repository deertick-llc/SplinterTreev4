# 🌳 Splintertree v4

A powerful Discord bot that provides access to multiple AI language models with advanced features like shared conversation context, image processing, and dynamic prompting.

## ✨ Features

### Core Features
- **Multi-Model Support**: Access to various AI models through OpenRouter and OpenPipe
- **Shared Context Database**: SQLite-based persistent conversation history shared between all models
- **Image Processing**: Automatic image description and analysis
- **File Handling**: Support for text files and images
- **Response Reroll**: Button to generate alternative responses
- **Emotion Analysis**: Reactions based on message sentiment
- **Status Updates**: Rotating status showing uptime, last interaction, and current model
- **Dynamic System Prompts**: Customizable per-channel system prompts with variable support

### Special Capabilities
- **Vision Processing**: Direct image analysis with compatible models
- **Context Management**: Per-channel message history with configurable window size
- **Cross-Model Context**: Models can see and reference each other's responses
- **File Processing**: Automatic content extraction from text files
- **Dynamic Prompting**: Customizable system prompts per channel/server

## 🤖 Available Models

### OpenRouter Models
- **Claude-3 Opus**: State-of-the-art model with exceptional capabilities
- **Claude-3 Sonnet**: Balanced performance and efficiency
- **Claude-2**: Reliable general-purpose model
- **Claude-1.1**: Legacy model for specific use cases
- **Magnum**: High-performance 72B parameter model
- **Gemini Pro**: Google's advanced model
- **Mistral**: Efficient open-source model
- **Llama-2**: Open-source model with vision capabilities
- **NoroMaid-20B**: Advanced conversational model
- **MythoMax-L2-13B**: Versatile language model
- **Grok Beta**: xAI's latest conversational model

### OpenPipe Models
- **Hermes**: Specialized conversation model
- **Sonar**: Enhanced context understanding
- **Liquid**: Optimized for specific tasks
- **O1-Mini**: Lightweight, efficient model

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

4. Initialize database:
```bash
sqlite3 databases/interaction_logs.db < databases/schema.sql
```

5. Run the bot:
```bash
python bot.py
```

## ⚙️ Configuration

### Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENPIPE_API_KEY`: OpenPipe API key

### Configuration Files
- `config.py`: Main configuration settings
- `temperatures.json`: Model temperature settings
- `dynamic_prompts.json`: Custom prompts per channel
- `databases/interaction_logs.db`: SQLite database for conversation history

## 📝 Usage

### Slash Commands
- `/help`: Show comprehensive help information
- `/listmodels`: Show all available AI models
- `/set_system_prompt`: Set a custom system prompt for an AI agent
- `/reset_system_prompt`: Reset an AI agent's system prompt to default

### System Prompt Variables
When setting custom system prompts, you can use these variables:
- `{MODEL_ID}`: The AI model's name
- `{USERNAME}`: The user's Discord display name
- `{DISCORD_USER_ID}`: The user's Discord ID
- `{TIME}`: Current local time
- `{TZ}`: Local timezone
- `{SERVER_NAME}`: Current Discord server name
- `{CHANNEL_NAME}`: Current channel name

### Triggering Models
- **Random Model**: Mention the bot or use "splintertree" keyword
- **Specific Model**: Use model-specific triggers (e.g., "claude", "gemini", "grok", etc.)
- **Image Analysis**: Simply attach an image to your message
- **File Processing**: Attach .txt or .md files

### Examples
```
@Splintertree How does photosynthesis work?
splintertree explain quantum computing
claude what is the meaning of life?
gemini analyze this image [attached image]
grok tell me a joke

# Setting a custom system prompt
/set_system_prompt agent:Claude-3 prompt:"You are {MODEL_ID}, an expert in science communication. You're chatting with {USERNAME} in {SERVER_NAME}'s {CHANNEL_NAME} channel at {TIME} {TZ}."
```

## 🏗️ Architecture

### Core Components
- **Base Cog**: Foundation for all model implementations
- **Context Management**: SQLite-based conversation history
- **API Integration**: OpenRouter and OpenPipe connections
- **File Processing**: Handles various file types
- **Image Processing**: Vision model integration
- **Settings Management**: Handles dynamic system prompts

### Directory Structure
```
SplinterTreev4/
├── bot.py              # Main bot implementation
├── config.py           # Configuration settings
├── cogs/               # Model-specific implementations
│   ├── base_cog.py    # Base cog implementation
│   ├── context_cog.py # Context management
│   ├── settings_cog.py # Settings management
│   └── [model]_cog.py # Individual model cogs
├── databases/          # SQLite database
│   ├── schema.sql     # Database schema
│   └── interaction_logs.db # Conversation history
└── shared/            # Shared utilities
```

## 🔧 Development

### Adding New Models
1. Create a new cog file in `cogs/`
2. Inherit from `BaseCog`
3. Configure model-specific settings
4. The default system prompt template will be used

### Custom Prompts
Channel-specific prompts are stored in `dynamic_prompts.json`:
```json
{
  "guild_id": {
    "channel_id": "Custom system prompt with {MODEL_ID} and other variables"
  }
}
```

### Database Schema
The SQLite database includes tables for:
- `messages`: Stores all conversation messages
- `context_windows`: Stores per-channel context settings

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

For support or inquiries, use the `!contact` command in Discord or visit the contact card at https://sydney.gwyn.tel/contactcard
