#!/usr/bin/env python3
"""
Debug Gemini CLI process to see what's actually happening
"""

import asyncio
import subprocess
import sys
import os

async def debug_gemini_process():
    """Debug what happens when we start a Gemini CLI process"""
    print("Starting Gemini CLI process in debug mode...")

    # Get the user's environment
    env = os.environ.copy()

    # Start the process with inherited environment
    process = await asyncio.create_subprocess_exec(
        "gemini",
        cwd=".",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    print(f"Process started with PID: {process.pid}")

    async def read_stderr():
        """Read stderr to see any errors or messages"""
        while True:
            try:
                data = await asyncio.wait_for(process.stderr.read(1024), timeout=1.0)
                if not data:
                    break
                message = data.decode('utf-8', errors='ignore')
                print(f"STDERR: {repr(message)}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error reading stderr: {e}")
                break

    # Start reading stderr in background
    stderr_task = asyncio.create_task(read_stderr())

    # Give it a moment to start
    await asyncio.sleep(2.0)

    print("Sending /tools command...")
    process.stdin.write("/tools\n".encode())
    await process.stdin.drain()

    print("Waiting for response...")
    try:
        # Try to read stdout
        data = await asyncio.wait_for(process.stdout.read(1024), timeout=5.0)
        if data:
            response = data.decode('utf-8', errors='ignore')
            print(f"STDOUT: {repr(response)}")
        else:
            print("No data received on stdout")
    except asyncio.TimeoutError:
        print("Timeout waiting for stdout response")

    print("Sending /help command...")
    process.stdin.write("/help\n".encode())
    await process.stdin.drain()

    try:
        # Try to read stdout again
        data = await asyncio.wait_for(process.stdout.read(1024), timeout=5.0)
        if data:
            response = data.decode('utf-8', errors='ignore')
            print(f"STDOUT: {repr(response)}")
        else:
            print("No data received on stdout")
    except asyncio.TimeoutError:
        print("Timeout waiting for stdout response")

    print("Checking process status...")
    print(f"Return code: {process.returncode}")

    # Try to terminate gracefully
    print("Terminating process...")
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=3.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()

    stderr_task.cancel()
    print("Process terminated")

if __name__ == "__main__":
    asyncio.run(debug_gemini_process())
