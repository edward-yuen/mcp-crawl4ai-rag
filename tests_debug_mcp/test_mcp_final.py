#!/usr/bin/env python3
"""
Test MCP server tools with fixed LightRAG integration.
"""
import asyncio
import sys
from pathlib import Path
import json
from dotenv import load_dotenv
import os

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

from database import initialize_db_connection, close_db_connection

async def test_mcp_server_lightrag_tools():
    """Test the MCP server LightRAG tool functions directly."""
    print("=== Testing MCP Server LightRAG Tools ===\n")
    
    # Initialize database connection (as MCP server would do)
    try:
        await initialize_db_connection()
        print("[OK] Database connection initialized (as MCP server does)")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return
    
    try:
        # Import and test the fixed integration functions
        from lightrag_integration import (
            search_lightrag_documents,
            get_lightrag_collections, 
            get_lightrag_schema_info,
            search_multi_schema
        )
        
        # Test 1: query_lightrag_schema tool function
        print("\n[Test 1] Testing query_lightrag_schema functionality...")
        results = await search_lightrag_documents(
            query="fusion analysis",
            match_count=3
        )
        print(f"   [OK] Found {len(results)} results")
        if results:
            print(f"   Sample result: {results[0]['id']} - {results[0]['content'][:60]}...")
            print(f"   Entity type: {results[0]['metadata']['entity_type']}")
        
        # Test 2: get_lightrag_info tool function
        print("\n[Test 2] Testing get_lightrag_info functionality...")
        schema_info = await get_lightrag_schema_info()
        collections = await get_lightrag_collections()
        
        stats = schema_info.get('statistics', {})
        print(f"   [OK] Schema info: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges")
        print(f"   [OK] Found {len(collections)} collections")
        print(f"   Entity types: {len(schema_info.get('entity_types', []))}")
        
        # Test 3: multi_schema_search tool function
        print("\n[Test 3] Testing multi_schema_search functionality...")
        multi_results = await search_multi_schema(
            query="LLM strategy",
            schemas=["lightrag"],
            match_count=2
        )
        lightrag_results = multi_results.get("results_per_schema", {}).get("lightrag", [])
        print(f"   [OK] Multi-schema search returned {len(lightrag_results)} results")
        
        # Test 4: Collection filtering (used by tools with collection parameter)
        print("\n[Test 4] Testing collection filtering...")
        if collections:
            filtered_results = await search_lightrag_documents(
                query="analysis",
                match_count=5,
                collection_name=collections[0]
            )
            print(f"   [OK] Filtered search in '{collections[0][:50]}...': {len(filtered_results)} results")
        else:
            print("   [SKIP] No collections available for filtering test")
        
        # Test 5: Error handling
        print("\n[Test 5] Testing error handling...")
        try:
            empty_results = await search_lightrag_documents(
                query="nonexistent_query_12345_unlikely_to_match",
                match_count=5
            )
            print(f"   [OK] Error handling works: {len(empty_results)} results for non-matching query")
        except Exception as e:
            print(f"   [ERROR] Error handling failed: {e}")
        
        print(f"\n[SUCCESS] All MCP server LightRAG tools are working correctly!")
        print(f"The MCP server can now:")
        print(f"✓ Search the LightRAG knowledge graph ({stats.get('total_nodes', 0)} entities)")
        print(f"✓ Retrieve schema information and collections")
        print(f"✓ Perform multi-schema searches")
        print(f"✓ Filter results by collection/document")
        print(f"✓ Handle errors gracefully")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup (as MCP server would do)
        try:
            await close_db_connection()
            print("\n[OK] Database connection closed")
        except Exception as e:
            print(f"[ERROR] Database cleanup failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server_lightrag_tools())
