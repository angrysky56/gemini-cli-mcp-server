#!/usr/bin/env python3
"""
Test sending actual keyboard shortcuts to the PTY
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper_pty_fixed import GeminiCLIWrapper

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_keyboard_shortcuts():
    """Test using keyboard shortcuts instead of slash commands"""
    print("Testing PTY with keyboard shortcuts...")

    try:
        wrapper = GeminiCLIWrapper()
        print("✓ PTY Wrapper initialized successfully")

        print("\n=== Starting persistent session ===")
        session = await wrapper.start_interactive_session()
        print("✓ Session started")

        # Test Ctrl+T for MCP servers (based on the "ctrl+t to view" message)
        print("\n=== Testing Ctrl+T for MCP servers ===")
        start_time = asyncio.get_event_loop().time()
        try:
            # Send Ctrl+T (ASCII 20)
            os.write(session.master_fd, b'\x14')  # Ctrl+T
            await asyncio.sleep(1.0)  # Give it time to respond

            # Try to read the response using the send_command method (which handles reading)
            response = await session._read_incremental_response()
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"✓ Ctrl+T completed in {elapsed:.2f}s")
            print(f"Response: {response[:300]}...")

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"✗ Ctrl+T failed after {elapsed:.2f}s: {e}")

        # Test some other potential shortcuts
        shortcuts_to_test = [
            (b'\x08', "Ctrl+H (help)"),  # Ctrl+H
            (b'\x0c', "Ctrl+L (clear)"),  # Ctrl+L
            (b'\x01', "Ctrl+A"),  # Ctrl+A
        ]

        for shortcut, description in shortcuts_to_test:
            print(f"\n=== Testing {description} ===")
            start_time = asyncio.get_event_loop().time()
            try:
                os.write(session.master_fd, shortcut)
                await asyncio.sleep(1.0)

                response = await session._read_incremental_response()
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"✓ {description} completed in {elapsed:.2f}s")
                if response.strip():
                    print(f"Response: {response[:200]}...")
                else:
                    print("No response")

            except Exception as e:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"✗ {description} failed after {elapsed:.2f}s: {e}")

        # Now test if slash commands work after getting into the right state
        print("\n=== Testing slash commands again ===")
        for command in ["/tools", "/mcp", "/help"]:
            print(f"Testing {command}...")
            start_time = asyncio.get_event_loop().time()
            try:
                response = await session.send_command(command, timeout=10.0)
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"✓ {command} completed in {elapsed:.2f}s")
                if response.strip() and "Tips for getting started" not in response:
                    print(f"Good response: {response[:200]}...")
                else:
                    print("Still getting generic response")

            except Exception as e:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"✗ {command} failed after {elapsed:.2f}s: {e}")

        await session.close()
        print("✓ Session closed successfully")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_keyboard_shortcuts())
