#!/usr/bin/env python3
"""
Debug script to test the wrapper interactive sessions
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

async def debug_interactive_session():
    """Test interactive session with /tools and /mcp commands"""
    wrapper = GeminiCLIWrapper()

    print("Testing interactive session...")

    try:
        # Test /tools command
        print("\n1. Testing /tools command...")
        start_time = asyncio.get_event_loop().time()

        tools_response = await wrapper.list_tools()
        end_time = asyncio.get_event_loop().time()

        print(f"✓ /tools completed in {end_time - start_time:.2f} seconds")
        print(f"Tools response length: {len(tools_response)}")
        print(f"First 200 chars: {tools_response[:200]}")

        # Test /mcp command
        print("\n2. Testing /mcp command...")
        start_time = asyncio.get_event_loop().time()

        mcp_response = await wrapper.list_mcp_servers()
        end_time = asyncio.get_event_loop().time()

        print(f"✓ /mcp completed in {end_time - start_time:.2f} seconds")
        print(f"MCP response length: {len(mcp_response)}")
        print(f"First 200 chars: {mcp_response[:200]}")

        # Test simple chat in session
        print("\n3. Testing simple chat in session...")
        start_time = asyncio.get_event_loop().time()

        session = await wrapper.start_interactive_session()
        try:
            response = await session.send_command("Hello, how are you?")
            end_time = asyncio.get_event_loop().time()

            print(f"✓ Chat completed in {end_time - start_time:.2f} seconds")
            print(f"Chat response length: {len(response)}")
            print(f"First 200 chars: {response[:200]}")
        finally:
            await session.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_interactive_session())
