#!/usr/bin/env python3
"""
Test the lightrag function without exception handling to see the real error.
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

async def test_without_exception_handling():
    """Test the lightrag function without exception handling."""
    print("=== Test Without Exception Handling ===\n")
    
    from database import initialize_db_connection, get_db_connection, close_db_connection
    
    await initialize_db_connection()
    print("[OK] Database connection initialized")
    
    # Test that we can get the connection
    db = await get_db_connection()
    print(f"[OK] Got database connection: {type(db)}")
    
    # Test basic functionality
    count = await db.fetchval("SELECT count(*) FROM chunk_entity_relation._ag_label_vertex")
    print(f"[OK] Node count: {count}")
    
    # Now manually execute the lightrag function logic WITHOUT try/catch
    print("\n[Testing] Running lightrag function logic without exception handling...")
    
    query = "fusion"
    match_count = 3
    collection_name = None
    
    # This is the exact code from the function, but without try/catch
    db = await get_db_connection()
    
    # Load AGE extension and set search path
    await db.execute("LOAD 'age'")
    await db.execute("SET search_path = ag_catalog, '$user', public")
    
    # Search by description (using string formatting to avoid agtype parameter issues)
    # Escape single quotes to prevent SQL injection
    safe_query = query.replace("'", "''")
    query_pattern = f"%{safe_query}%"
    desc_results = await db.fetch(f"""
        SELECT id, properties::json->>'entity_id' as entity_id,
               properties::json->>'description' as description,
               properties::json->>'entity_type' as entity_type,
               properties::json->>'file_path' as file_path,
               properties::json->>'source_id' as source_id
        FROM chunk_entity_relation._ag_label_vertex 
        WHERE properties::json->>'description' ILIKE '{query_pattern}'
        LIMIT {match_count}
    """)
    
    # Search by entity_id  
    id_results = await db.fetch(f"""
        SELECT id, properties::json->>'entity_id' as entity_id,
               properties::json->>'description' as description,
               properties::json->>'entity_type' as entity_type,
               properties::json->>'file_path' as file_path,
               properties::json->>'source_id' as source_id
        FROM chunk_entity_relation._ag_label_vertex 
        WHERE properties::json->>'entity_id' ILIKE '{query_pattern}'
        LIMIT {match_count}
    """)
    
    print(f"[OK] Description search: {len(desc_results)} results")
    print(f"[OK] Entity ID search: {len(id_results)} results")
    
    # Combine and deduplicate results
    all_results = {}
    for row in desc_results + id_results:
        if row['id'] not in all_results:
            all_results[row['id']] = row
    
    results = list(all_results.values())[:match_count]
    
    # Filter by collection if specified
    if collection_name:
        results = [r for r in results if collection_name.lower() in (r['file_path'] or '').lower()]
    
    print(f"[OK] Combined results: {len(results)}")
    
    # Convert results to standard format
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
    
    print(f"[SUCCESS] Manual execution returned {len(documents)} documents!")
    for doc in documents:
        print(f"  - {doc['id']}: {doc['content'][:50]}...")
    
    # Now test the actual function
    print(f"\n[Testing] Actual function call...")
    from lightrag_integration import search_lightrag_documents
    actual_results = await search_lightrag_documents("fusion", 3)
    print(f"[RESULT] Function returned {len(actual_results)} results")
    
    await close_db_connection()

if __name__ == "__main__":
    asyncio.run(test_without_exception_handling())
