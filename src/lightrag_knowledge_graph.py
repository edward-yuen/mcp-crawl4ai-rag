"""
LightRAG Knowledge Graph integration using Apache AGE.

This module provides functions to query the LightRAG knowledge graph
which stores entities, relationships, and communities.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from src.database import get_db_connection

# Set up logging
logger = logging.getLogger(__name__)


def _clean_agtype_string(value: Any) -> str:
    """
    Clean an AGE agtype value to extract the string content.
    
    Args:
        value: AGE agtype value
        
    Returns:
        str: Cleaned string value
    """
    if value is None:
        return ""
    
    # Convert to string and remove AGE quotes and escaping
    str_value = str(value)
    
    # Remove outer quotes if present
    if str_value.startswith('"') and str_value.endswith('"'):
        str_value = str_value[1:-1]
    
    # Handle escaped quotes and other escape sequences
    str_value = str_value.replace('\\"', '"')
    str_value = str_value.replace('\\\\', '\\')
    
    return str_value


async def query_knowledge_graph(
    cypher_query: str,
    parameters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a Cypher query on the LightRAG knowledge graph using AGE.
    
    Args:
        cypher_query: Cypher query to execute
        parameters: Optional parameters for the query (not used with AGE)
        
    Returns:
        List of query results
    """
    db = await get_db_connection()
    
    try:
        # Load AGE extension and set search path
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        # Escape single quotes in the cypher query for safety
        safe_cypher_query = cypher_query.replace("'", "\\'")
        
        # Execute the Cypher query using AGE with the correct graph name
        sql_query = f"""
        SELECT * FROM ag_catalog.cypher('chunk_entity_relation', $$
        {safe_cypher_query}
        $$) as (result agtype);
        """
        
        results = await db.fetch(sql_query)
        
        # Convert AGE results to Python dictionaries
        processed_results = []
        for row in results:
            # AGE returns results as agtype, convert to Python objects
            result = row['result']
            if result is not None:
                try:
                    # Handle different types of AGE results
                    if hasattr(result, 'items'):
                        # It's already a dict-like object
                        processed_results.append(dict(result))
                    else:
                        # Convert to dict if possible
                        result_dict = {}
                        result_str = str(result)
                        if result_str and result_str != 'null':
                            result_dict = {'value': _clean_agtype_string(result)}
                        processed_results.append(result_dict)
                except Exception as convert_e:
                    logger.warning(f"Could not convert AGE result: {convert_e}")
                    # Fallback: try to extract as string
                    processed_results.append({'value': _clean_agtype_string(result)})
        
        return processed_results
        
    except Exception as e:
        logger.error(f"Error executing knowledge graph query: {e}")
        logger.error(f"Query was: {cypher_query}")
        return []


