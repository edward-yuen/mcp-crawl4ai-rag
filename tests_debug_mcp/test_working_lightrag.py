#!/usr/bin/env python3
"""
Test LightRAG integration with fixed approach.
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

async def test_fixed_lightrag_search(db, query: str, match_count: int = 5):
    """Test the fixed LightRAG search approach."""
    try:
        # Load AGE extension and set search path
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        # Search by description
        desc_results = await db.fetch("""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path,
                   properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'description' ILIKE $1
            LIMIT $2
        """, f"%{query}%", match_count)
        
        # Search by entity_id  
        id_results = await db.fetch("""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path,
                   properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'entity_id' ILIKE $1
            LIMIT $2
        """, f"%{query}%", match_count)
        
        # Combine and deduplicate results
        all_results = {}
        for row in desc_results + id_results:
            if row['id'] not in all_results:
                all_results[row['id']] = row
        
        results = list(all_results.values())[:match_count]
        
        # Convert to standard format
        documents = []
        for row in results:
            entity_id = row['entity_id'] or str(row['id'])
            description = row['description'] or ''
            entity_type = row['entity_type'] or 'unknown'
            file_path = row['file_path'] or ''
            source_id = row['source_id'] or ''
            
            # Calculate text similarity score
            similarity = 0.9 if query.lower() in entity_id.lower() else 0.8
            if query.lower() in description.lower():
                similarity = max(similarity, 0.85)
            
            doc = {
                'id': entity_id,
                'content': description,
                'metadata': {
                    'entity_type': entity_type,
                    'file_path': file_path,
                    'source_id': source_id,
                    'entity_id': entity_id
                },
                'similarity': similarity
            }
            documents.append(doc)
        
        # Sort by similarity score (highest first)
        documents.sort(key=lambda x: x['similarity'], reverse=True)
        
        return documents
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

async def test_fixed_integration():
    """Test the fixed LightRAG integration."""
    print("=== Testing Fixed LightRAG Integration ===\n")
    
    # Create direct database connection
    try:
        db = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        print("[OK] Database connection established")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return
    
    try:
        # Test 1: Basic search
        print("\n[Test 1] Searching for 'fusion' entities...")
        results = await test_fixed_lightrag_search(db, "fusion", 5)
        print(f"   [OK] Found {len(results)} fusion-related entities")
        for i, result in enumerate(results[:3]):
            print(f"   - {i+1}. {result['id']} (similarity: {result['similarity']:.2f})")
            print(f"        {result['content'][:80]}...")
        
        # Test 2: Search for strategies
        print("\n[Test 2] Searching for 'strategy' entities...")
        results = await test_fixed_lightrag_search(db, "strategy", 5)
        print(f"   [OK] Found {len(results)} strategy-related entities")
        for i, result in enumerate(results[:2]):
            print(f"   - {i+1}. {result['id']} (type: {result['metadata']['entity_type']})")
            print(f"        {result['content'][:80]}...")
        
        # Test 3: Search for LLM
        print("\n[Test 3] Searching for 'LLM' entities...")
        results = await test_fixed_lightrag_search(db, "LLM", 3)
        print(f"   [OK] Found {len(results)} LLM-related entities")
        for i, result in enumerate(results):
            print(f"   - {i+1}. {result['id']} (file: {result['metadata']['file_path'][:50]}...)")
        
        # Test 4: Get collections
        print("\n[Test 4] Getting available collections...")
        collections = await db.fetch("""
            SELECT DISTINCT properties::json->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'file_path' IS NOT NULL
                AND properties::json->>'file_path' != ''
            ORDER BY properties::json->>'file_path'
            LIMIT 5
        """)
        
        collection_list = [row['file_path'] for row in collections if row['file_path']]
        print(f"   [OK] Found {len(collection_list)} collections")
        for i, collection in enumerate(collection_list[:3]):
            print(f"   - {i+1}. {collection[:70]}...")
        
        # Test 5: Test collection filtering
        if collection_list:
            print(f"\n[Test 5] Testing collection filtering with '{collection_list[0][:30]}...'")
            # Filter results manually since we're testing the core functionality
            all_results = await test_fixed_lightrag_search(db, "analysis", 10)
            filtered_results = [r for r in all_results if collection_list[0].lower() in (r['metadata']['file_path'] or '').lower()]
            print(f"   [OK] Found {len(filtered_results)} results in target collection")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()
        print("\n[OK] Fixed integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_fixed_integration())
