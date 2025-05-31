#!/usr/bin/env python3
"""
Test script to diagnose and fix options strategies search in LightRAG schema.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import initialize_db_connection, close_db_connection
from src.lightrag_integration import search_lightrag_documents, get_lightrag_schema_info
from src.lightrag_knowledge_graph import (
    search_entities_by_embedding,
    get_entities_by_type,
    query_knowledge_graph
)


async def test_lightrag_search():
    """Test various search methods for options strategies."""
    print("=" * 60)
    print("Testing LightRAG Search for Options Strategies")
    print("=" * 60)
    
    await initialize_db_connection()
    
    # Test 1: Basic search
    print("\n1. Basic search for 'options':")
    results = await search_lightrag_documents("options", match_count=5)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. {result['id']}")
        print(f"   Content: {result['content'][:150]}...")
    
    # Test 2: Search for 'strategies'
    print("\n\n2. Basic search for 'strategies':")
    results = await search_lightrag_documents("strategies", match_count=5)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. {result['id']}")
        print(f"   Content: {result['content'][:150]}...")
    
    # Test 3: Search for 'advanced options'
    print("\n\n3. Search for 'advanced options':")
    results = await search_lightrag_documents("advanced options", match_count=5)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. {result['id']}")
        print(f"   Content: {result['content'][:150]}...")
    
    # Test 4: Search using entity search
    print("\n\n4. Entity search for 'options':")
    entities = await search_entities_by_embedding("options", None, 5)
    print(f"Found {len(entities)} entities")
    for i, entity in enumerate(entities[:3], 1):
        print(f"\n{i}. {entity['entity_id']} ({entity['entity_type']})")
        print(f"   Description: {entity['description'][:150]}...")
    
    # Test 5: Get all category entities (might include options strategies)
    print("\n\n5. Get category entities:")
    categories = await get_entities_by_type("category", 10)
    print(f"Found {len(categories)} categories")
    # Filter for options-related categories
    options_categories = [c for c in categories if 'option' in c.get('entity_id', '').lower() or 'option' in c.get('description', '').lower()]
    print(f"Options-related categories: {len(options_categories)}")
    for cat in options_categories[:5]:
        print(f"\n- {cat['entity_id']}")
        print(f"  {cat['description'][:150]}...")
    
    # Test 6: Direct Cypher query
    print("\n\n6. Direct Cypher query for options-related entities:")
    cypher_query = """
    MATCH (n)
    WHERE n.description =~ '(?i).*option.*' OR n.entity_id =~ '(?i).*option.*'
    RETURN n.entity_id, n.description, n.entity_type
    LIMIT 10
    """
    results = await query_knowledge_graph(cypher_query)
    print(f"Found {len(results)} results via Cypher")
    for result in results[:5]:
        print(f"\n- Result: {result}")
    
    await close_db_connection()


async def search_options_strategies():
    """Search specifically for advanced options strategies."""
    print("\n\n" + "=" * 60)
    print("Searching for Advanced Options Strategies")
    print("=" * 60)
    
    await initialize_db_connection()
    
    # List of options strategy keywords to search
    strategy_keywords = [
        "spread", "straddle", "strangle", "butterfly", "condor", 
        "collar", "covered call", "protective put", "iron condor",
        "calendar spread", "diagonal spread", "ratio spread"
    ]
    
    all_results = {}
    
    for keyword in strategy_keywords:
        results = await search_lightrag_documents(keyword, match_count=3)
        if results:
            all_results[keyword] = results
            print(f"\nFound {len(results)} results for '{keyword}'")
    
    # Display summary
    print("\n\nSummary of options strategies found:")
    print("-" * 40)
    for strategy, results in all_results.items():
        print(f"\n{strategy.upper()}:")
        for result in results[:2]:
            print(f"  - {result['id']}")
            print(f"    {result['content'][:100]}...")
    
    await close_db_connection()


async def main():
    """Run all tests."""
    await test_lightrag_search()
    await search_options_strategies()


if __name__ == "__main__":
    asyncio.run(main())
