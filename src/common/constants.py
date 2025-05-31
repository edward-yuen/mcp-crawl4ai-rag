"""
Constants and configuration values for the MCP server.

This module contains all the constants used throughout the application to ensure
consistency and make configuration changes easier.
"""

# Database Constants
DEFAULT_DB_MIN_CONNECTIONS = 10
DEFAULT_DB_MAX_CONNECTIONS = 20
DEFAULT_DB_MAX_QUERIES = 50000
DEFAULT_DB_MAX_INACTIVE_LIFETIME = 300.0  # seconds
DEFAULT_DB_RETRY_ATTEMPTS = 3
DEFAULT_DB_RETRY_DELAY = 1.0  # seconds

# Embedding Constants
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
MAX_EMBEDDING_BATCH_SIZE = 100

# Chunking Constants
DEFAULT_CHUNK_SIZE = 5000  # characters
MAX_CHUNK_SIZE = 10000
MIN_CHUNK_SIZE = 100
DEFAULT_CHUNK_OVERLAP = 200

# Crawling Constants
DEFAULT_MAX_CRAWL_DEPTH = 3
DEFAULT_MAX_CONCURRENT_CRAWLS = 10
DEFAULT_CRAWL_TIMEOUT = 30.0  # seconds
MAX_URL_LENGTH = 2048

# Search Constants
DEFAULT_SEARCH_LIMIT = 5
MAX_SEARCH_LIMIT = 100
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# Server Constants
DEFAULT_SERVER_HOST = "localhost"
DEFAULT_SERVER_PORT = 8765
LOG_FILE_NAME = "crawl4ai_mcp.log"

# Rate Limiting Constants
MAX_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_WINDOW = 60  # seconds
