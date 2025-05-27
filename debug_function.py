#!/usr/bin/env python3
"""
Debug what happens inside the search_lightrag_documents function.
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

async def debug_function():
    """Debug the search_lightrag_documents function step by step."""
    print("=== Function Debug ===\n")
    
    from src.database import initialize_db_connection, get_db_connection, close_db_connection
    
    await initialize_db_connection()
    
    try:
        # Manually execute the function logic step by step
        query = "fusion"
        match_count = 3
        collection_name = None
        
        print(f"[Step 1] Getting database connection...")
        db = await get_db_connection()
        print(f"   Database connection: {type(db)}")
        
        print(f"[Step 2] Loading AGE extension...")
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        print("   AGE extension loaded")
        
        print(f"[Step 3] Running description search...")
        safe_query = query.replace("'", "''")
        query_pattern = f"%{safe_query}%"
        
        desc_query = f"""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path,
                   properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'description' ILIKE '{query_pattern}'
            LIMIT {match_count}
        """
        print(f"   Query: {desc_query[:100]}...")
        
        desc_results = await db.fetch(desc_query)
        print(f"   Description search found {len(desc_results)} results")
        
        print(f"[Step 4] Running entity_id search...")
        id_query = f"""
            SELECT id, properties::json->>'entity_id' as entity_id,
                   properties::json->>'description' as description,
                   properties::json->>'entity_type' as entity_type,
                   properties::json->>'file_path' as file_path,
                   properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'entity_id' ILIKE '{query_pattern}'
            LIMIT {match_count}
        """
        
        id_results = await db.fetch(id_query)
        print(f"   Entity ID search found {len(id_results)} results")
        
        print(f"[Step 5] Combining and deduplicating results...")
        all_results = {}
        for row in desc_results + id_results:
            if row['id'] not in all_results:
                all_results[row['id']] = row
        
        results = list(all_results.values())[:match_count]
        print(f"   Combined results: {len(results)}")
        
        print(f"[Step 6] Processing results into documents...")
        documents = []
        for i, row in enumerate(results):
            try:
                print(f"   Processing row {i+1}: {row['entity_id']}")
                
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
                print(f"   Created document: {entity_id} (similarity: {similarity})")
                
            except Exception as e:
                print(f"   [ERROR] Processing row {i+1} failed: {e}")
                continue
        
        print(f"[Step 7] Final results: {len(documents)} documents")
        for doc in documents:
            print(f"   - {doc['id']}: {doc['content'][:50]}... (score: {doc['similarity']})")
        
        # Now test the actual function
        print(f"\n[Step 8] Testing actual function...")
        from src.lightrag_integration import search_lightrag_documents
        
        function_results = await search_lightrag_documents("fusion", 3)
        print(f"   Function returned {len(function_results)} results")
        
    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    await close_db_connection()
    print("\n[OK] Debug completed")

if __name__ == "__main__":
    asyncio.run(debug_function())
