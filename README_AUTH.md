# Authentication and Tool Approval in Gemini CLI MCP Server

## Overview

The Gemini CLI MCP Server now includes improved handling for tool execution approvals and authentication prompts. This document explains how to configure and use these features.

## Auto-Approval for Tool Execution

When Gemini CLI executes tools (like file operations, shell commands, etc.), it normally asks for user approval. In an MCP server context, this can interrupt the workflow. We've implemented several solutions:

### 1. Default Auto-Approval (Recommended)

By default, when starting a session through the MCP server, auto-approval is enabled. This means:
- Tool executions will be automatically approved
- You won't see authentication prompts blocking your tasks
- The session runs with the `--yolo` flag internally for smooth operation

### 2. Manual Control

You can control auto-approval when starting a session:

```json
{
  "tool": "gemini_start_session",
  "arguments": {
    "session_id": "my_session",
    "auto_approve": false  // Set to false to require manual approval
  }
}
```

### 3. Handling Interactive Prompts

If auto-approval is disabled or if other interactive prompts appear:

1. Check task status:
```json
{
  "tool": "gemini_check_task_status",
  "arguments": {
    "task_id": "your-task-id"
  }
}
```

2. If status is `BLOCKED_ON_INTERACTION`, respond:
```json
{
  "tool": "gemini_session_respond_to_interaction",
  "arguments": {
    "task_id": "your-task-id",
    "response_text": "y"  // or appropriate response
  }
}
```

## Improved Response Cleaning

The server now better filters out:
- Unicode box-drawing characters (└ ─ │ etc.)
- Interface elements from Gemini CLI
- Status messages and prompts
- ANSI escape codes

This ensures you get clean, readable responses without interface artifacts.

## Best Practices

1. **For Development/Testing**: Use default auto-approval for smooth workflow
2. **For Production**: Consider your security requirements - you may want manual approval for sensitive operations
3. **Session Management**: Close sessions when done to free resources
4. **Error Handling**: Always check task status before assuming completion

## Troubleshooting

### Tasks Stuck in RUNNING State
- Check if Gemini CLI is waiting for approval
- Use `gemini_check_task_status` to see if it's blocked
- Consider enabling auto-approval

### Weird Characters in Output
- The improved Unicode filtering should handle this
- Report any remaining issues with specific examples

### Authentication Errors
- Ensure Gemini CLI is properly authenticated before starting MCP server
- Check if your API key or auth method is correctly configured

## Security Considerations

Auto-approval means Gemini CLI will execute all tools without asking. Ensure:
- You trust the prompts being sent
- The MCP server is only accessible by trusted clients
- Consider the scope of operations Gemini CLI can perform

For maximum security, disable auto-approval and handle each prompt manually.
