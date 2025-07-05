#!/usr/bin/env python3
"""
Test the improved Gemini CLI wrapper with better environment handling
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_meta_commands():
    """Test meta commands that should work instantly"""
    print("Testing improved Gemini CLI wrapper...")

    try:
        wrapper = GeminiCLIWrapper()
        print("✓ Wrapper initialized successfully")

        print("\n=== Testing /tools command ===")
        start_time = asyncio.get_event_loop().time()
        tools_response = await wrapper.list_tools()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Tools response (took {elapsed:.2f}s): {tools_response[:200]}...")

        print("\n=== Testing /mcp command ===")
        start_time = asyncio.get_event_loop().time()
        mcp_response = await wrapper.list_mcp_servers()
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"MCP response (took {elapsed:.2f}s): {mcp_response[:200]}...")

        print("\n=== Testing interactive session directly ===")
        session = await wrapper.start_interactive_session()

        # Test /help command
        print("Testing /help command...")
        start_time = asyncio.get_event_loop().time()
        help_response = await session.send_command("/help")
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Help response (took {elapsed:.2f}s): {help_response[:200]}...")

        # Test /stats command
        print("Testing /stats command...")
        start_time = asyncio.get_event_loop().time()
        stats_response = await session.send_command("/stats")
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"Stats response (took {elapsed:.2f}s): {stats_response[:200]}...")

        await session.close()
        print("✓ All tests completed successfully")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_meta_commands())
