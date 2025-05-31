"""
Example of how to refactor existing code to use the new response formatting utilities.

This demonstrates how the response formatting in the tools can be simplified.
"""

# BEFORE: Current approach with manual JSON formatting
def old_get_available_sources():
    try:
        sources = ["example.com", "test.org"]
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


# AFTER: Using the new response formatting utilities
from src.models.responses import format_list_response, format_error_response

def new_get_available_sources():
    try:
        sources = ["example.com", "test.org"]
        return format_list_response("sources", sources)
    except Exception as e:
        return format_error_response(e)


# Example for crawling responses
def old_crawl_response(url, success, pages_crawled, chunks_created, error=None):
    if success:
        return json.dumps({
            "success": True,
            "url": url,
            "pages_crawled": pages_crawled,
            "chunks_created": chunks_created
        }, indent=2)
    else:
        return json.dumps({
            "success": False,
            "url": url,
            "error": str(error)
        }, indent=2)


# Using the new utility
from src.models.responses import format_crawl_response

def new_crawl_response(url, success, pages_crawled, chunks_created, error=None):
    return format_crawl_response(
        url=url,
        success=success,
        pages_crawled=pages_crawled,
        chunks_created=chunks_created,
        error=error
    )


# Example for search responses
def old_search_response(query, results, source=None):
    try:
        return json.dumps({
            "success": True,
            "query": query,
            "source": source,
            "results": results,
            "result_count": len(results)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "query": query,
            "error": str(e)
        }, indent=2)


# Using the new utility
from src.models.responses import format_search_response, format_error_response

def new_search_response(query, results, source=None):
    try:
        return format_search_response(
            query=query,
            results=results,
            source_filter=source
        )
    except Exception as e:
        return format_error_response(e, context={"query": query})
