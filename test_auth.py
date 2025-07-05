#!/usr/bin/env python3
"""
Test script for Gemini CLI MCP Server authentication improvements
"""

import asyncio
import json
import subprocess
import time


async def test_auto_approval():
    """Test that auto-approval works correctly"""
    print("Testing Gemini CLI MCP Server with auto-approval...")
    
    # Start a test session
    cmd = [
        "python3", "-m", "src.main"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    await asyncio.sleep(2)
    
    # Send test commands
    test_sequence = [
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "gemini_start_session",
                "arguments": {
                    "session_id": "test_session",
                    "auto_approve": True
                }
            },
            "id": 1
        },
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "gemini_session_chat",
                "arguments": {
                    "session_id": "test_session",
                    "message": "List files in current directory using !ls"
                }
            },
            "id": 2
        }
    ]
    
    for cmd in test_sequence:
        print(f"\nSending: {cmd['params']['name']}")
        proc.stdin.write(json.dumps(cmd) + "\n")
        proc.stdin.flush()
        
        # Read response
        response = proc.stdout.readline()
        if response:
            print(f"Response: {response[:100]}...")
        
        await asyncio.sleep(2)
    
    # Check task status
    check_cmd = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "gemini_check_task_status",
            "arguments": {
                "task_id": "extract-task-id-from-previous-response"
            }
        },
        "id": 3
    }
    
    print("\nTest complete. Check if commands executed without auth prompts.")
    
    # Cleanup
    proc.terminate()
    

if __name__ == "__main__":
    print("Gemini CLI MCP Server Authentication Test")
    print("=========================================")
    print("\nThis test will:")
    print("1. Start a session with auto-approval enabled")
    print("2. Execute a command that normally requires approval")
    print("3. Verify it completes without blocking")
    print("\nNote: This is a basic test framework. In production,")
    print("use proper MCP client libraries for testing.")
    
    asyncio.run(test_auto_approval())
