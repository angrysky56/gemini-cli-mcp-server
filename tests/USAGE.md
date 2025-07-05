# Gemini CLI MCP Server - Usage Example

## Setup Instructions

1. **Install dependencies:**
```bash
cd /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server
uv sync  # or pip install -r requirements.txt
```

2. **Configure Gemini CLI to use this MCP server:**

Create or edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "gemini-cli-tools": {
      "command": "python3",
      "args": ["/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server/src/main.py"],
      "cwd": "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server",
      "timeout": 30000,
      "trust": false
    }
  }
}
```

Or for project-specific usage, create `.gemini/settings.json` in your project:

```json
{
  "mcpServers": {
    "gemini-cli-tools": {
      "command": "python3",
      "args": ["/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server/src/main.py"],
      "cwd": "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server",
      "timeout": 30000
    }
  }
}
```

## Available Tools

### 1. gemini_chat
Start an interactive chat session with Gemini AI
- **message** (required): Initial message to send to Gemini
- **working_directory** (optional): Working directory for the chat session

### 2. gemini_analyze_code  
Analyze code in a directory using Gemini AI
- **directory** (required): Directory containing code to analyze
- **query** (required): Specific analysis query or task

### 3. gemini_generate_app
Generate a new application using Gemini AI
- **description** (required): Description of the application to generate
- **output_directory** (required): Directory where the app should be generated
- **framework** (optional): Framework preference (e.g., React, Flask, etc.)

### 4. gemini_code_assist
Get AI assistance for specific code problems
- **file_path** (required): Path to the file needing assistance
- **task** (required): What you want help with (e.g., 'fix bugs', 'optimize', 'add tests')

### 5. gemini_git_assist
Get AI assistance with Git operations and analysis
- **repository_path** (required): Path to the Git repository
- **operation** (required): Git operation or analysis (e.g., 'analyze recent changes', 'help with merge conflict')

### 6. gemini_list_models
List available Gemini models from Google's API
- **api_key** (optional): Gemini API key (optional if set in environment)

## Example Usage

After configuring Gemini CLI, you can use natural language prompts like:

```bash
# Start Gemini CLI
gemini

# Then use prompts like:
> "Use the gemini tools to analyze the code in ./src and tell me about potential improvements"
> "Generate a React app for a todo list in ./my-new-app"
> "Help me fix the bugs in ./src/main.py focusing on error handling"
> "Analyze my git repository in ./my-project and suggest next steps"
> "List all available Gemini models"
```

## Testing

Run the validation script to ensure schemas are compatible:

```bash
cd /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server
python3 validate_schemas.py
```

## Troubleshooting

1. **Schema validation errors**: Run `python3 validate_schemas.py` to check schema compatibility
2. **Connection issues**: Check that the paths in your settings.json are correct
3. **Permission errors**: Ensure the Python script is executable and dependencies are installed
4. **Tool not found**: Verify the MCP server is properly configured in your Gemini CLI settings

## What Was Fixed

✅ Added `additionalProperties: false` to all tool schemas for Gemini CLI compatibility  
✅ Improved parameter validation with proper error handling  
✅ Fixed required vs optional parameter definitions  
✅ Added proper default values for optional parameters  
✅ Enhanced error messages for better debugging  
✅ Added comprehensive type and value validation  

The server now fully complies with Gemini CLI's schema requirements and automatic sanitization process.
