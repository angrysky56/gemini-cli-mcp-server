# Gemini API MCP Server

A Model Context Protocol (MCP) server that provides direct access to Google Gemini API capabilities. This server enables Claude Desktop and other MCP clients to use Gemini models for text generation, code analysis, vision tasks, and model comparison.

## Features

🤖 **Direct API Access** - No CLI wrapping, uses Google Generative AI SDK directly
🔧 **Multiple Tools** - Text generation, file analysis, code review, vision analysis, model comparison
🎯 **Configurable** - Choose models, adjust temperature, set token limits
🖼️ **Vision Support** - Analyze images with Gemini's multimodal capabilities
⚡ **Async & Fast** - Non-blocking operations for better performance
🛡️ **Error Handling** - Comprehensive error handling and logging

## Prerequisites

### Google Gemini API Key

You need a Gemini API key from Google AI Studio:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or alternatively, you can use `GOOGLE_API_KEY` if you prefer.

## Installation

1. Clone this repository:
   ```bash
   cd /home/ty/Repositories/ai_workspace
   git clone <repository-url> gemini-cli-mcp-server
   cd gemini-cli-mcp-server
   ```

2. Set up Python environment with uv:
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate
   uv sync
   ```

## Configuration

### Claude Desktop Setup

Edit your Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

Add this server configuration:

```json
{
  "mcpServers": {
    "gemini-api": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server",
        "run",
        "python",
        "src/main.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop after making this change.

## Available Tools

### 🚀 gemini_generate
Generate text using any Gemini model with full parameter control.

**Parameters:**
- `prompt` (required): The text prompt
- `model`: Model to use (default: gemini-1.5-flash)
- `temperature`: Randomness control 0.0-2.0 (default: 1.0)
- `max_output_tokens`: Maximum tokens to generate (default: 2048)

**Available Models:**
- `gemini-2.0-flash-exp` - Latest experimental model
- `gemini-1.5-pro` - Most capable model
- `gemini-1.5-flash` - Fast and efficient
- `gemini-1.5-flash-8b` - Smallest and fastest

### 📄 gemini_analyze_file
Analyze any file using Gemini (supports both text and image files).

**Parameters:**
- `file_path` (required): Path to the file
- `analysis_prompt`: What to analyze (default: "Analyze this file and provide insights")
- `model`: Gemini model to use

### 🔍 gemini_compare_models  
Compare responses from multiple Gemini models for the same prompt.

**Parameters:**
- `prompt` (required): The prompt to test
- `models`: List of models to compare (default: ["gemini-1.5-flash", "gemini-1.5-pro"])
- `temperature`: Temperature setting for all models

### 🖼️ gemini_with_vision
Use Gemini's vision capabilities to analyze images.

**Parameters:**
- `image_path` (required): Path to image file
- `prompt`: What to analyze about the image (default: "Describe this image in detail")
- `model`: Vision-capable model to use

**Supported Image Formats:** JPG, JPEG, PNG, GIF, BMP, WebP

### 🧑‍💻 gemini_code_review
Perform comprehensive code review using Gemini.

**Parameters:**
- `file_path` (required): Path to code file
- `focus_areas`: Areas to focus on (default: ["code quality", "best practices", "potential bugs"])
- `model`: Model to use (default: gemini-1.5-pro)

## Usage Examples

### Basic Text Generation
```
Use gemini_generate with:
- prompt: "Explain quantum computing in simple terms"
- model: "gemini-1.5-pro"
- temperature: 0.7
```

### File Analysis
```
Use gemini_analyze_file with:
- file_path: "/path/to/script.py"
- analysis_prompt: "Review this code for security issues"
```

### Image Analysis
```
Use gemini_with_vision with:
- image_path: "/path/to/diagram.png"
- prompt: "Explain this architecture diagram"
```

### Model Comparison
```
Use gemini_compare_models with:
- prompt: "Write a Python function to calculate fibonacci numbers"
- models: ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
```

### Code Review
```
Use gemini_code_review with:
- file_path: "/path/to/component.tsx"
- focus_areas: ["performance", "accessibility", "React best practices"]
```

## Key Differences from CLI Wrapper Approach

This server provides **direct API access** rather than wrapping the CLI tool:

✅ **Advantages:**
- Much more reliable and faster
- Configurable parameters (temperature, tokens, models)
- Better error handling and debugging
- No complex session management
- Supports all file types including images
- Async/non-blocking operations

❌ **What it doesn't do:**
- It doesn't provide the interactive Gemini CLI session experience
- It doesn't include CLI-specific features like `/memory` or `/tools` commands
- It's focused on API capabilities rather than CLI workflow

## Troubleshooting

### Common Issues

**"API key not found"**
- Ensure `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set
- Verify the key is valid at [Google AI Studio](https://aistudio.google.com/)

**"Model not available"**
- Check the model name spelling
- Some models may not be available in your region
- Try using `gemini-1.5-flash` as a fallback

**"File not found"**
- Verify file paths are absolute or relative to where Claude Desktop runs
- Check file permissions

**"Image analysis fails"**
- Ensure image format is supported (JPG, PNG, GIF, BMP, WebP)
- Check image file isn't corrupted
- Try with a smaller image if very large

### Debug Mode

For detailed logging, check Claude Desktop logs:

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Linux:**
```bash
tail -f ~/.local/share/Claude/logs/mcp*.log
```

## Development

### Running Manually
```bash
source .venv/bin/activate
python src/main.py
```

### Testing Tools
You can test individual tools using the MCP inspector or by calling them directly through Claude Desktop.

### Project Structure
```
src/
├── main.py              # Main MCP server implementation
└── __init__.py          # Package initialization

archived/
└── gemini_cli_wrapper.py # Old CLI wrapper (archived)
```

## Performance Notes

- **Model Speed**: flash models are fastest, pro models are most capable
- **Temperature**: Lower values (0.1-0.5) for factual tasks, higher (0.8-1.5) for creative tasks
- **Token Limits**: Adjust `max_output_tokens` based on your needs
- **Vision Tasks**: Image analysis may take longer depending on image size

## Security Considerations

- API keys are passed through environment variables (secure)
- No data is stored locally (stateless server)
- Safety settings are configured to be permissive for development use
- All operations run with your API key quotas and billing

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! This server uses:
- **uv** for dependency management
- **asyncio** for async operations
- **google-generativeai** for API access
- **MCP SDK** for protocol implementation

Please test changes thoroughly and update documentation as needed.
