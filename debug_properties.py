#!/usr/bin/env python3
"""Debug properties structure in LightRAG AGE graph."""
import asyncio
import asyncpg
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

async def debug_properties():
    """Debug the properties structure in the AGE graph."""
    print("=== Properties Structure Debug ===\n")
    
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        # Get a sample vertex and examine its properties
        sample = await conn.fetchrow(
            "SELECT id, properties FROM chunk_entity_relation._ag_label_vertex LIMIT 1"
        )
        
        print(f"Properties type: {type(sample['properties'])}")
        print(f"Properties raw content (first 200 chars): {str(sample['properties'])[:200]}...")
        
        # Try to parse as JSON
        try:
            props_dict = json.loads(sample['properties'])
            print(f"\nParsed JSON successfully!")
            print(f"Keys: {list(props_dict.keys())}")
            
            # Show sample values
            for key, value in props_dict.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"\nJSON parse error: {e}")
        
        # Test Cypher property access
        print("\n=== Testing Cypher Property Access ===")
        await conn.execute("LOAD 'age'")
        await conn.execute("SET search_path = ag_catalog, '$user', public")
        
        # Try different property access methods
        try:
            result = await conn.fetchrow("""
                SELECT * FROM cypher('chunk_entity_relation', $$
                MATCH (n)
                RETURN n
                LIMIT 1
                $$) as (node agtype)
            """)
            
            print(f"Cypher node result type: {type(result['node'])}")
            print(f"Cypher node result: {str(result['node'])[:200]}...")
            
        except Exception as e:
            print(f"Cypher access error: {e}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_properties())
