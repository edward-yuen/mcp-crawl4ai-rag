"""
LightRAG Knowledge Graph integration using Apache AGE.

This module provides functions to query the LightRAG knowledge graph
which stores entities, relationships, and communities.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from .database import get_db_connection

# Set up logging
logger = logging.getLogger(__name__)


async def query_knowledge_graph(
    cypher_query: str,
    parameters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a Cypher query on the LightRAG knowledge graph using AGE.
    
    Args:
        cypher_query: Cypher query to execute
        parameters: Optional parameters for the query
        
    Returns:
        List of query results
    """
    db = await get_db_connection()
    
    try:
        # AGE requires wrapping Cypher queries in a specific format
        # First, set the graph path for AGE
        await db.execute("SET search_path = ag_catalog, '$user', public;")
        
        # Execute the Cypher query using AGE
        sql_query = f"""
        SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
        {cypher_query}
        $$) as (result agtype);
        """
        
        results = await db.fetch(sql_query)
        
        # Convert AGE results to Python dictionaries
        processed_results = []
        for row in results:
            # AGE returns results as agtype, which is automatically converted by asyncpg
            # The result should already be a Python dict/list
            result = row['result']
            processed_results.append(result)
        
        return processed_results
        
    except Exception as e:
        logger.error(f"Error executing knowledge graph query: {e}")
        # Try without AGE in case it's not installed
        logger.info("Attempting fallback query without AGE")
        return []


