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
- ✅ **Asynchronous task execution** for long-running operations

## 🚫 What This Does NOT Do (Unlike Broken Implementations)

- ❌ Create a separate API client that bypasses gemini-cli
- ❌ Require separate API key management for the MCP server itself
- ❌ Lose contextual conversation abilities
- ❌ Miss built-in tools and capabilities
- ❌ Recreate functionality that gemini-cli already provides

## Prerequisites

1.  **Gemini CLI must be installed and working:**
    ```bash
    npm install -g @google/gemini-cli
    gemini --version  # Verify it works
    ```

2.  **Gemini CLI must be authenticated:**
    -   Run `gemini` once and complete the authentication flow.
    -   Use either "Login with Google" (recommended for free tier) or API key.
    -   **This MCP server does NOT require its own API key.** It relies on your `gemini-cli`'s existing authentication.

3.  **Python 3.12+ with uv:**
    ```bash
    uv --version  # Should be available
    ```

## Installation

1.  **Clone and setup:**
    ```bash
    cd /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server
    uv venv --python 3.12 --seed
    source .venv/bin/activate
    uv sync
    ```

2.  **Test the server:**
    ```bash
    python src/main.py
    ```

## Usage Patterns

### Interactive Sessions (Recommended for All Tasks)

All interactions with a Gemini CLI session are now asynchronous. When you send a message or command, the server will immediately return a `task_id` and an estimated completion time. You then use `gemini_check_task_status` to retrieve the result.

```json
// 1. Start a new session
{
  "tool": "gemini_start_session", 
  "arguments": {
    "session_id": "my_coding_project"
  }
}

// Expected response:
// "Interactive session my_coding_project started successfully"

// 2. Send a message/prompt to the session (e.g., a complex analysis)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project", 
    "message": "Analyze the main.py file and suggest improvements for performance and readability. Provide code examples."
  }
}

// Expected response (example):
/*
{
  "status": "STARTED",
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "estimated_completion": "10-30+ minutes",
  "note": "Please use gemini_check_task_status with the returned task_id to get the result. Recommended check time is in 10-30+ minutes. IMPORTANT: This is a long-running task. Do not close the chat or client connection, as it will terminate the process."
}
*/

// 3. Check the status of the task (poll periodically based on estimated_completion)
{
  "tool": "gemini_check_task_status",
  "arguments": {
    "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
  }
}

// Expected response while running:
/*
{
  "status": "RUNNING"
}
*/

// Expected response when complete:
/*
{
  "status": "COMPLETE",
  "result": "..." // The full response from gemini-cli
}
*/

// 4. Include files dynamically (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "Review these files for security vulnerabilities: @src/auth.py @src/database.py"
  }
}

// 5. Run shell commands (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "!ls -la /home/ty/Repositories/ai_workspace/gemini-cli-mcp-server"
  }
}

// 6. Manage memory (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "/memory add User prefers Python for backend development."
  }
}

// 7. Get available tools (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "/tools"
  }
}

// 8. Get session statistics (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "/stats"
  }
}

// 9. Compress conversation context (also returns a task_id)
{
  "tool": "gemini_session_chat",
  "arguments": {
    "session_id": "my_coding_project",
    "message": "/compress"
  }
}

// 10. Close the session when done
{
  "tool": "gemini_close_session",
  "arguments": {"session_id": "my_coding_project"}
}
```

## Configuration for Claude Desktop

Add this to your MCP configuration file (e.g., `~/.gemini/settings.json` or a project-specific `.gemini/settings.json`):

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
        "LOG_LEVEL": "INFO"
      },
      "timeout": 60000,
      "trust": false
    }
  }
}
```

## Architecture Benefits

This implementation is **correct** because it:

1.  **Respects the user's setup** - Uses existing `gemini-cli` auth and config.
2.  **Preserves all capabilities** - Nothing is lost from the original CLI.
3.  **Maintains context** - Interactive sessions keep conversation history.
4.  **Leverages built-ins** - All the sophisticated tools and ReAct loops work.
5.  **Handles complexity** - Multi-step workflows, file operations, shell commands.
6.  **Stays updated** - Benefits from `gemini-cli` improvements automatically.
7.  **Enables Asynchronous Workflows** - Allows long-running tasks to execute in the background without blocking the client.

## Troubleshooting

**"Gemini CLI not found"**
-   Install: `npm install -g @google/gemini-cli`
-   Verify: `which gemini` and `gemini --version`

**"Session did not become ready"**  
-   Gemini CLI may still be authenticating.
-   Try running `gemini` manually first to complete auth flow.

**"Authentication required"**
-   Run `gemini` once and complete the auth process.
-   This MCP server uses your existing authentication.

## Development

The key insight is that this MCP server acts as a **bridge** to `gemini-cli` rather than **replacing** it. This preserves all the sophisticated capabilities while making them available through the MCP protocol.

For extending functionality, consider:
1.  Adding new tools that combine multiple `gemini-cli` commands.
2.  Session management features (save/restore, branching).
3.  Workflow automation using the interactive session capabilities.

## Why This Approach Matters

Previous implementations tried to bypass `gemini-cli` and create direct API clients. This fails because:

1.  **Missing the ReAct loop** - Gemini CLI's sophisticated reasoning patterns.
2.  **No built-in tools** - File operations, shell commands, web search, etc.
3.  **Lost context management** - `GEMINI.md` files, memory, persistent sessions.
4.  **Authentication complexity** - Separate setup instead of using existing config.
5.  **Feature lag** - Manual recreation of features instead of automatic benefits.

This implementation **correctly** leverages the `gemini-cli` binary as intended.