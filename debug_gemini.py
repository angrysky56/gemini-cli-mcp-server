#!/usr/bin/env python3
"""
Debug script to understand what's happening with Gemini CLI
"""

import pexpect
import sys
import time
import re

# ANSI escape code removal regex
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_ansi(text):
    """Remove ANSI escape codes from text"""
    return ansi_escape.sub('', text)

print("Starting Gemini CLI debug test...")

# Start gemini with --yolo flag
child = pexpect.spawn('gemini --yolo', 
                     timeout=30,
                     dimensions=(24, 80),
                     encoding='utf-8',
                     codec_errors='replace')

# Enable logging to see raw output
child.logfile_read = sys.stdout

print("\n=== Waiting for initial prompt ===")

# Try to read initial output
try:
    # Wait for something - let's see what we get
    index = child.expect([
        'Waiting for auth',
        'Login with Google',
        'Use an API key',
        '> ',  # Normal prompt
        pexpect.TIMEOUT,
        pexpect.EOF
    ], timeout=10)
    
    print(f"\n=== Matched pattern {index} ===")
    print(f"Before: {repr(child.before)}")
    print(f"After: {repr(child.after)}")
    
    # Clean output
    if child.before:
        cleaned = clean_ansi(child.before)
        print(f"\n=== Cleaned output ===")
        print(cleaned)
    
except pexpect.TIMEOUT:
    print("\n=== TIMEOUT - dumping buffer ===")
    print(f"Buffer content: {repr(child.buffer)}")
    print(f"Before: {repr(child.before)}")
    
except Exception as e:
    print(f"\n=== ERROR: {e} ===")

# Try sending a simple command
print("\n=== Sending test command ===")
child.sendline("What is 2+2?")

# Wait for response
try:
    child.expect(['> ', pexpect.TIMEOUT], timeout=5)
    print(f"\n=== Response ===")
    print(clean_ansi(child.before))
except:
    print("\n=== No response ===")

child.close()
print("\n=== Test complete ===")
