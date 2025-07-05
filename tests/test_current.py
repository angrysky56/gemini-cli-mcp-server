#!/usr/bin/env python3
"""
Simple test for the current PTY wrapper
"""

import asyncio
import os
import sys

sys.path.insert(0, 'src')
from src.gemini_cli_wrapper import GeminiCLIWrapper


async def test_current_wrapper():
    """Test the current PTY implementation"""
    print("Testing current PTY wrapper...")

    wrapper = GeminiCLIWrapper()
    session = await wrapper.start_interactive_session()

    print("\n=== Testing /tools ===")
    response = await session.send_command("/tools", timeout=10.0)
    print(f"Response ({len(response)} chars):")
    print(repr(response[:300]))

    await session.close()

if __name__ == "__main__":
    asyncio.run(test_current_wrapper())
