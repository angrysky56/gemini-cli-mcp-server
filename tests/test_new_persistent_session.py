#!/usr/bin/env python3
"""
Test the persistent session functionality
"""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gemini_cli_wrapper import GeminiCLIWrapper


async def test_persistent_session():
    """Test that the session persists across multiple prompts"""
    print("Testing persistent session...")
    
    wrapper = GeminiCLIWrapper()
    
    try:
        # Send first prompt
        print("\n1. Sending first prompt...")
        response1 = await wrapper.send_prompt_to_gemini("Hello! What's 2+2?")
        print(f"Response 1: {response1[:200]}...")
        
        # Send second prompt - this should use the same session
        print("\n2. Sending second prompt to same session...")
        response2 = await wrapper.send_prompt_to_gemini("What was my previous question?")
        print(f"Response 2: {response2[:200]}...")
        
        # Send third prompt with context reference
        print("\n3. Testing session memory...")
        response3 = await wrapper.send_prompt_to_gemini("Can you remind me what math problem I asked earlier?")
        print(f"Response 3: {response3[:200]}...")
        
        # Test file inclusion
        print("\n4. Testing file inclusion...")
        response4 = await wrapper.include_file("README.md")
        print(f"File inclusion response: {response4[:200]}...")
        
        # Test shell command
        print("\n5. Testing shell command...")
        response5 = await wrapper.run_shell_command("pwd")
        print(f"Shell command response: {response5[:200]}...")
        
        print("\n✅ Persistent session test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during persistent session test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await wrapper.close_persistent_session()
        print("🧹 Cleaned up persistent session")


if __name__ == "__main__":
    asyncio.run(test_persistent_session())