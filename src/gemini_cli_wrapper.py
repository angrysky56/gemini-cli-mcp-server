#!/usr/bin/env python3
"""
Simple Gemini CLI Wrapper for MCP Server

A lightweight wrapper that interfaces with the user's pre-authenticated gemini-cli.
"""

import asyncio
import logging
import os
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

# ANSI escape code removal regex
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class InteractivePromptDetected(Exception):
    """Exception raised when an interactive prompt is detected that requires user input"""
    def __init__(self, prompt_text: str):
        super().__init__(f"Interactive prompt detected: {prompt_text}")
        self.prompt_text = prompt_text


class GeminiCLIWrapper:
    """Simple wrapper for the user's authenticated gemini CLI"""

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


class GeminiInteractiveSession:
    """Manages an interactive Gemini CLI session"""

    def __init__(self, cmd_parts: list[str], working_directory: str, auto_approve: bool = False):
        self.cmd_parts = cmd_parts
        self.working_directory = working_directory
        self.auto_approve = auto_approve
        self.child: pexpect.spawn | None = None
        self._ready = False

    async def start(self) -> None:
        """Start the gemini session"""
        try:
            logger.info(f"Starting gemini session in {self.working_directory}")

            # Start the process
            self.child = await asyncio.get_event_loop().run_in_executor(
                None, self._start_pexpect_session
            )

            # Wait for it to be ready
            await self._wait_for_ready()
            self._ready = True
            logger.info("Gemini session ready")

        except Exception as e:
            logger.error(f"Failed to start gemini session: {e}")
            raise

    def _start_pexpect_session(self) -> pexpect.spawn:
        """Start the pexpect session (blocking operation)"""
        command = self.cmd_parts[0]
        args = self.cmd_parts[1:] if len(self.cmd_parts) > 1 else []

        # Set up environment
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'

        # Start gemini in the specified directory
        child = pexpect.spawn(
            command,
            args=args,
            cwd=self.working_directory,
            timeout=None,
            dimensions=(24, 80),            encoding='utf-8',
            codec_errors='replace'
        )

        return child

    async def _wait_for_ready(self) -> None:
        """Wait for Gemini to show the prompt"""
        if not self.child:
            raise Exception("Pexpect child process is not started")

        try:
            logger.info("Waiting for Gemini to be ready...")

            # Wait for the main prompt pattern
            index = await asyncio.get_event_loop().run_in_executor(
                None, self._wait_for_prompt
            )

            if index == 0:  # Got prompt
                logger.info("Gemini session ready - prompt detected")
            else:
                raise Exception(f"Unexpected response during startup: {index}")

        except Exception as e:
            logger.error(f"Error during startup: {e}")
            if self.child and self.child.before:
                logger.error(f"Available output: {self.child.before[:500]}...")
            raise

    def _wait_for_prompt(self) -> int:
        """Wait for the Gemini prompt (blocking)"""
        if not self.child:
            raise Exception("Pexpect child process is not started")

        # Simple patterns to match the actual gemini CLI
        patterns = [
            r'> ',              # Normal prompt
            r'[Ee]rror',        # Error messages
            r'[Ff]ailed',       # Failed messages
            pexpect.TIMEOUT,    # Timeout
            pexpect.EOF         # End of file
        ]

        try:
            logger.info("Waiting for Gemini prompt...")
            index = self.child.expect(patterns, timeout=30)

            if index == 0:  # Got normal prompt
                logger.info("Successfully matched Gemini prompt")
                return index
            elif index in [1, 2]:  # Got error
                error_output = self.child.before if self.child.before else "Unknown error"
                raise Exception(f"Gemini CLI error: {error_output}")
            elif index == 3:  # Timeout
                output = self.child.before if self.child.before else "No output"
                raise Exception(f"Timeout waiting for prompt. Output: {output[:500]}...")
            elif index == 4:  # EOF
                raise Exception("Gemini CLI process ended unexpectedly")

        except Exception as e:
            logger.error(f"Exception while waiting for prompt: {e}")
            if self.child and self.child.before:
                logger.error(f"Child output: {self.child.before[:500]}...")
            raise

        return index

    async def send_prompt(self, prompt: str) -> str:
        """Send a prompt to Gemini and get the response"""
        if not self._ready or not self.child:
            raise Exception("Session not ready")

        try:
            if prompt.strip():  # Only send if there's actual content
                logger.info(f"Sending prompt: {prompt[:100]}...")

                # Send the prompt
                await asyncio.get_event_loop().run_in_executor(
                    None, self.child.sendline, prompt
                )

            # Read the response
            response = await self._read_response()

            # Clean and return
            cleaned = self._clean_output(response)
            logger.info(f"Received response length: {len(cleaned)}")
            return cleaned

        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            raise

    async def _read_response(self) -> str:
        """Read response until we see the prompt again"""
        if not self.child:
            raise Exception("Pexpect child process is not started")

        response_parts = []

        try:
            # Wait for the next prompt or timeout
            patterns = [
                r'> ',              # Normal prompt - response complete
                r'[Yy]/[Nn]',       # Yes/No prompt - needs interaction
                r'[Pp]ress.*key',   # Press any key prompt
                pexpect.TIMEOUT,    # Timeout
                pexpect.EOF         # End of file
            ]

            while True:
                index = await asyncio.get_event_loop().run_in_executor(
                    None, self.child.expect, patterns, 120  # 2 minute timeout
                )

                # Collect output before the match
                if self.child.before:
                    response_parts.append(self.child.before)

                if index == 0:  # Normal prompt - done
                    break
                elif index == 1:  # Y/N prompt - needs interaction
                    prompt_text = self.child.after if self.child.after else "Unknown prompt"
                    raise InteractivePromptDetected(f"User input required: {prompt_text}")
                elif index == 2:  # Press key prompt
                    prompt_text = self.child.after if self.child.after else "Press any key"
                    raise InteractivePromptDetected(f"User interaction required: {prompt_text}")
                elif index == 3:  # Timeout
                    logger.warning("Timeout waiting for response, assuming complete")
                    break
                elif index == 4:  # EOF
                    logger.warning("EOF while reading response")
                    break

        except InteractivePromptDetected:
            # Re-raise interactive prompts
            raise
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            raise

        return ''.join(response_parts)

    def _clean_output(self, text: str) -> str:
        """Remove ANSI escape codes and clean up output"""
        if not text:
            return ""

        # Remove ANSI escape codes
        cleaned = ANSI_ESCAPE.sub('', text)

        # Remove empty lines and common interface elements
        lines = cleaned.split('\n')
        filtered_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip interface elements, empty lines, and echoed commands
            if (not stripped or
                'no sandbox' in stripped or
                'context left)' in stripped or
                '(see /docs)' in stripped or
                stripped.startswith('> ') or  # Echoed prompt
                'gemini-' in stripped and 'pro' in stripped):  # Model info line
                continue
            filtered_lines.append(line.rstrip())

        result = '\n'.join(filtered_lines).strip()
        return result

    def is_running(self) -> bool:
        """Check if the session is still running"""
        return self._ready and self.child is not None and self.child.isalive()

    async def close(self) -> None:
        """Close the session"""
        self._ready = False
        if self.child and self.child.isalive():
            try:
                # Send quit command
                self.child.sendline("/quit")
                await asyncio.sleep(0.5)

                # Force termination if still alive
                if self.child.isalive():
                    self.child.terminate()
                    await asyncio.sleep(0.5)

                # Kill if really stubborn
                if self.child.isalive():
                    self.child.kill(9)

            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self.child = None
