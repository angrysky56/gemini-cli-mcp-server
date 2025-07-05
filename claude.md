# Guide for Claude: Interacting with the Gemini CLI MCP Server

Hello, Claude! This document is your guide to effectively using the `gemini-cli-mcp-server`. This server acts as your direct interface to a live, interactive Gemini CLI instance running on the user's system. Think of it as your dedicated terminal window into the Gemini CLI, allowing you to perform complex tasks, manage projects, and interact with the user's local environment.

## Why Use This Server?

This server is designed to give you full access to the Gemini CLI's powerful capabilities, including:

*   **Persistent Sessions:** Maintain context and conversation history across multiple interactions.
*   **Built-in Tools:** Leverage all of Gemini CLI's integrated tools (file system operations, shell commands, web search, memory management, etc.).
*   **Asynchronous Operations:** Initiate long-running tasks without blocking your current workflow.
*   **Interactive Control:** Respond to prompts and confirmations from the Gemini CLI.
*   **Real-world Interaction:** Directly interact with the user's local files and shell.

## Core Interaction Model: Asynchronous Polling

All interactions with a Gemini CLI session through this server are **asynchronous and non-blocking**. This means:

1.  When you send a command, the server will immediately return a `task_id`.
2.  The actual command execution happens in the background.
3.  You must **poll** the server using the `gemini_check_task_status` tool to get the result.

This model is crucial for handling tasks that might take seconds, minutes, or even hours, without locking up your processing.

## Your Tools for Interaction

You have four primary tools to interact with the `gemini-cli-mcp-server`:

### 1. `gemini_start_session`

*   **Purpose:** To initiate a new, persistent Gemini CLI session. Each session is isolated and maintains its own context.
*   **When to Use:** Always use this as the first step before sending any commands to a new session.
*   **Arguments:**
    *   `session_id` (string, required): A unique identifier you choose for this session (e.g., "project_alpha_coding", "bug_fix_session").
    *   `working_directory` (string, optional): The absolute path to the directory where the Gemini CLI session should operate. If omitted, it defaults to the server's working directory.
    *   `model` (string, optional): The Gemini model to use for this session (e.g., 'gemini-2.5-pro', 'gemini-2.5-flash').
    *   `debug` (boolean, optional): Enable debug mode for the Gemini CLI.
    *   `checkpointing` (boolean, optional): Enable checkpointing for file changes.
*   **Example Call:**
    ```json
    {
      "tool": "gemini_start_session",
      "arguments": {
        "session_id": "my_new_project",
        "working_directory": "/home/user/projects/my_new_project",
        "model": "gemini-2.5-pro"
      }
    }
    ```
*   **Expected Response:** `"Interactive session <session_id> started successfully"`

### 2. `gemini_session_chat`

*   **Purpose:** To send any command or prompt to an active Gemini CLI session. This includes natural language prompts, `@` commands, `!` commands, and `/` meta-commands.
*   **When to Use:** For all interactions *after* starting a session.
*   **Arguments:**
    *   `session_id` (string, required): The identifier of the session you want to interact with.
    *   `message` (string, required): The command or prompt you want to send to the Gemini CLI.
*   **Example Call:**
    ```json
    {
      "tool": "gemini_session_chat",
      "arguments": {
        "session_id": "my_new_project",
        "message": "Analyze the `src/utils.py` file for potential optimizations."
      }
    }
    ```
*   **Expected Response (Asynchronous Task Initiation):**
    ```json
    {
      "status": "STARTED",
      "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "estimated_completion": "1-5 minutes", // Varies based on complexity
      "note": "Please use gemini_check_task_status with the returned task_id to get the result. Recommended check time is in 1-5 minutes. IMPORTANT: This is a long-running task. Do not close the chat or client connection, as it will terminate the process."
    }
    ```
    *   **Important:** The `note` field provides crucial instructions. Pay attention to the `estimated_completion` to determine how frequently to poll. For tasks estimated over 10 minutes, it's vital to keep your connection to the user's client open.

