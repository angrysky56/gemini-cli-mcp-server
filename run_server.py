#!/usr/bin/env python3
"""
CLI runner for the Gemini CLI MCP Server
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main CLI entry point"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Activate virtual environment and run the server
    venv_activate = script_dir / ".venv" / "bin" / "activate"
    server_script = script_dir / "src" / "main.py"

    if not venv_activate.exists():
        print("❌ Virtual environment not found. Please run:")
        print("   cd", script_dir)
        print("   uv venv --python 3.12 --seed")
        print("   source .venv/bin/activate")
        print("   uv add mcp aiofiles pydantic typing-extensions")
        sys.exit(1)

    if not server_script.exists():
        print("❌ Server script not found:", server_script)
        sys.exit(1)

    # Set up environment
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(script_dir / ".venv")
    env["PATH"] = f"{script_dir / '.venv' / 'bin'}:{env['PATH']}"

    print("🚀 Starting Gemini CLI MCP Server...")
    print("📍 Project directory:", script_dir)
    print("🐍 Server script:", server_script)
    print()

    try:
        # Run the server
        result = subprocess.run([
            str(script_dir / ".venv" / "bin" / "python"),
            str(server_script)
        ], env=env, cwd=str(script_dir))

        sys.exit(result.returncode)

    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
