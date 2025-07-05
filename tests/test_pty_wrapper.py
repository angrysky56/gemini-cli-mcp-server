#!/usr/bin/env python3
"""
Test the PTY-based Gemini CLI wrapper
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper_pty import GeminiCLIWrapper

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pty_wrapper():
    """Test PTY-based wrapper with meta commands that should work instantly"""
    print("Testing PTY-based Gemini CLI wrapper...")

    try:
        wrapper = GeminiCLIWrapper()
        print("✓ PTY Wrapper initialized successfully")

        print("\n=== Testing /tools command ===")
        start_time = asyncio.get_event_loop().time()
        tools_response = await wrapper.list_tools()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Tools response (took {elapsed:.2f}s):")
        print(tools_response[:500] + "..." if len(tools_response) > 500 else tools_response)

        print("\n=== Testing /mcp command ===")
        start_time = asyncio.get_event_loop().time()
        mcp_response = await wrapper.list_mcp_servers()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"MCP response (took {elapsed:.2f}s):")
        print(mcp_response[:500] + "..." if len(mcp_response) > 500 else mcp_response)

        print("\n=== Testing direct interactive session ===")
        session = await wrapper.start_interactive_session()

        # Test /help command
        print("Testing /help command...")
        start_time = asyncio.get_event_loop().time()
        help_response = await session.send_command("/help")
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Help response (took {elapsed:.2f}s):")
        print(help_response[:500] + "..." if len(help_response) > 500 else help_response)

        await session.close()
        print("✓ All PTY tests completed successfully")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pty_wrapper())
