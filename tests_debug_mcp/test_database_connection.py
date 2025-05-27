"""
Test script for the database connection module.
"""
import asyncio
import os
from src.database import (
    DatabaseConfig, 
    DatabaseConnection, 
    initialize_db_connection, 
    get_db_connection,
    close_db_connection
)


async def test_database_connection():
    """Test database connection functionality."""
    print("Testing database connection module...")
    
    # Test 1: Environment variable validation
    print("\n1. Testing environment variable validation...")
    try:
        config = DatabaseConfig()
        print(f"✓ Configuration loaded successfully")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Database: {config.database}")
        print(f"  User: {config.user}")
    except ValueError as e:
        print(f"✗ Configuration validation failed: {e}")
        return
    
    # Test 2: Connection pool initialization
    print("\n2. Testing connection pool initialization...")
    try:
        db = await initialize_db_connection(
            min_size=2,
            max_size=5,
            retry_attempts=3,
            retry_delay=1.0
        )
        print("✓ Connection pool initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize connection pool: {e}")
        return
    
    # Test 3: Health check
    print("\n3. Testing health check...")
    try:
        is_healthy = await db.health_check()
        if is_healthy:
            print("✓ Database connection is healthy")
        else:
            print("✗ Database connection is not healthy")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    
    # Test 4: Basic query execution
    print("\n4. Testing basic query execution...")
    try:
        result = await db.fetchval("SELECT version()")
        print(f"✓ PostgreSQL version: {result}")
    except Exception as e:
        print(f"✗ Query execution failed: {e}")
    
    # Test 5: Check if pgvector extension is available
    print("\n5. Checking pgvector extension...")
    try:
        result = await db.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
        )
        if result > 0:
            print("✓ pgvector extension is installed")
        else:
            print("✗ pgvector extension is not installed")
            print("  Run: CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception as e:
        print(f"✗ Failed to check pgvector: {e}")
    
    # Test 6: Schema creation
    print("\n6. Testing schema creation...")
    try:
        await db.create_schema_if_not_exists()
        print("✓ Schema created/verified successfully")
        
        # Verify the crawl schema exists
        schema_exists = await db.fetchval(
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'crawl'"
        )
        if schema_exists:
            print("✓ 'crawl' schema exists")
        
        # Verify the crawled_pages table exists
        table_exists = await db.fetchval(
            """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'crawl' AND table_name = 'crawled_pages'
            """
        )
        if table_exists:
            print("✓ 'crawl.crawled_pages' table exists")
        
    except Exception as e:
        print(f"✗ Schema creation failed: {e}")
    
    # Test 7: Transaction support
    print("\n7. Testing transaction support...")
    try:
        async with db.transaction():
            # This is just a test transaction that doesn't modify data
            count = await db.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages")
            print(f"✓ Transaction support works (current row count: {count})")
    except Exception as e:
        print(f"✗ Transaction test failed: {e}")
    
    # Test 8: Get global connection
    print("\n8. Testing global connection access...")
    try:
        global_db = await get_db_connection()
        if global_db == db:
            print("✓ Global connection access works correctly")
        else:
            print("✗ Global connection mismatch")
    except Exception as e:
        print(f"✗ Failed to get global connection: {e}")
    
    # Clean up
    print("\n9. Closing connection pool...")
    try:
        await close_db_connection()
        print("✓ Connection pool closed successfully")
    except Exception as e:
        print(f"✗ Failed to close connection pool: {e}")
    
    print("\n✅ Database connection module tests completed!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the tests
    asyncio.run(test_database_connection())
