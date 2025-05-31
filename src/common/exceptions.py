"""
Custom exceptions for the MCP server.

This module defines all custom exceptions used throughout the application for
better error handling and debugging.
"""


class MCPServerError(Exception):
    """Base exception for all MCP server errors."""
    pass


# Database Exceptions
class DatabaseError(MCPServerError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when unable to connect to the database."""
    pass


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    pass


class DatabasePoolError(DatabaseError):
    """Raised when there's an issue with the connection pool."""
    pass


# Crawling Exceptions
class CrawlingError(MCPServerError):
    """Base exception for crawling-related errors."""
    pass


class InvalidURLError(CrawlingError):
    """Raised when an invalid URL is provided."""
    pass


class CrawlTimeoutError(CrawlingError):
    """Raised when a crawl operation times out."""
    pass


class CrawlDepthExceededError(CrawlingError):
    """Raised when maximum crawl depth is exceeded."""
    pass


# Validation Exceptions
class ValidationError(MCPServerError):
    """Base exception for validation errors."""
    pass


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""
    pass


class InvalidParameterError(ValidationError):
    """Raised when a parameter has an invalid value."""
    pass


# API Exceptions
class APIError(MCPServerError):
    """Base exception for API-related errors."""
    pass


class EmbeddingAPIError(APIError):
    """Raised when embedding API call fails."""
    pass


class RateLimitExceededError(APIError):
    """Raised when API rate limit is exceeded."""
    pass
