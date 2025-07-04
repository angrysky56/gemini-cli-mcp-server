# Gemini CLI MCP Server

A **proper** Model Context Protocol (MCP) server that provides access to Google's Gemini CLI with all its built-in capabilities and tools.

## 🎯 What This Does RIGHT

This MCP server **correctly** wraps the actual `gemini` command-line tool, preserving all of its sophisticated features:

- ✅ **Uses your existing gemini-cli authentication** (Google login or API key)
- ✅ **Leverages all built-in tools** (file reading, shell commands, web search, etc.)
- ✅ **Maintains conversation context** through interactive sessions
- ✅ **Supports `@` file inclusion** and `!` shell command syntax  
- ✅ **Access to `/memory`, `/tools`, `/stats`** and other CLI commands
- ✅ **Preserves ReAct loops** and sophisticated reasoning capabilities
- ✅ **Checkpointing and debugging** support
- ✅ **MCP server discovery** via `/mcp` command

## 🚫 What This Does NOT Do (Unlike Broken Implementations)

- ❌ Create a separate API client that bypasses gemini-cli
- ❌ Require separate API key management  
- ❌ Lose contextual conversation abilities
- ❌ Miss built-in tools and capabilities
- ❌ Recreate functionality that gemini-cli already provides

## Prerequisites

1. **Gemini CLI must be installed and working:**
   ```bash
   npm install -g @google/gemini-cli
   gemini --version  # Verify it works
   ```

2. **Gemini CLI must be authenticated:**
   - Run `gemini` once and complete the authentication flow
   - Use either "Login with Google" (recommended for free tier) or API key
   - No additional authentication needed for this MCP server

3. **Python 3.12+ with uv:**
   ```bash
   uv --version  # Should be available
   ```

## Installation

1. **Clone and setup:**
   ```bash
   cd /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server
   uv venv --python 3.12 --seed
   source .venv/bin/activate
   uv sync
   ```

2. **Test the server:**
   ```bash
   python src/main.py
   ```

## Usage Patterns

### 1. Single Prompts (Non-Interactive)
```json
{
  "tool": "gemini_prompt",
  "arguments": {
    "prompt": "Explain this codebase",
    "include_files": ["src/main.py", "README.md"],
    "working_directory": "/path/to/project",
    "model": "gemini-2.5-pro",
    "checkpointing": true
  }
}
```

### 2. Interactive Sessions (Recommended for Complex Tasks)
```json
// Start session
{
  "tool": "gemini_start_session", 
  "arguments": {
    "session_id": "coding_session_1",
    "working_directory": "/path/to/project",
    "checkpointing": true
  }
}

// Chat with context
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "coding_session_1", 
    "message": "Analyze the main.py file and suggest improvements"
  }
}

// Include files dynamically
{
  "tool": "gemini_session_include_files",
  "arguments": {
    "session_id": "coding_session_1",
    "files": ["src/components/*.py", "tests/test_*.py"]
  }
}

// Run shell commands
{
  "tool": "gemini_session_shell",
  "arguments": {
    "session_id": "coding_session_1",
    "command": "pytest tests/ -v"
  }
}

// Save important info to memory
{
  "tool": "gemini_session_memory",
  "arguments": {
    "session_id": "coding_session_1",
    "action": "add",
    "text": "User prefers TypeScript with strict mode enabled"
  }
}

// Close when done
{
  "tool": "gemini_close_session",
  "arguments": {"session_id": "coding_session_1"}
}
```

### 3. Discovery and Status
```json
// List all built-in tools
{"tool": "gemini_list_tools"}

// List configured MCP servers  
{"tool": "gemini_list_mcp_servers"}

// Get session statistics
{"tool": "gemini_session_stats", "arguments": {"session_id": "coding_session_1"}}
```

## Configuration for Claude Desktop

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "gemini-cli": {
      "command": "python",
      "args": ["/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server/src/main.py"],
      "cwd": "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server",
      "env": {
        "PATH": "/home/ty/Repositories/ai_workspace/gemini-cli-mcp-server/.venv/bin:${PATH}"
      }
    }
  }
}
```

## Architecture Benefits

This implementation is **correct** because it:

1. **Respects the user's setup** - Uses existing gemini-cli auth and config
2. **Preserves all capabilities** - Nothing is lost from the original CLI
3. **Maintains context** - Interactive sessions keep conversation history
4. **Leverages built-ins** - All the sophisticated tools and ReAct loops work
5. **Handles complexity** - Multi-step workflows, file operations, shell commands
6. **Stays updated** - Benefits from gemini-cli improvements automatically

## Troubleshooting

**"Gemini CLI not found"**
- Install: `npm install -g @google/gemini-cli`
- Verify: `which gemini` and `gemini --version`

**"Session did not become ready"**  
- Gemini CLI may still be authenticating
- Try running `gemini` manually first to complete auth flow

**"Authentication required"**
- Run `gemini` once and complete the auth process
- This MCP server uses your existing authentication

## Development

The key insight is that this MCP server acts as a **bridge** to gemini-cli rather than **replacing** it. This preserves all the sophisticated capabilities while making them available through the MCP protocol.

For extending functionality, consider:
1. Adding new tools that combine multiple gemini-cli commands
2. Session management features (save/restore, branching)
3. Workflow automation using the interactive session capabilities

## Why This Approach Matters

Previous implementations tried to bypass gemini-cli and create direct API clients. This fails because:

1. **Missing the ReAct loop** - Gemini CLI's sophisticated reasoning patterns
2. **No built-in tools** - File operations, shell commands, web search, etc.
3. **Lost context management** - GEMINI.md files, memory, persistent sessions
4. **Authentication complexity** - Separate setup instead of using existing config
5. **Feature lag** - Manual recreation of features instead of automatic benefits

This implementation **correctly** leverages the gemini-cli binary as intended.
