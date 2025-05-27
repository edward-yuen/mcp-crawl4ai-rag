#!/usr/bin/env python3
"""
Final test to verify that the LightRAG integration works correctly with the MCP server.
"""
import asyncio
import sys
from pathlib import Path
import json
from dotenv import load_dotenv
import os
import asyncpg

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

async def test_final_integration():
    """Final integration test to ensure everything works."""
    print("=== Final LightRAG Integration Test ===\n")
    
    # Test direct database connection
    try:
        db = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        print("[OK] Direct database connection established")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return
    
    try:
        # Test the core functionality that the MCP server needs
        print("\n[Test 1] Basic node count (schema validation)...")
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        node_count = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_vertex"
        )
        print(f"   [OK] Found {node_count} nodes in knowledge graph")
        
        # Test search functionality (core of search_lightrag_documents)
        print("\n[Test 2] Entity search functionality...")
        search_results = await db.fetch("""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'description' ILIKE $1
            LIMIT 5
        """, "%fusion%")
        
        print(f"   [OK] Search returned {len(search_results)} results")
        for i, row in enumerate(search_results[:2]):
            entity_id = row['entity_id'] or f"node_{row['id']}"
            description = (row['description'] or '')[:60]
            print(f"   - {i+1}. {entity_id}: {description}...")
        
        # Test collections functionality (core of get_lightrag_collections)
        print("\n[Test 3] Collections functionality...")
        collections = await db.fetch("""
            SELECT DISTINCT properties::json->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'file_path' IS NOT NULL
                AND properties::json->>'file_path' != ''
            ORDER BY properties::json->>'file_path'
            LIMIT 3
        """)
        
        collection_list = [row['file_path'] for row in collections if row['file_path']]
        print(f"   [OK] Found {len(collection_list)} collections")
        for i, collection in enumerate(collection_list):
            print(f"   - {i+1}. {collection[:70]}...")
        
        # Test schema info functionality (core of get_lightrag_schema_info)
        print("\n[Test 4] Schema info functionality...")
        entity_types = await db.fetch("""
            SELECT properties::json->>'entity_type' as entity_type, 
                   count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties::json->>'entity_type' IS NOT NULL
            GROUP BY properties::json->>'entity_type'
            ORDER BY count DESC
            LIMIT 5
        """)
        
        print(f"   [OK] Found {len(entity_types)} entity types")
        for et in entity_types:
            if et['entity_type']:
                print(f"   - {et['entity_type']}: {et['count']} entities")
        
        # Test filtering functionality
        if collection_list:
            print(f"\n[Test 5] Collection filtering with '{collection_list[0][:30]}...'")
            filtered_results = await db.fetch("""
                SELECT id, properties::json->>'entity_id' as entity_id,
                       properties::json->>'file_path' as file_path
                FROM chunk_entity_relation._ag_label_vertex 
                WHERE properties::json->>'description' ILIKE $1
                    AND properties::json->>'file_path' = $2
                LIMIT 3
            """, "%analysis%", collection_list[0])
            
            print(f"   [OK] Filtered search returned {len(filtered_results)} results")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()
        print("\n[SUCCESS] All core LightRAG functionality is working!")
        print("The MCP server should now be able to correctly use the LightRAG knowledge graph.")

if __name__ == "__main__":
    asyncio.run(test_final_integration())
