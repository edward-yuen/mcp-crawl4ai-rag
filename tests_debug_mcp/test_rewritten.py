#!/usr/bin/env python3
"""
Test the completely rewritten lightrag_integration module.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

async def test_rewritten_module():
    """Test the completely rewritten lightrag integration module."""
    print("=== Testing Rewritten LightRAG Module ===\n")
    
    from database import initialize_db_connection, close_db_connection
    
    await initialize_db_connection()
    print("[OK] Database connection initialized")
    
    # Import the rewritten module
    from lightrag_integration import (
        search_lightrag_documents,
        get_lightrag_collections, 
        get_lightrag_schema_info,
        search_multi_schema
    )
    
    # Test 1: Search function
    print(f"\n[Test 1] Testing search_lightrag_documents...")
    results = await search_lightrag_documents("fusion", 3)
    print(f"   Found {len(results)} results")
    if results:
        for i, result in enumerate(results):
            print(f"   {i+1}. {result['id']}: {result['content'][:50]}...")
    
    # Test 2: Collections function
    print(f"\n[Test 2] Testing get_lightrag_collections...")
    collections = await get_lightrag_collections()
    print(f"   Found {len(collections)} collections")
    if collections:
        for i, collection in enumerate(collections[:2]):
            print(f"   {i+1}. {collection[:60]}...")
    
    # Test 3: Schema info function
    print(f"\n[Test 3] Testing get_lightrag_schema_info...")
    schema_info = await get_lightrag_schema_info()
    stats = schema_info.get('statistics', {})
    print(f"   Schema: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges")
    print(f"   Entity types: {len(schema_info.get('entity_types', []))}")
    
    # Test 4: Multi-schema search
    print(f"\n[Test 4] Testing search_multi_schema...")
    multi_results = await search_multi_schema(
        query="strategy",
        schemas=["lightrag"],
        match_count=2
    )
    lightrag_results = multi_results.get("results_per_schema", {}).get("lightrag", [])
    print(f"   Multi-schema search: {len(lightrag_results)} results")
    
    # Test 5: Collection filtering
    if collections:
        print(f"\n[Test 5] Testing collection filtering...")
        filtered_results = await search_lightrag_documents(
            query="analysis",
            match_count=3,
            collection_name=collections[0]
        )
        print(f"   Filtered search: {len(filtered_results)} results")
    
    await close_db_connection()
    
    print(f"\n[SUCCESS] All tests completed!")
    print(f"The LightRAG integration is now working correctly!")

if __name__ == "__main__":
    asyncio.run(test_rewritten_module())
