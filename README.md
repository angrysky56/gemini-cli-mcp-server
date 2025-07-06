# Gemini CLI MCP Server

A Model Context Protocol (MCP) server that provides access to your pre-authenticated gemini-cli, enabling seamless integration with Claude Desktop and other MCP clients.

## Prerequisites

### 1. Install and Authenticate Gemini CLI

**Important**: You must have gemini-cli installed and authenticated before using this MCP server.

#### Install Gemini CLI
```bash
npm install -g @google-ai/gemini-cli
```

#### Authenticate (choose one method)

**Option A: API Key** (Recommended)
```bash
export GEMINI_API_KEY="your-api-key-here"
```
Get your API key from: https://aistudio.google.com/app/apikey

**Option B: Google Login (OAuth)**
```bash
gemini  # First run will prompt for authentication
```

**Option C: Vertex AI**
```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_GENAI_USE_VERTEXAI=true
```

### 2. Verify Installation
```bash
gemini --version
gemini -p "Hello world"  # Test that authentication works
```

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd gemini-cli-mcp-server
   ```

2. Set up Python environment:
   ```bash
   uv venv --python 3.12 --seed
   source .venv/bin/activate
   uv sync
   ```

## Configuration

### Claude Desktop Setup

1. Edit your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. Add this server configuration:
   ```json
   {
     "mcpServers": {
       "gemini-cli": {
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/gemini-cli-mcp-server",
           "run",
           "python",
           "src/main.py"
         ],
         "env": {
           "LOG_LEVEL": "INFO"
         },
         "timeout": 60000
       }
     }
   }
   ```

3. Replace `/path/to/gemini-cli-mcp-server` with the actual path to this repository.

4. Restart Claude Desktop.

## Available Tools

### 🚀 gemini_start_session
Start a new interactive Gemini CLI session.

**Parameters:**
- `session_id` (required): Unique identifier for the session
- `starting_directory` (optional): Directory to start in (defaults to home directory)
- `auto_approve` (optional): Auto-approve tool executions (default: true)

### 💬 gemini_session_chat
Send a message to an active session. Returns immediately with a task_id for monitoring.

**Parameters:**
- `session_id` (required): The session to send the message to
- `message` (required): The prompt/message to send to Gemini

### 📊 gemini_check_task_status
Check the status of a background task and retrieve results when complete.

**Parameters:**
- `task_id` (required): ID returned from gemini_session_chat

**Possible Statuses:**
- `RUNNING`: Task is still executing
- `COMPLETED`: Task finished successfully (includes result)
- `BLOCKED_ON_INTERACTION`: Task needs user input
- `ERROR`: Task failed

### 🔄 gemini_session_respond_to_interaction
Respond to interactive prompts when a task is blocked.

**Parameters:**
- `task_id` (required): ID of the blocked task
- `response_text` (required): Response to send (e.g., "y", "n", or specific answer)

### 🛑 gemini_close_session
Close an active session and clean up resources.

**Parameters:**
- `session_id` (required): Session identifier to close

## Usage Examples

### Basic Workflow

1. **Start a session**:
   ```
   Use gemini_start_session with:
   - session_id: "main"
   - starting_directory: "/home/user/project"
   ```

2. **Send a task**:
   ```
   Use gemini_session_chat with:
   - session_id: "main"
   - message: "Analyze the files in @src/ and suggest improvements"
   ```
   → Returns task_id: "abc123"

3. **Check progress**:
   ```
   Use gemini_check_task_status with:
   - task_id: "abc123"
   ```

4. **Handle interactions** (if needed):
   ```
   Use gemini_session_respond_to_interaction with:
   - task_id: "abc123"
   - response_text: "y"
   ```

5. **Close session**:
   ```
   Use gemini_close_session with:
   - session_id: "main"
   ```

### Working with Files

Use Gemini CLI's `@` syntax to include file content:
```
"Analyze this code: @app.py"
"Review all files in @src/ and suggest improvements"
"Compare @old-version.py with @new-version.py"
```

### Gemini CLI Commands

You can use any Gemini CLI command:
```
"/stats"           # Show session statistics
"/memory show"     # Display current memory
"/tools"           # List available tools
"/chat save backup" # Save conversation state
"!ls -la"          # Execute shell commands
```

## Key Features

- **Pre-authenticated**: Uses your existing gemini-cli authentication
- **Persistent sessions**: Sessions stay active until explicitly closed
- **Asynchronous**: Long-running tasks don't block the interface
- **Interactive support**: Handles prompts that require user input
- **File integration**: Full support for `@file-path` syntax
- **Auto-approval**: Optional auto-approval for seamless operation

## Troubleshooting

### Common Issues

**"gemini command not found"**
- Install gemini-cli: `npm install -g @google-ai/gemini-cli`
- Check PATH: `which gemini`

**Authentication errors**
- Verify authentication: `gemini -p "test"`
- Check environment variables (GEMINI_API_KEY, etc.)
- Re-authenticate if needed

**Session won't start**
- Verify gemini works manually
- Check starting directory exists
- Try home directory first

**Tasks stuck running**
- Some tasks take 10+ minutes for complex analysis
- Check for interactive prompts (BLOCKED_ON_INTERACTION status)
- Be patient with large file analysis

### Debug Mode

For detailed logs, set:
```json
"env": {
  "LOG_LEVEL": "DEBUG"
}
```

Check Claude Desktop logs:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Performance Notes

- **Task Duration**: Simple commands take seconds, complex analysis can take 10+ minutes
- **Memory Usage**: Each session uses modest memory, clean up when done
- **File Access**: Large directories may take time to analyze
- **Concurrent Sessions**: Multiple sessions supported but use resources

## Security Considerations

- Auto-approval (`--yolo`) executes tools without confirmation
- Sessions run with your user permissions
- Use `auto_approve=false` for sensitive operations
- Close sessions when done to free resources

## Development

### Running Manually
```bash
uv run python src/main.py
```

### Project Structure
```
src/
├── main.py              # MCP server implementation
└── gemini_cli_wrapper.py # Gemini CLI interface
prompts/
├── usage_guide.md       # Detailed usage instructions
└── troubleshooting.md   # Common issues and solutions
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Test your changes with real gemini-cli
2. Update documentation
3. Follow existing code style
4. Add appropriate error handling
