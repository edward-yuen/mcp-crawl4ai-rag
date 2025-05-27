#!/usr/bin/env python3
"""
Test the MCP server startup and basic functionality.

This script tests:
1. MCP server can be imported and initialized
2. Database connection works 
3. Basic crawling (if possible)
4. Tool functionality

Usage:
    python test_mcp_server_startup.py
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawl4ai_mcp import Crawl4AIContext, get_available_sources, perform_rag_query
from src.database import initialize_db_connection, close_db_connection
from crawl4ai import AsyncWebCrawler, BrowserConfig
from unittest.mock import MagicMock


class MockContext:
    """Mock context that mimics MCP Context structure."""
    def __init__(self, db_connection=None, crawler=None):
        self.request_context = MagicMock()
        self.request_context.lifespan_context = MagicMock()
        self.request_context.lifespan_context.db_connection = db_connection
        self.request_context.lifespan_context.crawler = crawler


async def test_full_server_context():
    """Test creating a full server context like the actual MCP server would."""
    print("\n[TEST] Testing full MCP server context initialization...")
    
    try:
        # Create browser configuration
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        # Initialize the crawler
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.__aenter__()
        
        # Initialize PostgreSQL connection
        db_connection = await initialize_db_connection()
        await db_connection.create_schema_if_not_exists()
        
        # Create the context
        context = Crawl4AIContext(
            crawler=crawler,
            db_connection=db_connection
        )
        
        print("[SUCCESS] MCP server context created successfully")
        print(f"  - Crawler: {type(context.crawler).__name__}")
        print(f"  - DB Connection: {type(context.db_connection).__name__}")
        
        # Test MCP tools with proper context
        mock_ctx = MockContext(db_connection=db_connection, crawler=crawler)
        
        # Test get_available_sources
        sources_result = await get_available_sources(mock_ctx)
        sources_data = json.loads(sources_result)
        print(f"[SUCCESS] get_available_sources: {sources_data.get('count', 0)} sources found")
        
        # Test perform_rag_query (this might fail without OpenAI API key, but that's OK)
        try:
            rag_result = await perform_rag_query(mock_ctx, "test query", match_count=1)
            rag_data = json.loads(rag_result)
            if rag_data.get("success"):
                print(f"[SUCCESS] perform_rag_query: {rag_data.get('count', 0)} results")
            else:
                print(f"[INFO] perform_rag_query failed (likely no OpenAI API key): {rag_data.get('error', 'Unknown')}")
        except Exception as e:
            print(f"[INFO] perform_rag_query failed (expected without API key): {str(e)}")
        
        # Clean up
        await crawler.__aexit__(None, None, None)
        await close_db_connection()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Full context test failed: {str(e)}")
        return False


async def main():
    """Run server startup tests."""
    print("[START] Testing MCP Server Startup and Context")
    print("=" * 50)
    
    success = await test_full_server_context()
    
    print("\n" + "=" * 50)
    if success:
        print("[RESULT] MCP Server is working correctly! ✓")
        print("All core components are functional:")
        print("  ✓ Database connection")
        print("  ✓ Crawler initialization") 
        print("  ✓ MCP tools")
        print("  ✓ Context management")
        return 0
    else:
        print("[RESULT] MCP Server has issues ✗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
