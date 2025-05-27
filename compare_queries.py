#!/usr/bin/env python3
"""
Compare working direct queries with lightrag function queries.
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

async def compare_queries():
    """Compare working queries with lightrag function queries."""
    print("=== Query Comparison ===\n")
    
    from database import initialize_db_connection, get_db_connection, close_db_connection
    
    await initialize_db_connection()
    
    try:
        db = await get_db_connection()
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        # Test 1: Direct working query (from our successful tests)
        print("[Test 1] Direct working query...")
        query = "fusion"
        results = await db.fetch(f"""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'description' ILIKE '%{query}%'
            LIMIT 3
        """)
        print(f"   Direct query found {len(results)} results")
        for row in results:
            print(f"   - {row['entity_id']}: {row['description'][:50]}...")
        
        # Test 2: Exact same query as in lightrag function
        print(f"\n[Test 2] LightRAG function query...")
        safe_query = query.replace("'", "''")
        query_pattern = f"%{safe_query}%"
        lightrag_results = await db.fetch(f"""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path,
                   properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'description' ILIKE '{query_pattern}'
            LIMIT 3
        """)
        print(f"   LightRAG-style query found {len(lightrag_results)} results")
        for row in lightrag_results:
            print(f"   - {row['entity_id']}: {row['description'][:50]}...")
        
        # Test 3: Check if the issue is with the additional fields
        print(f"\n[Test 3] Checking field access...")
        if lightrag_results:
            for row in lightrag_results:
                print(f"   Row data: entity_id={row['entity_id']}, type={type(row['entity_id'])}")
                print(f"   Description: {row['description'][:100] if row['description'] else 'None'}")
                print(f"   Entity type: {row['entity_type']}")
                print(f"   File path: {row['file_path'][:50] if row['file_path'] else 'None'}...")
        
        # Test 4: Check what the lightrag function is actually doing
        print(f"\n[Test 4] Testing lightrag function step by step...")
        from lightrag_integration import search_lightrag_documents
        
        # Run the function and see what happens
        function_results = await search_lightrag_documents("fusion", 3)
        print(f"   Function returned {len(function_results)} results")
        
        if function_results:
            for result in function_results:
                print(f"   - {result['id']}: {result['content'][:50]}...")
        
    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")
        import traceback
        traceback.print_exc()
    
    await close_db_connection()
    print("\n[OK] Comparison completed")

if __name__ == "__main__":
    asyncio.run(compare_queries())
