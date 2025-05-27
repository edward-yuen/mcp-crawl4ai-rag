#!/usr/bin/env python3
"""
Comprehensive test script for the crawl4ai-rag MCP server.

This script tests the MCP server functionality including:
1. Database connectivity
2. MCP tool functionality 
3. Vector search capabilities
4. Error handling

Usage:
    python test_mcp_server_functionality.py
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock
from contextlib import asynccontextmanager
import traceback

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import MCP server components
try:
    from src.database import DatabaseConnection, initialize_db_connection, close_db_connection
    from src.utils import add_documents_to_postgres, search_documents, get_db_connection
    from src.crawl4ai_mcp import (
        Crawl4AIContext, 
        crawl_single_page, 
        get_available_sources, 
        perform_rag_query,
        smart_crawl_url,
        query_lightrag_schema,
        get_lightrag_info,
        multi_schema_search
    )
    from crawl4ai import AsyncWebCrawler, BrowserConfig
    print("[SUCCESS] All imports successful")
except Exception as e:
    print(f"[ERROR] Import error: {e}")
    traceback.print_exc()
    sys.exit(1)



class TestResults:
    """Track test results and provide summary."""
    
    def __init__(self):
        self.tests: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def add_test(self, name: str, success: bool, message: str = "", details: Any = None):
        """Add a test result."""
        self.tests.append({
            "name": name,
            "success": success,
            "message": message,
            "details": details
        })
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.total_tests}")
        print(f"[PASS] Passed: {self.passed_tests}")
        print(f"[FAIL] Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%" if self.total_tests > 0 else "N/A")
        
        if self.failed_tests > 0:
            print(f"\n{'='*60}")
            print("FAILED TESTS:")
            print(f"{'='*60}")
            for test in self.tests:
                if not test["success"]:
                    print(f"[FAIL] {test['name']}: {test['message']}")
        
        print(f"\n{'='*60}")


# Mock context for testing MCP tools
class MockContext:
    """Mock context that mimics MCP Context structure."""
    
    def __init__(self, db_connection=None, crawler=None):
        self.request_context = MagicMock()
        self.request_context.lifespan_context = MagicMock()
        self.request_context.lifespan_context.db_connection = db_connection
        self.request_context.lifespan_context.crawler = crawler



async def test_database_connection(results: TestResults):
    """Test PostgreSQL database connection."""
    print("\n[TEST] Testing database connection...")
    
    try:
        # Test database configuration
        from src.database import DatabaseConfig
        config = DatabaseConfig()
        results.add_test(
            "Database Configuration", 
            True, 
            f"Config loaded: {config.host}:{config.port}/{config.database}"
        )
    except Exception as e:
        results.add_test(
            "Database Configuration", 
            False, 
            f"Failed to load config: {str(e)}"
        )
        return False
    
    try:
        # Test database connection
        db_connection = await initialize_db_connection()
        
        # Test basic query
        result = await db_connection.fetch("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            results.add_test(
                "Database Connection", 
                True, 
                "Successfully connected and executed test query"
            )
            
            # Test schema existence
            schema_result = await db_connection.fetch(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'crawl'"
            )
            if schema_result:
                results.add_test(
                    "Crawl Schema", 
                    True, 
                    "Crawl schema exists"
                )
            else:
                results.add_test(
                    "Crawl Schema", 
                    False, 
                    "Crawl schema does not exist - run setup SQL first"
                )
        else:
            results.add_test(
                "Database Connection", 
                False, 
                "Connection succeeded but test query failed"
            )
        
        await close_db_connection()
        return True
        
    except Exception as e:
        results.add_test(
            "Database Connection", 
            False, 
            f"Connection failed: {str(e)}"
        )
        return False



async def test_mcp_tool_get_available_sources(results: TestResults):
    """Test get_available_sources MCP tool."""
    print("\n[TEST] Testing get_available_sources tool...")
    
    try:
        # Initialize database connection properly
        db_connection = await initialize_db_connection()
        ctx = MockContext(db_connection=db_connection)
        
        # Call the MCP tool
        result = await get_available_sources(ctx)
        
        # Parse the JSON result
        result_data = json.loads(result)
        
        if result_data.get("success", False):
            results.add_test(
                "get_available_sources", 
                True, 
                f"Retrieved {result_data.get('count', 0)} sources"
            )
        else:
            results.add_test(
                "get_available_sources", 
                False, 
                f"Tool failed: {result_data.get('error', 'Unknown error')}"
            )
        
        # Clean up
        await close_db_connection()
            
    except Exception as e:
        results.add_test(
            "get_available_sources", 
            False, 
            f"Exception: {str(e)}"
        )


async def test_environment_variables(results: TestResults):
    """Test environment variable configuration."""
    print("\n[TEST] Testing environment variables...")
    
    required_vars = [
        "POSTGRES_HOST", 
        "POSTGRES_PORT", 
        "POSTGRES_DB", 
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var) 
    
    if not missing_vars:
        results.add_test(
            "Required Environment Variables", 
            True, 
            "All required PostgreSQL environment variables are set"
        )
    else:
        results.add_test(
            "Required Environment Variables", 
            False, 
            f"Missing environment variables: {', '.join(missing_vars)}"
        )



async def main():
    """Run all tests and display results."""
    print("[START] Starting Crawl4AI-RAG MCP Server Functionality Tests")
    print("=" * 60)
    
    results = TestResults()
    
    # Test suite
    await test_environment_variables(results)
    await test_database_connection(results)
    await test_mcp_tool_get_available_sources(results)
    
    # Print final results
    results.print_summary()
    
    # Return exit code based on results
    return 0 if results.failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
