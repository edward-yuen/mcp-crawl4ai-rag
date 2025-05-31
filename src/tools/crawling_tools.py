"""
Crawling tools for the MCP server.

This module contains MCP tools for web crawling operations.
"""
from mcp.server.fastmcp import Context
from crawl4ai import CrawlerRunConfig, CacheMode
from urllib.parse import urlparse
import asyncio
import json

from src.crawling.utils import (
    is_sitemap, is_txt, parse_sitemap, 
    smart_chunk_markdown, extract_section_info
)
from src.crawling.core import (
    crawl_markdown_file, crawl_batch, 
    crawl_recursive_internal_links
)
from src.utils import add_documents_to_postgres


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
