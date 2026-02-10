"""
MCP (Model Context Protocol) client for ASTRO.

Enables connecting to MCP servers for extended capabilities.
"""

from .client import MCPClient
from .server_connection import ServerConnection

__all__ = ['MCPClient', 'ServerConnection']
