"""
PostgreSQL database connection management module for Crawl4AI MCP server.

This module provides connection pooling, health checks, retry logic, and
environment variable validation for PostgreSQL connections.
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager
import asyncpg
from asyncpg.pool import Pool

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuration for PostgreSQL database connection."""
    
    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        
        # Validate required environment variables
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate that all required environment variables are set.
        
        Raises:
            ValueError: If any required environment variable is missing
        """
        missing = []
        if not self.host:
            missing.append("POSTGRES_HOST")
        if not self.database:
            missing.append("POSTGRES_DB")
        if not self.user:
            missing.append("POSTGRES_USER")
        if not self.password:
            missing.append("POSTGRES_PASSWORD")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @property
    def connection_string(self) -> str:
        """
        Get the PostgreSQL connection string.
        
        Returns:
            str: PostgreSQL connection string
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """Manages PostgreSQL connection pooling with health checks and retry logic."""
    
    def __init__(
        self, 
        config: Optional[DatabaseConfig] = None,
        min_size: int = 10,
        max_size: int = 20,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize database connection manager.
        
        Args:
            config: Database configuration (creates new one if None)
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
            max_queries: Maximum number of queries per connection before reconnect
            max_inactive_connection_lifetime: Maximum idle time for connections
            retry_attempts: Number of connection retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.config = config or DatabaseConfig()
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self._pool: Optional[Pool] = None
    
    async def initialize(self) -> None:
        """
        Initialize the connection pool with retry logic.
        
        Raises:
            asyncpg.PostgresError: If connection fails after all retries
        """
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Attempting to create connection pool (attempt {attempt + 1}/{self.retry_attempts})")
                
                self._pool = await asyncpg.create_pool(
                    self.config.connection_string,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    max_queries=self.max_queries,
                    max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
                    command_timeout=60
                )
                
                # Test the connection
                await self.health_check()
                logger.info("Connection pool created successfully")
                return
                
            except Exception as e:
                logger.error(f"Failed to create connection pool (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Connection pool closed")
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the database connection.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self._pool:
            logger.error("Connection pool not initialized")
            return False
        
        try:
            async with self._pool.acquire() as connection:
                # Simple query to check connection
                result = await connection.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """
        Execute a query that doesn't return rows.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            str: Query result status
            
        Raises:
            asyncpg.PostgresError: If query execution fails
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> list:
        """
        Execute a query and fetch all rows.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            list: List of Record objects
            
        Raises:
            asyncpg.PostgresError: If query execution fails
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """
        Execute a query and fetch a single row.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Optional[asyncpg.Record]: First row or None
            
        Raises:
            asyncpg.PostgresError: If query execution fails
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            return await connection.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, timeout: Optional[float] = None) -> Any:
        """
        Execute a query and fetch a single value.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Any: First column of first row
            
        Raises:
            asyncpg.PostgresError: If query execution fails
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, *args, timeout=timeout)
    
    async def execute_many(self, query: str, args_list: list, *, timeout: Optional[float] = None) -> None:
        """
        Execute the same query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            args_list: List of parameter tuples
            timeout: Query timeout in seconds
            
        Raises:
            asyncpg.PostgresError: If query execution fails
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            await connection.executemany(query, args_list, timeout=timeout)
    
    @asynccontextmanager
    async def transaction(self):
        """
        Create a transaction context manager.
        
        Usage:
            async with db.transaction():
                await db.execute("INSERT INTO ...")
                await db.execute("UPDATE ...")
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                # Temporarily replace pool methods with connection methods
                original_methods = {
                    'execute': self.execute,
                    'fetch': self.fetch,
                    'fetchrow': self.fetchrow,
                    'fetchval': self.fetchval,
                }
                
                # Reason: We need to use the same connection for all queries in a transaction
                self.execute = connection.execute
                self.fetch = connection.fetch
                self.fetchrow = connection.fetchrow
                self.fetchval = connection.fetchval
                
                try:
                    yield
                finally:
                    # Restore original methods
                    for method_name, method in original_methods.items():
                        setattr(self, method_name, method)
    
    async def create_schema_if_not_exists(self) -> None:
        """
        Create the crawl schema and required tables if they don't exist.
        
        This method reads and executes the SQL from setup_crawl_schema.sql.
        """
        sql_file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "setup_crawl_schema.sql"
        )
        
        try:
            with open(sql_file_path, 'r') as f:
                sql_script = f.read()
            
            # Split SQL script handling dollar-quoted functions properly
            statements = []
            current_statement = ""
            in_dollar_quotes = False
            dollar_tag = ""
            
            lines = sql_script.split('\n')
            for line in lines:
                # Skip empty lines and comments at the start of lines
                if not line.strip() or line.strip().startswith('--'):
                    continue
                
                current_statement += line + '\n'
                
                # Check for dollar quoting
                if not in_dollar_quotes:
                    # Look for start of dollar quoting
                    if '$$' in line:
                        dollar_pos = line.find('$$')
                        if dollar_pos >= 0:
                            # Find the tag (if any) before $$
                            before_dollar = line[:dollar_pos].strip()
                            if before_dollar and not before_dollar.endswith('$'):
                                dollar_tag = before_dollar.split()[-1] if before_dollar.split() else ""
                            else:
                                dollar_tag = ""
                            in_dollar_quotes = True
                else:
                    # Look for end of dollar quoting
                    end_pattern = f'$${dollar_tag}' if dollar_tag else '$$'
                    if end_pattern in line:
                        in_dollar_quotes = False
                        dollar_tag = ""
                
                # If not in dollar quotes and line ends with semicolon, it's end of statement
                if not in_dollar_quotes and line.strip().endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""
            
            # Add any remaining statement
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        await self.execute(statement)
                        logger.debug(f"Executed statement {i+1}/{len(statements)}")
                    except Exception as e:
                        # Log warnings for non-critical errors (like extension already exists)
                        error_msg = str(e).lower()
                        if any(phrase in error_msg for phrase in ["already exists", "does not exist"]):
                            logger.debug(f"Skipping statement (already exists): {e}")
                        else:
                            logger.warning(f"Error executing statement {i+1}: {e}")
                            logger.debug(f"Statement was: {statement[:200]}...")
            
            logger.info("Database schema created/verified successfully")
            
        except FileNotFoundError:
            logger.error(f"SQL file not found: {sql_file_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise


# Global connection instance
_db_connection: Optional[DatabaseConnection] = None


async def get_db_connection() -> DatabaseConnection:
    """
    Get the global database connection instance.
    
    Returns:
        DatabaseConnection: The database connection instance
        
    Raises:
        RuntimeError: If connection is not initialized
    """
    global _db_connection
    if not _db_connection:
        raise RuntimeError("Database connection not initialized. Call initialize_db_connection() first.")
    return _db_connection


async def initialize_db_connection(**kwargs) -> DatabaseConnection:
    """
    Initialize the global database connection.
    
    Args:
        **kwargs: Arguments to pass to DatabaseConnection constructor
        
    Returns:
        DatabaseConnection: The initialized database connection
    """
    global _db_connection
    _db_connection = DatabaseConnection(**kwargs)
    await _db_connection.initialize()
    return _db_connection


async def close_db_connection() -> None:
    """Close the global database connection."""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
