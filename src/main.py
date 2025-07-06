#!/usr/bin/env python3
"""
Gemini CLI MCP Server

A simple MCP server that provides access to the user's pre-authenticated gemini-cli.
The user must already have gemini-cli installed and authenticated.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import uuid
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions

from gemini_cli_wrapper import GeminiCLIWrapper, GeminiInteractiveSession, InteractivePromptDetected

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Global cleanup handlers
def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def find_gemini_command() -> str:
    """Find the gemini command in PATH"""
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
        logger.info(f"Found gemini command at: {path}")
        return "gemini"  # Use the command name, not the full path
    except subprocess.CalledProcessError:
        raise Exception("gemini command not found in PATH. Please install and authenticate gemini-cli first.")


class GeminiCLIMCPServer:
    """MCP Server for Gemini CLI"""

    def __init__(self) -> None:
        self.server = Server("gemini-cli-mcp-server")
        self.sessions: dict[str, GeminiInteractiveSession] = {}
        self.background_tasks: dict[str, dict[str, Any]] = {}

        # Verify gemini is available
        try:
            gemini_command = find_gemini_command()
            self.gemini_cli = GeminiCLIWrapper(gemini_command)
            logger.info("Gemini CLI wrapper initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini CLI wrapper: {e}")
            raise

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up all MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="gemini_start_session",
                    description="Start an interactive Gemini CLI session for ongoing conversation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Unique identifier for this session"
                            },
                            "starting_directory": {
                                "type": "string",
                                "description": "Optional: The directory to start the Gemini CLI session in. Defaults to the user's home directory.",
                                "default": "~"
                            },
                            "auto_approve": {
                                "type": "boolean",
                                "description": "Optional: Auto-approve tool executions. Defaults to true for MCP usage.",
                                "default": True
                            }
                        },
                        "required": ["session_id"]
                    }
                ),
                types.Tool(
                    name="gemini_session_chat",
                    description="Send a message to a session. This is non-blocking and returns a task_id.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier"
                            },
                            "message": {
                                "type": "string",
                                "description": "Message/prompt to send to the session"
                            }
                        },
                        "required": ["session_id", "message"]
                    }
                ),
                types.Tool(
                    name="gemini_check_task_status",
                    description="Check the status of a background task and retrieve the result when complete.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID of the task to check"
                            }
                        },
                        "required": ["task_id"]
                    }
                ),
                types.Tool(
                    name="gemini_session_respond_to_interaction",
                    description="Respond to an interactive prompt in a blocked session.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID of the blocked task"
                            },
                            "response_text": {
                                "type": "string",
                                "description": "The text to send as a response to the prompt"
                            }
                        },
                        "required": ["task_id", "response_text"]
                    }
                ),
                types.Tool(
                    name="gemini_close_session",
                    description="Close an interactive Gemini CLI session.",
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
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool execution requests"""
            try:
                if name == "gemini_start_session":
                    result = await self._start_session(arguments)
                elif name == "gemini_session_chat":
                    result = await self._session_chat(arguments)
                elif name == "gemini_check_task_status":
                    result = await self._check_task_status(arguments)
                elif name == "gemini_session_respond_to_interaction":
                    result = await self._respond_to_interaction(arguments)
                elif name == "gemini_close_session":
                    result = await self._close_session(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [types.TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=error_msg)]

    async def _start_session(self, arguments: dict[str, Any]) -> str:
        """Start a new Gemini CLI session"""
        session_id = arguments["session_id"]
        starting_directory = arguments.get("starting_directory", os.path.expanduser("~"))
        auto_approve = arguments.get("auto_approve", True)

        # Clean up any dead sessions first
        await self._cleanup_dead_sessions()

        if session_id in self.sessions:
            return f"Error: Session {session_id} already exists"

        try:
            # Build command - just use basic gemini with auto-approve if requested
            cmd_parts = ["gemini"]
            if auto_approve:
                cmd_parts.append("--yolo")

            # Create and start the session
            session = GeminiInteractiveSession(
                cmd_parts=cmd_parts,
                working_directory=starting_directory,
                auto_approve=auto_approve
            )

            # Start the session
            await session.start()

            # Store the session
            self.sessions[session_id] = session

            logger.info(f"Started session {session_id} in {starting_directory}")
            return f"Session {session_id} started successfully in {starting_directory}"

        except Exception as e:
            logger.error(f"Failed to start session {session_id}: {e}")
            return f"Error: Failed to start session {session_id}: {str(e)}"

    async def _session_chat(self, arguments: dict[str, Any]) -> str:
        """Send a message to a session (async)"""
        session_id = arguments["session_id"]
        message = arguments["message"]

        # Validate session exists
        if session_id not in self.sessions:
            return f"Error: Session {session_id} not found"

        session = self.sessions[session_id]
        if not session.is_running():
            await self._cleanup_dead_sessions()
            return f"Error: Session {session_id} is no longer active"

        # Start background task
        task_id = str(uuid.uuid4())

        try:
            # Estimate completion time
            estimate = self._estimate_task_time(message)

            # Create the background task
            task = asyncio.create_task(self._execute_chat_task(task_id, session, message))

            self.background_tasks[task_id] = {
                'status': 'RUNNING',
                'task': task,
                'session_id': session_id,
                'estimate': estimate
            }

            return json.dumps({
                "status": "STARTED",
                "task_id": task_id,
                "estimated_completion": estimate,
                "message": f"Task started. Check status with gemini_check_task_status using task_id: {task_id}"
            }, indent=2)

        except Exception as e:
            logger.error(f"Error starting chat task: {e}")
            return f"Error: Failed to start chat task: {str(e)}"

    async def _execute_chat_task(self, task_id: str, session: GeminiInteractiveSession, message: str) -> None:
        """Execute a chat task in the background"""
        try:
            logger.info(f"Executing task {task_id}: {message[:50]}...")
            result = await session.send_prompt(message)

            # Task completed successfully
            self.background_tasks[task_id]['status'] = 'COMPLETED'
            self.background_tasks[task_id]['result'] = result
            logger.info(f"Task {task_id} completed successfully")

        except InteractivePromptDetected as e:
            # Task blocked on user interaction
            logger.info(f"Task {task_id} blocked on interaction: {e.prompt_text}")
            self.background_tasks[task_id]['status'] = 'BLOCKED_ON_INTERACTION'
            self.background_tasks[task_id]['prompt'] = e.prompt_text

        except Exception as e:
            # Task failed
            logger.error(f"Task {task_id} failed: {e}")
            self.background_tasks[task_id]['status'] = 'ERROR'
            self.background_tasks[task_id]['result'] = str(e)

    def _estimate_task_time(self, message: str) -> str:
        """Estimate how long a task might take"""
        message_lower = message.lower()

        # Quick commands
        if message.strip().startswith('/'):
            return "5-10 seconds"

        # File operations with @
        if '@' in message:
            return "30 seconds - 2 minutes"

        # Complex requests
        complex_keywords = ["analyze", "refactor", "implement", "create", "write", "generate"]
        if any(keyword in message_lower for keyword in complex_keywords) or len(message) > 500:
            return "2-10 minutes"

        # Default
        return "30-60 seconds"

    async def _check_task_status(self, arguments: dict[str, Any]) -> str:
        """Check the status of a background task"""
        task_id = arguments["task_id"]

        if task_id not in self.background_tasks:
            return json.dumps({"status": "NOT_FOUND", "message": f"Task {task_id} not found"})

        task_info = self.background_tasks[task_id]
        status = task_info["status"]

        if status == 'RUNNING':
            return json.dumps({
                "status": "RUNNING",
                "estimated_completion": task_info.get('estimate', 'Unknown'),
                "message": "Task is still running. Check again later."
            })

        elif status == 'BLOCKED_ON_INTERACTION':
            return json.dumps({
                "status": "BLOCKED_ON_INTERACTION",
                "prompt": task_info.get('prompt', 'Unknown prompt'),
                "message": "Task is waiting for user input. Use gemini_session_respond_to_interaction to respond."
            }, indent=2)

        elif status == 'COMPLETED':
            result = task_info.get('result', 'No result available')
            # Clean up completed task
            del self.background_tasks[task_id]
            return json.dumps({
                "status": "COMPLETED",
                "result": result
            }, indent=2)

        elif status == 'ERROR':
            error = task_info.get('result', 'Unknown error')
            # Clean up failed task
            del self.background_tasks[task_id]
            return json.dumps({
                "status": "ERROR",
                "error": error
            }, indent=2)

        return json.dumps({"status": "UNKNOWN"})

    async def _respond_to_interaction(self, arguments: dict[str, Any]) -> str:
        """Respond to an interactive prompt"""
        task_id = arguments["task_id"]
        response_text = arguments["response_text"]

        if task_id not in self.background_tasks:
            return f"Error: Task {task_id} not found"

        task_info = self.background_tasks[task_id]

        if task_info['status'] != 'BLOCKED_ON_INTERACTION':
            return f"Error: Task {task_id} is not blocked on interaction (status: {task_info['status']})"

        session_id = task_info.get('session_id')
        if not session_id or session_id not in self.sessions:
            return f"Error: Session for task {task_id} not found"

        session = self.sessions[session_id]

        try:
            # Send the response to the child process
            if session.child:
                await asyncio.get_event_loop().run_in_executor(
                    None, session.child.sendline, response_text
                )

                # Resume the task
                task_info['status'] = 'RUNNING'
                if 'prompt' in task_info:
                    del task_info['prompt']

                # Restart monitoring the task
                task_info['task'] = asyncio.create_task(
                    self._execute_chat_task(task_id, session, "")  # Empty message to continue
                )

                return f"Response '{response_text}' sent to task {task_id}. Task is now running."
            else:
                return f"Error: Session child process not available for task {task_id}"

        except Exception as e:
            logger.error(f"Error responding to interaction: {e}")
            return f"Error: Failed to send response: {str(e)}"

    async def _close_session(self, arguments: dict[str, Any]) -> str:
        """Close a session"""
        session_id = arguments["session_id"]

        if session_id not in self.sessions:
            return f"Error: Session {session_id} not found"

        session = self.sessions[session_id]

        try:
            await session.close()
            del self.sessions[session_id]

            # Cancel any background tasks for this session
            tasks_to_remove = [
                task_id for task_id, task_info in self.background_tasks.items()
                if task_info.get('session_id') == session_id
            ]

            for task_id in tasks_to_remove:
                task_info = self.background_tasks[task_id]
                if 'task' in task_info and not task_info['task'].done():
                    task_info['task'].cancel()
                del self.background_tasks[task_id]

            logger.info(f"Closed session {session_id}")
            return f"Session {session_id} closed successfully"

        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")
            return f"Error: Failed to close session {session_id}: {str(e)}"

    async def _cleanup_dead_sessions(self) -> None:
        """Remove sessions that are no longer running"""
        dead_sessions = [
            session_id for session_id, session in self.sessions.items()
            if not session.is_running()
        ]

        for session_id in dead_sessions:
            logger.info(f"Cleaning up dead session: {session_id}")
            try:
                await self.sessions[session_id].close()
            except Exception:
                pass
            del self.sessions[session_id]

    async def cleanup(self) -> None:
        """Clean up all resources"""
        logger.info("Cleaning up server resources...")

        # Cancel all background tasks
        for task_info in self.background_tasks.values():
            if 'task' in task_info and not task_info['task'].done():
                task_info['task'].cancel()

        # Close all sessions
        for session in self.sessions.values():
            try:
                await session.close()
            except Exception as e:
                logger.warning(f"Error closing session during cleanup: {e}")

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
                        ),
                    )
                )
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


async def main() -> None:
    """Main entry point"""
    server = None
    try:
        logger.info("Initializing Gemini CLI MCP Server")
        server = GeminiCLIMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        if server:
            await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
