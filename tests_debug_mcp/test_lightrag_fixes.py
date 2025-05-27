#!/usr/bin/env python3
"""
Test script to verify LightRAG integration fixes.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Override host for local testing (outside Docker)
os.environ['POSTGRES_HOST'] = 'localhost'

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import initialize_db_connection, close_db_connection
from lightrag_integration import search_lightrag_documents, get_lightrag_schema_info, get_lightrag_collections
from lightrag_knowledge_graph import get_entities_by_type, get_entity_relationships, get_graph_statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lightrag_fixes():
    """Test the LightRAG integration fixes."""
    try:
        logger.info("Initializing database connection...")
        db = await initialize_db_connection()
        
        # Test a direct database query first
        logger.info("Testing direct database query...")
        node_count = await db.fetchval("SELECT count(*) FROM chunk_entity_relation._ag_label_vertex")
        print(f"Total nodes in graph: {node_count}")
        
        logger.info("Testing LightRAG schema info...")
        schema_info = await get_lightrag_schema_info()
        print(f"Schema Info: {schema_info}")
        
        logger.info("Testing graph statistics...")
        stats = await get_graph_statistics()
        print(f"Graph Statistics: {stats}")
        
        logger.info("Testing collection retrieval...")
        collections = await get_lightrag_collections()
        print(f"Collections ({len(collections)}): {collections[:3]}...")  # Show first 3
        
        logger.info("Testing entity search for 'Fusion Analysis'...")
        fusion_entities = await search_lightrag_documents("Fusion Analysis", match_count=5)
        print(f"Fusion Analysis entities ({len(fusion_entities)}):")
        for entity in fusion_entities:
            print(f"  - {entity['id']}: {entity['content'][:100]}...")
        
        logger.info("Testing entities by type...")
        category_entities = await get_entities_by_type("category", limit=5)
        print(f"Category entities ({len(category_entities)}):")
        for entity in category_entities:
            print(f"  - {entity['entity_id']}: {entity['description'][:50]}...")
        
        if fusion_entities:
            logger.info("Testing entity relationships...")
            first_entity = fusion_entities[0]['id']
            relationships = await get_entity_relationships(first_entity)
            print(f"Relationships for '{first_entity}' ({relationships['total_connections']}):")
            for rel in relationships['relationships'][:3]:  # Show first 3
                print(f"  - {rel['connected_entity']}: {rel['description'][:50]}...")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db_connection()

if __name__ == "__main__":
    asyncio.run(test_lightrag_fixes())
