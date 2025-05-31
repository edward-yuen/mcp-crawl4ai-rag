"""
Knowledge graph tools for the Crawl4AI MCP server.

This module contains all knowledge graph related tools that interact with the LightRAG
knowledge graph using Apache AGE and PostgreSQL.
"""
from mcp.server.fastmcp import Context
from typing import Optional
import json

from src.lightrag_knowledge_graph import (
    query_knowledge_graph,
    get_entities_by_type,
    get_entity_relationships,
    search_entities_by_embedding,
    get_communities,
    find_path_between_entities,
    get_graph_statistics
)
from src.enhanced_kg_integration import (
    enhanced_query_graph,
    build_knowledge_graph_from_crawled_data,
    analyze_knowledge_graph,
    get_entity_suggestions,
    KnowledgeGraphManager
)


async def query_graph(ctx: Context, cypher_query: str) -> str:
    """
    Execute a Cypher query on the LightRAG knowledge graph.
    
    This tool allows direct querying of the knowledge graph using Cypher query language,
    enabling complex graph traversals and pattern matching.
    
    Args:
        ctx: The MCP server provided context
        cypher_query: Cypher query to execute (e.g., "MATCH (n:Person) RETURN n LIMIT 10")
    
    Returns:
        JSON string with query results
    """
    try:
        results = await query_knowledge_graph(cypher_query)
        
        return json.dumps({
            "success": True,
            "query": cypher_query,
            "results": results,
            "count": len(results)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": cypher_query,
            "error": str(e)
        }, indent=2)


