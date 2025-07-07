#!/usr/bin/env python3
"""
Fixed Gemini CLI MCP Server

Based on VibeKit's proven working implementation pattern.
Uses the exact same approach that works in production VibeKit environments.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class FixedGeminiMCPServer:
    """Fixed MCP Server using VibeKit's proven gemini-cli integration pattern"""

    def __init__(self) -> None:
        self.server = Server("fixed-gemini-mcp-server")
        self._verified = False  # Track if gemini-cli has been verified
        self._setup_handlers()

    async def _verify_gemini(self) -> None:
        """Verify gemini-cli is available (only once)"""
        if self._verified:
            return

        try:
            process = await asyncio.create_subprocess_exec(
                "gemini", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Gemini CLI not working: {stderr.decode()}")
            logger.info(f"Gemini CLI available: {stdout.decode().strip()}")
            self._verified = True
        except Exception as e:
            raise Exception(f"Gemini CLI not found or not working: {e}")

    def _setup_handlers(self) -> None:
        """Set up MCP handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="gemini_ask",
                    description="Ask Gemini a question (uses VibeKit's proven pattern)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Question or prompt for Gemini"
                            },
                            "model": {
                                "type": "string",
                                "description": "Gemini model to use",
                                "default": "gemini-2.5-flash"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory (for file context)",
                                "default": "."
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files to include using @ syntax",
                                "default": []
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in seconds",
                                "default": 60
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                types.Tool(
                    name="gemini_code",
                    description="Generate code changes using Gemini (VibeKit code mode)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Code generation request"
                            },
                            "model": {
                                "type": "string",
                                "description": "Gemini model to use",
                                "default": "gemini-2.5-pro"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory",
                                "default": "."
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in seconds",
                                "default": 120
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                types.Tool(
                    name="gemini_with_files",
                    description="Ask Gemini with specific files (uses @ syntax)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The question or prompt"
                            },
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to include"
                            },
                            "model": {
                                "type": "string",
                                "description": "Gemini model to use",
                                "default": "gemini-2.5-flash"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory",
                                "default": "."
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Timeout in seconds",
                                "default": 90
                            }
                        },
                        "required": ["prompt", "file_paths"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            try:
                # Verify gemini on first use
                await self._verify_gemini()

                if name == "gemini_ask":
                    result = await self._ask_gemini(arguments)
                elif name == "gemini_code":
                    result = await self._code_generation(arguments)
                elif name == "gemini_with_files":
                    result = await self._ask_with_files(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [types.TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=error_msg)]

    async def _ask_gemini(self, arguments: dict[str, Any]) -> str:
        """Ask Gemini using VibeKit's ask mode"""
        prompt = arguments["prompt"]
        model = arguments.get("model", "gemini-2.5-flash")
        working_dir = arguments.get("working_dir", ".")
        files = arguments.get("files", [])
        timeout = arguments.get("timeout", 60)

        # VibeKit's ask mode instruction
        instruction = (
            "Research the repository and answer the user's questions. "
            "Do NOT make any changes to any files in the repository."
        )

        # Build full prompt with files
        user_prompt = prompt
        if files:
            file_refs = " ".join(f"@{f}" for f in files)
            user_prompt = f"{file_refs} {prompt}"

        full_prompt = f"{instruction}\n\nUser: {user_prompt}"

        return await self._execute_vibekit_pattern(full_prompt, model, working_dir, timeout)

    async def _code_generation(self, arguments: dict[str, Any]) -> str:
        """Generate code using VibeKit's code mode"""
        prompt = arguments["prompt"]
        model = arguments.get("model", "gemini-2.5-pro")
        working_dir = arguments.get("working_dir", ".")
        timeout = arguments.get("timeout", 120)

        # VibeKit's code mode instruction
        instruction = (
            "Do the necessary changes to the codebase based on the users input.\n"
            "Don't ask any follow up questions."
        )

        full_prompt = f"{instruction}\n\nUser: {prompt}"

        return await self._execute_vibekit_pattern(full_prompt, model, working_dir, timeout)

    async def _ask_with_files(self, arguments: dict[str, Any]) -> str:
        """Ask with files using VibeKit pattern"""
        prompt = arguments["prompt"]
        file_paths = arguments["file_paths"]
        model = arguments.get("model", "gemini-2.5-flash")
        working_dir = arguments.get("working_dir", ".")
        timeout = arguments.get("timeout", 90)

        # Build prompt with file references
        file_refs = " ".join(f"@{f}" for f in file_paths)
        full_prompt = f"{file_refs} {prompt}"

        return await self._execute_vibekit_pattern(full_prompt, model, working_dir, timeout)

    async def _escape_prompt_python(self, prompt: str) -> str:
        """Python version of VibeKit's prompt escaping"""
        # Escape backticks, quotes, dollar signs, and backslashes
        import re
        return re.sub(r'[`"$\\]', r'\\\g<0>', prompt)

    async def _execute_vibekit_pattern(self, prompt: str, model: str, working_dir: str, timeout: int) -> str:
        """Execute using VibeKit's exact pattern"""
        try:
            logger.info(f"Executing VibeKit pattern in {working_dir}: {prompt[:50]}...")

            # Escape prompt like VibeKit
            escaped_prompt = self._escape_prompt_python(prompt)

            # Build environment like VibeKit (set both keys)
            exec_env = {
                **os.environ,
                'NODE_NO_WARNINGS': '1',
                'TERM': 'xterm-256color'
            }

            # Add API keys if available
            if 'GEMINI_API_KEY' in os.environ:
                exec_env['GEMINI_API_KEY'] = os.environ['GEMINI_API_KEY']
                exec_env['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']  # VibeKit sets both

            # Use VibeKit's exact command pattern
            cmd_args = [
                "gemini",
                "--model", model,
                "--prompt", escaped_prompt,
                "--yolo"  # VibeKit's auto-approval pattern
            ]

            logger.info(f"VibeKit command: gemini --model {model} --prompt [escaped] --yolo")

            # Execute like VibeKit
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=working_dir,
                env=exec_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Command timed out after {timeout} seconds")

            # Process output
            stdout_text = stdout.decode('utf-8').strip()
            stderr_text = stderr.decode('utf-8').strip()

            if process.returncode != 0:
                if stderr_text:
                    raise Exception(f"Gemini failed (code {process.returncode}): {stderr_text}")
                else:
                    raise Exception(f"Gemini failed with exit code {process.returncode}")

            result = stdout_text or "Command completed successfully"

            if not result:
                return "No output from Gemini"

            logger.info(f"VibeKit pattern success: {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"Error in VibeKit pattern: {e}")
            raise

    async def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting Fixed Gemini MCP Server (VibeKit Pattern)")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="fixed-gemini-mcp-server",
                    server_version="0.4.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                )
            )


async def main() -> None:
    """Main entry point"""
    try:
        server = FixedGeminiMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
