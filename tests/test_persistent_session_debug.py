#!/usr/bin/env python3
"""
Test the persistent session approach
"""

import asyncio
import sys
import logging
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_persistent_session():
    """Test the persistent session functionality"""
    print("Testing persistent session...")

    try:
        wrapper = GeminiCLIWrapper()

        # Test 1: Simple prompt using persistent session
        print("\n=== Test 1: Simple prompt via persistent session ===")
        response = await wrapper.send_prompt_to_gemini("Hello, what is 1+1?")
        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:200]}...")

        # Test 2: Another prompt using same persistent session
        print("\n=== Test 2: Another prompt via same session ===")
        response = await wrapper.send_prompt_to_gemini("What is the capital of France?")
        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:200]}...")

        # Test 3: File inclusion
        print("\n=== Test 3: File inclusion ===")
        response = await wrapper.include_file("README.md")
        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:200]}...")

        # Close the persistent session
        await wrapper.close_persistent_session()
        print("✓ Persistent session closed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_persistent_session())
