#!/usr/bin/env python3
"""
Quick test of improved LightRAG search.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.database import initialize_db_connection, close_db_connection
from src.lightrag_search_improved import search_lightrag_documents_improved


async def main():
    """Test the improved search."""
    print("Testing improved LightRAG search...")
    
    await initialize_db_connection()
    
    # Test queries
    queries = [
        "options strategies",
        "advanced options",
        "covered call",
        "butterfly spread",
        "iron condor",
        "options trading"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Searching for: '{query}'")
        print('='*60)
        
        results = await search_lightrag_documents_improved(query, match_count=5)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['id']} (score: {result['similarity']:.2f})")
                print(f"   Type: {result['metadata']['entity_type']}")
                print(f"   Content: {result['content'][:150]}...")
        else:
            print("No results found.")
    
    await close_db_connection()


if __name__ == "__main__":
    asyncio.run(main())
