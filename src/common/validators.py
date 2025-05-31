"""
Input validation utilities for the MCP server.

This module provides validation functions for various inputs to ensure data
integrity and prevent errors.
"""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from src.common.exceptions import (
    InvalidURLError, InvalidParameterError, MissingParameterError
)
from src.common.constants import (
    MAX_URL_LENGTH, MAX_SEARCH_LIMIT, DEFAULT_SEARCH_LIMIT,
    MAX_CHUNK_SIZE, MIN_CHUNK_SIZE
)


def validate_url(url: str) -> str:
    """
    Validate and normalize a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Normalized URL
        
    Raises:
        InvalidURLError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError("URL must be a non-empty string")
    
    if len(url) > MAX_URL_LENGTH:
        raise InvalidURLError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")
    
    # Parse URL to validate structure
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            raise InvalidURLError("URL must include a scheme (http:// or https://)")
        if parsed.scheme not in ['http', 'https']:
            raise InvalidURLError("URL scheme must be http or https")
        if not parsed.netloc:
            raise InvalidURLError("URL must include a domain")
    except Exception as e:
        raise InvalidURLError(f"Invalid URL format: {str(e)}")
    
    return url.strip()


def validate_search_params(
    query: str,
    limit: Optional[int] = None,
    source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate search parameters.
    
    Args:
        query: Search query
        limit: Maximum number of results
        source: Optional source filter
        
    Returns:
        Dictionary of validated parameters
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    if not query or not isinstance(query, str):
        raise InvalidParameterError("Query must be a non-empty string")
    
    validated = {"query": query.strip()}
    
    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            raise InvalidParameterError("Limit must be a positive integer")
        if limit > MAX_SEARCH_LIMIT:
            raise InvalidParameterError(f"Limit cannot exceed {MAX_SEARCH_LIMIT}")
        validated["limit"] = limit
    else:
        validated["limit"] = DEFAULT_SEARCH_LIMIT
    
    if source is not None:
        if not isinstance(source, str):
            raise InvalidParameterError("Source must be a string")
        validated["source"] = source.strip()
    
    return validated


def validate_chunk_size(chunk_size: int) -> int:
    """
    Validate chunk size parameter.
    
    Args:
        chunk_size: Chunk size in characters
        
    Returns:
        Validated chunk size
        
    Raises:
        InvalidParameterError: If chunk size is invalid
    """
    if not isinstance(chunk_size, int):
        raise InvalidParameterError("Chunk size must be an integer")
    
    if chunk_size < MIN_CHUNK_SIZE:
        raise InvalidParameterError(f"Chunk size must be at least {MIN_CHUNK_SIZE} characters")
    
    if chunk_size > MAX_CHUNK_SIZE:
        raise InvalidParameterError(f"Chunk size cannot exceed {MAX_CHUNK_SIZE} characters")
    
    return chunk_size


def validate_environment_variables(required_vars: List[str]) -> Dict[str, str]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary of environment variable values
        
    Raises:
        MissingParameterError: If any required variable is missing
    """
    import os
    
    missing = []
    env_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            env_vars[var] = value
    
    if missing:
        raise MissingParameterError(f"Missing required environment variables: {', '.join(missing)}")
    
    return env_vars


def validate_crawl_depth(depth: int) -> int:
    """
    Validate crawl depth parameter.
    
    Args:
        depth: Maximum crawl depth
        
    Returns:
        Validated depth
        
    Raises:
        InvalidParameterError: If depth is invalid
    """
    if not isinstance(depth, int) or depth < 0:
        raise InvalidParameterError("Crawl depth must be a non-negative integer")
    
    if depth > 10:  # Reasonable maximum to prevent infinite crawls
        raise InvalidParameterError("Crawl depth cannot exceed 10")
    
    return depth


def validate_cypher_query(query: str) -> str:
    """
    Basic validation for Cypher queries.
    
    Args:
        query: Cypher query string
        
    Returns:
        Validated query
        
    Raises:
        InvalidParameterError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise InvalidParameterError("Cypher query must be a non-empty string")
    
    # Basic safety checks
    dangerous_keywords = ['DELETE', 'REMOVE', 'DROP', 'DETACH']
    query_upper = query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise InvalidParameterError(f"Query contains potentially dangerous operation: {keyword}")
    
    return query.strip()
