#!/usr/bin/env python3
"""
Test the wrapper for its intended MCP server use case - AI prompts and responses
"""

import asyncio
import sys
import logging
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_ai_interaction():
    """Test the real use case - sending prompts to Gemini AI"""
    print("Testing AI interaction through Gemini CLI...")

    try:
        wrapper = GeminiCLIWrapper()
        session = await wrapper.start_interactive_session()

        print("✓ Session started")

        # Test a simple AI prompt
        print("\n=== Testing simple prompt ===")
        response = await session.send_prompt("What is 2+2?")
        print(f"Response length: {len(response)}")
        print(f"Response: {response[:20000]}...")

        # Test another prompt to ensure session persistence
        print("\n=== Testing follow-up prompt ===")
        response = await session.send_prompt("What did I just ask you?")
        print(f"Response length: {len(response)}")
        print(f"Response: {response[:20000]}...")

        await session.close()
        print("✓ Session closed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_interaction())
