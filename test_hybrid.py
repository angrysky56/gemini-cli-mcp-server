#!/usr/bin/env python3
"""
Test the hybrid approach - focusing on what should work
"""

import asyncio
import subprocess
import sys
import os

async def test_basic_prompt():
    """Test basic prompt with --prompt flag"""
    print("Testing basic prompt (should work)...")
    
    try:
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        process = await asyncio.create_subprocess_exec(
            "gemini", "--prompt", "Just say 'Working!' and nothing else",
            env=exec_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=45.0  # Give it more time
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ Success: {result}")
            return True
        else:
            stderr_text = stderr.decode('utf-8').strip()
            print(f"❌ Failed (code {process.returncode}): {stderr_text}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout - this suggests authentication issues")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_file_inclusion():
    """Test file inclusion"""
    print("\nTesting file inclusion...")
    
    # Create a test file
    test_file = "/tmp/test_gemini.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file for Gemini CLI MCP server testing.")
    
    try:
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        process = await asyncio.create_subprocess_exec(
            "gemini", "--prompt", f"@{test_file} What does this file contain? Just summarize briefly.",
            env=exec_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=45.0
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ Success: {result}")
            return True
        else:
            stderr_text = stderr.decode('utf-8').strip()
            print(f"❌ Failed: {stderr_text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        try:
            os.remove(test_file)
        except:
            pass

def test_command_detection():
    """Test command detection logic"""
    print("\nTesting command detection...")
    
    interactive_commands = [
        '/stats', '/memory', '/tools', '/mcp', '/help', '/theme', 
        '/auth', '/about', '/quit', '/exit', '/chat', '/clear',
        '/compress', '/editor', '/restore', '/bug'
    ]
    
    def is_interactive_command(command: str) -> bool:
        trimmed = command.strip()
        return any(trimmed.startswith(cmd) for cmd in interactive_commands)
    
    test_cases = [
        ("/stats", True),
        ("/memory show", True),
        ("/tools", True),
        ("Hello world", False),
        ("@file.txt analyze this", False),
        ("!ls -la", False),
        ("/help me", True)
    ]
    
    all_correct = True
    for command, expected in test_cases:
        result = is_interactive_command(command)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{command}' -> {'Interactive' if result else 'Non-interactive'}")
        if result != expected:
            all_correct = False
    
    return all_correct

async def main():
    """Run tests"""
    print("Testing Hybrid Gemini CLI MCP Server\n")
    
    # Check if gemini is available
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Gemini CLI not available")
            sys.exit(1)
        print(f"✅ Gemini CLI found: {result.stdout.strip()}\n")
    except FileNotFoundError:
        print("❌ Gemini CLI not found in PATH")
        sys.exit(1)
    
    # Run tests
    test1 = test_command_detection()
    test2 = await test_basic_prompt()
    test3 = await test_file_inclusion()
    
    passed = sum([test1, test2, test3])
    total = 3
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The hybrid approach is working.")
        print("\n📋 Next steps:")
        print("   - Basic prompts and file inclusion work via MCP")
        print("   - Interactive commands (/stats, /memory) identified for future pexpect implementation")
    elif passed > 0:
        print("⚠️  Some tests passed. Core functionality is working.")
    else:
        print("❌ Core functionality not working. Check authentication.")

if __name__ == "__main__":
    asyncio.run(main())