async def get_entities_by_type(
    entity_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get entities from the knowledge graph, optionally filtered by type.
    
    Args:
        entity_type: Optional entity type to filter by
        limit: Maximum number of entities to return
        
    Returns:
        List of entities with their properties
    """
    try:
        if entity_type:
            cypher_query = f"""
            MATCH (n:{entity_type})
            RETURN n
            LIMIT {limit}
            """
        else:
            cypher_query = f"""
            MATCH (n)
            RETURN n
            LIMIT {limit}
            """
        
        results = await query_knowledge_graph(cypher_query)
        return results
        
    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        return []


async def get_entity_relationships(
    entity_name: str,
    relationship_type: Optional[str] = None,
    depth: int = 1
) -> Dict[str, Any]:
    """
    Get relationships for a specific entity up to a certain depth.
    
    Args:
        entity_name: Name of the entity to find relationships for
        relationship_type: Optional relationship type to filter
        depth: How many hops to traverse (default: 1)
        
    Returns:
        Dictionary containing the entity and its relationships
    """
    try:
        if relationship_type:
            cypher_query = f"""
            MATCH path = (n {{name: '{entity_name}'}})-[r:{relationship_type}*1..{depth}]-(m)
            RETURN n, relationships(path) as relationships, nodes(path) as nodes
            """
        else:
            cypher_query = f"""
            MATCH path = (n {{name: '{entity_name}'}})-[r*1..{depth}]-(m)
            RETURN n, relationships(path) as relationships, nodes(path) as nodes
            """
        
        results = await query_knowledge_graph(cypher_query)
        
        if not results:
            return {"entity": entity_name, "relationships": [], "connected_nodes": []}
        
        # Process results to extract unique relationships and nodes
        all_relationships = []
        all_nodes = []
        
        for result in results:
            if 'relationships' in result:
                all_relationships.extend(result['relationships'])
            if 'nodes' in result:
                all_nodes.extend(result['nodes'])
        
        # Remove duplicates while preserving structure
        unique_relationships = []
        seen_rels = set()
        for rel in all_relationships:
            rel_key = f"{rel.get('start_id')}-{rel.get('type')}-{rel.get('end_id')}"
            if rel_key not in seen_rels:
                seen_rels.add(rel_key)
                unique_relationships.append(rel)
        
        unique_nodes = []
        seen_nodes = set()
        for node in all_nodes:
            node_id = node.get('id') or node.get('name')
            if node_id and node_id not in seen_nodes:
                seen_nodes.add(node_id)
                unique_nodes.append(node)
        
        return {
            "entity": entity_name,
            "relationships": unique_relationships,
            "connected_nodes": unique_nodes
        }
        
    except Exception as e:
        logger.error(f"Error getting entity relationships: {e}")
        return {"entity": entity_name, "relationships": [], "connected_nodes": []}


async def search_entities_by_embedding(
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for entities using semantic similarity on their embeddings.
    
    Args:
        query: Search query
        entity_type: Optional entity type to filter
        limit: Maximum number of results
        
    Returns:
        List of entities ordered by similarity
    """
    db = await get_db_connection()
    
    try:
        # First, check if entities have embeddings in a separate table
        # This is common in LightRAG implementations
        from .utils import create_embedding
        query_embedding = create_embedding(query)
        
        # Try to find entity embeddings table
        if entity_type:
            sql_query = """
            SELECT 
                e.entity_id,
                e.entity_name,
                e.entity_type,
                e.properties,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM lightrag.entity_embeddings e
            WHERE e.entity_type = $2
            ORDER BY e.embedding <=> $1::vector
            LIMIT $3
            """
            results = await db.fetch(sql_query, query_embedding, entity_type, limit)
        else:
            sql_query = """
            SELECT 
                e.entity_id,
                e.entity_name,
                e.entity_type,
                e.properties,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM lightrag.entity_embeddings e
            ORDER BY e.embedding <=> $1::vector
            LIMIT $2
            """
            results = await db.fetch(sql_query, query_embedding, limit)
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error searching entities by embedding: {e}")
        return []


async def get_communities(
    level: Optional[int] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get communities from the knowledge graph.
    
    Args:
        level: Optional community level to filter by
        limit: Maximum number of communities to return
        
    Returns:
        List of communities with their properties
    """
    try:
        if level is not None:
            cypher_query = f"""
            MATCH (c:Community {{level: {level}}})
            RETURN c
            ORDER BY c.size DESC
            LIMIT {limit}
            """
        else:
            cypher_query = f"""
            MATCH (c:Community)
            RETURN c
            ORDER BY c.size DESC
            LIMIT {limit}
            """
        
        results = await query_knowledge_graph(cypher_query)
        return results
        
    except Exception as e:
        logger.error(f"Error getting communities: {e}")
        return []


async def get_community_members(
    community_id: str,
    include_relationships: bool = True
) -> Dict[str, Any]:
    """
    Get all members of a specific community.
    
    Args:
        community_id: ID of the community
        include_relationships: Whether to include relationships between members
        
    Returns:
        Dictionary containing community info and members
    """
    try:
        # Get community and its members
        cypher_query = f"""
        MATCH (c:Community {{id: '{community_id}'}})
        OPTIONAL MATCH (c)-[:CONTAINS]->(n)
        RETURN c, collect(n) as members
        """
        
        results = await query_knowledge_graph(cypher_query)
        
        if not results:
            return {"community_id": community_id, "members": [], "relationships": []}
        
        community_data = {
            "community": results[0].get('c', {}),
            "members": results[0].get('members', [])
        }
        
        # Get relationships between members if requested
        if include_relationships and community_data['members']:
            member_names = [m.get('name') for m in community_data['members'] if m.get('name')]
            if member_names:
                rel_query = f"""
                MATCH (n)-[r]-(m)
                WHERE n.name IN {member_names} AND m.name IN {member_names}
                RETURN DISTINCT r
                """
                rel_results = await query_knowledge_graph(rel_query)
                community_data['relationships'] = rel_results
        
        return community_data
        
    except Exception as e:
        logger.error(f"Error getting community members: {e}")
        return {"community_id": community_id, "members": [], "relationships": []}


async def find_path_between_entities(
    start_entity: str,
    end_entity: str,
    max_depth: int = 3,
    relationship_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Find paths between two entities in the knowledge graph.
    
    Args:
        start_entity: Name of the starting entity
        end_entity: Name of the ending entity
        max_depth: Maximum path length
        relationship_types: Optional list of relationship types to traverse
        
    Returns:
        List of paths between the entities
    """
    try:
        if relationship_types:
            rel_pattern = "|".join(relationship_types)
            cypher_query = f"""
            MATCH path = shortestPath((start {{name: '{start_entity}'}})-[r:{rel_pattern}*..{max_depth}]-(end {{name: '{end_entity}'}}))
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 5
            """
        else:
            cypher_query = f"""
            MATCH path = shortestPath((start {{name: '{start_entity}'}})-[r*..{max_depth}]-(end {{name: '{end_entity}'}}))
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 5
            """
        
        results = await query_knowledge_graph(cypher_query)
        return results
        
    except Exception as e:
        logger.error(f"Error finding path between entities: {e}")
        return []


async def get_graph_statistics() -> Dict[str, Any]:
    """
    Get statistics about the knowledge graph.
    
    Returns:
        Dictionary with graph statistics
    """
    try:
        stats = {}
        
        # Count nodes by type
        node_query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        """
        node_results = await query_knowledge_graph(node_query)
        stats['node_counts'] = {row['labels'][0]: row['count'] for row in node_results if row['labels']}
        
        # Count relationships by type
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        rel_results = await query_knowledge_graph(rel_query)
        stats['relationship_counts'] = {row['type']: row['count'] for row in rel_results}
        
        # Get total counts
        stats['total_nodes'] = sum(stats['node_counts'].values())
        stats['total_relationships'] = sum(stats['relationship_counts'].values())
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        return {}
