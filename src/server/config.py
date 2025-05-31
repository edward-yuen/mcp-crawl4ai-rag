"""
Server configuration utilities.

This module handles reading configuration from environment variables and
providing default values for the MCP server.
"""
import os


def get_port() -> int:
    """Get port from environment, handling empty string values."""
    port_str = os.getenv("PORT", "8051")
    if not port_str or port_str.strip() == "":
        return 8051
    try:
        return int(port_str)
    except ValueError:
        return 8051


def get_host() -> str:
    """Get host from environment, handling empty string values."""
    host_str = os.getenv("HOST", "0.0.0.0")
    if not host_str or host_str.strip() == "":
        return "0.0.0.0"
    return host_str


def get_server_config() -> dict:
    """
    Get server configuration for FastMCP.
    
    Returns:
        Dictionary with host and port configuration
    """
    return {
        "host": get_host(),
        "port": get_port()
    }
