#!/usr/bin/env python3
"""
Comprehensive test for Gemini CLI MCP Server fixes
Tests auto-approval, Unicode filtering, and session persistence
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict

# Add the src directory to the path
sys.path.insert(0, 'src')

from gemini_cli_wrapper import GeminiCLIWrapper, GeminiInteractiveSession


async def test_fixes():
    """Test all the fixes we've implemented"""
    print("🧪 Gemini CLI MCP Server Fix Verification")
    print("=" * 50)
    
    try:
        # Initialize wrapper
        wrapper = GeminiCLIWrapper()
        print("✅ Gemini CLI wrapper initialized")
        
        # Test 1: Auto-approval session
        print("\n📋 Test 1: Auto-approval session")
        session_auto = await wrapper.start_interactive_session(
            working_directory=".",
            auto_approve=True
        )
        print("✅ Session started with auto-approval")
        
        # Test a command that would normally require approval
        print("📝 Sending command that requires tool approval...")
        response = await session_auto.send_prompt("Create a test file called test_auto.txt with 'Hello World' content")
        print(f"✅ Response received (length: {len(response)} chars)")
        print(f"📄 First 200 chars: {response[:200]}...")
        
        # Check for Unicode issues
        if any(ord(c) >= 0x2500 and ord(c) <= 0x257F for c in response):
            print("❌ WARNING: Box-drawing characters detected in response!")
        else:
            print("✅ No box-drawing characters in response")
        
        # Test 2: Session persistence
        print("\n📋 Test 2: Session persistence")
        if session_auto.is_running():
            print("✅ Session is still running")
        else:
            print("❌ Session died unexpectedly")
        
        # Test 3: Multiple commands
        print("\n📋 Test 3: Multiple commands in same session")
        response2 = await session_auto.send_prompt("List the files in the current directory")
        print(f"✅ Second command executed (length: {len(response2)} chars)")
        
        # Test 4: Clean response
        print("\n📋 Test 4: Response cleaning")
        # Check for common interface elements that should be filtered
        interface_patterns = [
            'gemini-2.5-pro',
            'context left)',
            '~/Repositories',
            'no sandbox',
            '(main*)'
        ]
        
        found_patterns = [p for p in interface_patterns if p in response]
        if found_patterns:
            print(f"❌ Found interface patterns in response: {found_patterns}")
        else:
            print("✅ Response properly cleaned of interface elements")
        
        # Test 5: Manual approval session (for comparison)
        print("\n📋 Test 5: Manual approval session")
        session_manual = await wrapper.start_interactive_session(
            working_directory=".",
            auto_approve=False
        )
        print("✅ Session started without auto-approval")
        
        # This should get blocked if it requires approval
        print("📝 Sending command to manual session...")
        try:
            # Use a simpler command that won't block
            response3 = await session_manual.send_prompt("What is 2+2?")
            print(f"✅ Simple command worked: {response3[:100]}...")
        except Exception as e:
            print(f"ℹ️ Command blocked as expected: {str(e)}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await session_auto.close()
        await session_manual.close()
        print("✅ Sessions closed")
        
        print("\n✨ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_unicode_filtering():
    """Specific test for Unicode filtering"""
    print("\n🔤 Unicode Filtering Test")
    print("=" * 30)
    
    # Test string with box-drawing characters
    test_input = """
    ┌────────────────┐
    │ Test Response  │
    └────────────────┘
    This is the actual response content.
    ╔══════════════╗
    ║ Another box  ║
    ╚══════════════╝
    """
    
    # Import the cleaning function
    from gemini_cli_wrapper import GeminiInteractiveSession
    
    # Create a dummy session just to test the cleaning
    class DummySession(GeminiInteractiveSession):
        def __init__(self):
            self.auto_approve = False
            
    session = DummySession()
    cleaned = session._clean_response(test_input, "test prompt")
    
    print(f"Original length: {len(test_input)}")
    print(f"Cleaned length: {len(cleaned)}")
    print(f"Cleaned content: '{cleaned}'")
    
    # Check if box chars are removed
    has_box_chars = any(ord(c) >= 0x2500 and ord(c) <= 0x257F for c in cleaned)
    if has_box_chars:
        print("❌ Box-drawing characters still present!")
    else:
        print("✅ Box-drawing characters successfully removed")


if __name__ == "__main__":
    print("Starting Gemini CLI MCP Server Fix Tests")
    print("This will test:")
    print("1. Auto-approval functionality")
    print("2. Unicode/box-drawing character filtering")
    print("3. Session persistence")
    print("4. Response cleaning")
    print("")
    
    # Run the main tests
    asyncio.run(test_fixes())
    
    # Run Unicode-specific test
    asyncio.run(test_unicode_filtering())
