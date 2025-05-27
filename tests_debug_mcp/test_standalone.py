#!/usr/bin/env python3
"""
Standalone test with function code copied directly (no imports).
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import logging

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)
os.environ['POSTGRES_HOST'] = 'localhost'

# Set up logging
logger = logging.getLogger(__name__)

async def standalone_search_lightrag_documents(
    query: str,
    match_count: int = 10,
    collection_name = None
):
    """
    Standalone version of search_lightrag_documents with the exact same code.
    """
    from database import get_db_connection
    
    try:
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
        
        # Combine and deduplicate results
        all_results = {}
        for row in desc_results + id_results:
            if row['id'] not in all_results:
                all_results[row['id']] = row
        
        results = list(all_results.values())[:match_count]
        
        # Filter by collection if specified
        if collection_name:
            results = [r for r in results if collection_name.lower() in (r['file_path'] or '').lower()]
        
        # Convert results to standard format
        documents = []
        for row in results:
            try:
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
                
            except Exception as e:
                logger.warning(f"Failed to process row {row['id']}: {e}")
                continue
        
        # Sort by similarity score (highest first)
        documents.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.info(f"LightRAG search returned {len(documents)} results")
        return documents
        
    except Exception as e:
        logger.error(f"Error searching LightRAG knowledge graph: {e}")
        # Return empty list on error
        return []

async def test_standalone():
    """Test the standalone function."""
    print("=== Standalone Function Test ===\n")
    
    from database import initialize_db_connection, close_db_connection
    
    await initialize_db_connection()
    print("[OK] Database connection initialized")
    
    print(f"\n[Testing] Standalone function...")
    results = await standalone_search_lightrag_documents("fusion", 3)
    print(f"[RESULT] Standalone function returned {len(results)} results")
    
    if results:
        for result in results:
            print(f"  - {result['id']}: {result['content'][:50]}...")
    else:
        print("  No results returned")
    
    await close_db_connection()

if __name__ == "__main__":
    asyncio.run(test_standalone())
