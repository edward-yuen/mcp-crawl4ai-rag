"""
Crawling strategies for different types of content.

This module contains strategy-specific implementations for:
- Sitemap crawling
- Text file crawling  
- Recursive webpage crawling with internal link following
"""
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, urljoin, urldefrag
from xml.etree import ElementTree
import requests
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from src.crawling.core import crawl_batch, crawl_markdown_file
from src.crawling.utils import is_sitemap, is_txt, parse_sitemap, extract_internal_links


async def crawl_sitemap_strategy(crawler: AsyncWebCrawler, url: str, max_concurrent: int = 10) -> Dict[str, Any]:
    """
    Crawl all URLs found in a sitemap.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL of the sitemap
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        Dictionary with crawl results and metadata
    """
    # Parse sitemap to get all URLs
    urls = parse_sitemap(url)
    
    if not urls:
        return {
            "crawl_type": "sitemap",
            "urls_found": 0,
            "pages_crawled": 0,
            "content": []
        }
    
    # Batch crawl all URLs from sitemap
    results = await crawl_batch(crawler, urls, max_concurrent)
    
    return {
        "crawl_type": "sitemap",
        "urls_found": len(urls),
        "pages_crawled": len(results),
        "content": results
    }


async def crawl_text_file_strategy(crawler: AsyncWebCrawler, url: str) -> Dict[str, Any]:
    """
    Crawl a text or markdown file directly.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL of the text file
        
    Returns:
        Dictionary with crawl results and metadata
    """
    results = await crawl_markdown_file(crawler, url)
    
    return {
        "crawl_type": "text_file",
        "urls_found": 1,
        "pages_crawled": len(results),
        "content": results
    }


async def crawl_recursive_strategy(
    crawler: AsyncWebCrawler, 
    url: str, 
    max_depth: int = 3,
    max_concurrent: int = 10
) -> Dict[str, Any]:
    """
    Recursively crawl a webpage and follow internal links.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL to start crawling from
        max_depth: Maximum recursion depth
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        Dictionary with crawl results and metadata
    """
    results = await crawl_recursive_internal_links(crawler, [url], max_depth, max_concurrent)
    
    return {
        "crawl_type": "webpage",
        "urls_found": len(results),
        "pages_crawled": len(results),
        "max_depth": max_depth,
        "content": results
    }


async def crawl_recursive_internal_links(
    crawler: AsyncWebCrawler,
    start_urls: List[str],
    max_depth: int = 3,
    max_concurrent: int = 10
) -> List[Dict[str, Any]]:
    """
    Recursively crawl internal links from start URLs up to a maximum depth.
    
    Args:
        crawler: AsyncWebCrawler instance
        start_urls: Initial URLs to start crawling from
        max_depth: Maximum recursion depth
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    crawled_urls: Set[str] = set()
    to_crawl: List[tuple[str, int]] = [(url, 0) for url in start_urls]
    results: List[Dict[str, Any]] = []
    
    while to_crawl:
        # Get current batch of URLs at same depth
        current_depth = to_crawl[0][1]
        current_batch = []
        
        while to_crawl and to_crawl[0][1] == current_depth:
            url, depth = to_crawl.pop(0)
            if url not in crawled_urls:
                current_batch.append(url)
                crawled_urls.add(url)
        
        if not current_batch:
            continue
            
        # Crawl current batch
        batch_results = await crawl_batch(crawler, current_batch, max_concurrent)
        results.extend(batch_results)
        
        # Extract internal links if not at max depth
        if current_depth < max_depth:
            for result in batch_results:
                if 'url' in result and 'markdown' in result:
                    internal_links = extract_internal_links(result['url'], result['markdown'])
                    for link in internal_links:
                        if link not in crawled_urls:
                            to_crawl.append((link, current_depth + 1))
    
    return results


async def smart_crawl_strategy(
    crawler: AsyncWebCrawler,
    url: str,
    max_depth: int = 3,
    max_concurrent: int = 10
) -> Dict[str, Any]:
    """
    Intelligently select and execute the appropriate crawling strategy based on URL type.
    
    Args:
        crawler: AsyncWebCrawler instance
        url: URL to crawl
        max_depth: Maximum recursion depth for webpage crawling
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        Dictionary with crawl results and metadata
    """
    # Detect URL type and select appropriate strategy
    if is_sitemap(url):
        return await crawl_sitemap_strategy(crawler, url, max_concurrent)
    elif is_txt(url):
        return await crawl_text_file_strategy(crawler, url)
    else:
        return await crawl_recursive_strategy(crawler, url, max_depth, max_concurrent)
