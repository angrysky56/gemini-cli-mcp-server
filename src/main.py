#!/usr/bin/env python3
"""
Proper Gemini CLI MCP Server

An MCP server that provides access to the actual gemini-cli binary,
leveraging all its built-in tools and capabilities.
"""

import asyncio
import json
import logging
import signal
import subprocess
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

from gemini_cli_wrapper import GeminiCLIWrapper, GeminiInteractiveSession

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Global cleanup for graceful shutdown
def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    sys.exit(0)


# Register cleanup handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def find_gemini_command() -> str:
    """Find the gemini command path using 'which'"""
    try:
        result = subprocess.run(
            ["which", "gemini"],
            capture_output=True,
            text=True,
            check=True
        )
        path = result.stdout.strip()
        if not path:
            raise Exception("which gemini returned empty path")
        return path
    except subprocess.CalledProcessError:
        raise Exception("gemini command not found in PATH")
    except Exception as e:
        raise Exception(f"Failed to find gemini command: {str(e)}")


class GeminiCLIMCPServer:
    """MCP Server that wraps the actual Gemini CLI"""

    def __init__(self) -> None:
        self.server = Server("gemini-cli-mcp-server")
        try:
            # Dynamically find the gemini command path
            gemini_cli_path = find_gemini_command()
            self.gemini_cli = GeminiCLIWrapper(gemini_cli_path)
            self.interactive_sessions: dict[str, GeminiInteractiveSession] = {}
            logger.info(f"Gemini CLI wrapper initialized successfully (path: {gemini_cli_path})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini CLI wrapper: {str(e)}")
            raise
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up all MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available Gemini CLI tools"""

            tools = [
                types.Tool(
                    name="gemini_prompt",
                    description="Execute a single prompt using Gemini CLI (uses -p flag for non-interactive execution)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt to send to Gemini"
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory to run from",
                                "default": "."
                            },
                            "model": {
                                "type": "string",
                                "description": "Gemini model to use (e.g., 'gemini-2.5-pro', 'gemini-2.5-flash')"
                            },
                            "include_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files to include using @ syntax"
                            },
                            "debug": {
                                "type": "boolean",
                                "description": "Enable debug mode",
                                "default": False
                            },
                            "yolo": {
                                "type": "boolean",
                                "description": "Enable YOLO mode (auto-approve all actions)",
                                "default": False
                            },
                            "checkpointing": {
                                "type": "boolean",
                                "description": "Enable checkpointing for file changes",
                                "default": False
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                types.Tool(
                    name="gemini_start_session",
                    description="Start an interactive Gemini CLI session for ongoing conversation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Unique identifier for this session"
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory for the session",
                                "default": "."
                            },
                            "model": {
                                "type": "string",
                                "description": "Gemini model to use"
                            },
                            "debug": {
                                "type": "boolean",
                                "description": "Enable debug mode",
                                "default": False
                            },
                            "checkpointing": {
                                "type": "boolean",
                                "description": "Enable checkpointing",
                                "default": False
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_session_chat",
                    description="Send a message to an existing interactive Gemini CLI session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "message": {
                                "type": "string",
                                "description": "Message to send to the session"
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Timeout in seconds",
                                "default": 60
                            }
                        },
                        "required": ["session_id", "message"]
                    }
                ),
                types.Tool(
                    name="gemini_session_include_files",
                    description="Include files in an interactive session using @ syntax",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to include"
                            }
                        },
                        "required": ["session_id", "files"]
                    }
                ),
                types.Tool(
                    name="gemini_session_shell",
                    description="Execute shell commands in an interactive session using ! syntax",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": ["session_id", "command"]
                    }
                ),
                types.Tool(
                    name="gemini_session_memory",
                    description="Manage memory in an interactive session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["add", "show"],
                                "description": "Memory action: 'add' to save info, 'show' to view current memory"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to save to memory (required for 'add' action)"
                            }
                        },
                        "required": ["session_id", "action"]
                    }
                ),
                types.Tool(
                    name="gemini_session_tools",
                    description="Get available tools in an interactive session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_session_stats",
                    description="Get session statistics (token usage, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_session_compress",
                    description="Compress conversation context to save tokens",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_close_session",
                    description="Close an interactive Gemini CLI session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_list_tools",
                    description="Get the list of built-in tools from Gemini CLI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory",
                                "default": "."
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="gemini_list_mcp_servers",
                    description="Get the list of configured MCP servers in Gemini CLI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory",
                                "default": "."
                            }
                        },
                        "required": []
                    }
                )
            ]

            return tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent]:
            """Handle tool execution requests"""
            try:
                if name == "gemini_prompt":
                    result = await self._execute_gemini_prompt(arguments)
                elif name == "gemini_start_session":
                    result = await self._start_interactive_session(arguments)
                elif name == "gemini_session_chat":
                    result = await self._session_chat(arguments)
                elif name == "gemini_session_include_files":
                    result = await self._session_include_files(arguments)
                elif name == "gemini_session_shell":
                    result = await self._session_shell(arguments)
                elif name == "gemini_session_memory":
                    result = await self._session_memory(arguments)
                elif name == "gemini_session_tools":
                    result = await self._session_tools(arguments)
                elif name == "gemini_session_stats":
                    result = await self._session_stats(arguments)
                elif name == "gemini_session_compress":
                    result = await self._session_compress(arguments)
                elif name == "gemini_close_session":
                    result = await self._close_session(arguments)
                elif name == "gemini_list_tools":
                    result = await self._list_tools(arguments)
                elif name == "gemini_list_mcp_servers":
                    result = await self._list_mcp_servers(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [types.TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=error_msg)]

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources"""
            return [
                types.Resource(
                    uri=AnyUrl("gemini://status"),
                    name="Gemini CLI Status",
                    description="Current status and session information",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri=AnyUrl("gemini://help"),
                    name="Gemini CLI Help",
                    description="Help information for using this MCP server",
                    mimeType="text/plain"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            """Handle resource read requests"""
            if str(uri) == "gemini://status":
                return await self._get_status()
            elif str(uri) == "gemini://help":
                return await self._get_help()
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def _execute_gemini_prompt(self, arguments: dict[str, Any]) -> str:
        """Execute a single prompt using Gemini CLI"""
        prompt = arguments["prompt"]
        working_directory = arguments.get("working_directory", ".")
        model = arguments.get("model")
        include_files = arguments.get("include_files")
        debug = arguments.get("debug", False)
        yolo = arguments.get("yolo", False)
        checkpointing = arguments.get("checkpointing", False)

        return await self.gemini_cli.execute_prompt(
            prompt=prompt,
            working_directory=working_directory,
            model=model,
            include_files=include_files,
            debug=debug,
            yolo=yolo,
            checkpointing=checkpointing
        )

    async def _start_interactive_session(self, arguments: dict[str, Any]) -> str:
        """Start an interactive Gemini CLI session"""
        session_id = arguments["session_id"]
        working_directory = arguments.get("working_directory", ".")
        model = arguments.get("model")
        debug = arguments.get("debug", False)
        checkpointing = arguments.get("checkpointing", False)

        if session_id in self.interactive_sessions:
            return f"Session {session_id} already exists"

        try:
            session = await self.gemini_cli.start_interactive_session(
                working_directory=working_directory,
                model=model,
                debug=debug,
                checkpointing=checkpointing
            )

            self.interactive_sessions[session_id] = session
            return f"Interactive session {session_id} started successfully"

        except Exception as e:
            return f"Failed to start session {session_id}: {str(e)}"

    async def _session_chat(self, arguments: dict[str, Any]) -> str:
        """Send a message to an interactive session"""
        session_id = arguments["session_id"]
        message = arguments["message"]
        timeout = arguments.get("timeout", 60)

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.send_command(message, timeout)

    async def _session_include_files(self, arguments: dict[str, Any]) -> str:
        """Include files in an interactive session"""
        session_id = arguments["session_id"]
        files = arguments["files"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.include_files(files)

    async def _session_shell(self, arguments: dict[str, Any]) -> str:
        """Execute shell command in an interactive session"""
        session_id = arguments["session_id"]
        command = arguments["command"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.run_shell_command(command)

    async def _session_memory(self, arguments: dict[str, Any]) -> str:
        """Manage memory in an interactive session"""
        session_id = arguments["session_id"]
        action = arguments["action"]
        text = arguments.get("text")

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]

        if action == "add":
            if not text:
                return "Text required for 'add' action"
            return await session.save_memory(text)
        elif action == "show":
            return await session.get_memory()
        else:
            return f"Unknown memory action: {action}"

    async def _session_tools(self, arguments: dict[str, Any]) -> str:
        """Get available tools in an interactive session"""
        session_id = arguments["session_id"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.get_tools()

    async def _session_stats(self, arguments: dict[str, Any]) -> str:
        """Get session statistics"""
        session_id = arguments["session_id"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.get_stats()

    async def _session_compress(self, arguments: dict[str, Any]) -> str:
        """Compress conversation context"""
        session_id = arguments["session_id"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        return await session.compress_context()

    async def _close_session(self, arguments: dict[str, Any]) -> str:
        """Close an interactive session"""
        session_id = arguments["session_id"]

        if session_id not in self.interactive_sessions:
            return f"Session {session_id} not found"

        session = self.interactive_sessions[session_id]
        await session.close()
        del self.interactive_sessions[session_id]
        return f"Session {session_id} closed"

    async def _list_tools(self, arguments: dict[str, Any]) -> str:
        """List built-in tools from Gemini CLI"""
        working_directory = arguments.get("working_directory", ".")
        return await self.gemini_cli.list_tools(working_directory)

    async def _list_mcp_servers(self, arguments: dict[str, Any]) -> str:
        """List configured MCP servers"""
        working_directory = arguments.get("working_directory", ".")
        return await self.gemini_cli.list_mcp_servers(working_directory)

    async def _get_status(self) -> str:
        """Get current status"""
        status = {
            "gemini_cli_available": True,
            "active_sessions": list(self.interactive_sessions.keys()),
            "session_count": len(self.interactive_sessions)
        }
        return json.dumps(status, indent=2)

    async def _get_help(self) -> str:
        """Get help information"""
        return """
Gemini CLI MCP Server

This MCP server provides access to the actual Gemini CLI binary with all its built-in capabilities.

Key Features:
- Execute single prompts with gemini_prompt (uses -p flag)
- Start interactive sessions for ongoing conversations
- Use @ syntax to include files in prompts
- Use ! syntax to execute shell commands
- Manage memory and context with /memory commands
- Access all built-in Gemini CLI tools
- Support for checkpointing and debugging

Authentication:
This server uses your existing Gemini CLI authentication setup.
No additional API keys required - it leverages however you've configured gemini-cli.

Usage Patterns:

1. Single Prompts:
   Use gemini_prompt for one-off questions or tasks.

2. Interactive Sessions:
   - Start with gemini_start_session
   - Chat with gemini_session_chat
   - Include files with gemini_session_include_files
   - Run commands with gemini_session_shell
   - Manage memory with gemini_session_memory
   - Close with gemini_close_session

3. Discovery:
   - Use gemini_list_tools to see available built-in tools
   - Use gemini_list_mcp_servers to see configured MCP servers

This approach preserves all of Gemini CLI's sophisticated ReAct loops,
context management, and built-in tool integrations.
"""

    async def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting Gemini CLI MCP Server")

        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="gemini-cli-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise


async def main() -> None:
    """Main entry point"""
    try:
        logger.info("Initializing Gemini CLI MCP Server")
        server = GeminiCLIMCPServer()
        logger.info("Server initialized, starting...")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
