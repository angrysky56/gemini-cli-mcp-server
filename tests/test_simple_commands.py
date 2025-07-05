#!/usr/bin/env python3
"""
Simple test to debug command response reading
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

async def test_simple_commands():
    """Test simple commands to see actual output"""
    print("Testing command responses...")

    try:
        wrapper = GeminiCLIWrapper()
        session = await wrapper.start_interactive_session()

        print("✓ Session started")

        # Test a simple AI prompt first
        print("\n=== Testing simple AI prompt ===")
        response = await session.send_prompt("Hello, can you tell me what you are?")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        # Test /help first (should definitely have output)
        print("\n=== Testing /help ===")
        response = await session.send_prompt("/help")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        # Test /tools
        print("\n=== Testing /tools ===")
        response = await session.send_prompt("/tools")
        print(f"Response length: {len(response)}")
        print(f"Full Response:\n{response}")
        print("=" * 50)

        await session.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_commands())
