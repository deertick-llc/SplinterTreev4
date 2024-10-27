# 🌳 Splintertree v4

A powerful Discord bot that provides access to multiple AI language models with advanced features like conversation memory, image processing, and dynamic prompting.

## ✨ Features

### Core Features
- **Multi-Model Support**: Access to various AI models through OpenRouter and OpenPipe
- **Shared Message History**: Models maintain conversation context within channels
- **Image Processing**: Automatic image description and analysis
- **File Handling**: Support for text files and images
- **Response Reroll**: Button to generate alternative responses
- **Emotion Analysis**: Reactions based on message sentiment
- **Status Updates**: Rotating status showing uptime, last interaction, and current model

### Special Capabilities
- **Vision Processing**: Direct image analysis with compatible models
- **Context Management**: Per-channel message history with configurable window size
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

## ⚙️ Configuration

### Environment Variables
- `DISCORD_TOKEN`: Your Discord bot token
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENPIPE_API_KEY`: OpenPipe API key

### Configuration Files
- `config.py`: Main configuration settings
- `temperatures.json`: Model temperature settings
- `dynamic_prompts.json`: Custom prompts per channel
- `context_windows.json`: Context window sizes

## 📝 Usage

### Basic Commands
- `!splintertree_help [channel|dm]`: Show help information
- `!toggle_shared_history`: Toggle shared message history
- `!toggle_image_processing`: Toggle image processing
- `!contact`: Show contact information

### Triggering Models
- **Random Model**: Mention the bot or use "splintertree" keyword
- **Specific Model**: Use model-specific triggers (e.g., "claude", "gemini", etc.)
- **Image Analysis**: Simply attach an image to your message
- **File Processing**: Attach .txt or .md files

### Examples
```
@Splintertree How does photosynthesis work?
splintertree explain quantum computing
claude what is the meaning of life?
gemini analyze this image [attached image]
```

## 🏗️ Architecture

### Core Components
- **Base Cog**: Foundation for all model implementations
- **Context Management**: Handles conversation history
- **API Integration**: OpenRouter and OpenPipe connections
- **File Processing**: Handles various file types
- **Image Processing**: Vision model integration

### Directory Structure
```
SplinterTreev4/
├── bot.py              # Main bot implementation
├── config.py           # Configuration settings
├── cogs/               # Model-specific implementations
│   ├── base_cog.py    # Base cog implementation
│   └── [model]_cog.py # Individual model cogs
├── prompts/            # System prompts
├── shared/            # Shared utilities
└── history/           # Conversation history storage
```

## 🔧 Development

### Adding New Models
1. Create a new cog file in `cogs/`
2. Inherit from `BaseCog`
3. Configure model-specific settings
4. Add system prompt to `prompts/consolidated_prompts.json`

### Custom Prompts
Create channel-specific prompts in `dynamic_prompts.json`:
```json
{
  "channel_id": {
    "prompt": "Custom system prompt for this channel"
  }
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

For support or inquiries, use the `!contact` command in Discord or visit the contact card at https://sydney.gwyn.tel/contactcard