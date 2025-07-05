#!/usr/bin/env python3
"""
Test to debug the authentication and response detection
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

async def test_auth_and_response():
    """Test authentication and response detection more carefully"""
    print("Testing authentication and response patterns...")

    try:
        wrapper = GeminiCLIWrapper()
        session = await wrapper.start_interactive_session()

        print("✓ Session started")

        # Wait a bit more for the session to fully initialize
        print("Waiting for session to stabilize...")
        await asyncio.sleep(5.0)

        # Try a very simple prompt that should get a quick response
        print("\n=== Testing simple prompt: 'hi' ===")
        response = await session.send_prompt("hi", timeout=30.0)
        print(f"Response length: {len(response)}")
        print("="*20 + " FULL RESPONSE " + "="*20)
        print(response)
        print("="*50)

        # Let's see what happens with a longer wait
        print("\nWaiting 3 seconds...")
        await asyncio.sleep(3.0)

        print("\n=== Testing another simple prompt: 'what is 2+2?' ===")
        response = await session.send_prompt("what is 2+2?", timeout=30.0)
        print(f"Response length: {len(response)}")
        print("="*20 + " FULL RESPONSE " + "="*20)
        print(response)
        print("="*50)

        await session.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_and_response())
