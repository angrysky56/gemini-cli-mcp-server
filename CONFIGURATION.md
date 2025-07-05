# Gemini CLI MCP Server - Configuration Examples

## Basic Usage with Auto-Approval (Default)

```python
# Start a session - auto-approval is enabled by default
await gemini_start_session({
    "session_id": "my_project",
    "starting_directory": "/home/user/project"
})

# Commands will execute without auth prompts
await gemini_session_chat({
    "session_id": "my_project", 
    "message": "Create a new Python file with a hello world function"
})
```

## Manual Approval Mode

```python
# Start a session with manual approval required
await gemini_start_session({
    "session_id": "secure_session",
    "starting_directory": "/home/user/sensitive_project",
    "auto_approve": False  # Require manual approval
})

# When a tool needs approval, you'll get BLOCKED_ON_INTERACTION status
# Then use gemini_session_respond_to_interaction to approve/deny
```

## Environment Variables

You can also control behavior through environment variables:

```bash
# Set default behavior (optional)
export GEMINI_MCP_AUTO_APPROVE=true  # or false

# Run the MCP server
python -m src.main
```

## Example Claude Usage Pattern

```python
# 1. Start session
response = await use_mcp_tool(
    server_name="gemini-cli-mcp-server",
    tool_name="gemini_start_session",
    arguments={
        "session_id": "code_review",
        "starting_directory": "/home/ty/project"
    }
)

# 2. Send a command
response = await use_mcp_tool(
    server_name="gemini-cli-mcp-server",
    tool_name="gemini_session_chat",
    arguments={
        "session_id": "code_review",
        "message": "Review the main.py file and suggest improvements"
    }
)

# 3. Extract task_id from response
task_id = json.loads(response)["task_id"]

# 4. Poll for completion
while True:
    status_response = await use_mcp_tool(
        server_name="gemini-cli-mcp-server",
        tool_name="gemini_check_task_status",
        arguments={"task_id": task_id}
    )
    
    status = json.loads(status_response)
    if status["status"] == "COMPLETE":
        print(status["result"])
        break
    elif status["status"] == "ERROR":
        print(f"Error: {status['result']}")
        break
    elif status["status"] == "BLOCKED_ON_INTERACTION":
        # Handle if needed (won't happen with auto_approve=True)
        pass
    
    await asyncio.sleep(5)  # Wait before polling again
```

## Debugging Tips

1. Check server logs in stderr for detailed information
2. Use `debug=True` when starting sessions for verbose output
3. If responses seem incomplete, increase polling frequency
4. For long-running tasks, ensure client connection stays alive

## Security Notes

- Auto-approval means ALL tool executions are approved automatically
- Only use auto-approval in trusted environments
- Consider using manual approval for production or sensitive operations
- The --yolo flag is passed internally when auto_approve=True
