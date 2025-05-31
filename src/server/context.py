"""
Context management and lifespan handling for the MCP server.

This module handles the initialization and cleanup of resources needed by the server.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler, BrowserConfig
from src.database import initialize_db_connection, close_db_connection
from src.models.context import Crawl4AIContext

# Load environment variables from the project root .env file
project_root = Path(__file__).resolve().parent.parent.parent
dotenv_path = project_root / '.env'

# Force override of existing environment variables
load_dotenv(dotenv_path, override=True)


@asynccontextmanager
async def crawl4ai_lifespan(server: FastMCP) -> AsyncIterator[Crawl4AIContext]:
    """
    Manages the Crawl4AI client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        Crawl4AIContext: The context containing the Crawl4AI crawler and database connection
    """
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )
    
    # Initialize the crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    # Initialize PostgreSQL connection
    db_connection = await initialize_db_connection()
    
    # Create schema if it doesn't exist
    await db_connection.create_schema_if_not_exists()
    
    try:
        yield Crawl4AIContext(
            crawler=crawler,
            db_connection=db_connection
        )
    finally:
        # Clean up the crawler
        await crawler.__aexit__(None, None, None)
        # Close database connection
        await close_db_connection()
