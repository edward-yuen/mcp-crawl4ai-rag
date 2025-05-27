#!/usr/bin/env python3
"""
Direct test of the fixed LightRAG integration without global state.
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

async def test_lightrag_direct():
    """Test LightRAG integration with direct database connection."""
    print("=== Direct LightRAG Test ===\n")
    
    # Create direct database connection
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
        # Test 1: Get basic counts
        print("\n[Test 1] Getting basic node/edge counts...")
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        node_count = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_vertex"
        )
        edge_count = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_edge"
        )
        print(f"   [OK] Found {node_count} nodes, {edge_count} edges")
        
        # Test 2: Get collections using JSON queries
        print("\n[Test 2] Getting collections using JSON queries...")
        results = await db.fetch("""
            SELECT DISTINCT properties::json->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'file_path' IS NOT NULL
                AND properties::json->>'file_path' != ''
            ORDER BY properties::json->>'file_path'
            LIMIT 5
        """)
        
        collections = [row['file_path'] for row in results if row['file_path']]
        print(f"   [OK] Found {len(collections)} collections")
        for i, collection in enumerate(collections[:3]):
            print(f"   - Collection {i+1}: {collection[:80]}...")
        
        # Test 3: Search for entities (try with agtype handling)
        print("\n[Test 3] Searching for entities...")
        search_term = "fusion"
        
        # First, let's see the actual structure of a few properties
        sample_props = await db.fetch("""
            SELECT id, properties
            FROM chunk_entity_relation._ag_label_vertex 
            LIMIT 3
        """)
        
        print(f"   Sample properties structure:")
        for i, row in enumerate(sample_props):
            print(f"   - Row {i+1}: Type={type(row['properties'])}, Value={str(row['properties'])[:100]}...")
        
        # Try searching using different approaches
        try:
            # Method 1: Cast to text then use JSON operators
            search_results = await db.fetch(f"""
                SELECT id, properties::text
                FROM chunk_entity_relation._ag_label_vertex 
                WHERE (properties::text)::json->>'description' ILIKE '%{search_term}%'
                    OR (properties::text)::json->>'entity_id' ILIKE '%{search_term}%'
                LIMIT 5
            """)
            print(f"   [OK] Method 1 - Found {len(search_results)} results using cast to text")
        except Exception as e:
            print(f"   [ERROR] Method 1 failed: {e}")
            
            # Method 2: Try working directly with agtype
            try:
                search_results = await db.fetch("""
                    SELECT id, properties
                    FROM chunk_entity_relation._ag_label_vertex 
                    WHERE properties::text ILIKE '%fusion%'
                    LIMIT 5
                """)
                print(f"   [OK] Method 2 - Found {len(search_results)} results using text search")
            except Exception as e2:
                print(f"   [ERROR] Method 2 also failed: {e2}")
                search_results = []
        
        # Process results if we got any
        if search_results:
            print(f"   Processing {len(search_results)} search results...")
            for i, row in enumerate(search_results[:3]):
                try:
                    # Handle different possible property formats
                    props_value = row.get('properties') or row.get('properties::text')
                    if isinstance(props_value, str):
                        props = json.loads(props_value)
                    else:
                        props = props_value if isinstance(props_value, dict) else {}
                    
                    entity_id = props.get('entity_id', str(row['id']))
                    description = props.get('description', '')[:100]
                    print(f"   - Entity {i+1}: {entity_id}")
                    print(f"     Description: {description}...")
                except Exception as e:
                    print(f"   - Entity {i+1}: Failed to parse - {e}")
        else:
            print("   No search results to process")
        
        # Test 4: Entity types distribution
        print("\n[Test 4] Getting entity types distribution...")
        entity_types = await db.fetch("""
            SELECT properties::json->>'entity_type' as entity_type, 
                   count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties::json->>'entity_type' IS NOT NULL
            GROUP BY properties::json->>'entity_type'
            ORDER BY count DESC
            LIMIT 5
        """)
        
        print(f"   [OK] Top entity types:")
        for et in entity_types:
            if et['entity_type']:
                print(f"   - {et['entity_type']}: {et['count']} entities")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()
        print("\n[OK] Direct test completed!")

if __name__ == "__main__":
    asyncio.run(test_lightrag_direct())
