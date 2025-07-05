#!/usr/bin/env python3
"""
Debug the PTY-based Gemini CLI wrapper to see what's happening
"""

import asyncio
import sys
import logging
import os
import re

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper_pty import GeminiCLIWrapper

# Set up more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def debug_session():
    """Debug what's happening with command sending/receiving"""
    print("Debugging PTY-based Gemini CLI wrapper...")

    try:
        wrapper = GeminiCLIWrapper()
        print("✓ PTY Wrapper initialized successfully")

        print("\n=== Starting session with detailed debugging ===")
        session = await wrapper.start_interactive_session()
        print("✓ Session started")

        # Test a single command with detailed output
        command = "/tools"
        print(f"\n=== Debugging command: {command} ===")
        print(f"Sending command: '{command}'")

        # Send command and capture raw response
        try:
            raw_response = await session.send_command(command, timeout=15.0)
            print(f"\nRaw response length: {len(raw_response)} characters")
            print(f"Raw response (first 500 chars): {repr(raw_response[:500])}")

            # Clean ANSI codes
            clean_response = clean_ansi_codes(raw_response)
            print(f"\nCleaned response length: {len(clean_response)} characters")
            print(f"Cleaned response (first 500 chars): {clean_response[:500]}")

        except Exception as e:
            print(f"Command failed: {e}")

        # Try a different meta-command
        command = "/help"
        print(f"\n=== Debugging command: {command} ===")
        print(f"Sending command: '{command}'")

        try:
            raw_response = await session.send_command(command, timeout=15.0)
            print(f"\nRaw response length: {len(raw_response)} characters")
            print(f"Raw response (first 500 chars): {repr(raw_response[:500])}")

            clean_response = clean_ansi_codes(raw_response)
            print(f"\nCleaned response length: {len(clean_response)} characters")
            print(f"Cleaned response (first 500 chars): {clean_response[:500]}")

        except Exception as e:
            print(f"Command failed: {e}")

        await session.close()
        print("\n✓ Debug session completed")

    except Exception as e:
        print(f"✗ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_session())
