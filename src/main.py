#!/usr/bin/env python3
"""
Gemini CLI MCP Server

An MCP server that exposes the functionality of Google's Gemini API directly,
providing a more reliable alternative to the CLI with schema compatibility issues.
"""

import asyncio
import atexit
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Optional

import mcp.server.stdio
import mcp.types as types
from pydantic import AnyUrl
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from gemini_api_client import GeminiAPIClient

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


def clean_schema(schema: dict) -> dict:
    """Clean schema by keeping only allowed keys for Gemini API compatibility"""
    allowed_keys = {"type", "properties", "required", "description", "title", "default", "enum"}
    
    def clean_recursive(obj):
        if isinstance(obj, dict):
            # Clean current level
            cleaned = {k: v for k, v in obj.items() if k in allowed_keys}
            # Recursively clean nested objects
            for key, value in cleaned.items():
                cleaned[key] = clean_recursive(value)
            return cleaned
        elif isinstance(obj, list):
            return [clean_recursive(item) for item in obj]
        else:
            return obj
    
    return clean_recursive(schema)


class GeminiCLIServer:
    """MCP Server for Gemini API functionality"""

    def __init__(self) -> None:
        self.server = Server("gemini-cli-mcp-server")
        self.gemini_client: Optional[GeminiAPIClient] = None
        self._setup_handlers()
        
    async def _ensure_client(self) -> GeminiAPIClient:
        """Ensure the Gemini API client is initialized"""
        if self.gemini_client is None:
            try:
                self.gemini_client = GeminiAPIClient()
            except Exception as e:
                raise Exception(f"Failed to initialize Gemini API client: {str(e)}")
        return self.gemini_client

    def _setup_handlers(self) -> None:
        """Set up all MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available Gemini CLI tools with proper schema formatting"""
            
            # Define tool schemas with proper cleaning for Gemini API compatibility
            tools = [
                types.Tool(
                    name="gemini_chat",
                    description="Start an interactive chat session with Gemini AI",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Initial message to send to Gemini"
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory for the chat session",
                                "default": "."
                            }
                        },
                        "required": ["message"]
                    })
                ),
                types.Tool(
                    name="gemini_analyze_code",
                    description="Analyze code in a directory using Gemini AI",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory containing code to analyze"
                            },
                            "query": {
                                "type": "string",
                                "description": "Specific analysis query or task"
                            }
                        },
                        "required": ["directory", "query"]
                    })
                ),
                types.Tool(
                    name="gemini_generate_app",
                    description="Generate a new application using Gemini AI",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Description of the application to generate"
                            },
                            "output_directory": {
                                "type": "string",
                                "description": "Directory where the app should be generated"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Framework preference (e.g., React, Flask, etc.)",
                                "default": ""
                            }
                        },
                        "required": ["description", "output_directory"]
                    })
                ),
                types.Tool(
                    name="gemini_code_assist",
                    description="Get AI assistance for specific code problems",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file needing assistance"
                            },
                            "task": {
                                "type": "string",
                                "description": "What you want help with (e.g., 'fix bugs', 'optimize', 'add tests')"
                            }
                        },
                        "required": ["file_path", "task"]
                    })
                ),
                types.Tool(
                    name="gemini_git_assist",
                    description="Get AI assistance with Git operations and analysis",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "repository_path": {
                                "type": "string",
                                "description": "Path to the Git repository"
                            },
                            "operation": {
                                "type": "string",
                                "description": "Git operation or analysis (e.g., 'analyze recent changes', 'help with merge conflict')"
                            }
                        },
                        "required": ["repository_path", "operation"]
                    })
                ),
                types.Tool(
                    name="gemini_list_models",
                    description="List available Gemini models from Google's API",
                    inputSchema=clean_schema({
                        "type": "object",
                        "properties": {
                            "api_key": {
                                "type": "string",
                                "description": "Gemini API key (optional if set in environment)",
                                "default": ""
                            }
                        },
                        "required": []
                    })
                )
            ]
            
            return tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent]:
            """Handle tool execution requests with improved error handling"""
            try:
                # Validate arguments exist
                if not isinstance(arguments, dict):
                    raise ValueError(f"Invalid arguments format for {name}: expected dict, got {type(arguments)}")

                # Route to appropriate handler
                if name == "gemini_chat":
                    result = await self._execute_gemini_chat(arguments)
                elif name == "gemini_analyze_code":
                    result = await self._execute_gemini_analyze_code(arguments)
                elif name == "gemini_generate_app":
                    result = await self._execute_gemini_generate_app(arguments)
                elif name == "gemini_code_assist":
                    result = await self._execute_gemini_code_assist(arguments)
                elif name == "gemini_git_assist":
                    result = await self._execute_gemini_git_assist(arguments)
                elif name == "gemini_list_models":
                    result = await self._execute_gemini_list_models(arguments)
                else:
                    result = f"Unknown tool: {name}"

                return [types.TextContent(type="text", text=result)]

            except KeyError as e:
                error_msg = f"Missing required parameter for {name}: {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
            except ValueError as e:
                error_msg = f"Invalid parameter value for {name}: {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=error_msg)]

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """list available resources"""
            return [
                types.Resource(
                    uri=AnyUrl("gemini://status"),
                    name="Gemini CLI Status",
                    description="Current status and configuration of Gemini CLI",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri=AnyUrl("gemini://help"),
                    name="Gemini CLI Help",
                    description="Help information for Gemini CLI commands",
                    mimeType="text/plain"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            """Handle resource read requests"""
            if str(uri) == "gemini://status":
                return await self._get_gemini_status()
            elif str(uri) == "gemini://help":
                return await self._get_gemini_help()
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def _execute_gemini_chat(self, arguments: dict[str, Any]) -> str:
        """Execute a Gemini chat command using direct API access"""
        # Validate required parameters
        if "message" not in arguments:
            raise KeyError("message")

        message = arguments["message"]
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")

        working_dir = arguments.get("working_directory", ".")

        # Validate working directory exists
        if not Path(working_dir).exists():
            raise ValueError(f"Working directory does not exist: {working_dir}")

        try:
            client = await self._ensure_client()
            result = await client.chat_with_context(message, working_dir)
            return result

        except Exception as e:
            return f"Failed to execute Gemini chat: {str(e)}"

    async def _execute_gemini_analyze_code(self, arguments: dict[str, Any]) -> str:
        """Analyze code using Gemini API with proper parameter validation"""
        # Validate required parameters
        for param in ["directory", "query"]:
            if param not in arguments:
                raise KeyError(param)

        directory = arguments["directory"]
        query = arguments["query"]

        if not isinstance(directory, str) or not directory.strip():
            raise ValueError("directory must be a non-empty string")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        # Validate directory exists
        if not Path(directory).exists():
            raise ValueError(f"Directory does not exist: {directory}")
        if not Path(directory).is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        try:
            client = await self._ensure_client()
            result = await client.analyze_code(directory, query)
            return result

        except Exception as e:
            return f"Failed to analyze code: {str(e)}"

    async def _execute_gemini_generate_app(self, arguments: dict[str, Any]) -> str:
        """Generate an application using Gemini API with proper parameter validation"""
        # Validate required parameters
        for param in ["description", "output_directory"]:
            if param not in arguments:
                raise KeyError(param)

        description = arguments["description"]
        output_dir = arguments["output_directory"]
        framework = arguments.get("framework", "")

        if not isinstance(description, str) or not description.strip():
            raise ValueError("description must be a non-empty string")
        if not isinstance(output_dir, str) or not output_dir.strip():
            raise ValueError("output_directory must be a non-empty string")

        try:
            client = await self._ensure_client()
            result = await client.generate_application(description, output_dir, framework)
            return f"App generation completed for {output_dir}:\n{result}"

        except Exception as e:
            return f"Failed to generate app: {str(e)}"

    async def _execute_gemini_code_assist(self, arguments: dict[str, Any]) -> str:
        """Get code assistance from Gemini API with proper parameter validation"""
        # Validate required parameters
        for param in ["file_path", "task"]:
            if param not in arguments:
                raise KeyError(param)

        file_path = arguments["file_path"]
        task = arguments["task"]

        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("file_path must be a non-empty string")
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must be a non-empty string")

        # Validate file exists and is readable
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            client = await self._ensure_client()
            result = await client.code_assistance(file_path, task)
            return result

        except Exception as e:
            return f"Failed to get code assistance: {str(e)}"

    async def _execute_gemini_git_assist(self, arguments: dict[str, Any]) -> str:
        """Get Git assistance from Gemini API with proper parameter validation"""
        # Validate required parameters
        for param in ["repository_path", "operation"]:
            if param not in arguments:
                raise KeyError(param)

        repo_path = arguments["repository_path"]
        operation = arguments["operation"]

        if not isinstance(repo_path, str) or not repo_path.strip():
            raise ValueError("repository_path must be a non-empty string")
        if not isinstance(operation, str) or not operation.strip():
            raise ValueError("operation must be a non-empty string")

        # Validate repository path exists
        repo_path_obj = Path(repo_path)
        if not repo_path_obj.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path_obj.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")

        # Check if it's a git repository
        git_dir = repo_path_obj / ".git"
        if not git_dir.exists():
            raise ValueError(f"Directory is not a Git repository: {repo_path}")

        try:
            client = await self._ensure_client()
            result = await client.git_assistance(repo_path, operation)
            return result

        except Exception as e:
            return f"Failed to get Git assistance: {str(e)}"

    async def _execute_gemini_list_models(self, arguments: dict[str, Any]) -> str:
        """List available Gemini models using direct API access"""
        # Get API key from arguments or environment (no validation required since it's optional)
        api_key = arguments.get("api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "")

        try:
            if api_key:
                # Use provided API key
                client = GeminiAPIClient(api_key)
            else:
                # Use default client
                client = await self._ensure_client()
            
            result = await client.list_models()
            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "models": []
            }, indent=2)

    async def _get_gemini_status(self) -> str:
        """Get Gemini API status information"""
        try:
            client = await self._ensure_client()
            
            # Try to list models to verify API connectivity
            models_result = await client.list_models()
            
            status = {
                "available": models_result.get("success", False),
                "api_method": "Direct Gemini API",
                "models_available": models_result.get("count", 0),
                "api_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
                "error": models_result.get("error") if not models_result.get("success") else None
            }

            return json.dumps(status, indent=2)

        except Exception as e:
            return json.dumps({
                "available": False,
                "api_method": "Direct Gemini API",
                "error": str(e)
            }, indent=2)

    async def _get_gemini_help(self) -> str:
        """Get Gemini API help information"""
        help_text = """
Gemini MCP Server - Direct API Access

This MCP server provides direct access to Google's Gemini API, avoiding the
schema compatibility issues present in the current Gemini CLI.

Available Tools:
- gemini_chat: Interactive chat with project context
- gemini_analyze_code: Analyze code in directories
- gemini_generate_app: Generate complete applications
- gemini_code_assist: Get help with specific code files
- gemini_git_assist: Git repository assistance
- gemini_list_models: List available Gemini models

Configuration:
Set the GEMINI_API_KEY environment variable with your API key from:
https://aistudio.google.com/app/apikey

Features:
- Project context awareness (reads GEMINI.md, README.md)
- Code file analysis with syntax highlighting
- Git repository integration
- Direct API access for reliability
- No CLI schema compatibility issues

For more information, visit:
https://ai.google.dev/gemini-api/docs
"""
        return help_text

    async def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting Gemini CLI MCP Server")

        # MCP server transport setup
        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="gemini-cli-mcp-server",
                        server_version="0.1.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Failed to start stdio server: {e}")
            raise


async def main() -> None:
    """Main entry point"""
    try:
        logger.info("Initializing Gemini API MCP Server")
        server = GeminiCLIServer()
        logger.info("Server initialized, starting...")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
