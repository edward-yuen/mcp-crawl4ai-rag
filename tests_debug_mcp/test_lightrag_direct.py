#!/usr/bin/env python3
"""
Simple test to query LightRAG data directly.
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Override host for local testing (outside Docker)
os.environ['POSTGRES_HOST'] = 'localhost'

async def test_lightrag_direct():
    """Test LightRAG data directly with AGE queries."""
    try:
        # Connect directly to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        print("Connected to PostgreSQL successfully!")
        
        # Test basic counts
        node_count = await conn.fetchval("SELECT count(*) FROM chunk_entity_relation._ag_label_vertex")
        edge_count = await conn.fetchval("SELECT count(*) FROM chunk_entity_relation._ag_label_edge")
        print(f"Total nodes: {node_count}, Total edges: {edge_count}")
        
        # Test direct search for Fusion Analysis using AGE properties
        print("Searching for fusion-related entities...")
        
        # First, let's see what we can get with a simple properties lookup
        sample_entities = await conn.fetch("""
            SELECT properties
            FROM chunk_entity_relation._ag_label_vertex
            LIMIT 5
        """)
        
        print("Sample entity properties:")
        for i, entity in enumerate(sample_entities):
            props_str = str(entity['properties'])
            print(f"  {i+1}. Properties: {props_str[:100]}...")
        
        # Load AGE extension and try cypher query for fusion
        await conn.execute("LOAD 'age'")
        await conn.execute("SET search_path = ag_catalog, '$user', public")
        
        print("\nTrying Cypher query for fusion entities...")
        try:
            cypher_results = await conn.fetch("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n) 
                WHERE n.entity_id CONTAINS 'Fusion'
                RETURN n.entity_id, n.description, n.entity_type
                LIMIT 10
                $$) as (entity_id agtype, description agtype, entity_type agtype)
            """)
            
            print(f"Cypher fusion query results ({len(cypher_results)}):")
            for row in cypher_results:
                # Clean AGE string format
                entity_id = str(row['entity_id']).strip('"')
                description = str(row['description']).strip('"')
                entity_type = str(row['entity_type']).strip('"')
                print(f"- {entity_id}: {description[:100]}...")
                
        except Exception as cypher_e:
            print(f"Cypher fusion query failed: {cypher_e}")
            
        # Try a broader cypher query for any entities
        print("\nTrying broader Cypher query...")
        try:
            broad_results = await conn.fetch("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n) 
                RETURN n.entity_id, n.description, n.entity_type
                LIMIT 5
                $$) as (entity_id agtype, description agtype, entity_type agtype)
            """)
            
            print(f"Broad query results ({len(broad_results)}):")
            for row in broad_results:
                entity_id = str(row['entity_id']).strip('"')
                description = str(row['description']).strip('"')
                entity_type = str(row['entity_type']).strip('"')
                print(f"- {entity_id}: {description[:50]}...")
                
        except Exception as broad_e:
            print(f"Broad cypher query failed: {broad_e}")
        
        print(f"\nFusion entities found ({len(fusion_entities)}):")
        for entity in fusion_entities:
            print(f"- {entity['entity_id']}: {entity['description'][:100]}...")
        
        # Test AGE cypher query
        await conn.execute("LOAD 'age'")
        await conn.execute("SET search_path = ag_catalog, '$user', public")
        
        try:
            cypher_results = await conn.fetch("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n) 
                WHERE n.entity_id = 'Fusion Analysis'
                RETURN n.entity_id, n.description, n.entity_type
                LIMIT 5
                $$) as (entity_id agtype, description agtype, entity_type agtype)
            """)
            
            print(f"\nCypher query results ({len(cypher_results)}):")
            for row in cypher_results:
                entity_id = str(row['entity_id']).strip('"')
                description = str(row['description']).strip('"')
                entity_type = str(row['entity_type']).strip('"')
                print(f"- {entity_id}: {description[:100]}...")
                
        except Exception as cypher_e:
            print(f"Cypher query failed: {cypher_e}")
        
        await conn.close()
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lightrag_direct())
