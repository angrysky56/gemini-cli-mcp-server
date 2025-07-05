#!/usr/bin/env python3
"""
Test script to verify that meta-commands like /tools, /mcp work correctly
and don't invoke external MCP servers unnecessarily.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper


async def test_metacommands():
    """Test meta-commands that should work in interactive sessions"""

    wrapper = GeminiCLIWrapper()

    try:
        # Optionally: check CLI availability by running a simple command
        try:
            await wrapper.list_tools()
            print("✓ Gemini CLI verified (list_tools works)")
        except Exception as e:
            print(f"❌ Gemini CLI not available: {e}")
            return False

        print("\n=== Testing Meta-Commands ===")

        # Test /tools command
        print("\n1. Testing /tools command...")
        try:
            tools_response = await wrapper.list_tools()
            print(f"Tools response length: {len(tools_response)}")
            if "wolfram" in tools_response.lower():
                print("⚠️  WARNING: /tools response mentions WolframAlpha")
            else:
                print("✓ /tools response looks normal")
            print("First 200 chars:", tools_response[:200])
        except Exception as e:
            print(f"❌ /tools failed: {e}")

        # Test /mcp command
        print("\n2. Testing /mcp command...")
        try:
            mcp_response = await wrapper.list_mcp_servers()
            print(f"MCP response length: {len(mcp_response)}")
            print("First 200 chars:", mcp_response[:200])
        except Exception as e:
            print(f"❌ /mcp failed: {e}")

        # Test simple prompt that should NOT invoke external tools
        print("\n3. Testing simple prompt (should not invoke WolframAlpha)...")
        try:
            simple_response = await wrapper.execute_prompt("Hello, how are you?")
            print(f"Simple response length: {len(simple_response)}")
            if "wolfram" in simple_response.lower():
                print("❌ PROBLEM: Simple greeting invoked WolframAlpha!")
                print("Response:", simple_response[:500])
            else:
                print("✓ Simple greeting handled normally")
                print("First 200 chars:", simple_response[:200])
        except Exception as e:
            print(f"❌ Simple prompt failed: {e}")

        # Test /help command
        print("\n4. Testing /help command...")
        try:
            help_response = await wrapper._execute_session_command("/help")
            print(f"Help response length: {len(help_response)}")
            print("First 200 chars:", help_response[:200])
        except Exception as e:
            print(f"❌ /help failed: {e}")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    asyncio.run(test_metacommands())
