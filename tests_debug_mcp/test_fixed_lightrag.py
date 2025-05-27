#!/usr/bin/env python3
"""
Test the fixed LightRAG integration.
"""
import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import json
from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Override host for local testing (outside Docker)
os.environ['POSTGRES_HOST'] = 'localhost'

from lightrag_integration import (
    search_lightrag_documents,
    get_lightrag_collections, 
    get_lightrag_schema_info,
    search_multi_schema
)
from database import initialize_db_connection, close_db_connection

async def test_lightrag_integration():
    """Test the fixed LightRAG integration functions."""
    print("=== Testing Fixed LightRAG Integration ===\n")
    
    # Initialize database connection
    print("[Setup] Initializing database connection...")
    try:
        await initialize_db_connection()
        print("   [OK] Database connection initialized")
    except Exception as e:
        print(f"   [ERROR] Database initialization failed: {e}")
        return
    
    # Test 1: Get schema info
    print("[Test 1] Getting LightRAG schema info...")
    try:
        schema_info = await get_lightrag_schema_info()
        print(f"   [OK] Found {schema_info['statistics']['total_nodes']} nodes, {schema_info['statistics']['total_edges']} edges")
        print(f"   [OK] Found {len(schema_info['entity_types'])} entity types")
        print(f"   [OK] Top entity types: {[et['type'] for et in schema_info['entity_types'][:3]]}")
    except Exception as e:
        print(f"   [ERROR] Schema info failed: {e}")
        
    # Test 2: Get collections
    print("\n[Test 2] Getting available collections...")
    try:
        collections = await get_lightrag_collections()
        print(f"   [OK] Found {len(collections)} collections")
        if collections:
            print(f"   [OK] Sample collections: {collections[:3]}")
    except Exception as e:
        print(f"   [ERROR] Collections failed: {e}")
        
    # Test 3: Search for entities
    print("\n[Test 3] Searching for 'fusion' entities...")
    try:
        results = await search_lightrag_documents(
            query="fusion",
            match_count=5
        )
        print(f"   [OK] Found {len(results)} fusion-related entities")
        for i, result in enumerate(results[:3]):
            print(f"   - Result {i+1}: {result['id']} (similarity: {result['similarity']:.2f})")
            print(f"     Content: {result['content'][:100]}...")
    except Exception as e:
        print(f"   [ERROR] Search failed: {e}")
        
    # Test 4: Search with collection filter
    print("\n[Test 4] Searching with collection filter...")
    try:
        # Use the first collection we found
        collections = await get_lightrag_collections()
        if collections:
            test_collection = collections[0]
            results = await search_lightrag_documents(
                query="strategy",
                match_count=3,
                collection_name=test_collection
            )
            print(f"   [OK] Found {len(results)} results in collection '{test_collection[:50]}...'")
        else:
            print("   [SKIP] No collections found to test with")
    except Exception as e:
        print(f"   [ERROR] Filtered search failed: {e}")
        
    # Test 5: Multi-schema search (lightrag only to avoid circular imports)
    print("\n[Test 5] Testing multi-schema search (lightrag only)...")
    try:
        # Test just lightrag schema
        results = await search_lightrag_documents(
            query="LLM",
            match_count=3
        )
        print(f"   [OK] Direct lightrag search returned {len(results)} results")
        if results:
            print(f"   [OK] Sample result: {results[0]['id']}")
    except Exception as e:
        print(f"   [ERROR] Direct lightrag search failed: {e}")
        
    print("\n[OK] LightRAG integration test completed!")
    
    # Cleanup database connection
    print("\n[Cleanup] Closing database connection...")
    try:
        await close_db_connection()
        print("   [OK] Database connection closed")
    except Exception as e:
        print(f"   [ERROR] Database cleanup failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_lightrag_integration())
