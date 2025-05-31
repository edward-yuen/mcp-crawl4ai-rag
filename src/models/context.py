"""
Context models for the Crawl4AI MCP server.

This module contains the dataclasses and context objects used throughout the server.
"""
from dataclasses import dataclass
from crawl4ai import AsyncWebCrawler
from src.database import DatabaseConnection


@dataclass
class Crawl4AIContext:
    """Context for the Crawl4AI MCP server."""
    crawler: AsyncWebCrawler
    db_connection: DatabaseConnection
