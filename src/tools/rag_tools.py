"""
RAG (Retrieval Augmented Generation) tools for the MCP server.

This module contains MCP tools for searching and querying stored documents.
"""
from mcp.server.fastmcp import Context
from typing import List
import json

from src.utils import search_documents
from src.lightrag_integration import (
    search_lightrag_documents,
    get_lightrag_collections,
    get_lightrag_schema_info,
    search_multi_schema
)


async def get_available_sources(ctx: Context) -> str:
    """
    Get all available sources based on unique source metadata values.
    
    This tool returns a list of all unique sources (domains) that have been crawled and stored
    in the database. This is useful for discovering what content is available for querying.
    
    Args:
        ctx: The MCP server provided context
    
    Returns:
        JSON string with the list of available sources
    """
    try:
        # Get the database connection from the context
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Query to get unique sources from metadata
        # Reason: Using DISTINCT with JSONB extraction to get unique sources efficiently
        result = await db_connection.fetch(
            """
            SELECT DISTINCT metadata->>'source' as source
            FROM crawl.crawled_pages
            WHERE metadata->>'source' IS NOT NULL
            ORDER BY source
            """
        )
        
        # Extract sources from the result
        sources = [row['source'] for row in result if row['source']]
        
        return json.dumps({
            "success": True,
            "sources": sources,
            "count": len(sources)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def perform_rag_query(ctx: Context, query: str, source: str = None, match_count: int = 5) -> str:
    """
    Perform a RAG (Retrieval Augmented Generation) query on the stored content.
    
    This tool searches the vector database for content relevant to the query and returns
    the matching documents. Optionally filter by source domain.

    Use the tool to get source domains if the user is asking to use a specific tool or framework.
    
    Args:
        ctx: The MCP server provided context
        query: The search query
        source: Optional source domain to filter results (e.g., 'example.com')
        match_count: Maximum number of results to return (default: 5)
    
    Returns:
        JSON string with the search results
    """
    try:
        # Prepare filter if source is provided and not empty
        filter_metadata = None
        if source and source.strip():
            filter_metadata = {"source": source}
        
        # Perform the search
        results = await search_documents(
            query=query,
            match_count=match_count,
            filter_metadata=filter_metadata
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "url": result.get("url"),
                "content": result.get("content"),
                "metadata": result.get("metadata"),
                "similarity": result.get("similarity")
            })
        
        return json.dumps({
            "success": True,
            "query": query,
            "source_filter": source,
            "results": formatted_results,
            "count": len(formatted_results)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)


async def query_lightrag_schema(ctx: Context, query: str, collection: str = None, match_count: int = 5) -> str:
    """
    Search for entities in the LightRAG knowledge graph.
    
    This tool searches for ENTITIES (not documents) in the knowledge graph stored
    in the chunk_entity_relation schema. It searches entity IDs and descriptions.
    
    Args:
        ctx: The MCP server provided context
        query: The search query
        collection: Optional collection name to filter results
        match_count: Maximum number of results to return (default: 5)
    
    Returns:
        JSON string with the search results from lightrag schema
    """
    try:
        # Search lightrag documents
        results = await search_lightrag_documents(
            query=query,
            match_count=match_count,
            collection_name=collection
        )
        
        # Format the results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id"),
                "content": result.get("content"),
                "metadata": result.get("metadata"),
                "similarity": result.get("similarity")
            })
        
        return json.dumps({
            "success": True,
            "query": query,
            "schema": "lightrag",
            "collection_filter": collection,
            "results": formatted_results,
            "count": len(formatted_results)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)


async def get_lightrag_info(ctx: Context) -> str:
    """
    Get information about the LightRAG schema structure and available collections.
    
    This tool provides metadata about what data is available in the lightrag schema,
    including table structures and available collections.
    
    Args:
        ctx: The MCP server provided context
    
    Returns:
        JSON string with schema information and available collections
    """
    try:
        # Get schema information
        schema_info = await get_lightrag_schema_info()
        
        # Get available collections
        collections = await get_lightrag_collections()
        
        return json.dumps({
            "success": True,
            "schema_info": schema_info,
            "collections": collections
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


async def multi_schema_search(ctx: Context, query: str, schemas: List[str] = None, match_count: int = 5, combine: bool = True) -> str:
    """
    Search across multiple schemas (crawl and lightrag) simultaneously.
    
    This tool allows searching both the crawl schema (web-crawled data) and the lightrag
    schema (existing RAG data) in one query, optionally combining and re-ranking results.
    
    Args:
        ctx: The MCP server provided context
        query: The search query
        schemas: List of schemas to search (default: ["crawl", "lightrag"])
        match_count: Maximum number of results per schema (default: 5)
        combine: Whether to combine and re-rank results by similarity (default: True)
    
    Returns:
        JSON string with search results from multiple schemas
    """
    try:
        # Use default schemas if none provided
        if schemas is None:
            schemas = ["crawl", "lightrag"]
        
        # Perform multi-schema search
        results = await search_multi_schema(
            query=query,
            schemas=schemas,
            match_count=match_count,
            combine_results=combine
        )
        
        return json.dumps({
            "success": True,
            "query": query,
            "schemas_searched": schemas,
            "results": results
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)
