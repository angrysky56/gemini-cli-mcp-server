#!/usr/bin/env python3
"""
Proper Gemini CLI MCP Server

An MCP server that provides access to the actual gemini-cli binary,
leveraging all its built-in tools and capabilities.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import uuid
from collections.abc import Coroutine
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
    """MCP Server that wraps the actual Gemini CLI with persistent session"""

    def __init__(self) -> None:
        self.server = Server("gemini-cli-mcp-server")
        self.interactive_sessions: dict[str, GeminiInteractiveSession] = {}
        self.session_metadata: dict[str, dict[str, Any]] = {}
        self.background_tasks: dict[str, dict[str, Any]] = {}

        try:
            gemini_cli_path = find_gemini_command()
            self.gemini_cli = GeminiCLIWrapper(gemini_cli_path)
            logger.info(f"Gemini CLI wrapper initialized successfully (path: {gemini_cli_path})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini CLI wrapper: {str(e)}")
            raise
        self._setup_handlers()

    async def cleanup(self) -> None:
        """Clean up resources when shutting down"""
        logger.info("Cleaning up active sessions and tasks...")
        for task in self.background_tasks.values():
            if task.get('task') and not task['task'].done():
                task['task'].cancel()
        for session in self.interactive_sessions.values():
            await session.close()

    def _estimate_task(self, message: str) -> tuple[str, str]:
        """Estimates the complexity and duration of a task based on the prompt."""
        message_lower = message.lower()
        is_long_task = False

        # Complex, long-running tasks
        complex_keywords = ["analyze", "refactor", "implement", "write a program", "create a script", "summarize this book"]
        if any(keyword in message_lower for keyword in complex_keywords) or len(message) > 1000:
            estimate = "10-30+ minutes"
            is_long_task = True
        # Medium tasks involving I/O
        elif '@' in message or '!' in message:
            estimate = "1-5 minutes"
        # Simple, quick commands
        elif message.strip() in ["/stats", "/memory show", "/tools"]:
            estimate = "~5-10 seconds"
        else:
            estimate = "~1-2 minutes"

        note = f"Please use gemini_check_task_status with the returned task_id to get the result. Recommended check time is in {estimate}."
        if is_long_task:
            note += " IMPORTANT: This is a long-running task. Do not close the chat or client connection, as it will terminate the process."

        return estimate, note

    def _setup_handlers(self) -> None:
        """Set up all MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available Gemini CLI tools"""
            return [
                types.Tool(
                    name="gemini_start_session",
                    description="Start an interactive Gemini CLI session for ongoing conversation.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Unique identifier for this session"},
                            "starting_directory": {"type": "string", "description": "Optional: The directory to start the Gemini CLI session in. Defaults to the user's home directory."},
                            "auto_approve": {"type": "boolean", "description": "Optional: Auto-approve tool executions. Defaults to true for MCP usage."}
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
                            "session_id": {"type": "string", "description": "Session identifier"},
                            "message": {"type": "string", "description": "Message/prompt to send to the session"}
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
                            "task_id": {"type": "string", "description": "The ID of the task to check"}
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
                            "task_id": {"type": "string", "description": "The ID of the blocked task."},
                            "response_text": {"type": "string", "description": "The text to send as a response to the prompt."}
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
                            "session_id": {"type": "string", "description": "Session identifier"}
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
                    result = await self._start_interactive_session(arguments)
                elif name == "gemini_session_chat":
                    result = await self._session_chat(arguments)
                elif name == "gemini_check_task_status":
                    result = await self._check_task_status(arguments)
                elif name == "gemini_session_respond_to_interaction":
                    result = await self._session_respond_to_interaction(arguments)
                elif name == "gemini_close_session":
                    result = await self._close_session(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [types.TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=error_msg)]

    async def _run_and_monitor_task(self, task_id: str, coro: Coroutine):
        """Wrapper to run a coroutine and store its result, handling interactive prompts."""
        try:
            result = await coro
            self.background_tasks[task_id]['status'] = 'COMPLETE'
            self.background_tasks[task_id]['result'] = result
        except InteractivePromptDetected as e:
            logger.info(f"Task {task_id} blocked on interactive prompt: {e.prompt_text}")
            self.background_tasks[task_id]['status'] = 'BLOCKED_ON_INTERACTION'
            self.background_tasks[task_id]['prompt'] = e.prompt_text
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.background_tasks[task_id]['status'] = 'ERROR'
            self.background_tasks[task_id]['result'] = str(e)

    async def _start_background_task(self, session_id: str, coro: Coroutine, message: str) -> str:
        """Starts a background task and returns its ID with an estimated time."""
        await self._get_session(session_id)
        task_id = str(uuid.uuid4())

        estimated_completion, note = self._estimate_task(message)

        task = asyncio.create_task(self._run_and_monitor_task(task_id, coro))
        self.background_tasks[task_id] = {
            'status': 'RUNNING',
            'task': task,
            'session_id': session_id # Store session_id for responding to interaction
        }

        response = {
            "status": "STARTED",
            "task_id": task_id,
            "estimated_completion": estimated_completion,
            "note": note
        }
        return json.dumps(response, indent=2)

    async def _session_chat(self, arguments: dict[str, Any]) -> str:
        """Send a message to an interactive session as a background task."""
        session_id = arguments["session_id"]
        message = arguments["message"]
        session = await self._get_session(session_id)
        return await self._start_background_task(session_id, session.send_prompt(message), message)

    async def _check_task_status(self, arguments: dict[str, Any]) -> str:
        """Checks the status of a background task."""
        task_id = arguments["task_id"]
        task_info = self.background_tasks.get(task_id)

        if not task_info:
            return json.dumps({"status": "NOT_FOUND"})

        status = task_info["status"]
        if status == 'RUNNING':
            return json.dumps({"status": "RUNNING"})
        elif status == 'BLOCKED_ON_INTERACTION':
            return json.dumps({
                "status": "BLOCKED_ON_INTERACTION",
                "prompt": task_info.get('prompt', 'No prompt text available.')
            }, indent=2)
        else:
            result = task_info.get('result', 'No result found.')
            del self.background_tasks[task_id]
            return json.dumps({"status": status, "result": result}, indent=2)

    async def _session_respond_to_interaction(self, arguments: dict[str, Any]) -> str:
        """Responds to an interactive prompt in a blocked session."""
        task_id = arguments["task_id"]
        response_text = arguments["response_text"]
        task_info = self.background_tasks.get(task_id)

        if not task_info:
            return f"Error: Task {task_id} not found."
        if task_info['status'] != 'BLOCKED_ON_INTERACTION':
            return f"Error: Task {task_id} is not blocked on interaction. Current status: {task_info['status']}"

        session_id = task_info.get('session_id')
        if not session_id:
            return f"Error: Could not find session_id for task {task_id}."

        session = await self._get_session(session_id)

        # Send the response to the child process
        if session.child is None:
            return f"Error: Session child process is not available for session {session_id}."
        await asyncio.get_event_loop().run_in_executor(
            None, session.child.sendline, response_text
        )

        # Reset task status to RUNNING and restart monitoring
        task_info['status'] = 'RUNNING'
        # Re-start monitoring the task by calling send_prompt with an empty string
        # This will cause _read_response to continue reading from the child process
        task_info['task'] = asyncio.create_task(self._run_and_monitor_task(task_id, session.send_prompt("")))
        del task_info['prompt'] # Clear the prompt text

        return f"Response '{response_text}' sent to task {task_id}. Task is now RUNNING."

    async def _start_interactive_session(self, arguments: dict[str, Any]) -> str:
        """Start an interactive Gemini CLI session"""
        session_id = arguments["session_id"]
        starting_directory = arguments.get("starting_directory", os.path.expanduser("~"))
        await self._cleanup_dead_sessions()
        if session_id in self.interactive_sessions:
            return f"Session {session_id} already exists"
        try:
            session = await self.gemini_cli.start_interactive_session(
                working_directory=starting_directory, # Pass working_directory
                model=arguments.get("model"), # Pass model
                debug=arguments.get("debug", False), # Pass debug
                checkpointing=arguments.get("checkpointing", False), # Pass checkpointing
                auto_approve=arguments.get("auto_approve", True)  # Default to True for MCP usage
            )
            self.interactive_sessions[session_id] = session
            self.session_metadata[session_id] = {"created_at": asyncio.get_event_loop().time()}
            return f"Interactive session {session_id} started successfully with auto-approval enabled"
        except Exception as e:
            logger.error(f"Failed to start session {session_id}: {str(e)}")
            return f"Failed to start session {session_id}: {str(e)}"

    async def _close_session(self, arguments: dict[str, Any]) -> str:
        """Close an interactive session"""
        session_id = arguments["session_id"]
        session = await self._get_session(session_id)
        await session.close()
        if session_id in self.interactive_sessions:
            del self.interactive_sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        return f"Session {session_id} closed successfully"

    async def _get_session(self, session_id: str) -> GeminiInteractiveSession:
        """Get an existing session or raise an error if not found"""
        if session_id not in self.interactive_sessions:
            raise Exception(f"Session {session_id} not found or has been closed.")
        session = self.interactive_sessions[session_id]
        if not session.is_running():
            await self._cleanup_dead_sessions()
            raise Exception(f"Session {session_id} is no longer alive.")
        return session

    async def _cleanup_dead_sessions(self) -> None:
        """Remove sessions that are no longer running"""
        dead_sessions = [sid for sid, s in self.interactive_sessions.items() if not s.is_running()]
        for session_id in dead_sessions:
            logger.info(f"Cleaning up dead session: {session_id}")
            if session_id in self.interactive_sessions:
                del self.interactive_sessions[session_id]
            if session_id in self.session_metadata:
                del self.session_metadata[session_id]

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
            logger.error(f"Failed to start server: {e}")
            raise

async def main() -> None:
    """Main entry point"""
    server = None
    try:
        logger.info("Initializing Gemini CLI MCP Server")
        server = GeminiCLIMCPServer()
        logger.info("Server initialized, starting...")
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
