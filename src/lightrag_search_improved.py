"""
Improved LightRAG search function that works with PostgreSQL JSON queries.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from src.database import get_db_connection

logger = logging.getLogger(__name__)


async def search_lightrag_documents_improved(
    query: str,
    match_count: int = 10,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Improved search for entities in the LightRAG knowledge graph.
    Uses PostgreSQL JSON operators instead of AGE-specific functions.
    """
    try:
        db = await get_db_connection()
        
        # Prepare search pattern
        safe_query = query.replace("'", "''")
        
        # Split query into words for better matching
        query_words = query.lower().split()
        
        # Build search conditions for each word
        search_conditions = []
        for word in query_words:
            word_pattern = f"%{word}%"
            search_conditions.append(f"""
                (properties::json->>'entity_id' ILIKE '{word_pattern}' OR 
                 properties::json->>'description' ILIKE '{word_pattern}')
            """)
        
        # Combine conditions with OR for broader search
        where_clause = " OR ".join(search_conditions)
        
        # Add collection filter if specified
        if collection_name:
            safe_collection = collection_name.replace("'", "''")
            where_clause = f"({where_clause}) AND properties::json->>'file_path' ILIKE '%{safe_collection}%'"
        
        # Execute search query
        query_sql = f"""
            SELECT 
                id::text as internal_id,
                properties::json->>'entity_id' as entity_id,
                properties::json->>'description' as description,
                properties::json->>'entity_type' as entity_type,
                properties::json->>'file_path' as file_path,
                properties::json->>'source_id' as source_id
            FROM chunk_entity_relation._ag_label_vertex
            WHERE {where_clause}
            LIMIT {match_count * 2}
        """
        
        results = await db.fetch(query_sql)
        
        # Score and rank results
        documents = []
        for row in results:
            entity_id = row['entity_id'] or ''
            description = row['description'] or ''
            entity_type = row['entity_type'] or 'unknown'
            
            # Calculate relevance score
            score = 0.5  # Base score
            
            # Exact matches get highest score
            if query.lower() == entity_id.lower():
                score = 1.0
            elif query.lower() in entity_id.lower():
                score = 0.9
            elif query.lower() in description.lower():
                score = 0.8
            else:
                # Count matching words
                matches = sum(1 for word in query_words if word in entity_id.lower() or word in description.lower())
                score = 0.5 + (0.4 * matches / len(query_words))
            
            # Boost score for certain entity types
            if entity_type.lower() in ['strategy', 'technique', 'method']:
                score *= 1.1
            
            doc = {
                'id': entity_id,
                'content': description,
                'metadata': {
                    'entity_type': entity_type,
                    'file_path': row['file_path'] or '',
                    'source_id': row['source_id'] or '',
                    'entity_id': entity_id
                },
                'similarity': min(score, 1.0)  # Cap at 1.0
            }
            documents.append(doc)
        
        # Sort by similarity and limit
        documents.sort(key=lambda x: x['similarity'], reverse=True)
        documents = documents[:match_count]
        
        logger.info(f"Improved search returned {len(documents)} results for query: {query}")
        return documents
        
    except Exception as e:
        logger.error(f"Error in improved LightRAG search: {e}")
        return []


async def get_related_entities(
    entity_id: str,
    relationship_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get entities related to a specific entity.
    """
    try:
        db = await get_db_connection()
        
        safe_entity_id = entity_id.replace("'", "''")
        
        # Query for edges where this entity is the source
        edge_query = f"""
            SELECT 
                properties::json->>'target' as target_id,
                properties::json->>'relationship' as relationship_type,
                properties::json->>'description' as edge_description
            FROM chunk_entity_relation._ag_label_edge
            WHERE properties::json->>'source' = '{safe_entity_id}'
        """
        
        if relationship_types:
            rel_conditions = " OR ".join([f"properties::json->>'relationship' = '{rel}'" for rel in relationship_types])
            edge_query += f" AND ({rel_conditions})"
        
        edge_query += f" LIMIT {limit}"
        
        edges = await db.fetch(edge_query)
        
        # Get target entity details
        related = []
        for edge in edges:
            target_id = edge['target_id']
            if target_id:
                # Get target entity info
                target_query = f"""
                    SELECT 
                        properties::json->>'entity_id' as entity_id,
                        properties::json->>'description' as description,
                        properties::json->>'entity_type' as entity_type
                    FROM chunk_entity_relation._ag_label_vertex
                    WHERE properties::json->>'entity_id' = '{target_id}'
                    LIMIT 1
                """
                
                target_result = await db.fetch(target_query)
                if target_result:
                    target = target_result[0]
                    related.append({
                        'entity_id': target['entity_id'],
                        'description': target['description'],
                        'entity_type': target['entity_type'],
                        'relationship': edge['relationship_type'],
                        'relationship_description': edge['edge_description']
                    })
        
        return related
        
    except Exception as e:
        logger.error(f"Error getting related entities: {e}")
        return []
