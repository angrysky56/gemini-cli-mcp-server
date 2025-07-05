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
        checkpointing: bool = False,
        auto_approve: bool = False
    ) -> 'GeminiInteractiveSession':
        """
        Start an interactive Gemini CLI session using pexpect.

        Args:
            working_directory: Directory to run gemini from
            model: Optional model to use
            debug: Enable debug mode
            checkpointing: Enable checkpointing
            auto_approve: Enable auto-approval for tool executions

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
        if auto_approve:
            cmd_parts.append("--yolo")

        try:
            logger.debug(f"Starting pexpect-based interactive session: {' '.join(cmd_parts)}")

            session = GeminiInteractiveSession(cmd_parts, working_directory, auto_approve=auto_approve)
            await session.start()
            return session

        except Exception as e:
            error_msg = f"Failed to start interactive session: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


class GeminiInteractiveSession:
    """Manages an interactive Gemini CLI session using pexpect"""

    def __init__(self, cmd_parts: list[str], working_directory: str, auto_approve: bool = False):
        self.cmd_parts = cmd_parts
        self.working_directory = working_directory
        self.auto_approve = auto_approve
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
        """Send a prompt to Gemini and get the response asynchronously."""
        if not self._ready or not self.child:
            raise Exception("Session not ready")

        try:
            logger.debug(f"Sending prompt: {prompt[:100]}...")

            # Send the prompt (non-blocking)
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_prompt_blocking, prompt
            )

            # Read the response (this is where the time is spent)
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
        Reads the complete response from the Gemini CLI.
        """
        if not self.child:
            raise Exception("Child process not available")

        response_buffer = ""
        logger.debug("Reading response from Gemini CLI...")

        # Much simpler approach: keep reading until we see the prompt again
        max_wait_time = 300.0  # 5 minutes max
        start_time = asyncio.get_event_loop().time()

        # Track if we're handling tool approval
        handling_approval = False

        while self.child.isalive():
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > max_wait_time:
                logger.warning(f"Response reading timed out after {max_wait_time}s")
                break

            try:
                # Read available data
                data = await asyncio.get_event_loop().run_in_executor(
                    None, self.child.read_nonblocking, 4096, 1.0
                )

                if data:
                    text = data.decode('utf-8', errors='ignore')
                    response_buffer += text

                    # Check for tool approval prompts and auto-handle if enabled
                    if self.auto_approve and not handling_approval:
                        if any(pattern in response_buffer.lower() for pattern in [
                            'allow execution', 'approve this', 'proceed with',
                            'run this command', 'execute this tool'
                        ]):
                            logger.info("Auto-approving tool execution")
                            self.child.sendline('y')
                            handling_approval = True
                            # Continue reading after sending approval
                            continue

                    # Check for other interactive prompts
                    if self._is_interactive_prompt(response_buffer):
                        raise InteractivePromptDetected(prompt_text=response_buffer)

                    # Check if we've reached the end (look for the prompt pattern)
                    if self._response_seems_complete(response_buffer):
                        logger.info("Response appears complete")
                        break

            except pexpect.TIMEOUT:
                # No data available, but keep waiting
                await asyncio.sleep(0.1)
                continue
            except pexpect.EOF:
                logger.warning("EOF reached. Gemini CLI process terminated.")
                break
            except InteractivePromptDetected:
                raise
            except Exception as e:
                logger.error(f"Error reading response: {e}")
                break

        return response_buffer

    def _response_seems_complete(self, text: str) -> bool:
        """Check if the response seems complete by looking for the prompt pattern."""
        if not text:
            return False

        # Look for the prompt box pattern at the end
        lines = text.split('\n')
        if len(lines) < 3:
            return False

        # Check last few lines for the prompt box structure
        last_lines = '\n'.join(lines[-10:])  # Check last 10 lines

        # Look for the bottom of the prompt box with directory info
        if ('~/Repositories' in last_lines and
            'gemini-2.5-pro' in last_lines and
            'context left' in last_lines):
            return True

        return False

    def _is_interactive_prompt(self, text: str) -> bool:
        """
        Checks if the given text contains patterns indicative of an interactive prompt.
        If auto_approve is enabled, automatically handles tool approval prompts.
        """
        text_lower = text.lower().strip()

        # Specific patterns for Gemini CLI tool approval
        if self.auto_approve and self.child:
            # Check for tool execution approval prompts
            if any(pattern in text_lower for pattern in [
                'allow execution', 'allow this tool', 'approve this action',
                'proceed with', 'execute this command', 'run this tool'
            ]):
                # Auto-approve by sending 'y'
                logger.info("Auto-approving tool execution prompt")
                self.child.sendline('y')
                return False  # Don't treat as blocking prompt since we handled it

        # Common patterns for confirmation/input prompts
        prompt_patterns = [
            r'\(y/n\)', r'\[y/n\]', r'\(yes/no\)', r'\[yes/no\]',
            r'confirm', r'proceed', r'continue', r'allow',
            r'select an option', r'enter your choice',
            r'\[\d+\]', # e.g., [1], [2] for numbered options
            r'\(default: .*\)', # e.g., (default: yes)
            r'press enter to continue',
            r'type your response',
            r'authentication required', # Specific to gemini-cli auth
            r'waiting for auth', # Specific to gemini-cli tool auth
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
        if not text:
            return ""

        # 1. Remove ANSI escape codes first
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned_text = ansi_escape.sub('', text)

        # 2. Remove carriage returns and normalize line endings
        cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')

        # 3. Remove all Unicode box-drawing characters and similar interface elements
        # This includes the entire range from U+2500 to U+257F
        box_chars = re.compile(r'[\u2500-\u257F\u2580-\u259F\u2800-\u28FF]')
        cleaned_text = box_chars.sub('', cleaned_text)

        # 4. Also remove common Unicode characters that might appear in the interface
        # Like arrows, bullets, and other decorative elements
        interface_chars = re.compile(r'[\u2190-\u21FF\u25A0-\u25FF\u2600-\u26FF]')
        cleaned_text = interface_chars.sub('', cleaned_text)

        # 5. Split into lines and extract only meaningful content
        lines = cleaned_text.split('\n')
        meaningful_lines = []

        # Skip the initial echo of the prompt
        skip_until_after_prompt = True

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Skip the echoed prompt at the beginning
            if skip_until_after_prompt and line_stripped == prompt.strip():
                skip_until_after_prompt = False
                continue

            # Skip interface elements - be very aggressive
            if (line_stripped.startswith('Using ') and 'MCP servers' in line_stripped or
                line_stripped.startswith('~/') or
                'no sandbox' in line_stripped or
                'gemini-2.5-pro' in line_stripped or
                'context left)' in line_stripped or
                '(main*)' in line_stripped or
                '(see /docs)' in line_stripped or
                line_stripped == '>' or
                line_stripped.startswith('> ') or
                # Skip lines that look like file paths in the prompt box
                re.match(r'^[~\/].*\s+\(.*\)$', line_stripped) or
                # Skip status lines
                'Waiting for auth' in line_stripped or
                'Press ESC to cancel' in line_stripped):
                continue

            # Only keep lines with actual content
            if len(line_stripped) > 1:
                meaningful_lines.append(line_stripped)

        return '\n'.join(meaningful_lines).strip()

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
