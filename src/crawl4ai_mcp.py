"""
MCP server for web crawling with Crawl4AI.

This server provides tools to crawl websites using Crawl4AI, automatically detecting
the appropriate crawl method based on URL type (sitemap, txt file, or regular webpage).
"""
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urldefrag
from xml.etree import ElementTree
from dotenv import load_dotenv
from pathlib import Path
import requests
import asyncio
import json
import os
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher
from .database import DatabaseConnection, initialize_db_connection, close_db_connection
from .utils import add_documents_to_postgres, search_documents
from .lightrag_integration import (
    search_lightrag_documents, 
    get_lightrag_collections,
    get_lightrag_schema_info,
    search_multi_schema
)
from .lightrag_knowledge_graph import (
    query_knowledge_graph,
    get_entities_by_type,
    get_entity_relationships,
    search_entities_by_embedding,
    get_communities,
    find_path_between_entities,
    get_graph_statistics
)

from .enhanced_kg_integration import (
    enhanced_query_graph,
    build_knowledge_graph_from_crawled_data,
    analyze_knowledge_graph,
    get_entity_suggestions,
    KnowledgeGraphManager
)
# Load environment variables from the project root .env file
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / '.env'

# Force override of existing environment variables
load_dotenv(dotenv_path, override=True)

# Create a dataclass for our application context
@dataclass
class Crawl4AIContext:
    """Context for the Crawl4AI MCP server."""
    crawler: AsyncWebCrawler
    db_connection: DatabaseConnection
    
@asynccontextmanager
async def crawl4ai_lifespan(server: FastMCP) -> AsyncIterator[Crawl4AIContext]:
    """
    Manages the Crawl4AI client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        Crawl4AIContext: The context containing the Crawl4AI crawler and database connection
    """
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )
    
    # Initialize the crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    # Initialize PostgreSQL connection
    db_connection = await initialize_db_connection()
    
    # Create schema if it doesn't exist
    await db_connection.create_schema_if_not_exists()
    
    try:
        yield Crawl4AIContext(
            crawler=crawler,
            db_connection=db_connection
        )
    finally:
        # Clean up the crawler
        await crawler.__aexit__(None, None, None)
        # Close database connection
        await close_db_connection()

# Initialize FastMCP server
def get_port() -> int:
    """Get port from environment, handling empty string values."""
    port_str = os.getenv("PORT", "8051")
    if not port_str or port_str.strip() == "":
        return 8051
    try:
        return int(port_str)
    except ValueError:
        return 8051

def get_host() -> str:
    """Get host from environment, handling empty string values."""
    host_str = os.getenv("HOST", "0.0.0.0")
    if not host_str or host_str.strip() == "":
        return "0.0.0.0"
    return host_str

mcp = FastMCP(
    "mcp-crawl4ai-rag",
    description="MCP server for RAG and web crawling with Crawl4AI",
    lifespan=crawl4ai_lifespan,
    host=get_host(),
    port=get_port()
)

def is_sitemap(url: str) -> bool:
    """
    Check if a URL is a sitemap.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a sitemap, False otherwise
    """
    return url.endswith('sitemap.xml') or 'sitemap' in urlparse(url).path

def is_txt(url: str) -> bool:
    """
    Check if a URL is a text file.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a text file, False otherwise
    """
    return url.endswith('.txt')

def parse_sitemap(sitemap_url: str) -> List[str]:
    """
    Parse a sitemap and extract URLs.
    
    Args:
        sitemap_url: URL of the sitemap
        
    Returns:
        List of URLs found in the sitemap
    """
    resp = requests.get(sitemap_url)
    urls = []

    if resp.status_code == 200:
        try:
            tree = ElementTree.fromstring(resp.content)
            urls = [loc.text for loc in tree.findall('.//{*}loc')]
        except Exception as e:
            print(f"Error parsing sitemap XML: {e}")

    return urls

def smart_chunk_markdown(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = end

    return chunks

def extract_section_info(chunk: str) -> Dict[str, Any]:
    """
    Extracts headers and stats from a chunk.
    
    Args:
        chunk: Markdown chunk
        
    Returns:
        Dictionary with headers and stats
    """
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }

