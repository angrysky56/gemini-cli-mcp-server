#!/usr/bin/env python3
"""
Test the improved gemini CLI integration based on workstation analysis
"""

import asyncio
import subprocess
import sys
import os

async def test_command_parsing():
    """Test command parsing logic"""
    print("Testing command parsing...")
    
    def parse_command(command: str) -> list[str]:
        """Parse command using workstation logic"""
        trimmed_command = command.strip()
        
        if trimmed_command.startswith('/') and not trimmed_command.startswith('@') and not trimmed_command.startswith('!'):
            # For /commands like "/help" or "/tool list item"
            parts = trimmed_command.split(' ')
            main_command = parts[0]  # e.g., "/help" or "/tool"
            args_array = [main_command]
            if len(parts) > 1:
                args_array.extend(parts[1:])
            return args_array
        elif trimmed_command.startswith('@') or trimmed_command.startswith('!'):
            # For @file or !shell commands, pass the whole string as a single argument
            return [trimmed_command]
        else:
            # For plain prompts
            return ['--prompt', trimmed_command]
    
    test_cases = [
        ("Hello world", ['--prompt', 'Hello world']),
        ("/help", ['/help']),
        ("/stats", ['/stats']),
        ("@README.md What is this?", ['@README.md What is this?']),
        ("!ls -la", ['!ls -la'])
    ]
    
    for command, expected in test_cases:
        result = parse_command(command)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{command}' -> {result}")
        if result != expected:
            print(f"   Expected: {expected}")
    
    return True

async def test_simple_gemini_call():
    """Test a simple gemini call with proper parsing"""
    print("\nTesting simple gemini call...")
    
    try:
        # Test a simple prompt
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        process = await asyncio.create_subprocess_exec(
            "gemini", "--prompt", "Say 'test successful' if you can see this",
            env=exec_env,
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
            # Filter stderr like workstation
            stderr_text = stderr.decode('utf-8').strip()
            filtered_stderr = []
            for line in stderr_text.split('\n'):
                if not any(noise in line for noise in [
                    'DeprecationWarning', 'MCP STDERR', 'DEBUG:', 
                    '[vite] connecting', '[vite] connected'
                ]):
                    filtered_stderr.append(line)
            
            clean_stderr = '\n'.join(filtered_stderr).strip()
            print(f"❌ Failed (code {process.returncode}): {clean_stderr}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_command_execution():
    """Test command execution"""
    print("\nTesting /stats command...")
    
    try:
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        process = await asyncio.create_subprocess_exec(
            "gemini", "/stats",
            env=exec_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=15.0
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

async def main():
    """Run tests"""
    print("Testing Improved Gemini CLI Integration (Based on Workstation Analysis)\n")
    
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
    test1 = test_command_parsing()
    test2 = await test_simple_gemini_call()
    test3 = await test_command_execution()
    
    passed = sum([test1, test2, test3])
    total = 3
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The workstation-based approach should work.")
    elif passed > 0:
        print("⚠️  Some tests passed. The approach is promising but needs refinement.")
    else:
        print("❌ All tests failed. Check your gemini-cli authentication and setup.")

if __name__ == "__main__":
    asyncio.run(main())
