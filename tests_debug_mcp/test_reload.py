#!/usr/bin/env python3
"""
Test with explicit module reloading.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import importlib

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

async def test_with_reload():
    """Test with explicit module reloading."""
    print("=== Test With Module Reload ===\n")
    
    from database import initialize_db_connection, close_db_connection
    
    await initialize_db_connection()
    print("[OK] Database connection initialized")
    
    # Import and immediately reload the lightrag module
    print("\n[Testing] Importing and reloading lightrag_integration...")
    
    import lightrag_integration
    importlib.reload(lightrag_integration)
    print("[OK] Module reloaded")
    
    # Test the function
    print(f"\n[Testing] Calling search_lightrag_documents...")
    results = await lightrag_integration.search_lightrag_documents("fusion", 3)
    print(f"[RESULT] Function returned {len(results)} results")
    
    if results:
        for result in results:
            print(f"  - {result['id']}: {result['content'][:50]}...")
    else:
        print("  No results returned")
    
    # Also test the other functions
    print(f"\n[Testing] Other functions...")
    
    collections = await lightrag_integration.get_lightrag_collections()
    print(f"Collections: {len(collections)}")
    
    schema_info = await lightrag_integration.get_lightrag_schema_info()
    stats = schema_info.get('statistics', {})
    print(f"Schema info: {stats.get('total_nodes', 0)} nodes")
    
    await close_db_connection()

if __name__ == "__main__":
    asyncio.run(test_with_reload())