@mcp.tool()
async def crawl_single_page(ctx: Context, url: str) -> str:
    """
    Crawl a single web page and store its content in PostgreSQL.
    
    This tool is ideal for quickly retrieving content from a specific URL without following links.
    The content is stored in PostgreSQL for later retrieval and querying.
    
    Args:
        ctx: The MCP server provided context
        url: URL of the web page to crawl
    
    Returns:
        Summary of the crawling operation and storage in PostgreSQL
    """
    try:
        # Get the crawler and database connection from the context
        crawler = ctx.request_context.lifespan_context.crawler
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        # Configure the crawl
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
        
        # Crawl the page
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success and result.markdown:
            # Chunk the content
            chunks = smart_chunk_markdown(result.markdown)
            
            # Prepare data for PostgreSQL
            urls = []
            chunk_numbers = []
            contents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                urls.append(url)
                chunk_numbers.append(i)
                contents.append(chunk)
                
                # Extract metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = i
                meta["url"] = url
                meta["source"] = urlparse(url).netloc
                meta["crawl_time"] = str(asyncio.current_task().get_coro().__name__)
                metadatas.append(meta)
            
            # Create url_to_full_document mapping
            url_to_full_document = {url: result.markdown}
            
            # Add to PostgreSQL using the PostgreSQL functions
            await add_documents_to_postgres(urls, chunk_numbers, contents, metadatas, url_to_full_document)
            
            return json.dumps({
                "success": True,
                "url": url,
                "chunks_stored": len(chunks),
                "content_length": len(result.markdown),
                "links_count": {
                    "internal": len(result.links.get("internal", [])),
                    "external": len(result.links.get("external", []))
                }
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "url": url,
                "error": result.error_message
            }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "url": url,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def smart_crawl_url(ctx: Context, url: str, max_depth: int = 3, max_concurrent: int = 10, chunk_size: int = 5000) -> str:
    """
    Intelligently crawl a URL based on its type and store content in PostgreSQL.
    
    This tool automatically detects the URL type and applies the appropriate crawling method:
    - For sitemaps: Extracts and crawls all URLs in parallel
    - For text files (llms.txt): Directly retrieves the content
    - For regular webpages: Recursively crawls internal links up to the specified depth
    
    All crawled content is chunked and stored in PostgreSQL for later retrieval and querying.
    
    Args:
        ctx: The MCP server provided context
        url: URL to crawl (can be a regular webpage, sitemap.xml, or .txt file)
        max_depth: Maximum recursion depth for regular URLs (default: 3)
        max_concurrent: Maximum number of concurrent browser sessions (default: 10)
        chunk_size: Maximum size of each content chunk in characters (default: 1000)
    
    Returns:
        JSON string with crawl summary and storage information
    """
    try:
        # Get the crawler and database connection from the context
        crawler = ctx.request_context.lifespan_context.crawler
        db_connection = ctx.request_context.lifespan_context.db_connection
        
        crawl_results = []
        crawl_type = "webpage"
        
        # Detect URL type and use appropriate crawl method
        if is_txt(url):
            # For text files, use simple crawl
            crawl_results = await crawl_markdown_file(crawler, url)
            crawl_type = "text_file"
        elif is_sitemap(url):
            # For sitemaps, extract URLs and crawl in parallel
            sitemap_urls = parse_sitemap(url)
            if not sitemap_urls:
                return json.dumps({
                    "success": False,
                    "url": url,
                    "error": "No URLs found in sitemap"
                }, indent=2)
            crawl_results = await crawl_batch(crawler, sitemap_urls, max_concurrent=max_concurrent)
            crawl_type = "sitemap"
        else:
            # For regular URLs, use recursive crawl
            crawl_results = await crawl_recursive_internal_links(crawler, [url], max_depth=max_depth, max_concurrent=max_concurrent)
            crawl_type = "webpage"
        
        if not crawl_results:
            return json.dumps({
                "success": False,
                "url": url,
                "error": "No content found"
            }, indent=2)
        
        # Process results and store in PostgreSQL
        urls = []
        chunk_numbers = []
        contents = []
        metadatas = []
        chunk_count = 0
        
        for doc in crawl_results:
            source_url = doc['url']
            md = doc['markdown']
            chunks = smart_chunk_markdown(md, chunk_size=chunk_size)
            
            for i, chunk in enumerate(chunks):
                urls.append(source_url)
                chunk_numbers.append(i)
                contents.append(chunk)
                
                # Extract metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = i
                meta["url"] = source_url
                meta["source"] = urlparse(source_url).netloc
                meta["crawl_type"] = crawl_type
                meta["crawl_time"] = str(asyncio.current_task().get_coro().__name__)
                metadatas.append(meta)
                
                chunk_count += 1
        
        # Create url_to_full_document mapping
        url_to_full_document = {}
        for doc in crawl_results:
            url_to_full_document[doc['url']] = doc['markdown']
        
        # Add to PostgreSQL using the PostgreSQL functions
        # IMPORTANT: Adjust this batch size for more speed if you want! Just don't overwhelm your system or the embedding API ;)
        batch_size = 20
        await add_documents_to_postgres(urls, chunk_numbers, contents, metadatas, url_to_full_document, batch_size=batch_size)
        
        return json.dumps({
            "success": True,
            "url": url,
            "crawl_type": crawl_type,
            "pages_crawled": len(crawl_results),
            "chunks_stored": chunk_count,
            "urls_crawled": [doc['url'] for doc in crawl_results][:5] + (["..."] if len(crawl_results) > 5 else [])
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "url": url,
            "error": str(e)
        }, indent=2)

async def crawl_markdown_file(crawler: AsyncWebCrawler, url: str) -> List[Dict[str, Any]]:
    """
    Crawl a .txt or markdown file.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL of the file
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    crawl_config = CrawlerRunConfig()

    result = await crawler.arun(url=url, config=crawl_config)
    if result.success and result.markdown:
        return [{'url': url, 'markdown': result.markdown}]
    else:
        print(f"Failed to crawl {url}: {result.error_message}")
        return []

async def crawl_batch(crawler: AsyncWebCrawler, urls: List[str], max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """
    Batch crawl multiple URLs in parallel.
    
    Args:
        crawler: AsyncWebCrawler instance
        urls: List of URLs to crawl
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    results = await crawler.arun_many(urls=urls, config=crawl_config, dispatcher=dispatcher)
    return [{'url': r.url, 'markdown': r.markdown} for r in results if r.success and r.markdown]

async def crawl_recursive_internal_links(crawler: AsyncWebCrawler, start_urls: List[str], max_depth: int = 3, max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """
    Recursively crawl internal links from start URLs up to a maximum depth.
    
    Args:
        crawler: AsyncWebCrawler instance
        start_urls: List of starting URLs
        max_depth: Maximum recursion depth
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    visited = set()

    def normalize_url(url):
        return urldefrag(url)[0]

    current_urls = set([normalize_url(u) for u in start_urls])
    results_all = []

    for depth in range(max_depth):
        urls_to_crawl = [normalize_url(url) for url in current_urls if normalize_url(url) not in visited]
        if not urls_to_crawl:
            break

        results = await crawler.arun_many(urls=urls_to_crawl, config=run_config, dispatcher=dispatcher)
        next_level_urls = set()

        for result in results:
            norm_url = normalize_url(result.url)
            visited.add(norm_url)

            if result.success and result.markdown:
                results_all.append({'url': result.url, 'markdown': result.markdown})
                for link in result.links.get("internal", []):
                    next_url = normalize_url(link["href"])
                    if next_url not in visited:
                        next_level_urls.add(next_url)

        current_urls = next_level_urls

    return results_all

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
async def query_lightrag_schema(ctx: Context, query: str, collection: str = None, match_count: int = 5) -> str:
    """
    Query documents from the LightRAG schema.
    
    This tool searches for documents stored in the lightrag schema, which may contain
    data from other RAG applications or pre-existing document collections.
    
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
async def get_graph_entities(ctx: Context, entity_type: str = None, limit: int = 50) -> str:
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

@mcp.tool()
async def get_entity_graph(ctx: Context, entity_name: str, relationship_type: str = None, depth: int = 1) -> str:
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
        graph_data = await get_entity_relationships(entity_name, relationship_type, depth)
        
        return json.dumps({
            "success": True,
            "entity": entity_name,
            "depth": depth,
            "relationship_filter": relationship_type,
            "graph": graph_data
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def search_graph_entities(ctx: Context, query: str, entity_type: str = None, limit: int = 10) -> str:
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
            "entity_type_filter": entity_type,
            "entities": entities,
            "count": len(entities)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)

@mcp.tool()
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
            "paths_found": len(paths)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "start_entity": start_entity,
            "end_entity": end_entity,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def get_graph_communities(ctx: Context, level: int = None, limit: int = 20) -> str:
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
            "level_filter": level,
            "communities": communities,
            "count": len(communities)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

@mcp.tool()
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

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())

@mcp.tool()
async def build_knowledge_graph(ctx: Context, limit: int = 100) -> str:
    """
    Build knowledge graph from recently crawled documents.
    
    This tool automatically extracts entities and relationships from crawled content
    and populates the knowledge graph. It uses NLP patterns to identify:
    - Person entities (names)
    - Organization entities (companies, institutions)
    - Relationships between entities (works at, related to, etc.)
    
    Args:
        limit: Maximum number of recent documents to process (default: 100)
        
    Returns:
        JSON with build results including entities and relationships created
    """
    try:
        result = await build_knowledge_graph_from_crawled_data(limit)
        
        return json.dumps({
            "success": result.get("success", False),
            "documents_processed": result.get("documents_processed", 0),
            "entities_created": result.get("entities_created", 0),
            "relationships_created": result.get("relationships_created", 0),
            "error": result.get("error")
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def analyze_graph_patterns(ctx: Context) -> str:
    """
    Analyze patterns and structures in the knowledge graph.
    
    This tool performs advanced graph analytics to discover:
    - Central entities (highly connected nodes)
    - Isolated entities (disconnected nodes)
    - Triangular patterns (potential communities)
    - Cross-type connections (e.g., Person to Organization paths)
    
    Useful for understanding the structure and finding insights in your knowledge graph.
    
    Returns:
        JSON with various graph analysis results
    """
    try:
        analysis = await analyze_knowledge_graph()
        
        if "error" in analysis:
            return json.dumps({
                "success": False,
                "error": analysis["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "analysis": analysis,
            "insights": {
                "central_entities_count": len(analysis.get("central_entities", [])),
                "isolated_entities_count": len(analysis.get("isolated_entities", [])),
                "triangular_patterns_count": len(analysis.get("triangular_patterns", [])),
                "cross_type_connections_count": len(analysis.get("cross_type_connections", []))
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def suggest_entity_relationships(ctx: Context, entity_name: str) -> str:
    """
    Suggest potential new relationships for an entity.
    
    This tool analyzes the graph structure to suggest entities that might be
    related to the given entity based on shared connections and patterns.
    Useful for discovering missing relationships or expanding entity connections.
    
    Args:
        entity_name: Name of the entity to analyze
        
    Returns:
        JSON with suggested relationships and connection strengths
    """
    try:
        result = await get_entity_suggestions(entity_name)
        
        return json.dumps({
            "success": result["success"],
            "entity": result["entity"],
            "suggestions": result["suggested_relationships"],
            "count": result["count"],
            "explanation": "Suggestions based on shared connections in the graph"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def enhanced_graph_query(ctx: Context, cypher_query: str, parameters: str = "{}") -> str:
    """
    Execute an enhanced Cypher query with better error handling and diagnostics.
    
    This is an improved version of the basic query_graph tool that provides:
    - Better error messages and diagnostics
    - Parameter support
    - AGE availability checking
    - Result formatting and metadata
    
    Args:
        cypher_query: Cypher query to execute
        parameters: JSON string of parameters (optional)
        
    Returns:
        JSON with query results and metadata
    """
    try:
        # Parse parameters if provided
        params = {}
        if parameters and parameters != "{}":
            params = json.loads(parameters)
        
        result = await enhanced_query_graph(cypher_query, params)
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "query": cypher_query,
            "error": f"Invalid parameters JSON: {str(e)}"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": cypher_query,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def check_graph_health(ctx: Context) -> str:
    """
    Check the health and status of the knowledge graph.
    
    This tool verifies:
    - Apache AGE availability and configuration
    - Graph existence and accessibility
    - Basic connectivity and data integrity
    - Performance metrics
    
    Returns:
        JSON with comprehensive health status
    """
    try:
        kg_manager = KnowledgeGraphManager()
        
        # Check AGE availability
        age_available = await kg_manager.check_age_availability()
        
        # Get basic stats if AGE is available
        stats = {}
        if age_available:
            graph_exists = await kg_manager.ensure_graph_exists()
            if graph_exists:
                # Get node and relationship counts
                node_count = await kg_manager.execute_cypher("MATCH (n) RETURN count(n) as count")
                rel_count = await kg_manager.execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
                
                stats = {
                    "total_nodes": node_count[0]["count"] if node_count else 0,
                    "total_relationships": rel_count[0]["count"] if rel_count else 0
                }
        
        return json.dumps({
            "success": True,
            "age_available": age_available,
            "graph_accessible": age_available,
            "statistics": stats,
            "recommendations": [
                "Install Apache AGE extension" if not age_available else "Knowledge graph is ready",
                "Run 'build_knowledge_graph' to populate from crawled data" if stats.get("total_nodes", 0) == 0 else "Graph contains data"
            ]
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "recommendations": [
                "Check PostgreSQL connection",
                "Verify Apache AGE installation",
                "Check database permissions"
            ]
        }, indent=2)


@mcp.tool()
async def explore_entity_neighborhood(ctx: Context, entity_name: str, depth: int = 2, limit: int = 20) -> str:
    """
    Explore the neighborhood around an entity up to a specified depth.
    
    This tool provides a comprehensive view of an entity's connections,
    including direct relationships and extended network effects.
    
    Args:
        entity_name: Name of the entity to explore
        depth: How many hops to explore (1-3 recommended)
        limit: Maximum number of entities to return per level
        
    Returns:
        JSON with neighborhood structure and relationship details
    """
    try:
        kg_manager = KnowledgeGraphManager()
        
        if not await kg_manager.check_age_availability():
            return json.dumps({
                "success": False,
                "error": "Apache AGE not available"
            }, indent=2)
        
        # Get neighborhood at different depths
        neighborhood = {}
        
        for d in range(1, depth + 1):
            cypher_query = f"""
            MATCH path = (start {{name: '{entity_name}'}}-[*{d}]-(neighbor)
            WHERE neighbor <> start
            WITH neighbor, path, length(path) as path_length
            RETURN DISTINCT 
                neighbor.name as name,
                labels(neighbor)[0] as type,
                neighbor.properties as properties,
                path_length
            ORDER BY path_length, name
            LIMIT {limit}
            """
            
            results = await kg_manager.execute_cypher(cypher_query)
            neighborhood[f"depth_{d}"] = results
        
        # Get direct relationships for context
        direct_rels = await kg_manager.execute_cypher(f"""
            MATCH (start {{name: '{entity_name}'}})-[r]-(neighbor)
            RETURN 
                type(r) as relationship_type,
                neighbor.name as neighbor_name,
                labels(neighbor)[0] as neighbor_type,
                r.properties as relationship_properties
            LIMIT {limit}
        """)
        
        return json.dumps({
            "success": True,
            "entity": entity_name,
            "neighborhood": neighborhood,
            "direct_relationships": direct_rels,
            "metadata": {
                "max_depth": depth,
                "limit_per_level": limit
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "entity": entity_name,
            "error": str(e)
        }, indent=2)
