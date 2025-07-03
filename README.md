# Gemini CLI MCP Server

An MCP (Model Context Protocol) server that exposes the powerful functionality of Google's Gemini CLI to other MCP clients like Claude Desktop. This enables seamless integration of Gemini's AI capabilities, code analysis, and development tools into your workflow.

## 🌟 Features

- **AI-Powered Chat**: Interactive chat sessions with Gemini AI
- **Code Analysis**: Intelligent code analysis and insights
- **App Generation**: Generate new applications from descriptions
- **Code Assistance**: Get AI help for specific code problems
- **Git Integration**: AI-assisted Git operations and analysis
- **Multi-modal Capabilities**: Leverage Gemini's ability to work with text, code, and images

## Check out the project wikis for further guidance and ideas!

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (for Gemini CLI)
- A Google account or Gemini API key

### Installation

1. **Clone and set up the project:**
   ```bash
   cd /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server
   source .venv/bin/activate
   uv add mcp
   ```

2. **Test the server:**
   ```bash
   python src/main.py
   ```

### Claude Desktop Integration

Add this configuration to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-cli": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server",
        "run",
        "python",
        "src/main.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## 🛠️ Available Tools

### 1. **gemini_chat**
Start an interactive chat session with Gemini AI.

**Parameters:**
- `message` (required): Initial message to send to Gemini
- `working_directory` (optional): Working directory for the chat session

**Example:**
```
Help me understand this codebase structure
```

### 2. **gemini_analyze_code**
Analyze code in a directory using Gemini AI.

**Parameters:**
- `directory` (required): Directory containing code to analyze
- `query` (required): Specific analysis query or task

**Example:**
```
Directory: ./my-project
Query: Find potential security vulnerabilities
```

### 3. **gemini_generate_app**
Generate a new application using Gemini AI.

**Parameters:**
- `description` (required): Description of the application to generate
- `output_directory` (required): Directory where the app should be generated
- `framework` (optional): Framework preference (e.g., React, Flask, etc.)

**Example:**
```
Description: A todo app with user authentication
Output Directory: ./new-todo-app
Framework: React
```

### 4. **gemini_code_assist**
Get AI assistance for specific code problems.

**Parameters:**
- `file_path` (required): Path to the file needing assistance
- `task` (required): What you want help with

**Example:**
```
File Path: ./src/main.py
Task: Optimize this code for better performance
```

### 5. **gemini_list_models**
List available Gemini models from Google's API.

**Parameters:**
- `api_key` (optional): Gemini API key (uses environment variable if not provided)

**Example:**
```
# Uses GEMINI_API_KEY from environment
List available models

# Or specify API key directly
List models with api_key: your_key_here
```

### 6. **gemini_git_assist**
Get AI assistance with Git operations and analysis.

**Parameters:**
- `repository_path` (required): Path to the Git repository
- `operation` (required): Git operation or analysis

**Example:**
```
Repository Path: ./my-repo
Operation: Analyze recent changes and suggest improvements
```

## 📊 Available Resources

### **gemini://status**
Get current status and configuration of Gemini CLI.

### **gemini://help**
Get help information for Gemini CLI commands.

## 🔧 Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Gemini API key (get one from [Google AI Studio](https://aistudio.google.com/apikey))
- `LOG_LEVEL`: Logging level (default: INFO)

### Authentication

The server supports multiple authentication methods:

1. **API Key**: Set `GEMINI_API_KEY` environment variable
2. **Google Account**: The Gemini CLI will prompt for authentication
3. **Google Workspace**: Follow the Gemini CLI authentication guide

## 🧪 Development

### Running in Development Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Install development dependencies
uv add --dev pytest pytest-asyncio ruff mypy

# Run the server
python src/main.py

# Run tests
pytest

# Format code
ruff format .

# Type checking
mypy src/
```

### Testing with MCP Inspector

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server run python src/main.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Gemini CLI not found**: Make sure Node.js 18+ is installed
2. **Authentication errors**: Ensure your API key is valid or complete the authentication flow
3. **Permission errors**: Check that the working directories are accessible

### Debugging

- Check logs in stderr for detailed error information
- Use `LOG_LEVEL=DEBUG` for more verbose logging
- Test Gemini CLI directly: `npx https://github.com/google-gemini/gemini-cli`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🔗 Related Projects

- [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) - The underlying Gemini CLI tool
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification and documentation
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP servers collection

## ⚡ Advanced Usage

### Custom Prompts

You can create custom prompts by combining multiple tools:

1. Use `gemini_analyze_code` to understand a codebase
2. Use `gemini_code_assist` to get specific help
3. Use `gemini_generate_app` to create related components

### Integration with Other Tools

This MCP server works well with other MCP servers:

- Combine with file system servers for comprehensive project management
- Use with Git servers for advanced version control workflows
- Integrate with database servers for full-stack development assistance

### Performance Tips

- Use specific working directories to limit context size
- Break complex tasks into smaller, focused queries
- Cache API responses when appropriate for development workflows

---

**Note**: This MCP server requires an active internet connection and valid Gemini API credentials to function properly.
