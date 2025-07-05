#!/usr/bin/env python3
"""
Test shell commands with ! syntax and output capture
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_shell_commands():
    """Test shell commands with ! syntax"""
    print("Testing shell commands with ! syntax...")

    try:
        wrapper = GeminiCLIWrapper()

        print("\n=== Testing shell command: !ls with redirection ===")
        response = await wrapper.run_shell_command("ls -la 2>&1")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        print("\n=== Testing shell command: !pwd with redirection ===")
        response = await wrapper.run_shell_command("pwd 2>&1")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        print("\n=== Testing shell command with output redirection: !echo 'hello' 2>&1 ===")
        response = await wrapper.run_shell_command("echo 'hello world from shell' 2>&1")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        # Close the session
        await wrapper.close_persistent_session()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_shell_commands())
