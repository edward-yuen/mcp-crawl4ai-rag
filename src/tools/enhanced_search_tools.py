"""
Enhanced unified search tools for the Crawl4AI MCP server.

This module provides a unified search interface that intelligently routes queries
to the appropriate backend (crawl schema, lightrag schema, or knowledge graph)
based on query analysis and user preferences.
"""
from mcp.server.fastmcp import Context
from typing import List, Optional, Dict, Any, Union
import json
import re
from datetime import datetime

from src.utils import search_documents
from src.lightrag_integration import (
    search_lightrag_documents,
    search_multi_schema
)
from src.lightrag_knowledge_graph import (
    query_knowledge_graph,
    search_entities_by_embedding,
    get_entity_relationships
)
from src.enhanced_kg_integration import enhanced_query_graph


class QueryAnalyzer:
    """Analyzes queries to determine the best search strategy."""
    
    # Keywords that suggest different search types
    DOCUMENT_KEYWORDS = {
        'content', 'article', 'page', 'document', 'text', 'blog', 'website', 
        'crawl', 'scraped', 'markdown', 'html', 'url', 'source'
    }
    
    ENTITY_KEYWORDS = {
        'person', 'people', 'company', 'organization', 'entity', 'entities',
        'individual', 'who', 'what is', 'definition', 'concept', 'term'
    }
    
    RELATIONSHIP_KEYWORDS = {
        'relationship', 'connected', 'related', 'link', 'association',
        'how are', 'connection', 'path', 'between', 'and', 'versus', 'vs'
    }
    
    GRAPH_KEYWORDS = {
        'graph', 'network', 'cypher', 'query', 'traverse', 'path',
        'community', 'cluster', 'neighborhood', 'degree', 'centrality'
    }

    @classmethod
    def analyze_query(cls, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine the best search strategy.
        
        Args:
            query: The search query to analyze
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        query_lower = query.lower()
        words = set(query_lower.split())
        
        # Calculate keyword matches
        document_score = len(words.intersection(cls.DOCUMENT_KEYWORDS))
        entity_score = len(words.intersection(cls.ENTITY_KEYWORDS))
        relationship_score = len(words.intersection(cls.RELATIONSHIP_KEYWORDS))
        graph_score = len(words.intersection(cls.GRAPH_KEYWORDS))
        
        # Check for specific patterns
        is_cypher = 'match' in query_lower and ('return' in query_lower or 'where' in query_lower)
        has_entities = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query))
        is_question = query.strip().endswith('?')
        has_comparison = any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference'])
        
        # Determine primary search type
        scores = {
            'document': document_score,
            'entity': entity_score,
            'relationship': relationship_score,
            'graph': graph_score
        }
        
        if is_cypher:
            primary_type = 'cypher'
        elif relationship_score > 0 or has_comparison:
            primary_type = 'relationship'
        elif entity_score > document_score:
            primary_type = 'entity'
        elif graph_score > 0:
            primary_type = 'graph'
        else:
            primary_type = 'document'
        
        return {
            'primary_type': primary_type,
            'scores': scores,
            'patterns': {
                'is_cypher': is_cypher,
                'has_entities': has_entities,
                'is_question': is_question,
                'has_comparison': has_comparison
            },
            'confidence': max(scores.values()) / max(1, len(words)) if words else 0
        }



async def enhanced_search(
    ctx: Context,
    query: str,
    search_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    max_results: int = 10,
    include_metadata: bool = True,
    semantic_expansion: bool = True
) -> str:
    """
    Perform an enhanced unified search across all available data sources.
    
    This tool intelligently routes queries to the most appropriate backend based on
    query analysis, or allows manual specification of search type. It can search
    documents, entities, relationships, and perform graph queries.
    
    Args:
        ctx: The MCP server provided context
        query: The search query
        search_type: Optional search type override ("document", "entity", "relationship", "graph", "cypher", "multi")
        sources: Optional list of sources to filter by
        max_results: Maximum number of results to return (default: 10)
        include_metadata: Whether to include detailed metadata (default: True)
        semantic_expansion: Whether to use semantic query expansion (default: True)
    
    Returns:
        JSON string with unified search results
    """
    try:
        start_time = datetime.now()
        
        # Analyze query if no search type specified
        if not search_type:
            analysis = QueryAnalyzer.analyze_query(query)
            search_type = analysis['primary_type']
            query_analysis = analysis
        else:
            query_analysis = {"manually_specified": True, "type": search_type}
        
        results = []
        search_metadata = {
            "query": query,
            "search_type": search_type,
            "analysis": query_analysis,
            "timestamp": start_time.isoformat()
        }
        
        # Route to appropriate search backend(s)
        if search_type == "document":
            results = await _search_documents(query, sources, max_results)
        elif search_type == "entity":
            results = await _search_entities(query, max_results)
        elif search_type == "relationship":
            results = await _search_relationships(query, max_results)
        elif search_type == "graph":
            results = await _search_graph_context(ctx, query, max_results)
        elif search_type == "cypher":
            results = await _execute_cypher_query(query)
        elif search_type == "multi":
            results = await _multi_backend_search(query, sources, max_results)
        else:
            # Fallback to multi-backend search
            results = await _multi_backend_search(query, sources, max_results)
        
        # Add performance metrics
        end_time = datetime.now()
        search_metadata["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        search_metadata["results_count"] = len(results)
        
        # Format response
        response = {
            "success": True,
            "metadata": search_metadata,
            "results": results[:max_results]
        }
        
        if not include_metadata:
            # Strip detailed metadata for cleaner response
            for result in response["results"]:
                if "metadata" in result:
                    result["metadata"] = {
                        k: v for k, v in result["metadata"].items()
                        if k in ["source", "url", "type"]
                    }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "search_type": search_type,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, indent=2)


# Import helper functions
from .search_helpers import (
    _search_documents,
    _search_entities, 
    _search_relationships,
    _search_graph_context,
    _execute_cypher_query,
    _multi_backend_search
)


async def smart_search(
    ctx: Context,
    query: str,
    auto_expand: bool = True,
    max_results: int = 5,
    include_related: bool = False
) -> str:
    """
    Perform a smart search that automatically determines the best approach.
    
    This is a simplified interface to enhanced_search that automatically
    determines the search strategy and optionally expands results with
    related information.
    
    Args:
        ctx: The MCP server provided context
        query: The search query
        auto_expand: Whether to automatically expand with related results (default: True)
        max_results: Maximum number of results to return (default: 5)
        include_related: Whether to include related entities/documents (default: False)
    
    Returns:
        JSON string with smart search results
    """
    try:
        # Perform initial enhanced search
        initial_results = await enhanced_search(
            ctx, query, None, None, max_results, True, auto_expand
        )
        
        # Parse the results to potentially expand them
        parsed_results = json.loads(initial_results)
        
        if include_related and parsed_results.get("success"):
            # Try to find related content based on initial results
            related_results = []
            
            for result in parsed_results["results"]:
                if result.get("type") == "entity" and result.get("name"):
                    # Get related entities
                    try:
                        relationships = await get_entity_relationships(
                            result["name"], None, 1
                        )
                        for rel in relationships[:2]:  # Limit to 2 related per entity
                            related_results.append({
                                "type": "related_entity",
                                "name": rel.get("related_entity"),
                                "relationship": rel.get("relationship_type"),
                                "source": "knowledge_graph"
                            })
                    except Exception:
                        continue
            
            # Add related results to response
            if related_results:
                parsed_results["related_results"] = related_results[:max_results]
        
        return json.dumps(parsed_results, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
