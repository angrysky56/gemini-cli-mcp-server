# Gemini CLI MCP Server Troubleshooting

## Common Issues and Solutions

### 1. "gemini command not found in PATH"

**Problem**: The MCP server can't find the gemini-cli command.

**Solutions:**
- Install gemini-cli: `npm install -g @google-ai/gemini-cli`
- Check PATH: `which gemini` should return a path
- Restart terminal after installation
- Ensure npm global bin is in PATH

### 2. Authentication Issues

**Problem**: Gemini CLI reports authentication errors.

**Solutions:**
- Run `gemini` manually first to authenticate
- Check environment variables (GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT, etc.)
- Re-authenticate: `gemini /auth` to change auth method
- For API key: Set GEMINI_API_KEY environment variable
- For OAuth: Complete browser login flow outside MCP

### 3. Session Won't Start

**Problem**: `gemini_start_session` fails or times out.

**Solutions:**
- Verify gemini works manually: `gemini --version`
- Check starting directory exists and is accessible
- Try without auto_approve first
- Check logs in Claude Desktop for specific errors
- Restart Claude Desktop to clear any stuck processes

### 4. Tasks Get Stuck "RUNNING"

**Problem**: Tasks never complete, stuck in RUNNING status.

**Solutions:**
- Check if task needs interactive input (status will show BLOCKED_ON_INTERACTION)
- Some analysis tasks can take 10+ minutes - be patient
- For very long tasks, gemini may need user approval for tool executions
- Try setting auto_approve=false and respond to prompts manually

### 5. "Session not ready" or "Session no longer alive"

**Problem**: Session dies unexpectedly or never becomes ready.

**Solutions:**
- Wait 30-60 seconds after starting session before sending messages
- Check if gemini process crashed (look at stderr logs)
- Restart session with new session_id
- Verify directory permissions for starting_directory
- Try starting in home directory first

### 6. Interactive Prompts Not Working

**Problem**: Can't respond to BLOCKED_ON_INTERACTION tasks.

**Solutions:**
- Use exact response expected (usually "y", "n", or specific text)
- Check the prompt text in the status response for guidance
- Some prompts may timeout - restart task if needed
- Try responding through the gemini CLI directly first to understand expected responses

### 7. File Access Issues with @-syntax

**Problem**: `@file-path` doesn't work or files not found.

**Solutions:**
- Use absolute paths: `@/full/path/to/file`
- Check file permissions and existence
- Ensure gemini is running in correct directory
- Use `@./relative-path` for relative paths from working directory
- For directories, use `@directory/` with trailing slash

### 8. High Memory Usage or Process Leaks

**Problem**: Multiple gemini processes accumulating.

**Solutions:**
- Always close sessions when done: `gemini_close_session`
- Restart Claude Desktop periodically
- Check for zombie processes: `ps aux | grep gemini`
- Kill stuck processes manually if needed: `pkill -f gemini`

### 9. MCP Server Won't Start

**Problem**: Server fails to start in Claude Desktop.

**Solutions:**
- Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
- Verify uv is installed and working: `which uv`
- Check file paths in config are correct
- Ensure Python dependencies are installed: `uv sync`
- Try running server manually: `uv run python src/main.py`

### 10. Slow Response Times

**Problem**: Tasks take very long to complete.

**Solutions:**
- Large file analysis inherently takes time
- Break large tasks into smaller chunks
- Use gemini-cli commands like `/compress` to reduce context
- Consider using non-interactive mode for simple queries
- Check internet connection for API calls

## Debugging Steps

1. **Test gemini-cli directly**:
   ```bash
   gemini --version
   gemini -p "Hello, test message"
   ```

2. **Check MCP server logs**:
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

3. **Test with simple session**:
   ```json
   {"session_id": "test", "starting_directory": "~"}
   ```

4. **Verify environment**:
   ```bash
   echo $GEMINI_API_KEY
   which gemini
   which uv
   ```

5. **Manual server test**:
   ```bash
   cd /path/to/gemini-cli-mcp-server
   uv run python src/main.py
   ```

## Getting Help

If issues persist:

1. Check server logs for specific error messages
2. Try running gemini-cli manually to isolate issues
3. Verify all prerequisites are met
4. Test with minimal configuration first
5. Check for conflicting processes or versions

## Configuration Notes

- Timeout is set to 60 seconds - increase for very slow systems
- trust=false is recommended for security
- LOG_LEVEL=INFO provides good debugging information
- Set LOG_LEVEL=DEBUG for more verbose output
