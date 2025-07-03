# Gemini CLI MCP Server Usage Guide

## Overview

This MCP server provides access to Google's Gemini CLI capabilities through the Model Context Protocol. It allows you to leverage Gemini's powerful AI for code analysis, generation, and assistance directly from MCP-compatible clients like Claude Desktop.

## Tool Categories

### 🤖 AI Chat & Analysis
- **gemini_chat**: Direct interaction with Gemini AI
- **gemini_analyze_code**: Comprehensive code analysis
- **gemini_code_assist**: Targeted coding help

### 🛠️ Development Tools  
- **gemini_generate_app**: Full application generation
- **gemini_git_assist**: Git workflow assistance

### 📊 Information Resources
- **gemini://status**: Server and CLI status
- **gemini://help**: Command help and documentation

## Best Practices

### Effective Prompting
1. **Be Specific**: Provide clear, detailed requests
2. **Set Context**: Include relevant background information
3. **Define Scope**: Specify what you want analyzed or generated
4. **Iterate**: Build on previous responses for complex tasks

### Code Analysis Tips
- Point to specific directories or files
- Describe the type of analysis needed (security, performance, structure)
- Ask for actionable recommendations
- Request explanations for complex code patterns

### App Generation Guidelines
- Provide detailed functional requirements
- Specify preferred frameworks or technologies
- Include UI/UX considerations
- Mention deployment requirements

## Common Workflows

### 1. Understanding a New Codebase
```
1. Use gemini_analyze_code to get an overview
2. Ask specific questions with gemini_chat
3. Get targeted help with gemini_code_assist
```

### 2. Building New Features
```
1. Analyze existing code patterns
2. Generate component templates
3. Get implementation guidance
4. Review and refine with AI assistance
```

### 3. Debugging and Optimization
```
1. Analyze problematic code sections
2. Get specific debugging help
3. Receive optimization suggestions
4. Validate solutions
```

## Security Considerations

- API keys are handled securely through environment variables
- Code analysis respects local file permissions
- No sensitive data is logged or cached
- All operations respect working directory boundaries

## Performance Tips

- Use specific working directories to limit scope
- Break large tasks into smaller, focused requests
- Cache results when appropriate
- Consider API rate limits for heavy usage
