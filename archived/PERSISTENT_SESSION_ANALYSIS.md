### Analysis of Persistent Session Implementation for Gemini CLI MCP Server

After analyzing the code, here's a summary of how it enables a persistent session for Claude to interact with the Gemini CLI, along with the key components and their roles.

#### Key Components

1.  **`GeminiCLIMCPServer` (in `src/main.py`)**:
    *   This is the main MCP server class.
    *   It manages multiple interactive sessions, allowing for concurrent conversations.
    *   It exposes the Gemini CLI's functionality as a set of tools that Claude can use.

2.  **`GeminiCLIWrapper` (in `src/gemini_cli_wrapper.py`)**:
    *   This class is a crucial component that wraps the `gemini` command-line tool.
    *   It uses a pseudo-terminal (PTY) to create a persistent, interactive session with the Gemini CLI. This is the key to maintaining context and history across multiple interactions.
    *   It handles the low-level details of sending prompts, reading responses, and managing the session's lifecycle.

3.  **`GeminiInteractiveSession` (in `src/gemini_cli_wrapper.py`)**:
    *   Represents a single, persistent, interactive session with the Gemini CLI.
    *   It's responsible for sending prompts to the session, reading the output, and cleaning up the PTY output to provide a clean response to the user.

### How Persistent Sessions Work

The core of the persistent session is the use of a **pseudo-terminal (PTY)**. Here's a breakdown of the process:

1.  **Starting a Session**:
    *   When Claude initiates a `gemini_start_session` tool call, the `GeminiCLIMCPServer` creates a new `GeminiInteractiveSession`.
    *   The `GeminiCLIWrapper` starts the `gemini` command as a subprocess, but instead of using standard input/output, it connects it to a PTY. This makes the `gemini` process think it's running in a real terminal, allowing for interactive features like command history and context to be preserved.

2.  **Sending Prompts and Commands**:
    *   When Claude sends a message using `gemini_session_chat`, the message is written to the PTY, just as if a user were typing it into a terminal.
    *   The `GeminiInteractiveSession` then reads the output from the PTY, which is the Gemini CLI's response.

3.  **Maintaining Context**:
    *   Because the `gemini` process is running continuously in the PTY, it maintains its own internal state, including the conversation history and any files that have been loaded. This is how the session remains persistent.

4.  **Closing a Session**:
    *   When Claude calls `gemini_close_session`, the server sends a `/quit` command to the PTY to gracefully exit the `gemini` process and then cleans up the session resources.

### Summary for Claude's Interaction

This setup allows you, Claude, to have a persistent and interactive conversation with the Gemini CLI. You can:

*   **Start and manage multiple, independent sessions**, each with its own context.
*   **Send prompts and get responses** within a session, just like a human user.
*   **Use all of the Gemini CLI's built-in features**, such as loading files with `@`, running shell commands with `!`, and managing memory.
*   **Maintain context** throughout a project, allowing for more effective collaboration.
