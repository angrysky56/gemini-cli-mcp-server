# Troubleshooting Guide

## Common Issues and Solutions

### 1. Server Won't Start

**Problem**: MCP server fails to initialize
**Solutions**:
- Check Python version (3.10+ required)
- Verify virtual environment is activated
- Ensure all dependencies are installed: `uv add mcp`
- Check for port conflicts

**Diagnostic Commands**:
```bash
python --version
which python
pip list | grep mcp
```

### 2. Authentication Errors

**Problem**: Gemini API authentication fails
**Solutions**:
- Verify GEMINI_API_KEY environment variable is set
- Check API key validity at Google AI Studio
- Ensure proper permissions for the API key
- Try re-generating the API key

**Diagnostic Commands**:
```bash
echo $GEMINI_API_KEY
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1/models
```

### 3. Node.js/Gemini CLI Issues

**Problem**: Gemini CLI not found or fails to execute
**Solutions**:
- Install Node.js 18+ 
- Verify npx is available
- Test Gemini CLI directly: `npx https://github.com/google-gemini/gemini-cli --version`
- Check network connectivity

### 4. Permission Errors

**Problem**: File access or directory permission errors
**Solutions**:
- Verify working directory permissions
- Use absolute paths when possible
- Check file/directory ownership
- Ensure proper read/write permissions

### 5. Timeout Issues

**Problem**: Operations timeout or hang
**Solutions**:
- Increase timeout values in configuration
- Check network connectivity
- Verify API quota and rate limits
- Break large operations into smaller chunks

## Debugging Steps

### 1. Enable Debug Logging
Set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

### 2. Test Components Individually

**Test Gemini CLI**:
```bash
npx https://github.com/google-gemini/gemini-cli --help
```

**Test MCP Server**:
```bash
python src/main.py
```

**Test with MCP Inspector**:
```bash
npx @modelcontextprotocol/inspector uv --directory . run python src/main.py
```

### 3. Check System Requirements

- Python 3.10+
- Node.js 18+
- Active internet connection
- Valid Gemini API key
- Sufficient disk space

### 4. Verify Configuration

Check your Claude Desktop config:
```json
{
  "mcpServers": {
    "gemini-cli": {
      "command": "uv",
      "args": ["--directory", "/path/to/gemini-cli-mcp-server", "run", "python", "src/main.py"],
      "env": {
        "GEMINI_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Getting Help

### Log Information to Collect
- Error messages from stderr
- Full stack traces
- Configuration files (with sensitive data removed)
- System information (OS, Python version, Node.js version)

### Useful Commands for Diagnostics
```bash
# System info
python --version
node --version
uv --version

# Check installation
pip list | grep mcp
npm list -g

# Test connectivity
ping google.com
curl -I https://generativelanguage.googleapis.com

# Check permissions
ls -la /path/to/project
whoami
id
```

### Support Resources
- [Gemini CLI GitHub Issues](https://github.com/google-gemini/gemini-cli/issues)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Google AI Studio Support](https://aistudio.google.com/)

## Performance Optimization

### Memory Usage
- Monitor memory consumption during large operations
- Use streaming for large file processing
- Implement pagination for bulk operations

### Network Optimization
- Cache API responses when appropriate
- Batch similar requests
- Implement retry logic with exponential backoff

### File System Optimization
- Use absolute paths to avoid ambiguity
- Implement proper file locking for concurrent access
- Clean up temporary files regularly
