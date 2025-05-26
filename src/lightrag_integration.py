"""
LightRAG schema integration for the Crawl4AI MCP server.

This module provides functions to query data from the lightrag schema
in addition to the crawl schema.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from src.database import get_db_connection
from src.utils import create_embedding

# Set up logging
logger = logging.getLogger(__name__)


async def search_lightrag_documents(
    query: str,
    match_count: int = 10,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents in the lightrag schema.
    
    Args:
        query: Query text
        match_count: Maximum number of results to return
        collection_name: Optional collection name to filter results
        
    Returns:
        List of matching documents from lightrag schema
    """
    # Get database connection
    db = await get_db_connection()
    
    # Create embedding for the query
    query_embedding = create_embedding(query)
    
    try:
        # Build the SQL query based on common LightRAG table structures
        # This assumes the lightrag schema has a documents table with embeddings
        if collection_name:
            results = await db.fetch(
                """
                SELECT 
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM lightrag.documents
                WHERE collection_name = $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                query_embedding,
                collection_name,
                match_count
            )
        else:
            results = await db.fetch(
                """
                SELECT 
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM lightrag.documents
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                query_embedding,
                match_count
            )
        
        # Convert results to list of dictionaries
        documents = []
        for row in results:
            doc = {
                'id': row['id'],
                'content': row['content'],
                'metadata': row.get('metadata', {}),
                'similarity': row['similarity']
            }
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"Error searching lightrag documents: {e}")
        # Try alternative table structure if the first one fails
        try:
            # Alternative query for different LightRAG schema structure
            results = await db.fetch(
                """
                SELECT 
                    id,
                    text as content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM lightrag.embeddings
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                query_embedding,
                match_count
            )
            
            documents = []
            for row in results:
                doc = {
                    'id': row['id'],
                    'content': row['content'],
                    'metadata': row.get('metadata', {}),
                    'similarity': row['similarity']
                }
                documents.append(doc)
            
            return documents
            
        except Exception as inner_e:
            logger.error(f"Error with alternative lightrag schema: {inner_e}")
            return []


async def get_lightrag_collections() -> List[str]:
    """
    Get all available collections from the lightrag schema.
    
    Returns:
        List of collection names
    """
    db = await get_db_connection()
    
    try:
        # Try to get collections from a collections table
        results = await db.fetch(
            """
            SELECT DISTINCT collection_name 
            FROM lightrag.documents
            WHERE collection_name IS NOT NULL
            ORDER BY collection_name
            """
        )
        return [row['collection_name'] for row in results]
        
    except Exception as e:
        logger.error(f"Error getting lightrag collections: {e}")
        # Try alternative approaches
        try:
            # Check if there's a separate collections table
            results = await db.fetch(
                """
                SELECT name 
                FROM lightrag.collections
                ORDER BY name
                """
            )
            return [row['name'] for row in results]
            
        except Exception as inner_e:
            logger.error(f"Error with alternative collections query: {inner_e}")
            return []


async def get_lightrag_schema_info() -> Dict[str, Any]:
    """
    Get information about the lightrag schema structure.
    
    Returns:
        Dictionary with schema information
    """
    db = await get_db_connection()
    
    try:
        # Get all tables in the lightrag schema
        tables = await db.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'lightrag'
            ORDER BY table_name
            """
        )
        
        schema_info = {
            "tables": [row['table_name'] for row in tables],
            "table_details": {}
        }
        
        # Get column information for each table
        for table in schema_info["tables"]:
            columns = await db.fetch(
                """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'lightrag' 
                AND table_name = $1
                ORDER BY ordinal_position
                """,
                table
            )
            
            schema_info["table_details"][table] = [
                {
                    "column": row['column_name'],
                    "type": row['data_type'],
                    "nullable": row['is_nullable'] == 'YES'
                }
                for row in columns
            ]
        
        return schema_info
        
    except Exception as e:
        logger.error(f"Error getting lightrag schema info: {e}")
        return {"error": str(e)}


async def search_multi_schema(
    query: str,
    schemas: List[str] = ["crawl", "lightrag"],
    match_count: int = 10,
    combine_results: bool = True
) -> Dict[str, Any]:
    """
    Search across multiple schemas and optionally combine results.
    
    Args:
        query: Query text
        schemas: List of schema names to search
        match_count: Maximum results per schema
        combine_results: Whether to combine and re-rank results
        
    Returns:
        Dictionary with search results from multiple schemas
    """
    db = await get_db_connection()
    query_embedding = create_embedding(query)
    
    results_by_schema = {}
    all_results = []
    
    for schema in schemas:
        try:
            if schema == "crawl":
                # Use the existing crawl schema function
                results = await db.fetch(
                    """
                    SELECT * FROM crawl.match_crawled_pages($1::vector, $2, '{}'::jsonb)
                    """,
                    query_embedding,
                    match_count
                )
                
                schema_results = []
                for row in results:
                    result = {
                        'schema': 'crawl',
                        'id': row['id'],
                        'url': row.get('url'),
                        'content': row['content'],
                        'metadata': row.get('metadata', {}),
                        'similarity': row['similarity']
                    }
                    schema_results.append(result)
                    all_results.append(result)
                
                results_by_schema[schema] = schema_results
                
            elif schema == "lightrag":
                # Search lightrag schema
                lightrag_results = await search_lightrag_documents(query, match_count)
                for result in lightrag_results:
                    result['schema'] = 'lightrag'
                    all_results.append(result)
                results_by_schema[schema] = lightrag_results
                
        except Exception as e:
            logger.error(f"Error searching {schema} schema: {e}")
            results_by_schema[schema] = []
    
    if combine_results:
        # Sort all results by similarity score
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        # Take top match_count results
        combined_results = all_results[:match_count]
        
        return {
            "combined": combined_results,
            "by_schema": results_by_schema
        }
    else:
        return {
            "by_schema": results_by_schema
        }