### 3. `gemini_check_task_status`

*   **Purpose:** To check the current status of a background task and retrieve its result once complete.
*   **When to Use:** After calling `gemini_session_chat` (or any other async session tool) to get the outcome of the operation. Poll periodically based on the `estimated_completion` provided.
*   **Arguments:**
    *   `task_id` (string, required): The ID of the task you want to check.
*   **Example Call:**
    ```json
    {
      "tool": "gemini_check_task_status",
      "arguments": {
        "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
      }
    }
    ```
*   **Expected Responses:**
    *   **Task Still Running:**
        ```json
        {
          "status": "RUNNING"
        }
        ```
    *   **Task Complete:**
        ```json
        {
          "status": "COMPLETE",
          "result": "..." // The full, cleaned output from the Gemini CLI.
        }
        ```
    *   **Task Failed:**
        ```json
        {
          "status": "ERROR",
          "result": "..." // Error message from the Gemini CLI or server.
        }
        ```
    *   **Task Blocked on Interactive Prompt:**
        ```json
        {
          "status": "BLOCKED_ON_INTERACTION",
          "prompt": "Authentication required. Please select an option: [1] OAuth [2] API Key" // The exact prompt text.
        }
        ```
    *   **Task Not Found (e.g., already retrieved or invalid ID):**
        ```json
        {
          "status": "NOT_FOUND"
        }
        ```

### 4. `gemini_session_respond_to_interaction`

*   **Purpose:** To provide input to a Gemini CLI session that is currently blocked by an interactive prompt.
*   **When to Use:** Only when `gemini_check_task_status` returns `{"status": "BLOCKED_ON_INTERACTION", "prompt": "..."}`.
*   **Arguments:**
    *   `task_id` (string, required): The ID of the blocked task.
    *   `response_text` (string, required): The text you want to send as a response to the prompt (e.g., "Y", "1", "my_password").
*   **Example Call:**
    ```json
    {
      "tool": "gemini_session_respond_to_interaction",
      "arguments": {
        "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "response_text": "1" // Responding to the "select an option" prompt
      }
    }
    ```
*   **Expected Response:** `"Response '<response_text>' sent to task <task_id>. Task is now RUNNING."`
    *   After sending a response, you should continue polling `gemini_check_task_status` for the `task_id`.

### 5. `gemini_close_session`

*   **Purpose:** To gracefully terminate an active Gemini CLI session and release its resources.
*   **When to Use:** When you are finished with a session and no longer need its context.
*   **Arguments:**
    *   `session_id` (string, required): The identifier of the session to close.
*   **Example Call:**
    ```json
    {
      "tool": "gemini_close_session",
      "arguments": {
        "session_id": "my_new_project"
      }
    }
    ```
*   **Expected Response:** `"Session <session_id> closed successfully"`

## Key Interaction Patterns for Claude

*   **Always Start a Session:** Before any other interaction, use `gemini_start_session`.
*   **All Commands via `gemini_session_chat`:** Whether it's a natural language prompt, `@` command, `!` command, or `/` meta-command (like `/tools`, `/memory`, `/stats`, `/compress`), always send it through `gemini_session_chat`.
*   **Poll for Results:** After sending a command via `gemini_session_chat`, always follow up by polling `gemini_check_task_status` until the task is `COMPLETE`, `ERROR`, or `BLOCKED_ON_INTERACTION`.
*   **Handle Interactive Prompts:** If a task is `BLOCKED_ON_INTERACTION`, carefully read the `prompt` text and use `gemini_session_respond_to_interaction` to provide the necessary input.
*   **Manage Session Lifecycles:** Close sessions with `gemini_close_session` when they are no longer needed.
*   **Context is Key:** Remember that the session maintains context. You can build on previous interactions within the same `session_id`.

By following this guide, you will be able to effectively communicate with and control the Gemini CLI, enabling powerful and persistent interactions with the user's local environment. Let's build amazing things together!
