#!/usr/bin/env python3
"""
Test the persistent session approach using the high-level wrapper methods
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

async def test_persistent_wrapper():
    """Test the persistent session wrapper methods"""
    print("Testing persistent session wrapper...")

    try:
        wrapper = GeminiCLIWrapper()

        # Test 1: Simple prompt using persistent session
        print("\n=== Test 1: Simple AI prompt ===")
        response = await wrapper.send_prompt_to_gemini("Hello, what are you?")
        print(f"Response length: {len(response)}")
        print(f"Response: {response}")
        print("=" * 50)

        # Test 2: Another prompt (should reuse same session)
        print("\n=== Test 2: Second prompt (reusing session) ===")
        response = await wrapper.send_prompt_to_gemini("What is 2 + 2?")
        print(f"Response length: {len(response)}")
        print(f"Response: {response}")
        print("=" * 50)

        # Test 3: Include file
        print("\n=== Test 3: Include file ===")
        response = await wrapper.include_file("README.md")
        print(f"Response length: {len(response)}")
        print(f"Response: {response[:500]}...")
        print("=" * 50)

        # Test 4: Shell command
        print("\n=== Test 4: Shell command ===")
        response = await wrapper.run_shell_command("ls -la")
        print(f"Response length: {len(response)}")
        print(f"Response: {response[:500]}...")
        print("=" * 50)

        # Clean up
        await wrapper.close_persistent_session()
        print("✓ Persistent session closed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_persistent_wrapper())
