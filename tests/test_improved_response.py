#!/usr/bin/env python3
"""
Test the improved response reading from Gemini CLI.
This test verifies that we can get clean AI responses without UI artifacts.
"""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gemini_cli_wrapper import GeminiCLIWrapper


async def test_clean_responses():
    """Test that we get clean AI responses"""
    wrapper = GeminiCLIWrapper()

    try:
        print("Testing clean AI response extraction...")

        # Simple question that should get a clear response
        response = await wrapper.send_prompt_to_gemini("What is 2 + 2?")
        print(f"Response: {response}")
        print(f"Response length: {len(response)}")

        # Check that response doesn't contain obvious UI artifacts
        ui_artifacts = [
            "Type your message",
            "ctrl+",
            "╭─",
            "│",
            "context left",
            "accepting edits"
        ]

        artifacts_found = [artifact for artifact in ui_artifacts if artifact in response]

        if artifacts_found:
            print(f"⚠️  Found UI artifacts in response: {artifacts_found}")
        else:
            print("✅ Response appears clean (no obvious UI artifacts)")

        # Test another question
        print("\nTesting second question...")
        response2 = await wrapper.send_prompt_to_gemini("Name three colors.")
        print(f"Response 2: {response2}")

        artifacts_found2 = [artifact for artifact in ui_artifacts if artifact in response2]
        if artifacts_found2:
            print(f"⚠️  Found UI artifacts in response 2: {artifacts_found2}")
        else:
            print("✅ Response 2 appears clean")

        print("\n✅ Response reading test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await wrapper.close_persistent_session()

if __name__ == "__main__":
    asyncio.run(test_clean_responses())
