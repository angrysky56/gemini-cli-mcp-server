#!/usr/bin/env python3
"""
PTY-based Gemini CLI Wrapper for MCP Server

This module provides a proper interface to the actual gemini-cli binary using PTY,
which allows proper terminal interaction for meta-commands like /tools, /mcp, etc.
"""

import asyncio
import fcntl
import logging
import os
import pty
import shlex
import signal
import subprocess
import sys

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class GeminiCLIWrapper:
    """PTY-based wrapper for the actual gemini CLI binary"""

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
            result = subprocess.run(
                [self.gemini_command, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception(f"Gemini CLI not working (exit code {result.returncode}): {result.stderr}")

            version_info = result.stdout.strip()
            logger.info(f"Gemini CLI available: {version_info}")

        except FileNotFoundError:
            raise Exception(f"Gemini CLI command '{self.gemini_command}' not found in PATH")
        except subprocess.TimeoutExpired:
            raise Exception("Gemini CLI version check timed out")
        except Exception as e:
            raise Exception(f"Failed to verify Gemini CLI: {str(e)}")

    async def start_interactive_session(
        self,
        working_directory: str = ".",
        model: str | None = None,
        debug: bool = False,
        checkpointing: bool = False
    ) -> 'GeminiInteractiveSession':
        """
        Start an interactive Gemini CLI session using PTY.

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
            cmd_parts.extend(["-m", model])
        if debug:
            cmd_parts.append("-d")
        if checkpointing:
            cmd_parts.append("-c")

        try:
            logger.debug(f"Starting PTY-based interactive session: {' '.join(cmd_parts)}")

            # Create a pseudo-terminal for proper CLI interaction
            master_fd, slave_fd = pty.openpty()

            # Start the process with the PTY
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=working_directory,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=os.environ.copy(),
                preexec_fn=os.setsid  # Create a new process group
            )

            # Close the slave fd in the parent process
            os.close(slave_fd)

            session = GeminiInteractiveSession(process, master_fd, working_directory)
            await session.wait_for_ready()
            return session

        except Exception as e:
            error_msg = f"Failed to start interactive session: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def list_tools(self, working_directory: str = ".") -> str:
        """Get the list of available tools from Gemini CLI"""
        try:
            session = await self.start_interactive_session(working_directory=working_directory)
            try:
                response = await session.send_command("/tools", timeout=20.0)
                return response if response.strip() else "No tools information returned"
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error getting tools info: {str(e)}")
            return f"Error getting tools info: {str(e)}"

    async def list_mcp_servers(self, working_directory: str = ".") -> str:
        """Get the list of configured MCP servers"""
        try:
            session = await self.start_interactive_session(working_directory=working_directory)
            try:
                response = await session.send_command("/mcp", timeout=20.0)
                return response if response.strip() else "No MCP server information returned"
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error getting MCP servers: {str(e)}")
            return f"Error getting MCP servers: {str(e)}"

    async def get_memory(self, working_directory: str = ".") -> str:
        """Get the current memory/context from Gemini CLI"""
        return await self._execute_session_command("/memory show", working_directory)

    async def get_stats(self, working_directory: str = ".") -> str:
        """Get session statistics from Gemini CLI"""
        return await self._execute_session_command("/stats", working_directory)

    async def _execute_session_command(self, command: str, working_directory: str = ".") -> str:
        """Execute a command in a temporary interactive session"""
        try:
            logger.debug(f"Executing session command: {command}")
            session = await self.start_interactive_session(working_directory)
            try:
                response = await session.send_command(command)
                return response
            finally:
                await session.close()
        except Exception as e:
            error_msg = f"Failed to execute session command '{command}': {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"


class GeminiInteractiveSession:
    """Manages an interactive Gemini CLI session with PTY support"""

    def __init__(self, process: asyncio.subprocess.Process, master_fd: int, working_directory: str):
        self.process = process
        self.master_fd = master_fd
        self.working_directory = working_directory
        self._ready = False

    async def wait_for_ready(self, timeout: float = 10.0) -> None:
        """Wait for the session to be ready for input"""
        try:
            # Give the process a moment to start up
            await asyncio.sleep(2.0)

            # Check if process is still running
            if self.process.returncode is not None:
                raise Exception(f"Gemini CLI process terminated during startup: {self.process.returncode}")

            # Try to read any initial output and discard it
            await self._drain_initial_output()

            self._ready = True
            logger.info("Gemini PTY session ready")
        except Exception as e:
            await self._cleanup()
            raise Exception(f"Failed to initialize PTY session: {str(e)}")

    async def _drain_initial_output(self) -> None:
        """Read and discard any initial output from Gemini CLI startup"""
        try:
            # Set the master fd to non-blocking mode
            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Read any available data for a short time
            for _ in range(10):
                try:
                    data = os.read(self.master_fd, 1024)
                    if data:
                        chunk = data.decode('utf-8', errors='ignore')
                        logger.debug(f"Initial output: {repr(chunk[:100])}")
                    else:
                        break
                except OSError:
                    # No more data available
                    break
                await asyncio.sleep(0.1)

            # Set back to blocking mode
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags)

        except Exception as e:
            logger.debug(f"Error draining initial output: {e}")

    async def send_command(self, command: str, timeout: float = 30.0) -> str:
        """Send a command to the PTY session and get the response"""
        if not self._ready:
            raise Exception("Session not ready")

        try:
            logger.debug(f"Sending command to PTY: {command}")

            # Send the command
            command_bytes = f"{command}\n".encode()
            os.write(self.master_fd, command_bytes)

            # Wait for the response - focus on reading what comes AFTER the command
            response = await asyncio.wait_for(
                self._read_incremental_response(),
                timeout
            )

            logger.debug(f"Command '{command}' response length: {len(response)}")
            return response.strip()

        except asyncio.TimeoutError:
            logger.error(f"PTY command timed out: {command}")
            raise Exception(f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Error sending PTY command '{command}': {str(e)}")
            raise Exception(f"Error: {str(e)}")

    async def _read_incremental_response(self) -> str:
        """Read only the new output that appears after sending a command"""
        buffer = ""
        start_time = asyncio.get_event_loop().time()
        last_data_time = start_time
        consecutive_empty_reads = 0

        # Wait a moment for the command to start producing output
        await asyncio.sleep(0.5)

        logger.debug("Reading incremental response...")

        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            time_since_data = current_time - last_data_time

            # Stop conditions
            if elapsed > 20.0:  # Max time to wait
                logger.debug("Max wait time reached")
                break

            # If we have content and no new data for a while, assume done
            if len(buffer.strip()) > 50 and time_since_data > 2.0:
                logger.debug(f"Have output ({len(buffer)} chars) and no data for {time_since_data:.1f}s")
                break

            # If no output at all after reasonable time, assume command had no output
            if len(buffer.strip()) == 0 and elapsed > 5.0:
                logger.debug("No output after 5s, command may have no response")
                break

            try:
                # Try to read new data
                loop = asyncio.get_event_loop()
                data = await asyncio.wait_for(
                    loop.run_in_executor(None, self._read_pty_nonblocking),
                    timeout=1.0
                )

                if data:
                    consecutive_empty_reads = 0
                    last_data_time = current_time
                    chunk = data.decode('utf-8', errors='ignore')
                    buffer += chunk
                    logger.debug(f"Read {len(chunk)} chars")
                else:
                    consecutive_empty_reads += 1
                    if consecutive_empty_reads > 5 and len(buffer.strip()) > 0:
                        logger.debug("Multiple empty reads with content, stopping")
                        break

            except asyncio.TimeoutError:
                # No data available, continue
                continue
            except Exception as e:
                logger.debug(f"Read error: {e}")
                break

        logger.debug(f"Incremental response complete: {len(buffer)} chars")
        return self._clean_pty_output(buffer)


    def _command_output_complete(self, buffer: str) -> bool:
        """Check if command output appears complete"""
        if not buffer:
            return False

        # Clean the buffer first
        clean_buffer = self._clean_pty_output(buffer)

        # For meta commands like /tools, /mcp, etc., look for specific completion patterns
        # These commands typically show lists and then return to prompt
        if len(clean_buffer.strip()) > 50:  # Reasonable amount of output
            lines = clean_buffer.split('\n')
            if len(lines) > 3:  # Multiple lines of output
                # Check if we see a prompt or completion at the end
                last_lines = ' '.join(lines[-2:]).lower()
                if any(indicator in last_lines for indicator in [
                    'type your message',
                    'enter your prompt',
                    'what can i help',
                    'ctrl+',  # Control key hints
                    '>'  # Prompt character
                ]):
                    return True

        return False

    def _looks_like_prompt_ready(self, buffer: str) -> bool:
        """Check if the buffer contains indicators that we're back at a ready prompt"""
        if not buffer:
            return False

        # Look for common prompt indicators (without colors)
        clean_buffer = self._clean_pty_output(buffer).lower()

        # Check for Gemini CLI prompt indicators
        prompt_indicators = [
            "type your message",
            "enter your prompt",
            "what can i help",
            "waiting for input",
            "> ",  # Common prompt character
        ]

        # Also check if we see the command echo followed by output
        lines = clean_buffer.split('\n')
        if len(lines) > 5:  # If we have multiple lines, might be complete
            last_few_lines = ' '.join(lines[-3:]).strip()
            if any(indicator in last_few_lines for indicator in prompt_indicators):
                return True

        return False

    def _clean_pty_output(self, text: str) -> str:
        """Clean up PTY output by removing ANSI codes, loading bars, etc."""
        import re

        # Remove ANSI escape sequences (colors, cursor movements, etc.)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)

        # Remove common loading/progress indicators
        progress_patterns = [
            r'░+',  # Block characters used in progress bars
            r'▓+',  # Block characters
            r'█+',  # Block characters
            r'[▏▎▍▌▋▊▉█]+',  # Progress bar characters
            r'[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]+',  # Spinner characters
            r'\s*\.\.\.\s*',  # Loading dots
            r'\s*Loading.*?\n',  # Loading messages
            r'\s*Initializing.*?\n',  # Initialization messages
        ]

        for pattern in progress_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple empty lines
        text = re.sub(r'[ \t]+\n', '\n', text)  # Trailing spaces
        text = re.sub(r'\n+$', '', text)  # Trailing newlines
        text = re.sub(r'^\n+', '', text)  # Leading newlines

        return text.strip()

    def _read_pty_nonblocking(self) -> bytes:
        """Non-blocking read from PTY"""
        try:
            return os.read(self.master_fd, 1024)
        except OSError:
            return b""

    async def include_files(self, files: list[str]) -> str:
        """Include files in the conversation using @ syntax"""
        if not files:
            raise Exception("No files specified")
        file_refs = " ".join(f"@{shlex.quote(file)}" for file in files)
        return await self.send_command(file_refs)

    async def run_shell_command(self, command: str) -> str:
        """Run a shell command using the ! syntax"""
        if not command.strip():
            raise Exception("Empty command")
        return await self.send_command(f"!{command}")

    async def save_memory(self, text: str) -> str:
        """Save something to memory"""
        if not text.strip():
            raise Exception("Empty text to save")
        return await self.send_command(f"/memory add {shlex.quote(text)}")

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

    async def _cleanup(self) -> None:
        """Clean up the PTY and process"""
        try:
            if self.master_fd:
                os.close(self.master_fd)
        except Exception:
            pass

        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except Exception:
                self.process.kill()
                await self.process.wait()

    async def close(self) -> None:
        """Close the interactive session"""
        self._ready = False
        try:
            if self.process.returncode is None:
                logger.debug("Attempting to close PTY session gracefully")

                # Try to send quit commands
                for close_command in ["/quit", "/exit"]:
                    try:
                        command_bytes = f"{close_command}\n".encode()
                        os.write(self.master_fd, command_bytes)

                        # Give it time to respond
                        await asyncio.sleep(1.0)

                        if self.process.returncode is not None:
                            logger.debug(f"Session closed gracefully with '{close_command}'")
                            return
                    except Exception:
                        continue

                # If quit commands didn't work, send Ctrl+C
                logger.debug("Quit commands failed, sending Ctrl+C")
                try:
                    os.write(self.master_fd, b'\x03')  # Ctrl+C
                    await asyncio.sleep(1.0)

                    if self.process.returncode is not None:
                        logger.debug("Session closed with Ctrl+C")
                        return
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error during graceful close: {e}")
        finally:
            await self._cleanup()
