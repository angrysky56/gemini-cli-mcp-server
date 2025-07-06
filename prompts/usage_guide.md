# Gemini CLI MCP Server Usage Guide

## Overview
This MCP server provides access to the user's pre-authenticated gemini-cli. The user must have gemini-cli installed and authenticated before using this server.

## Prerequisites
- User has gemini-cli installed (`npm install -g @google-ai/gemini-cli` or equivalent)
- User has authenticated with Google (API key, OAuth, or Vertex AI)
- gemini command is available in PATH

## Tool Usage

### 1. gemini_start_session
Start a new interactive session with Gemini CLI.

**Parameters:**
- `session_id` (required): Unique identifier for the session
- `starting_directory` (optional): Directory to start in (defaults to user's home directory)
- `auto_approve` (optional): Auto-approve tool executions (defaults to true)

**Example:**
```json
{
  "session_id": "main-session",
  "starting_directory": "/home/user/project",
  "auto_approve": true
}
```

### 2. gemini_session_chat
Send a message to an active session. Returns immediately with a task_id.

**Parameters:**
- `session_id` (required): The session to send the message to
- `message` (required): The prompt/message to send

**Example:**
```json
{
  "session_id": "main-session",
  "message": "Analyze the files in @src/ and suggest improvements"
}
```

### 3. gemini_check_task_status
Check the status of a background task.

**Parameters:**
- `task_id` (required): ID returned from gemini_session_chat

**Returns:**
- `RUNNING`: Task is still executing
- `COMPLETED`: Task finished successfully (includes result)
- `BLOCKED_ON_INTERACTION`: Task needs user input
- `ERROR`: Task failed

### 4. gemini_session_respond_to_interaction
Respond to interactive prompts when task is blocked.

**Parameters:**
- `task_id` (required): ID of the blocked task
- `response_text` (required): Response to send (e.g., "y", "n", specific answer)

### 5. gemini_close_session
Close an active session and clean up resources.

**Parameters:**
- `session_id` (required): Session to close

## Workflow Example

1. Start a session:
   ```
   gemini_start_session(session_id="work", starting_directory="/home/user/project")
   ```

2. Send a task:
   ```
   gemini_session_chat(session_id="work", message="Review @README.md and suggest improvements")
   ```
   → Returns task_id: "abc123"

3. Check progress:
   ```
   gemini_check_task_status(task_id="abc123")
   ```
   → Returns status and result when complete

4. For blocked tasks:
   ```
   gemini_session_respond_to_interaction(task_id="abc123", response_text="y")
   ```

5. Close when done:
   ```
   gemini_close_session(session_id="work")
   ```

## Important Notes

- **Authentication**: User must be pre-authenticated with gemini-cli
- **File Access**: Use `@file-path` or `@directory/` to include file content
- **Commands**: Use `/stats`, `/memory show`, `/tools` etc. for gemini-cli commands
- **Shell**: Use `!command` for shell commands within gemini
- **Timeouts**: Some tasks may take 10+ minutes - check status periodically
- **Persistence**: Sessions persist until explicitly closed or server restart

## Troubleshooting

- **"gemini command not found"**: Install and authenticate gemini-cli first
- **Session not ready**: Wait a moment after starting, gemini needs time to initialize
- **Task blocked**: Check for interactive prompts that need user response
- **Authentication errors**: Re-authenticate gemini-cli outside of MCP

## Best Practices

1. Use descriptive session IDs
2. Set appropriate starting directories for projects
3. Check task status regularly for long-running operations
4. Respond promptly to interactive prompts
5. Close sessions when done to free resources
6. Use auto_approve=true for MCP usage to reduce manual intervention
