#!/usr/bin/env python3
"""
Test authentication handling in the persistent session
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

async def test_auth_handling():
    """Test authentication handling with file inclusion"""
    print("Testing authentication handling...")

    try:
        wrapper = GeminiCLIWrapper()

        # Test using the persistent session wrapper method
        print("\n=== Testing persistent session with file inclusion ===")

        # Create a test file to include
        test_file = "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test file for authentication testing.\nIt should be included in the prompt.")

        try:
            # Try to include the file - this should trigger auth
            response = await wrapper.include_file(test_file)
            print(f"Response length: {len(response)}")
            print(f"Full Response:\n{response}")

        finally:
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)

        # Close the session
        await wrapper.close_persistent_session()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_handling())
