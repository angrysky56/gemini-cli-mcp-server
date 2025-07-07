#!/usr/bin/env python3
"""
Test the simple gemini CLI integration
"""

import asyncio
import subprocess
import sys

async def test_simple_call():
    """Test a simple gemini call"""
    print("Testing simple gemini call...")
    
    try:
        process = await asyncio.create_subprocess_exec(
            "gemini", "-p", "Say 'test successful' if you can see this",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ Success: {result}")
            return True
        else:
            error = stderr.decode('utf-8') if stderr else "Unknown error"
            print(f"❌ Failed: {error}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_with_files():
    """Test with file inclusion"""
    print("\nTesting with file inclusion...")
    
    # Create a test file
    with open("/tmp/test_file.txt", "w") as f:
        f.write("This is a test file for MCP server testing.")
    
    try:
        process = await asyncio.create_subprocess_exec(
            "gemini", "-p", "@/tmp/test_file.txt What is in this file?",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ Success: {result}")
            return True
        else:
            error = stderr.decode('utf-8') if stderr else "Unknown error"
            print(f"❌ Failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run tests"""
    print("Testing Simple Gemini CLI Integration\n")
    
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
    test1 = await test_simple_call()
    test2 = await test_with_files()
    
    print(f"\nResults: {2 if test1 and test2 else 1 if test1 or test2 else 0}/2 tests passed")
    
    if test1 and test2:
        print("🎉 All tests passed! The simple approach should work.")
    else:
        print("⚠️  Some tests failed. Check your gemini-cli authentication.")

if __name__ == "__main__":
    asyncio.run(main())
