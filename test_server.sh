#!/bin/bash
# Test script for Gemini CLI MCP Server

echo "🧪 Testing Gemini CLI MCP Server..."

# Activate virtual environment
source .venv/bin/activate

echo "📦 Checking dependencies..."
python -c "import mcp; print('✅ MCP installed')"
python -c "import aiofiles; print('✅ aiofiles installed')"
python -c "import pydantic; print('✅ pydantic installed')"

echo "🚀 Testing server startup..."
timeout 3s python src/main.py 2>&1 | head -5

echo "🔍 Testing with MCP Inspector (requires Node.js)..."
echo "Run this command to test interactively:"
echo "npx @modelcontextprotocol/inspector uv --directory $(pwd) run python src/main.py"

echo "✅ Server test completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Set your GEMINI_API_KEY environment variable"
echo "2. Add the server to your Claude Desktop configuration:"
echo "   See: example_mcp_config.json"
echo "3. Restart Claude Desktop to load the server"
