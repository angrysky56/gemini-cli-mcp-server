#!/usr/bin/env python3
"""
Proper Gemini CLI Wrapper for MCP Server

This module provides a proper interface to the actual gemini-cli binary,
leveraging all its built-in capabilities and tools.
"""

import asyncio
import logging
import shlex
import subprocess

logger = logging.getLogger(__name__)


class GeminiCLIWrapper:
    """Wrapper for the actual gemini CLI binary"""

    def __init__(self, gemini_command: str = "gemini"):
        """
        Args:
            gemini_command: The command to run gemini-cli (default: "gemini")
        """
        self.gemini_command = gemini_command
        self._verify_gemini_available()

    def _verify_gemini_available(self) -> None:
        """Verify that gemini-cli is available and working"""
        try:
            # Use shell=True to properly inherit PATH from the environment
            result = subprocess.run(
                f"{self.gemini_command} --version",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception(f"Gemini CLI not working: {result.stderr}")
            logger.info(f"Gemini CLI available: {result.stdout.strip()}")
        except Exception as e:
            raise Exception(f"Failed to verify Gemini CLI: {str(e)}")

    async def execute_prompt(
        self,
        prompt: str,
        working_directory: str = ".",
        model: str | None = None,
        include_files: list[str] | None = None,
        debug: bool = False,
        yolo: bool = False,
        checkpointing: bool = False
    ) -> str:
        """
        Execute a single prompt using gemini CLI with -p flag.

        Args:
            prompt: The prompt to send to Gemini
            working_directory: Directory to run gemini from
            model: Optional model to use (e.g., "gemini-2.5-pro")
            include_files: Optional list of files to include with @ syntax
            debug: Enable debug mode
            yolo: Enable auto-approval mode
            checkpointing: Enable checkpointing

        Returns:
            The response from Gemini CLI
        """
        # Build the command string
        cmd_parts = [self.gemini_command]

        if model:
            cmd_parts.extend(["-m", shlex.quote(model)])
        if debug:
            cmd_parts.append("-d")
        if yolo:
            cmd_parts.append("-y")
        if checkpointing:
            cmd_parts.append("-c")

        # Include files using @ syntax if specified
        if include_files:
            file_refs = " ".join(f"@{shlex.quote(file)}" for file in include_files)
            prompt = f"{file_refs} {prompt}"

        cmd_parts.extend(["-p", shlex.quote(prompt)])
        cmd_string = " ".join(cmd_parts)

        try:
            # Run gemini CLI from the specified working directory using shell=True
            result = await asyncio.create_subprocess_shell(
                cmd_string,
                cwd=working_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()
            if stdout is not None:
                stdout = stdout.decode()
            if stderr is not None:
                stderr = stderr.decode()

            if result.returncode != 0:
                error_msg = f"Gemini CLI failed: {stderr}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

            return stdout.strip()

        except Exception as e:
            error_msg = f"Failed to execute Gemini CLI: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    async def start_interactive_session(
        self,
        working_directory: str = ".",
        model: str | None = None,
        debug: bool = False,
        checkpointing: bool = False
    ) -> 'GeminiInteractiveSession':
        """
        Start an interactive Gemini CLI session.

        Args:
            working_directory: Directory to run gemini from
            model: Optional model to use
            debug: Enable debug mode
            checkpointing: Enable checkpointing

        Returns:
            A GeminiInteractiveSession object
        """
        cmd_parts = [self.gemini_command]

        if model:
            cmd_parts.extend(["-m", shlex.quote(model)])
        if debug:
            cmd_parts.append("-d")
        if checkpointing:
            cmd_parts.append("-c")

        cmd_string = " ".join(cmd_parts)

        try:
            process = await asyncio.create_subprocess_shell(
                cmd_string,
                cwd=working_directory,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            session = GeminiInteractiveSession(process, working_directory)
            await session.wait_for_ready()
            return session

        except Exception as e:
            error_msg = f"Failed to start interactive session: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def list_tools(self, working_directory: str = ".") -> str:
        """Get the list of available tools from Gemini CLI"""
        return await self.execute_prompt("/tools", working_directory)

    async def list_mcp_servers(self, working_directory: str = ".") -> str:
        """Get the list of configured MCP servers"""
        return await self.execute_prompt("/mcp", working_directory)

    async def get_memory(self, working_directory: str = ".") -> str:
        """Get the current memory/context from Gemini CLI"""
        return await self.execute_prompt("/memory show", working_directory)

    async def get_stats(self, working_directory: str = ".") -> str:
        """Get session statistics from Gemini CLI"""
        return await self.execute_prompt("/stats", working_directory)


class GeminiInteractiveSession:
    """Manages an interactive Gemini CLI session"""

    def __init__(self, process: asyncio.subprocess.Process, working_directory: str):
        self.process = process
        self.working_directory = working_directory
        self._ready = False

    async def wait_for_ready(self, timeout: float = 30.0) -> None:
        """Wait for the session to be ready for input"""
        try:
            # Wait for the gemini prompt to appear
            await asyncio.wait_for(self._wait_for_prompt(), timeout)
            self._ready = True
        except asyncio.TimeoutError:
            raise Exception("Gemini CLI session did not become ready within timeout")

    async def _wait_for_prompt(self) -> None:
        """Wait for the gemini prompt to appear"""
        buffer = ""
        while True:
            if self.process.stdout is None:
                raise Exception("Process stdout is None")

            data = await self.process.stdout.read(1)
            if not data:
                break

            buffer += data.decode()
            # Look for common prompt indicators
            if any(indicator in buffer for indicator in ["> ", "$ ", "gemini"]):
                break

    async def send_command(self, command: str, timeout: float = 60.0) -> str:
        """
        Send a command to the interactive session and get the response.

        Args:
            command: The command to send
            timeout: Maximum time to wait for response

        Returns:
            The response from Gemini
        """
        if not self._ready:
            raise Exception("Session not ready")

        if self.process.stdin is None:
            raise Exception("Process stdin is None")

        try:
            # Send the command
            self.process.stdin.write(f"{command}\n".encode())
            await self.process.stdin.drain()

            # Read the response
            response = await asyncio.wait_for(
                self._read_until_prompt(),
                timeout
            )

            return response.strip()

        except asyncio.TimeoutError:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _read_until_prompt(self) -> str:
        """Read output until we see a prompt again"""
        buffer = ""
        if self.process.stdout is None:
            return "Error: Process stdout is None"

        while True:
            try:
                data = await self.process.stdout.read(1024)
                if not data:
                    break

                buffer += data.decode()

                # Look for prompt indicators that suggest we're ready for next input
                lines = buffer.split('\n')
                if len(lines) > 1 and any(
                    line.strip().endswith('>') or
                    line.strip().endswith('$') or
                    '>' in line[-10:]  # Look for prompt in last 10 chars
                    for line in lines[-3:]  # Check last 3 lines
                ):
                    break

            except Exception:
                break

        return buffer

    async def include_files(self, files: list[str]) -> str:
        """Include files in the conversation using @ syntax"""
        file_refs = " ".join(f"@{file}" for file in files)
        return await self.send_command(f"Include these files: {file_refs}")

    async def run_shell_command(self, command: str) -> str:
        """Run a shell command using the ! syntax"""
        return await self.send_command(f"!{command}")

    async def save_memory(self, text: str) -> str:
        """Save something to memory"""
        return await self.send_command(f"/memory add {text}")

    async def get_tools(self) -> str:
        """Get available tools"""
        return await self.send_command("/tools")

    async def get_memory(self) -> str:
        """Get current memory"""
        return await self.send_command("/memory show")

    async def get_stats(self) -> str:
        """Get session stats"""
        return await self.send_command("/stats")

    async def compress_context(self) -> str:
        """Compress the conversation context"""
        return await self.send_command("/compress")

    async def close(self) -> None:
        """Close the interactive session"""
        try:
            if self._ready and self.process.stdin:
                self.process.stdin.write(b"/quit\n")
                await self.process.stdin.drain()

            await self.process.wait()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
            if self.process.returncode is None:
                self.process.terminate()
                await self.process.wait()
