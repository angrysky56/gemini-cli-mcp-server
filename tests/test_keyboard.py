#!/usr/bin/env python3
"""
Test keyboard shortcuts directly
"""

import asyncio
import sys
import logging
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_ctrl_commands():
    """Test actual keyboard shortcuts"""
    print("Testing keyboard shortcuts...")

    try:
        wrapper = GeminiCLIWrapper()
        session = await wrapper.start_interactive_session()

        print("✓ Session started")

        # Test Ctrl+T (as mentioned in the CLI: "ctrl+t to view")
        print("\n=== Testing Ctrl+T ===")

        # Send Ctrl+T directly
        os.write(session.master_fd, b'\x14')  # Ctrl+T

        # Wait and read response
        await asyncio.sleep(2.0)
        response = await session._read_command_output()
        print(f"Ctrl+T Response length: {len(response)}")
        print(f"Response: {repr(response[:200])}")

        await session.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ctrl_commands())