async def get_entities_by_type(
    entity_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get entities from the knowledge graph, optionally filtered by type.
    
    Args:
        entity_type: Optional entity type to filter by (e.g., "person", "organization", "category")
        limit: Maximum number of entities to return
        
    Returns:
        List of entities with their properties
    """
    try:
        db = await get_db_connection()
        
        # Load AGE extension and set search path  
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        if entity_type:
            # Escape single quotes for safety
            safe_entity_type = entity_type.replace("'", "\\'")
            cypher_query = f"""
            MATCH (n)
            WHERE n.entity_type = '{safe_entity_type}'
            RETURN n.entity_id, n.description, n.entity_type, n.file_path, n.source_id
            LIMIT {limit}
            """
        else:
            cypher_query = f"""
            MATCH (n)
            RETURN n.entity_id, n.description, n.entity_type, n.file_path, n.source_id
            LIMIT {limit}
            """
        
        # Execute cypher query with proper return type mapping
        results = await db.fetch(
            f"""
            SELECT * FROM cypher('chunk_entity_relation', $$
            {cypher_query}
            $$) as (entity_id agtype, description agtype, entity_type agtype, file_path agtype, source_id agtype)
            """
        )
        
        # Convert results to proper format
        entities = []
        for row in results:
            entity = {
                'entity_id': _clean_agtype_string(row['entity_id']),
                'description': _clean_agtype_string(row['description']),
                'entity_type': _clean_agtype_string(row['entity_type']),
                'file_path': _clean_agtype_string(row['file_path']),
                'source_id': _clean_agtype_string(row['source_id'])
            }
            entities.append(entity)
        
        return entities
        
    except Exception as e:
        logger.error(f"Error getting entities by type: {e}")
        
        # Fallback: use direct SQL query on vertex table
        try:
            logger.info("Attempting fallback entity query using direct SQL...")
            
            db = await get_db_connection()
            
            if entity_type:
                results = await db.fetch(
                    """
                    SELECT properties->>'entity_id' as entity_id,
                           properties->>'description' as description,
                           properties->>'entity_type' as entity_type,
                           properties->>'file_path' as file_path,
                           properties->>'source_id' as source_id
                    FROM chunk_entity_relation._ag_label_vertex
                    WHERE properties->>'entity_type' = $1
                    LIMIT $2
                    """,
                    entity_type,
                    limit
                )
            else:
                results = await db.fetch(
                    """
                    SELECT properties->>'entity_id' as entity_id,
                           properties->>'description' as description,
                           properties->>'entity_type' as entity_type,
                           properties->>'file_path' as file_path,
                           properties->>'source_id' as source_id
                    FROM chunk_entity_relation._ag_label_vertex
                    LIMIT $1
                    """,
                    limit
                )
            
            entities = []
            for row in results:
                entity = {
                    'entity_id': row['entity_id'] or '',
                    'description': row['description'] or '',
                    'entity_type': row['entity_type'] or '',
                    'file_path': row['file_path'] or '',
                    'source_id': row['source_id'] or ''
                }
                entities.append(entity)
            
            logger.info(f"Fallback entity query returned {len(entities)} results")
            return entities
            
        except Exception as fallback_e:
            logger.error(f"Fallback entity query also failed: {fallback_e}")
            return []


async def get_entity_relationships(
    entity_name: str,
    relationship_type: Optional[str] = None,
    depth: int = 1
) -> Dict[str, Any]:
    """
    Get relationships for a specific entity up to a certain depth.
    
    Args:
        entity_name: Name of the entity to find relationships for (entity_id)
        relationship_type: Optional relationship type to filter (not used in current AGE setup)
        depth: How many hops to traverse (default: 1)
        
    Returns:
        Dictionary containing the entity and its relationships
    """
    try:
        # Escape single quotes for safety
        safe_entity_name = entity_name.replace("'", "\\'")
        
        # Use entity_id property instead of name since that's what we have
        cypher_query = f"""
        MATCH (n)-[r]-(m)
        WHERE n.entity_id = '{safe_entity_name}'
        RETURN n.entity_id, r.description, m.entity_id, m.description, m.entity_type
        LIMIT 20
        """
        
        # Use direct database access for AGE  
        db = await get_db_connection()
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        results = await db.fetch(
            f"""
            SELECT * FROM cypher('chunk_entity_relation', $$
            {cypher_query}
            $$) as (entity_id agtype, rel_description agtype, connected_entity agtype, connected_description agtype, connected_type agtype)
            """
        )
        
        relationships = []
        connected_nodes = []
        
        for row in results:
            # Extract relationship information using the helper function
            rel_info = {
                'description': _clean_agtype_string(row['rel_description']),
                'connected_entity': _clean_agtype_string(row['connected_entity']),
                'connected_description': _clean_agtype_string(row['connected_description']),
                'connected_type': _clean_agtype_string(row['connected_type'])
            }
            relationships.append(rel_info)
            
            # Add connected node info
            node_info = {
                'entity_id': rel_info['connected_entity'],
                'description': rel_info['connected_description'], 
                'entity_type': rel_info['connected_type']
            }
            connected_nodes.append(node_info)
        
        return {
            "entity": entity_name,
            "relationships": relationships,
            "connected_nodes": connected_nodes,
            "total_connections": len(relationships)
        }
        
    except Exception as e:
        logger.error(f"Error getting entity relationships for '{entity_name}': {e}")
        
        # Fallback: query edges directly using SQL
        try:
            logger.info("Attempting fallback relationship query using direct SQL...")
            
            db = await get_db_connection()
            
            # Query relationships from edge table
            results = await db.fetch(
                """
                SELECT e.properties as edge_props,
                       v1.properties as start_props,
                       v2.properties as end_props
                FROM chunk_entity_relation._ag_label_edge e
                JOIN chunk_entity_relation._ag_label_vertex v1 ON e.start_id = v1.id
                JOIN chunk_entity_relation._ag_label_vertex v2 ON e.end_id = v2.id
                WHERE v1.properties->>'entity_id' = $1
                   OR v2.properties->>'entity_id' = $1
                LIMIT 20
                """,
                entity_name
            )
            
            relationships = []
            connected_nodes = []
            
            for row in results:
                try:
                    edge_props = dict(row['edge_props'])
                    start_props = dict(row['start_props'])
                    end_props = dict(row['end_props'])
                    
                    # Determine which is the connected entity
                    if start_props.get('entity_id') == entity_name:
                        connected_props = end_props
                    else:
                        connected_props = start_props
                    
                    rel_info = {
                        'description': edge_props.get('description', ''),
                        'connected_entity': connected_props.get('entity_id', ''),
                        'connected_description': connected_props.get('description', ''),
                        'connected_type': connected_props.get('entity_type', '')
                    }
                    relationships.append(rel_info)
                    
                    node_info = {
                        'entity_id': rel_info['connected_entity'],
                        'description': rel_info['connected_description'],
                        'entity_type': rel_info['connected_type']
                    }
                    connected_nodes.append(node_info)
                    
                except Exception as parse_e:
                    logger.warning(f"Could not parse relationship properties: {parse_e}")
                    continue
            
            logger.info(f"Fallback relationship query returned {len(relationships)} results")
            
            return {
                "entity": entity_name,
                "relationships": relationships,
                "connected_nodes": connected_nodes,
                "total_connections": len(relationships)
            }
            
        except Exception as fallback_e:
            logger.error(f"Fallback relationship query also failed: {fallback_e}")
            return {"entity": entity_name, "relationships": [], "connected_nodes": [], "total_connections": 0}


async def search_entities_by_embedding(
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for entities using text similarity (fallback from embedding search).
    
    Args:
        query: Search query
        entity_type: Optional entity type to filter
        limit: Maximum number of results
        
    Returns:
        List of entities ordered by text similarity
    """
    try:
        # Since we don't have embeddings in the current AGE setup,
        # we'll use text-based search as a fallback
        safe_query = query.replace("'", "\\'")
        
        if entity_type:
            safe_entity_type = entity_type.replace("'", "\\'")
            cypher_query = f"""
            MATCH (n)
            WHERE n.entity_type = '{safe_entity_type}'
            AND (n.description CONTAINS '{safe_query}' OR n.entity_id CONTAINS '{safe_query}')
            RETURN n.entity_id, n.description, n.entity_type, n.file_path, n.source_id
            LIMIT {limit}
            """
        else:
            cypher_query = f"""
            MATCH (n)
            WHERE n.description CONTAINS '{safe_query}' OR n.entity_id CONTAINS '{safe_query}'
            RETURN n.entity_id, n.description, n.entity_type, n.file_path, n.source_id
            LIMIT {limit}
            """
        
        # Use direct database access for AGE  
        db = await get_db_connection()
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        results = await db.fetch(
            f"""
            SELECT * FROM cypher('chunk_entity_relation', $$
            {cypher_query}
            $$) as (entity_id agtype, description agtype, entity_type agtype, file_path agtype, source_id agtype)
            """
        )
        
        # Convert results to proper format with text similarity score
        entities = []
        for row in results:
            entity_id = _clean_agtype_string(row['entity_id'])
            description = _clean_agtype_string(row['description'])
            
            # Calculate text similarity score
            similarity = 0.7  # Base similarity
            if query.lower() in entity_id.lower():
                similarity = 0.9
            elif query.lower() in description.lower():
                similarity = 0.8
            
            entity = {
                'entity_id': entity_id,
                'description': description,
                'entity_type': _clean_agtype_string(row['entity_type']),
                'file_path': _clean_agtype_string(row['file_path']),
                'source_id': _clean_agtype_string(row['source_id']),
                'similarity': similarity
            }
            entities.append(entity)
        
        # Sort by similarity score (highest first)
        entities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return entities
        
    except Exception as e:
        logger.error(f"Error searching entities by text: {e}")
        
        # Fallback: use direct SQL query
        try:
            logger.info("Attempting fallback entity search using direct SQL...")
            
            db = await get_db_connection()
            
            if entity_type:
                results = await db.fetch(
                    """
                    SELECT properties->>'entity_id' as entity_id,
                           properties->>'description' as description,
                           properties->>'entity_type' as entity_type,
                           properties->>'file_path' as file_path,
                           properties->>'source_id' as source_id
                    FROM chunk_entity_relation._ag_label_vertex
                    WHERE (properties->>'description' ILIKE $1 OR properties->>'entity_id' ILIKE $1)
                    AND properties->>'entity_type' = $2
                    LIMIT $3
                    """,
                    f'%{query}%',
                    entity_type,
                    limit
                )
            else:
                results = await db.fetch(
                    """
                    SELECT properties->>'entity_id' as entity_id,
                           properties->>'description' as description,
                           properties->>'entity_type' as entity_type,
                           properties->>'file_path' as file_path,
                           properties->>'source_id' as source_id
                    FROM chunk_entity_relation._ag_label_vertex
                    WHERE properties->>'description' ILIKE $1 
                    OR properties->>'entity_id' ILIKE $1
                    LIMIT $2
                    """,
                    f'%{query}%',
                    limit
                )
            
            entities = []
            for row in results:
                entity_id = row['entity_id'] or ''
                description = row['description'] or ''
                
                # Calculate similarity
                similarity = 0.6  # Base fallback similarity
                if query.lower() in entity_id.lower():
                    similarity = 0.8
                elif query.lower() in description.lower():
                    similarity = 0.7
                
                entity = {
                    'entity_id': entity_id,
                    'description': description,
                    'entity_type': row['entity_type'] or '',
                    'file_path': row['file_path'] or '',
                    'source_id': row['source_id'] or '',
                    'similarity': similarity
                }
                entities.append(entity)
            
            entities.sort(key=lambda x: x['similarity'], reverse=True)
            logger.info(f"Fallback entity search returned {len(entities)} results")
            
            return entities
            
        except Exception as fallback_e:
            logger.error(f"Fallback entity search also failed: {fallback_e}")
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
        db = await get_db_connection()
        await db.execute("LOAD 'age'")
        await db.execute("SET search_path = ag_catalog, '$user', public")
        
        stats = {}
        
        # Count nodes by entity type using direct SQL
        entity_type_counts = await db.fetch(
            """
            SELECT properties->>'entity_type' as entity_type, count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties->>'entity_type' IS NOT NULL
            GROUP BY properties->>'entity_type'
            ORDER BY count DESC
            """
        )
        
        stats['node_counts'] = {
            row['entity_type']: row['count'] for row in entity_type_counts if row['entity_type']
        }
        
        # Count total relationships
        total_relationships = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_edge"
        )
        
        # Count total nodes
        total_nodes = await db.fetchval(
            "SELECT count(*) FROM chunk_entity_relation._ag_label_vertex"
        )
        
        # Get file path counts
        file_path_counts = await db.fetch(
            """
            SELECT properties->>'file_path' as file_path, count(*) as count
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties->>'file_path' IS NOT NULL
            GROUP BY properties->>'file_path'
            ORDER BY count DESC
            LIMIT 5
            """
        )
        
        stats['file_path_counts'] = {
            row['file_path']: row['count'] for row in file_path_counts if row['file_path']
        }
        
        stats['relationship_counts'] = {'DIRECTED': total_relationships}
        stats['total_nodes'] = total_nodes
        stats['total_relationships'] = total_relationships
        
        # Calculate some additional statistics
        if total_nodes > 0:
            stats['average_connections_per_node'] = round(total_relationships * 2 / total_nodes, 2)
        else:
            stats['average_connections_per_node'] = 0
        
        # Get unique source count
        unique_sources = await db.fetchval(
            """
            SELECT count(DISTINCT properties->>'source_id')
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties->>'source_id' IS NOT NULL
            """
        )
        stats['unique_sources'] = unique_sources
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        return {
            'node_counts': {},
            'relationship_counts': {},
            'file_path_counts': {},
            'total_nodes': 0,
            'total_relationships': 0,
            'average_connections_per_node': 0,
            'unique_sources': 0,
            'error': str(e)
        }
