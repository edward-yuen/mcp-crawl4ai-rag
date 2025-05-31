"""
Response formatting utilities for the MCP server.

This module provides standardized response formatting for all MCP tools to ensure
consistent JSON responses across the entire API.
"""
import json
from typing import Any, Dict, Optional, List, Union
from datetime import datetime


def format_success_response(
    data: Dict[str, Any],
    message: Optional[str] = None,
    indent: int = 2
) -> str:
    """
    Format a successful response with consistent structure.
    
    Args:
        data: The response data dictionary
        message: Optional success message
        indent: JSON indentation level (default: 2)
        
    Returns:
        JSON formatted string with success=True and provided data
    """
    response = {"success": True}
    
    if message:
        response["message"] = message
        
    # Merge the data into the response
    response.update(data)
    
    return json.dumps(response, indent=indent)


def format_error_response(
    error: Union[str, Exception],
    context: Optional[Dict[str, Any]] = None,
    indent: int = 2
) -> str:
    """
    Format an error response with consistent structure.
    
    Args:
        error: The error message or exception
        context: Optional context data (e.g., query, url, etc.)
        indent: JSON indentation level (default: 2)
        
    Returns:
        JSON formatted string with success=False and error details
    """
    response = {
        "success": False,
        "error": str(error)
    }
    
    # Add any context data if provided
    if context:
        response.update(context)
    
    return json.dumps(response, indent=indent)


def format_crawl_response(
    url: str,
    success: bool,
    pages_crawled: Optional[int] = None,
    chunks_created: Optional[int] = None,
    error: Optional[str] = None,
    processing_time: Optional[float] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format a crawling operation response.
    
    Args:
        url: The URL that was crawled
        success: Whether the crawl was successful
        pages_crawled: Number of pages crawled
        chunks_created: Number of chunks created
        error: Error message if unsuccessful
        processing_time: Time taken in seconds
        additional_data: Any additional data to include
        
    Returns:
        JSON formatted string
    """
    data = {"url": url}
    
    if success:
        if pages_crawled is not None:
            data["pages_crawled"] = pages_crawled
        if chunks_created is not None:
            data["chunks_created"] = chunks_created
        if processing_time is not None:
            data["processing_time_seconds"] = round(processing_time, 2)
        if additional_data:
            data.update(additional_data)
        return format_success_response(data)
    else:
        return format_error_response(error or "Unknown error", context=data)


def format_search_response(
    query: str,
    results: List[Dict[str, Any]],
    total_matches: Optional[int] = None,
    source_filter: Optional[str] = None,
    processing_time: Optional[float] = None
) -> str:
    """
    Format a search/RAG query response.
    
    Args:
        query: The search query
        results: List of search results
        total_matches: Total number of matches found
        source_filter: Source filter applied (if any)
        processing_time: Time taken in seconds
        
    Returns:
        JSON formatted string
    """
    data = {
        "query": query,
        "results": results,
        "result_count": len(results)
    }
    
    if total_matches is not None:
        data["total_matches"] = total_matches
    if source_filter:
        data["source_filter"] = source_filter
    if processing_time is not None:
        data["processing_time_seconds"] = round(processing_time, 2)
    
    return format_success_response(data)


def format_graph_response(
    operation: str,
    result: Any,
    entity_count: Optional[int] = None,
    relationship_count: Optional[int] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format a knowledge graph operation response.
    
    Args:
        operation: The graph operation performed
        result: The operation result
        entity_count: Number of entities involved
        relationship_count: Number of relationships involved
        additional_data: Any additional data to include
        
    Returns:
        JSON formatted string
    """
    data = {
        "operation": operation,
        "result": result
    }
    
    if entity_count is not None:
        data["entity_count"] = entity_count
    if relationship_count is not None:
        data["relationship_count"] = relationship_count
    if additional_data:
        data.update(additional_data)
    
    return format_success_response(data)


def format_list_response(
    item_type: str,
    items: List[Any],
    total_count: Optional[int] = None
) -> str:
    """
    Format a response containing a list of items.
    
    Args:
        item_type: Type of items (e.g., "sources", "entities", "collections")
        items: List of items
        total_count: Total count if different from len(items)
        
    Returns:
        JSON formatted string
    """
    data = {
        item_type: items,
        f"{item_type}_count": total_count or len(items)
    }
    
    return format_success_response(data)


def format_batch_response(
    operation: str,
    total_items: int,
    successful_items: int,
    failed_items: int,
    errors: Optional[List[str]] = None,
    processing_time: Optional[float] = None
) -> str:
    """
    Format a batch operation response.
    
    Args:
        operation: The batch operation performed
        total_items: Total number of items processed
        successful_items: Number of successfully processed items
        failed_items: Number of failed items
        errors: List of error messages
        processing_time: Time taken in seconds
        
    Returns:
        JSON formatted string
    """
    data = {
        "operation": operation,
        "total_items": total_items,
        "successful_items": successful_items,
        "failed_items": failed_items,
        "success_rate": round(successful_items / total_items * 100, 2) if total_items > 0 else 0
    }
    
    if errors:
        data["errors"] = errors[:10]  # Limit to first 10 errors
        if len(errors) > 10:
            data["errors_truncated"] = True
            data["total_errors"] = len(errors)
    
    if processing_time is not None:
        data["processing_time_seconds"] = round(processing_time, 2)
    
    return format_success_response(data)


def sanitize_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize response data to ensure JSON serialization compatibility.
    
    Args:
        data: The data dictionary to sanitize
        
    Returns:
        Sanitized data dictionary
    """
    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        elif isinstance(value, dict):
            return {k: _sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_sanitize_value(item) for item in value]
        elif isinstance(value, (set, tuple)):
            return [_sanitize_value(item) for item in value]
        elif value is None or isinstance(value, (str, int, float, bool)):
            return value
        else:
            return str(value)
    
    return {key: _sanitize_value(value) for key, value in data.items()}
