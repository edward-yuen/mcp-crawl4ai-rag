"""
Helper functions for enhanced search tools.

This module contains the implementation details for different search backends
used by the enhanced search system.
"""
from typing import List, Dict, Optional
from src.utils import search_documents
from src.lightrag_knowledge_graph import (
    query_knowledge_graph,
    search_entities_by_embedding,
    get_entity_relationships
)
from src.enhanced_kg_integration import enhanced_query_graph


async def _search_documents(query: str, sources: Optional[List[str]], max_results: int) -> List[Dict]:
    """Search crawled documents."""
    filter_metadata = None
    if sources:
        # If multiple sources, we'll need to search each separately and combine
        if len(sources) == 1:
            filter_metadata = {"source": sources[0]}
    
    results = await search_documents(
        query=query,
        match_count=max_results,
        filter_metadata=filter_metadata
    )
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "type": "document",
            "url": result.get("url"),
            "content": result.get("content"),
            "metadata": result.get("metadata", {}),
            "similarity": result.get("similarity"),
            "source": "crawl_schema"
        })
    
    return formatted_results



async def _search_entities(query: str, max_results: int) -> List[Dict]:
    """Search entities using semantic similarity."""
    entities = await search_entities_by_embedding(query, None, max_results)
    
    formatted_results = []
    for entity in entities:
        formatted_results.append({
            "type": "entity",
            "name": entity.get("name"),
            "entity_type": entity.get("type"),
            "description": entity.get("description"),
            "properties": entity.get("properties", {}),
            "similarity": entity.get("similarity"),
            "source": "knowledge_graph"
        })
    
    return formatted_results


async def _search_relationships(query: str, max_results: int) -> List[Dict]:
    """Search for relationships between entities."""
    # First, try to extract entity names from the query
    words = query.split()
    potential_entities = [word for word in words if word[0].isupper()]
    
    if len(potential_entities) >= 1:
        # Get relationships for the first entity
        entity_name = potential_entities[0]
        relationships = await get_entity_relationships(entity_name, None, 2)
        
        formatted_results = []
        for rel in relationships[:max_results]:
            formatted_results.append({
                "type": "relationship",
                "entity": entity_name,
                "related_entity": rel.get("related_entity"),
                "relationship_type": rel.get("relationship_type"),
                "description": rel.get("description"),
                "source": "knowledge_graph"
            })
        
        return formatted_results
    else:
        # Fallback to entity search
        return await _search_entities(query, max_results)



async def _search_graph_context(ctx, query: str, max_results: int) -> List[Dict]:
    """Enhanced graph search with context."""
    try:
        db_connection = ctx.request_context.lifespan_context.db_connection
        results = await enhanced_query_graph(db_connection, query, True, True)
        
        if isinstance(results, list):
            formatted_results = []
            for result in results[:max_results]:
                formatted_results.append({
                    "type": "graph_result",
                    "content": result,
                    "source": "enhanced_knowledge_graph"
                })
            return formatted_results
        else:
            return [{
                "type": "graph_result",
                "content": results,
                "source": "enhanced_knowledge_graph"
            }]
    except Exception:
        # Fallback to regular entity search
        return await _search_entities(query, max_results)


async def _execute_cypher_query(query: str) -> List[Dict]:
    """Execute raw Cypher query."""
    results = await query_knowledge_graph(query)
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "type": "cypher_result",
            "data": result,
            "source": "direct_cypher"
        })
    
    return formatted_results


async def _multi_backend_search(query: str, sources: Optional[List[str]], max_results: int) -> List[Dict]:
    """Search across multiple backends and combine results."""
    all_results = []
    
    # Search documents (crawl schema)
    try:
        doc_results = await _search_documents(query, sources, max_results // 2)
        all_results.extend(doc_results)
    except Exception:
        pass  # Continue with other searches
    
    # Search entities (knowledge graph)
    try:
        entity_results = await _search_entities(query, max_results // 2)
        all_results.extend(entity_results)
    except Exception:
        pass  # Continue with other searches
    
    # Sort by similarity if available
    def get_similarity(result):
        return result.get("similarity", 0) or 0
    
    all_results.sort(key=get_similarity, reverse=True)
    return all_results[:max_results]
