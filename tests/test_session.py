#!/usr/bin/env python3
"""
Test script for the improved Gemini CLI wrapper
"""
import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper


async def test_session_startup():
    """Test if we can start a session without timeout"""
    try:
        wrapper = GeminiCLIWrapper()
        print("✓ Wrapper initialized successfully")

        # Test single prompt with a simple request that shouldn't need tools
        result = await wrapper.execute_prompt("Just say 'Hello' and nothing else")
        print(f"✓ Single prompt works: {result[:100]}...")

        # Test tool listing
        tools_result = await wrapper.list_tools()
        print(f"✓ Tools list retrieved: {len(tools_result)} chars")

        # Test MCP servers listing
        mcp_result = await wrapper.list_mcp_servers()
        print(f"✓ MCP servers list retrieved: {len(mcp_result)} chars")

        # Test interactive session
        print("Testing interactive session startup...")
        session = await wrapper.start_interactive_session()
        print("✓ Interactive session started!")

        # Test a simple interaction that shouldn't trigger tools
        response = await session.send_command("Please just respond with 'Hi there' and nothing else")
        print(f"✓ Session responds: {response[:100]}...")

        # Test getting tools in session
        tools_response = await session.get_tools()
        print(f"✓ Session tools command works: {len(tools_response)} chars")

        # Clean up
        await session.close()
        print("✓ Session closed cleanly")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_session_startup())
    sys.exit(0 if success else 1)
