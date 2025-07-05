#!/usr/bin/env python3
"""
Test different command formats with the Gemini CLI
"""

import asyncio
import sys
import logging
import os
import re

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper_pty import GeminiCLIWrapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def test_command_formats():
    """Test different ways to send commands to Gemini CLI"""
    print("Testing different command formats...")

    try:
        wrapper = GeminiCLIWrapper()
        session = await wrapper.start_interactive_session()

        # Try different command formats
        commands_to_try = [
            "/tools",      # Standard meta-command format
            "\\tools",     # Escaped slash
            "tools",       # Without slash
            "/help",       # Help command
            "help",        # Help without slash
            "/mcp",        # MCP command
            "mcp",         # MCP without slash
            "\x14",        # Ctrl+T (ASCII 20) - based on "ctrl+t to view"
        ]

        for command in commands_to_try:
            print(f"\n=== Testing command format: {repr(command)} ===")
            try:
                response = await session.send_command(command, timeout=10.0)
                clean_response = clean_ansi_codes(response)

                # Look for actual command output vs the generic prompt
                if "Tips for getting started" in clean_response:
                    print(f"❌ Got generic prompt (command not recognized)")
                elif len(clean_response.strip()) > 100:
                    print(f"✅ Got substantial response ({len(clean_response)} chars)")
                    # Show first few lines of actual content
                    lines = clean_response.strip().split('\n')
                    for i, line in enumerate(lines[:5]):
                        if line.strip():
                            print(f"  Line {i+1}: {line.strip()[:80]}")
                else:
                    print(f"⚠️ Got short response: {clean_response.strip()[:100]}")

            except Exception as e:
                print(f"❌ Command failed: {e}")

        await session.close()
        print("\n✓ Command format testing completed")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_command_formats())
