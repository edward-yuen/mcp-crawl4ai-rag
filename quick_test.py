#!/usr/bin/env python3
"""
Quick test script to run inside Docker container.
Usage: docker exec mcp-crawl4ai-rag python /app/quick_test.py
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, '/app/src')

async def main():
    print("Quick Docker Connection Test")
    print("=" * 40)
    
    # Test 1: Environment variables
    print("\n1. Environment Variables:")
    print(f"   POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'not set')}")
    print(f"   POSTGRES_PORT: {os.getenv('POSTGRES_PORT', '5432')}")
    print(f"   POSTGRES_DB: {os.getenv('POSTGRES_DB', 'lightrag')}")
    
    # Test 2: Direct connection
    print("\n2. Testing PostgreSQL Connection...")
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=5432,
            database='lightrag',
            user='postgres',
            password='postgres'
        )
        print("   ✓ Connected to PostgreSQL")
        
        # Test 3: Check schemas
        schemas = await conn.fetch("""
            SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name IN ('crawl', 'chunk_entity_relation')
        """)
        print(f"\n3. Available Schemas: {[s['schema_name'] for s in schemas]}")
        
        # Test 4: Check data
        if any(s['schema_name'] == 'chunk_entity_relation' for s in schemas):
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex"
            )
            print(f"\n4. LightRAG Knowledge Graph: {count} nodes")
            
            # Sample search
            results = await conn.fetch("""
                SELECT properties::json->>'entity_id' as id,
                       properties::json->>'description' as desc
                FROM chunk_entity_relation._ag_label_vertex
                WHERE properties::json->>'description' ILIKE '%fusion%'
                LIMIT 3
            """)
            
            if results:
                print("\n5. Sample 'fusion' entities:")
                for r in results:
                    print(f"   - {r['id']}: {r['desc'][:60]}...")
            else:
                print("\n5. No 'fusion' entities found")
        
        await conn.close()
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n   Troubleshooting:")
        print("   - Check if PostgreSQL container is running")
        print("   - Verify both containers are on the same network")
        print("   - Run: docker network connect ai-lightrag_lightrag-network mcp-crawl4ai-rag")

if __name__ == "__main__":
    asyncio.run(main())
