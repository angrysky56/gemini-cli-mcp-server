#!/usr/bin/env python3
"""
Test the pexpect-based wrapper
"""

import asyncio
import sys
import logging
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper_pexpect import GeminiCLIWrapper

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pexpect_wrapper():
    """Test the pexpect-based wrapper"""
    print("Testing pexpect-based wrapper...")

    try:
        wrapper = GeminiCLIWrapper()

        # Test a simple AI prompt
        print("\n=== Testing simple AI prompt ===")
        response = await wrapper.send_prompt_to_gemini("Hello! Please respond with a simple greeting.")
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
    asyncio.run(test_pexpect_wrapper())
