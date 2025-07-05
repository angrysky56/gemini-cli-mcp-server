#!/bin/bash
# Test script for the Gemini CLI MCP Server
# This script verifies that the server can properly connect to gemini-cli

set -e

echo "🧪 Testing Gemini CLI MCP Server"
echo "================================"

# Check if gemini-cli is available
echo "📋 Checking prerequisites..."

if ! command -v gemini &> /dev/null; then
    echo "❌ Error: gemini-cli not found"
    echo "   Please install: npm install -g @google/gemini-cli"
    exit 1
fi

echo "✅ Gemini CLI found: $(gemini --version 2>&1 | head -1)"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Error: Virtual environment not activated"
    echo "   Please run: source .venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment active: $VIRTUAL_ENV"

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python -c "import mcp; print('✅ MCP available')" || {
    echo "❌ MCP not available. Run: uv sync"
    exit 1
}

# Test gemini-cli authentication
echo "🔐 Testing Gemini CLI authentication..."
timeout 10s gemini -p "Hello, just testing authentication" > /tmp/gemini_test.out 2>&1 || {
    echo "❌ Gemini CLI authentication failed"
    echo "   Please run 'gemini' manually first to complete authentication"
    cat /tmp/gemini_test.out
    exit 1
}

echo "✅ Gemini CLI authentication working"

# Test the MCP server startup
echo "🚀 Testing MCP server startup..."
timeout 5s python src/main.py < /dev/null > /tmp/mcp_test.out 2>&1 && {
    echo "✅ MCP server starts successfully"
} || {
    if grep -q "Gemini CLI wrapper initialized successfully" /tmp/mcp_test.out; then
        echo "✅ MCP server initializes correctly"
    else
        echo "❌ MCP server failed to initialize"
        cat /tmp/mcp_test.out
        exit 1
    fi
}

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Next steps:"
echo "1. Add this server to your Claude Desktop MCP configuration"
echo "2. Test with the gemini_prompt tool for simple queries"
echo "3. Use gemini_start_session for complex interactive workflows"
echo ""
echo "Example MCP configuration:"
echo '{'
echo '  "mcpServers": {'
echo '    "gemini-cli": {'
echo '      "command": "python",'
echo '      "args": ["'$(pwd)'/src/main.py"],'
echo '      "cwd": "'$(pwd)'",'
echo '      "env": {'
echo '        "PATH": "'$(pwd)'/.venv/bin:${PATH}"'
echo '      }'
echo '    }'
echo '  }'
echo '}'

# Cleanup
rm -f /tmp/gemini_test.out /tmp/mcp_test.out
