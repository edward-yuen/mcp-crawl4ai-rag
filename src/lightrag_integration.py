"""
LightRAG integration module for the Crawl4AI MCP server.

This module provides functions to query data from the LightRAG knowledge graph
stored in Apache AGE format in the chunk_entity_relation schema.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from src.database import get_db_connection

# Set up logging
logger = logging.getLogger(__name__)


async def search_lightrag_documents(
    query: str,
    match_count: int = 10,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for entities and content in the LightRAG knowledge graph.
    
    Args:
        query: Query text  
        match_count: Maximum number of results to return
        collection_name: Optional collection name to filter results (file_path filtering)
        
    Returns:
        List of matching entities/documents from LightRAG knowledge graph
    """
    try:
        db = await get_db_connection()
        
        # Try improved search method first
        from src.lightrag_search_improved import search_lightrag_documents_improved
        results = await search_lightrag_documents_improved(query, match_count, collection_name)
        
        if results:
            logger.info(f"LightRAG improved search returned {len(results)} results")
            return results
        
        # Fallback to original AGE-based search if improved search returns no results
        logger.info("Trying AGE-based search as fallback...")
        
        # Load AGE extension and set search path
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        # Escape single quotes to prevent SQL injection
        safe_query = query.replace("'", "''")
        query_pattern = f"%{safe_query}%"
        
        # Search by description
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
        return []


async def get_lightrag_collections() -> List[str]:
    """
    Get all available collections (file paths) from the LightRAG knowledge graph.
    
    Returns:
        List of unique file paths/collections
    """
    try:
        db = await get_db_connection()
        
        # Use direct JSON query to get distinct file paths
        results = await db.fetch("""
            SELECT DISTINCT properties::json->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex 
            WHERE properties::json->>'file_path' IS NOT NULL
                AND properties::json->>'file_path' != ''
            ORDER BY properties::json->>'file_path'
        """)
        
        # Extract file paths
        collections = [row['file_path'] for row in results if row['file_path']]
        
        logger.info(f"Found {len(collections)} collections in LightRAG")
        return collections
        
    except Exception as e:
        logger.error(f"Error getting LightRAG collections: {e}")
        return []


async def get_lightrag_schema_info() -> Dict[str, Any]:
    """
    Get information about the LightRAG knowledge graph schema structure.
    
    Returns:
        Dictionary with schema information
    """
    try:
        db = await get_db_connection()
        
        # Load AGE extension for Cypher queries
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        # Get AGE graph information
        graph_info = await db.fetch(
            """
            SELECT name, namespace 
            FROM ag_catalog.ag_graph 
            WHERE name = 'chunk_entity_relation'
            """
        )
        
        # Get tables in the chunk_entity_relation schema
        tables = await db.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'chunk_entity_relation'
            ORDER BY table_name
            """
        )
        
        # Get node and edge counts
        node_count = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_vertex"
        )
        
        edge_count = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_edge"
        )
        
        # Get entity types distribution using JSON queries
        entity_types_results = await db.fetch("""
            SELECT properties::json->>'entity_type' as entity_type, 
                   count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties::json->>'entity_type' IS NOT NULL
            GROUP BY properties::json->>'entity_type'
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Get sample file paths using JSON queries
        file_paths_results = await db.fetch("""
            SELECT properties::json->>'file_path' as file_path,
                   count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties::json->>'file_path' IS NOT NULL
            GROUP BY properties::json->>'file_path'
            ORDER BY count DESC
            LIMIT 5
        """)
        
        # Parse entity types results
        entity_types = []
        for row in entity_types_results:
            if row['entity_type']:
                entity_types.append({
                    "type": row['entity_type'],
                    "count": row['count']
                })
        
        # Parse file paths results
        sample_collections = []
        for row in file_paths_results:
            if row['file_path']:
                sample_collections.append({
                    "file_path": row['file_path'],
                    "count": row['count']
                })
        
        schema_info = {
            "graphs": [dict(row) for row in graph_info],
            "tables": [row['table_name'] for row in tables],
            "statistics": {
                "total_nodes": node_count,
                "total_edges": edge_count
            },
            "entity_types": entity_types,
            "sample_collections": sample_collections
        }
        
        logger.info(f"LightRAG schema info: {node_count} nodes, {edge_count} edges")
        return schema_info
        
    except Exception as e:
        logger.error(f"Error getting LightRAG schema info: {e}")
        return {
            "error": str(e),
            "graphs": [],
            "tables": [],
            "statistics": {"total_nodes": 0, "total_edges": 0},
            "entity_types": [],
            "sample_collections": []
        }


async def search_multi_schema(
    query: str,
    schemas: List[str] = ["crawl", "lightrag"],
    match_count: int = 10,
    combine_results: bool = True
) -> Dict[str, Any]:
    """
    Search across multiple schemas (crawl and lightrag) simultaneously.
    
    Args:
        query: The search query
        schemas: List of schemas to search (default: ["crawl", "lightrag"])
        match_count: Maximum number of results per schema (default: 10)
        combine_results: Whether to combine and re-rank results by similarity (default: True)
    
    Returns:
        Dictionary with search results from multiple schemas
    """
    results = {
        "query": query,
        "schemas_searched": schemas,
        "results_per_schema": {},
        "combined_results": []
    }
    
    all_results = []
    
    try:
        # Search crawl schema if requested
        if "crawl" in schemas:
            try:
                from src.utils import search_documents
                crawl_results = await search_documents(
                    query=query,
                    match_count=match_count
                )
                results["results_per_schema"]["crawl"] = crawl_results
                
                # Add source info to each result
                for result in crawl_results:
                    result["source_schema"] = "crawl"
                    all_results.append(result)
                    
            except Exception as e:
                logger.error(f"Error searching crawl schema: {e}")
                results["results_per_schema"]["crawl"] = []
        
        # Search lightrag schema if requested
        if "lightrag" in schemas:
            try:
                lightrag_results = await search_lightrag_documents(
                    query=query,
                    match_count=match_count
                )
                results["results_per_schema"]["lightrag"] = lightrag_results
                
                # Add source info to each result
                for result in lightrag_results:
                    result["source_schema"] = "lightrag"
                    all_results.append(result)
                    
            except Exception as e:
                logger.error(f"Error searching lightrag schema: {e}")
                results["results_per_schema"]["lightrag"] = []
        
        # Combine and re-rank results if requested
        if combine_results and all_results:
            # Sort by similarity score (highest first)
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            results["combined_results"] = all_results[:match_count * 2]  # Return more combined results
        else:
            results["combined_results"] = all_results
        
        return results
        
    except Exception as e:
        logger.error(f"Error in multi-schema search: {e}")
        return {
            "query": query,
            "schemas_searched": schemas,
            "error": str(e),
            "results_per_schema": {},
            "combined_results": []
        }
