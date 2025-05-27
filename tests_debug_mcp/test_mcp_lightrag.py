#!/usr/bin/env python3
"""
Test MCP server LightRAG integration functions.
"""
import asyncio
import sys
from pathlib import Path
import json
from dotenv import load_dotenv
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

from src.database import initialize_db_connection, close_db_connection
from src.lightrag_integration import (
    search_lightrag_documents,
    get_lightrag_collections, 
    get_lightrag_schema_info,
    search_multi_schema
)

async def test_mcp_lightrag_functions():
    """Test all LightRAG functions used by the MCP server."""
    print("=== Testing MCP LightRAG Functions ===\n")
    
    # Initialize database connection
    print("[Setup] Initializing database connection...")
    try:
        await initialize_db_connection()
        print("   [OK] Database connection initialized")
    except Exception as e:
        print(f"   [ERROR] Database initialization failed: {e}")
        return
    
    try:
        # Test 1: search_lightrag_documents (used by query_lightrag_schema)
        print("\n[Test 1] Testing search_lightrag_documents...")
        try:
            results = await search_lightrag_documents(
                query="fusion",
                match_count=3
            )
            print(f"   [OK] Found {len(results)} results")
            if results:
                print(f"   Sample: {results[0]['id']} - {results[0]['content'][:50]}...")
        except Exception as e:
            print(f"   [ERROR] search_lightrag_documents failed: {e}")
        
        # Test 2: get_lightrag_schema_info (used by get_lightrag_info)
        print("\n[Test 2] Testing get_lightrag_schema_info...")
        try:
            schema_info = await get_lightrag_schema_info()
            stats = schema_info.get('statistics', {})
            print(f"   [OK] Schema info: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges")
            print(f"   Entity types: {len(schema_info.get('entity_types', []))}")
        except Exception as e:
            print(f"   [ERROR] get_lightrag_schema_info failed: {e}")
        
        # Test 3: get_lightrag_collections (used by get_lightrag_info)
        print("\n[Test 3] Testing get_lightrag_collections...")
        try:
            collections = await get_lightrag_collections()
            print(f"   [OK] Found {len(collections)} collections")
            if collections:
                print(f"   Sample: {collections[0][:60]}...")
        except Exception as e:
            print(f"   [ERROR] get_lightrag_collections failed: {e}")
        
        # Test 4: search_multi_schema (used by multi_schema_search)
        print("\n[Test 4] Testing search_multi_schema...")
        try:
            results = await search_multi_schema(
                query="strategy",
                schemas=["lightrag"],
                match_count=2
            )
            lightrag_results = results.get("results_per_schema", {}).get("lightrag", [])
            print(f"   [OK] Multi-schema search: {len(lightrag_results)} lightrag results")
            if lightrag_results:
                print(f"   Sample: {lightrag_results[0]['id']}")
        except Exception as e:
            print(f"   [ERROR] search_multi_schema failed: {e}")
        
        # Test 5: Collection filtering
        print("\n[Test 5] Testing collection filtering...")
        try:
            collections = await get_lightrag_collections()
            if collections:
                filtered_results = await search_lightrag_documents(
                    query="LLM",
                    match_count=3,
                    collection_name=collections[0]
                )
                print(f"   [OK] Filtered search: {len(filtered_results)} results in collection")
            else:
                print("   [SKIP] No collections available for filtering test")
        except Exception as e:
            print(f"   [ERROR] Collection filtering failed: {e}")
            
    except Exception as e:
        print(f"[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup database connection
        print("\n[Cleanup] Closing database connection...")
        try:
            await close_db_connection()
            print("   [OK] Database connection closed")
        except Exception as e:
            print(f"   [ERROR] Database cleanup failed: {e}")
    
    print("\n[OK] MCP LightRAG function test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_lightrag_functions())
