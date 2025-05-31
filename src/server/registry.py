"""
Tool registration system for the Crawl4AI MCP server.

This module handles the registration of all MCP tools from various modules.
"""
from mcp.server.fastmcp import FastMCP
from src.tools.crawling_tools import crawl_single_page, smart_crawl_url
from src.tools.rag_tools import (
    get_available_sources,
    perform_rag_query,
    query_lightrag_schema,
    get_lightrag_info,
    multi_schema_search
)
from src.tools.knowledge_graph_tools import (
    query_graph,
    get_graph_entities,
    get_entity_graph,
    search_graph_entities,
    find_entity_path,
    get_graph_communities,
    get_graph_stats,
    build_knowledge_graph,
    analyze_graph_patterns,
    suggest_entity_relationships,
    enhanced_graph_query,
    check_graph_health,
    explore_entity_neighborhood
)


def register_all_tools(mcp: FastMCP) -> None:
    """
    Register all tools with the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    # Register crawling tools
    mcp.tool()(crawl_single_page)
    mcp.tool()(smart_crawl_url)
    
    # Register RAG tools
    mcp.tool()(get_available_sources)
    mcp.tool()(perform_rag_query)
    mcp.tool()(query_lightrag_schema)
    mcp.tool()(get_lightrag_info)
    mcp.tool()(multi_schema_search)
    
    # Register knowledge graph tools
    mcp.tool()(query_graph)
    mcp.tool()(get_graph_entities)
    mcp.tool()(get_entity_graph)
    mcp.tool()(search_graph_entities)
    mcp.tool()(find_entity_path)
    mcp.tool()(get_graph_communities)
    mcp.tool()(get_graph_stats)
    mcp.tool()(build_knowledge_graph)
    mcp.tool()(analyze_graph_patterns)
    mcp.tool()(suggest_entity_relationships)
    mcp.tool()(enhanced_graph_query)
    mcp.tool()(check_graph_health)
    mcp.tool()(explore_entity_neighborhood)
