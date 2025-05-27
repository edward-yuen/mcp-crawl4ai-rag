#!/usr/bin/env python3
"""
Diagnostic test for LightRAG integration issues.
Tests connection and queries to the chunk_entity_relation schema.
"""
import asyncio
import asyncpg
import json
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Override host for local testing (outside Docker)
os.environ['POSTGRES_HOST'] = 'localhost'

async def test_lightrag_diagnosis():
    """Diagnose LightRAG connection and query issues."""
    print("=== LightRAG Diagnostic Test ===\n")
    
    try:
        # Connect directly to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        print("[OK] Connected to PostgreSQL successfully!")
        print(f"   Host: {os.getenv('POSTGRES_HOST')}")
        print(f"   Database: {os.getenv('POSTGRES_DB')}")
        
        # Test 1: Check if chunk_entity_relation schema exists
        print("\n[Test 1] Checking chunk_entity_relation schema...")
        schema_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_namespace 
                WHERE nspname = 'chunk_entity_relation'
            )
        """)
        print(f"   Schema exists: {schema_exists}")
        
        if not schema_exists:
            print("[ERROR] chunk_entity_relation schema not found!")
            await conn.close()
            return        
        # Test 2: Check AGE extension
        print("\n[Test 2] Checking AGE extension...")
        try:
            await conn.execute("LOAD 'age'")
            print("   [OK] AGE extension loaded successfully")
        except Exception as age_e:
            print(f"   [ERROR] AGE extension error: {age_e}")
        
        # Test 3: Check tables in chunk_entity_relation schema
        print("\n[Test 3] Checking tables in chunk_entity_relation schema...")
        tables = await conn.fetch("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'chunk_entity_relation'
            ORDER BY table_name
        """)
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']} ({table['table_type']})")
        
        # Test 4: Check vertex and edge counts
        print("\n[Test 4] Checking vertex and edge counts...")
        try:
            node_count = await conn.fetchval(
                "SELECT count(*) FROM chunk_entity_relation._ag_label_vertex"
            )
            edge_count = await conn.fetchval(
                "SELECT count(*) FROM chunk_entity_relation._ag_label_edge"
            )
            print(f"   Total nodes: {node_count}")
            print(f"   Total edges: {edge_count}")
        except Exception as count_e:
            print(f"   [ERROR] Count error: {count_e}")
        
        # Test 5: Sample vertex properties
        print("\n[Test 5] Examining vertex properties structure...")
        try:
            sample_vertices = await conn.fetch("""
                SELECT id, properties 
                FROM chunk_entity_relation._ag_label_vertex 
                LIMIT 3
            """)
            
            for i, vertex in enumerate(sample_vertices):
                print(f"\n   Vertex {i+1} (ID: {vertex['id']}):")
                props = vertex['properties']
                if isinstance(props, dict):
                    for key, value in props.items():
                        display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        print(f"     - {key}: {display_value}")
                else:
                    print(f"     Properties type: {type(props)}")
        except Exception as prop_e:
            print(f"   [ERROR] Properties error: {prop_e}")
        
        # Test 6: Try direct property search
        print("\n[Test 6] Testing direct property search...")
        try:
            fusion_results = await conn.fetch("""
                SELECT id, properties
                FROM chunk_entity_relation._ag_label_vertex
                WHERE properties->>'entity_id' ILIKE '%fusion%'
                   OR properties->>'description' ILIKE '%fusion%'
                LIMIT 5
            """)
            print(f"   Found {len(fusion_results)} fusion-related entities")
            for result in fusion_results:
                entity_id = result['properties'].get('entity_id', 'N/A')
                print(f"   - {entity_id}")
        except Exception as search_e:
            print(f"   [ERROR] Search error: {search_e}")
        
        # Test 7: Try Cypher query
        print("\n[Test 7] Testing Cypher query...")
        try:
            await conn.execute("SET search_path = ag_catalog, '$user', public")
            
            # First try a simple MATCH query
            cypher_results = await conn.fetch("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n)
                RETURN n
                LIMIT 2
                $$) as (n agtype)
            """)
            print(f"   [OK] Basic Cypher query successful! Found {len(cypher_results)} nodes")
            
            # Try a filtered query
            filtered_results = await conn.fetch("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n)
                WHERE n.entity_id CONTAINS 'Fusion'
                RETURN n.entity_id, n.description, n.entity_type
                LIMIT 5
                $$) as (entity_id agtype, description agtype, entity_type agtype)
            """)
            print(f"   [OK] Filtered Cypher query found {len(filtered_results)} fusion entities")
            
        except Exception as cypher_e:
            print(f"   [ERROR] Cypher error: {cypher_e}")
            import traceback
            traceback.print_exc()
        
        # Test 8: Check entity types distribution
        print("\n[Test 8] Checking entity types distribution...")
        try:
            entity_types = await conn.fetch("""
                SELECT properties->>'entity_type' as entity_type, count(*) as count
                FROM chunk_entity_relation._ag_label_vertex
                WHERE properties->>'entity_type' IS NOT NULL
                GROUP BY properties->>'entity_type'
                ORDER BY count DESC
                LIMIT 10
            """)
            print(f"   Top entity types:")
            for et in entity_types:
                print(f"   - {et['entity_type']}: {et['count']} entities")
        except Exception as type_e:
            print(f"   [ERROR] Entity type error: {type_e}")
        
        await conn.close()
        print("\n[OK] Diagnostic test completed!")
        
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lightrag_diagnosis())
