#!/usr/bin/env python3
"""
Pexpect-based Gemini CLI Wrapper for MCP Server

This module provides a proper interface to the actual gemini-cli binary using pexpect,
the standard library for controlling interactive applications.
"""

import asyncio
import logging
import re
import subprocess
import sys

import pexpect

# Configure logging to stderr for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Custom exception for interactive prompts
class InteractivePromptDetected(Exception):
    def __init__(self, prompt_text: str):
        super().__init__(f"Interactive prompt detected: {prompt_text}")
        self.prompt_text = prompt_text


class GeminiCLIWrapper:
    """Pexpect-based wrapper for the actual gemini CLI binary with persistent session"""

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
        Start an interactive Gemini CLI session using pexpect.

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
            logger.debug(f"Starting pexpect-based interactive session: {' '.join(cmd_parts)}")

            session = GeminiInteractiveSession(cmd_parts, working_directory)
            await session.start()
            return session

        except Exception as e:
            error_msg = f"Failed to start interactive session: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


class GeminiInteractiveSession:
    """Manages an interactive Gemini CLI session using pexpect"""

    def __init__(self, cmd_parts: list[str], working_directory: str):
        self.cmd_parts = cmd_parts
        self.working_directory = working_directory
        self.child: pexpect.spawn | None = None
        self._ready = False

    async def start(self) -> None:
        """Start the pexpect session"""
        try:
            self.child = await asyncio.get_event_loop().run_in_executor(
                None, self._start_pexpect_session
            )
            await self._wait_for_ready()
            self._ready = True
            logger.info("Gemini pexpect session ready")

        except Exception as e:
            raise Exception(f"Failed to start pexpect session: {str(e)}")

    def _start_pexpect_session(self) -> pexpect.spawn:
        """Start the pexpect session (blocking operation)"""
        command = ' '.join(self.cmd_parts)
        # Set a very long timeout for the spawn itself to avoid premature termination
        child = pexpect.spawn(command, cwd=self.working_directory, timeout=None)
        if logger.isEnabledFor(logging.DEBUG):
            child.logfile_read = sys.stderr.buffer
        return child

    async def _wait_for_ready(self) -> None:
        """Wait for Gemini to be ready for input by clearing initial output."""
        if not self.child:
            raise Exception("Pexpect child process is not started")
        try:
            # Clear any startup text by reading until the first prompt is likely shown
            await self._read_response()
            logger.debug("Gemini session startup complete.")
        except Exception as e:
            logger.warning(f"Error during initial session ready wait: {e}")
            raise

    async def send_prompt(self, prompt: str) -> str:
        """Send a prompt to Gemini and get the response, waiting indefinitely."""
        if not self._ready or not self.child:
            raise Exception("Session not ready")

        try:
            logger.debug(f"Sending prompt: {prompt[:100]}...")
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_prompt_blocking, prompt
            )
            raw_response = await self._read_response()
            cleaned_response = self._clean_response(raw_response, prompt)
            logger.debug(f"Received cleaned response length: {len(cleaned_response)}")
            return cleaned_response

        except InteractivePromptDetected:
            raise # Re-raise to be caught by the task monitor
        except Exception as e:
            logger.error(f"Error sending prompt: {str(e)}")
            await self.close() # Close session on error
            raise

    def _send_prompt_blocking(self, prompt: str) -> None:
        """Send prompt (blocking operation)"""
        if self.child:
            self.child.sendline(prompt)

    async def _read_response(self) -> str:
        """
        Reads the complete response from the Gemini CLI by waiting for output to cease,
        or raises InteractivePromptDetected if an interactive prompt is found.
        """
        if not self.child:
            raise Exception("Child process not available")

        response_buffer = ""
        logger.debug("Reading response until output ceases or prompt detected...")

        read_timeout = 3.0  # Consider the response complete after 3s of silence.
        while self.child.isalive():
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.child.expect, r'.+', read_timeout
                )
                if isinstance(self.child.after, bytes):
                    new_data = self.child.after.decode('utf-8', errors='ignore')
                    response_buffer += new_data
                else:
                    # This case should ideally not be reached if expect() is successful
                    # but handles type checker concerns.
                    new_data = ""

                # Check for interactive prompts after receiving new data
                if self._is_interactive_prompt(response_buffer):
                    raise InteractivePromptDetected(prompt_text=response_buffer)

            except pexpect.TIMEOUT:
                if response_buffer:
                    logger.info(f"Response complete (detected by {read_timeout}s of inactivity).")
                    break
                continue
            except pexpect.EOF:
                logger.warning("EOF reached. Gemini CLI process terminated.")
                break
            except InteractivePromptDetected:
                raise # Re-raise the custom exception
            except Exception as e:
                logger.error(f"An unexpected error occurred while reading response: {e}")
                break

        return response_buffer

    def _is_interactive_prompt(self, text: str) -> bool:
        """
        Checks if the given text (or its end) contains patterns indicative of an interactive prompt.
        This is a heuristic and might need refinement based on actual gemini-cli prompts.
        """
        text_lower = text.lower().strip()
        # Common patterns for confirmation/input prompts
        prompt_patterns = [
            r'\(y/n\)', r'\[y/n\]', r'\(yes/no\)', r'\[yes/no\]',
            r'confirm', r'proceed', r'continue', r'allow',
            r'select an option', r'enter your choice',
            r'\[\\d+\]', # e.g., [1], [2] for numbered options
            r'\(default: .*\)', # e.g., (default: yes)
            r'press enter to continue',
            r'type your response',
            r'authentication required', # Specific to gemini-cli auth
            r'allow execution', # Specific to gemini-cli tool execution
        ]

        # Check the last few lines for prompts
        last_lines = "\n".join(text_lower.splitlines()[-5:])
        for pattern in prompt_patterns:
            if re.search(pattern, last_lines):
                logger.debug(f"Detected interactive prompt pattern: {pattern}")
                return True
        return False

    def _clean_response(self, text: str, prompt: str) -> str:
        """Clean up the pexpect output to return only the AI's response."""
        # 1. Remove the prompt that was sent, as it's often echoed.
        # We'll remove the first line if it closely matches the prompt.
        lines = text.split('\n')
        if lines and lines[0].strip() == prompt.strip():
            cleaned_text = '\n'.join(lines[1:])
        else:
            cleaned_text = text

        # 2. Remove ANSI escape codes.
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[0-?]*[ -/]*[@-~])')
        cleaned_text = ansi_escape.sub('', cleaned_text)

        # 3. Final whitespace cleanup.
        return cleaned_text.strip()

    def is_running(self) -> bool:
        """Check if the session is still running"""
        return self._ready and self.child is not None and self.child.isalive()

    async def save_memory(self, text: str) -> str:
        return await self.send_prompt(f"Please remember this: {text}")

    async def get_memory(self) -> str:
        return await self.send_prompt("/memory")

    async def get_tools(self) -> str:
        return await self.send_prompt("/tools")

    async def get_stats(self) -> str:
        return await self.send_prompt("/stats")

    async def compress_context(self) -> str:
        return await self.send_prompt("/compress")

    async def close(self) -> None:
        """Close the session"""
        self._ready = False
        if self.child and self.child.isalive():
            try:
                self.child.sendline("/quit")
                await asyncio.sleep(0.5)
                self.child.terminate()
                await asyncio.sleep(0.5)
                if self.child.isalive():
                    self.child.kill(9)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self.child = None
