#!/usr/bin/env python3
"""
Test the VibeKit-based gemini CLI integration
"""

import asyncio
import subprocess
import sys
import os
import re

def escape_prompt(prompt: str) -> str:
    """Python version of VibeKit's prompt escaping"""
    # Escape backticks, quotes, dollar signs, and backslashes
    return re.sub(r'[`"$\\]', r'\\\g<0>', prompt)

async def test_vibekit_pattern():
    """Test using VibeKit's exact pattern"""
    print("Testing VibeKit pattern...")
    
    try:
        # VibeKit's ask mode instruction
        instruction = (
            "Research the repository and answer the user's questions. "
            "Do NOT make any changes to any files in the repository."
        )
        
        user_prompt = "Just say 'VibeKit pattern working!' and nothing else"
        full_prompt = f"{instruction}\n\nUser: {user_prompt}"
        
        # Escape like VibeKit
        escaped_prompt = escape_prompt(full_prompt)
        
        # Build environment like VibeKit
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        # Add API keys if available (VibeKit sets both)
        if 'GEMINI_API_KEY' in os.environ:
            exec_env['GEMINI_API_KEY'] = os.environ['GEMINI_API_KEY']
            exec_env['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
        
        # VibeKit's exact command pattern
        cmd_args = [
            "gemini",
            "--model", "gemini-2.5-flash",
            "--prompt", escaped_prompt,
            "--yolo"
        ]
        
        print(f"Command: gemini --model gemini-2.5-flash --prompt [escaped] --yolo")
        
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            env=exec_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60.0
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ VibeKit pattern success: {result}")
            return True
        else:
            error = stderr.decode('utf-8').strip()
            print(f"❌ Failed (code {process.returncode}): {error}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_vibekit_code_mode():
    """Test VibeKit's code generation mode"""
    print("\nTesting VibeKit code mode...")
    
    try:
        # VibeKit's code mode instruction
        instruction = (
            "Do the necessary changes to the codebase based on the users input.\n"
            "Don't ask any follow up questions."
        )
        
        user_prompt = "Just respond with 'Code mode working!' and nothing else"
        full_prompt = f"{instruction}\n\nUser: {user_prompt}"
        
        escaped_prompt = escape_prompt(full_prompt)
        
        exec_env = {
            **os.environ,
            'NODE_NO_WARNINGS': '1',
            'TERM': 'xterm-256color'
        }
        
        if 'GEMINI_API_KEY' in os.environ:
            exec_env['GEMINI_API_KEY'] = os.environ['GEMINI_API_KEY']
            exec_env['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']
        
        cmd_args = [
            "gemini",
            "--model", "gemini-2.5-pro",
            "--prompt", escaped_prompt,
            "--yolo"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            env=exec_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60.0
        )
        
        if process.returncode == 0:
            result = stdout.decode('utf-8').strip()
            print(f"✅ Code mode success: {result}")
            return True
        else:
            error = stderr.decode('utf-8').strip()
            print(f"❌ Failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_escape_function():
    """Test prompt escaping"""
    print("\nTesting prompt escaping...")
    
    test_cases = [
        ("Simple text", "Simple text"),
        ("Text with `backticks`", "Text with \\`backticks\\`"),
        ('Text with "quotes"', 'Text with \\"quotes\\"'),
        ("Text with $variables", "Text with \\$variables"),
        ("Text with \\backslashes", "Text with \\\\backslashes")
    ]
    
    all_correct = True
    for input_text, expected in test_cases:
        result = escape_prompt(input_text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_text}' -> '{result}'")
        if result != expected:
            print(f"    Expected: '{expected}'")
            all_correct = False
    
    return all_correct

def check_environment():
    """Check environment setup"""
    print("Checking environment...")
    
    issues = []
    
    # Check gemini-cli
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("Gemini CLI not working")
        else:
            print(f"✅ Gemini CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        issues.append("Gemini CLI not found in PATH")
    
    # Check API key
    if 'GEMINI_API_KEY' not in os.environ and 'GOOGLE_API_KEY' not in os.environ:
        issues.append("No GEMINI_API_KEY or GOOGLE_API_KEY found")
    else:
        key_source = "GEMINI_API_KEY" if 'GEMINI_API_KEY' in os.environ else "GOOGLE_API_KEY"
        print(f"✅ API Key found: {key_source}")
    
    return issues

async def main():
    """Run all tests"""
    print("Testing VibeKit-based Gemini CLI Integration\n")
    
    # Check environment
    issues = check_environment()
    if issues:
        print("\n❌ Environment issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before testing.")
        return
    
    print("")
    
    # Run tests
    test1 = test_escape_function()
    test2 = await test_vibekit_pattern()
    test3 = await test_vibekit_code_mode()
    
    passed = sum([test1, test2, test3])
    total = 3
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! VibeKit pattern is working perfectly.")
        print("\n✅ The MCP server should now work with this proven pattern.")
    elif passed > 0:
        print("⚠️  Some tests passed. The pattern is working but needs authentication.")
    else:
        print("❌ Pattern not working. Check authentication and setup.")

if __name__ == "__main__":
    asyncio.run(main())
