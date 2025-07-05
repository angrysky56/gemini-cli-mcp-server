"""
Gemini CLI MCP Server Package

This package provides an MCP (Model Context Protocol) server that exposes
the functionality of Google's Gemini CLI to other MCP clients.
"""

__version__ = "0.1.0"
__author__ = "AI Workspace"
__email__ = "workspace@example.com"

from .main import GeminiCLIMCPServer, main

__all__ = ["main", "GeminiCLIMCPServer"]