async def get_graph_entities(ctx: Context, entity_type: Optional[str] = None, limit: int = 50) -> str:
    """
    Get entities from the LightRAG knowledge graph.
    
    This tool retrieves entities (nodes) from the knowledge graph, optionally filtered
    by type (e.g., Person, Organization, Concept).
    
    Args:
        ctx: The MCP server provided context
        entity_type: Optional entity type to filter by (e.g., "Person", "Organization")
        limit: Maximum number of entities to return (default: 50)
    
    Returns:
        JSON string with entity list
    """
    try:
        entities = await get_entities_by_type(entity_type, limit)
        
        return json.dumps({
            "success": True,
            "entity_type": entity_type,
            "entities": entities,
            "count": len(entities)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def get_entity_graph(ctx: Context, entity_name: str, relationship_type: Optional[str] = None, depth: int = 1) -> str:
    """
    Get the relationship graph for a specific entity.
    
    This tool retrieves all relationships and connected entities for a given entity,
    up to a specified depth in the graph.
    
    Args:
        ctx: The MCP server provided context
        entity_name: Name of the entity to explore
        relationship_type: Optional relationship type to filter (e.g., "KNOWS", "WORKS_AT")
        depth: How many hops to traverse from the entity (default: 1)
    
    Returns:
        JSON string with entity relationships and connected nodes
    """
    try:
        relationships = await get_entity_relationships(entity_name, relationship_type, depth)
        
        return json.dumps({
            "success": True,
            "entity": entity_name,
            "depth": depth,
            "relationships": relationships,
            "count": len(relationships)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)


async def search_graph_entities(ctx: Context, query: str, entity_type: Optional[str] = None, limit: int = 10) -> str:
    """
    Search for entities in the knowledge graph using semantic similarity.
    
    This tool finds entities whose embeddings are most similar to the query,
    useful for finding relevant entities based on meaning rather than exact matches.
    
    Args:
        ctx: The MCP server provided context
        query: Search query
        entity_type: Optional entity type to filter results
        limit: Maximum number of results (default: 10)
    
    Returns:
        JSON string with matching entities ordered by similarity
    """
    try:
        entities = await search_entities_by_embedding(query, entity_type, limit)
        
        return json.dumps({
            "success": True,
            "query": query,
            "entity_type": entity_type,
            "entities": entities,
            "count": len(entities)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)


async def find_entity_path(ctx: Context, start_entity: str, end_entity: str, max_depth: int = 3) -> str:
    """
    Find paths between two entities in the knowledge graph.
    
    This tool discovers how two entities are connected through the graph,
    showing the shortest paths and relationships between them.
    
    Args:
        ctx: The MCP server provided context
        start_entity: Name of the starting entity
        end_entity: Name of the ending entity
        max_depth: Maximum path length to search (default: 3)
    
    Returns:
        JSON string with paths between the entities
    """
    try:
        paths = await find_path_between_entities(start_entity, end_entity, max_depth)
        
        return json.dumps({
            "success": True,
            "start_entity": start_entity,
            "end_entity": end_entity,
            "max_depth": max_depth,
            "paths": paths,
            "count": len(paths)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "start_entity": start_entity,
            "end_entity": end_entity,
            "error": str(e)
        }, indent=2)


async def get_graph_communities(ctx: Context, level: Optional[int] = None, limit: int = 20) -> str:
    """
    Get communities from the LightRAG knowledge graph.
    
    Communities are groups of highly connected entities. This tool retrieves
    community structures that LightRAG has identified in the knowledge graph.
    
    Args:
        ctx: The MCP server provided context
        level: Optional community level to filter by
        limit: Maximum number of communities to return (default: 20)
    
    Returns:
        JSON string with community information
    """
    try:
        communities = await get_communities(level, limit)
        
        return json.dumps({
            "success": True,
            "level": level,
            "communities": communities,
            "count": len(communities)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def get_graph_stats(ctx: Context) -> str:
    """
    Get statistics about the LightRAG knowledge graph.
    
    This tool provides an overview of the graph structure, including counts
    of different entity types and relationship types.
    
    Args:
        ctx: The MCP server provided context
    
    Returns:
        JSON string with graph statistics
    """
    try:
        stats = await get_graph_statistics()
        
        return json.dumps({
            "success": True,
            "statistics": stats
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def build_knowledge_graph(ctx: Context, source: Optional[str] = None, limit: int = 100) -> str:
    """
    Build a knowledge graph from crawled data.
    
    This tool extracts entities and relationships from crawled documents
    and builds a knowledge graph representation.
    
    Args:
        ctx: The MCP server provided context
        source: Optional source domain to filter documents
        limit: Maximum number of documents to process (default: 100)
    
    Returns:
        JSON string with knowledge graph building results
    """
    try:
        # Get database connection from context
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Build knowledge graph from crawled data
        kg_manager = KnowledgeGraphManager(db_connection)
        result = await build_knowledge_graph_from_crawled_data(db_connection, source, limit)
        
        return json.dumps({
            "success": True,
            "source": source,
            "documents_processed": result.get("documents_processed", 0),
            "entities_created": result.get("entities_created", 0),
            "relationships_created": result.get("relationships_created", 0),
            "details": result
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def analyze_graph_patterns(ctx: Context, pattern_type: str = "all") -> str:
    """
    Analyze patterns in the knowledge graph.
    
    This tool analyzes the knowledge graph to identify patterns such as
    central entities, communities, and common relationship types.
    
    Args:
        ctx: The MCP server provided context
        pattern_type: Type of pattern to analyze ("centrality", "communities", "relationships", "all")
    
    Returns:
        JSON string with pattern analysis results
    """
    try:
        # Get database connection from context
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Analyze knowledge graph patterns
        analysis = await analyze_knowledge_graph(db_connection, pattern_type)
        
        return json.dumps({
            "success": True,
            "pattern_type": pattern_type,
            "analysis": analysis
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def suggest_entity_relationships(ctx: Context, entity_name: str, relationship_types: Optional[list] = None) -> str:
    """
    Suggest potential relationships for an entity.
    
    This tool uses semantic similarity and graph patterns to suggest
    potential relationships for a given entity.
    
    Args:
        ctx: The MCP server provided context
        entity_name: Name of the entity to analyze
        relationship_types: Optional list of relationship types to consider
    
    Returns:
        JSON string with relationship suggestions
    """
    try:
        suggestions = await get_entity_suggestions(entity_name, relationship_types)
        
        return json.dumps({
            "success": True,
            "entity": entity_name,
            "suggestions": suggestions
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)


async def enhanced_graph_query(ctx: Context, query: str, use_embeddings: bool = True, expand_context: bool = True) -> str:
    """
    Execute an enhanced graph query with semantic understanding.
    
    This tool combines natural language understanding with graph queries,
    automatically expanding the query context and using embeddings for better results.
    
    Args:
        ctx: The MCP server provided context
        query: Natural language query
        use_embeddings: Whether to use embeddings for semantic matching (default: True)
        expand_context: Whether to expand query context (default: True)
    
    Returns:
        JSON string with enhanced query results
    """
    try:
        # Get database connection from context
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Execute enhanced query
        results = await enhanced_query_graph(db_connection, query, use_embeddings, expand_context)
        
        return json.dumps({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results) if isinstance(results, list) else 1
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)


async def check_graph_health(ctx: Context) -> str:
    """
    Check the health and integrity of the knowledge graph.
    
    This tool performs various checks on the knowledge graph to ensure
    data integrity and identify potential issues.
    
    Args:
        ctx: The MCP server provided context
    
    Returns:
        JSON string with health check results
    """
    try:
        # Get database connection from context
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Initialize KG manager
        kg_manager = KnowledgeGraphManager(db_connection)
        
        # Perform health checks
        health_status = {
            "connection": "healthy",
            "statistics": await get_graph_statistics(),
            "orphaned_nodes": await query_knowledge_graph(
                "MATCH (n) WHERE NOT exists((n)-[]-()) RETURN count(n) as count"
            ),
            "duplicate_entities": await query_knowledge_graph(
                "MATCH (n) WITH n.name as name, count(n) as cnt WHERE cnt > 1 RETURN name, cnt LIMIT 10"
            ),
            "missing_embeddings": await query_knowledge_graph(
                "MATCH (n) WHERE n.embedding IS NULL RETURN count(n) as count"
            )
        }
        
        return json.dumps({
            "success": True,
            "health_status": health_status,
            "timestamp": str(ctx.request_context.timestamp) if hasattr(ctx.request_context, 'timestamp') else None
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def explore_entity_neighborhood(ctx: Context, entity_name: str, max_nodes: int = 50, include_communities: bool = True) -> str:
    """
    Explore the neighborhood of an entity in the knowledge graph.
    
    This tool provides a comprehensive view of an entity's context,
    including its relationships, communities, and related entities.
    
    Args:
        ctx: The MCP server provided context
        entity_name: Name of the entity to explore
        max_nodes: Maximum number of nodes to include (default: 50)
        include_communities: Whether to include community information (default: True)
    
    Returns:
        JSON string with entity neighborhood information
    """
    try:
        # Get basic entity information
        entity_info = await get_entity_relationships(entity_name, None, 2)
        
        # Get community information if requested
        community_info = None
        if include_communities:
            community_query = f"""
            MATCH (n)-[:BELONGS_TO]->(c:Community)
            WHERE n.name = $1
            RETURN c
            """
            communities = await query_knowledge_graph(community_query)
            community_info = communities if communities else []
        
        # Get similar entities
        similar_entities = await search_entities_by_embedding(entity_name, None, 10)
        
        # Combine all information
        neighborhood = {
            "entity": entity_name,
            "direct_relationships": entity_info[:max_nodes],
            "communities": community_info,
            "similar_entities": similar_entities,
            "stats": {
                "total_relationships": len(entity_info),
                "communities_count": len(community_info) if community_info else 0,
                "similar_entities_count": len(similar_entities)
            }
        }
        
        return json.dumps({
            "success": True,
            "neighborhood": neighborhood
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)
