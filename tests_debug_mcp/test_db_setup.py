#!/usr/bin/env python3
"""
Database setup validation for mcp-crawl4ai-rag project.

This script validates that PostgreSQL is properly configured with pgvector
and creates the necessary schema for the crawl4ai integration tests.

Usage:
    python test_db_setup.py
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import DatabaseConnection, DatabaseConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def validate_database_setup():
    """
    Validate that the database is properly set up for integration tests.
    
    This includes:
    1. Testing database connection
    2. Checking pgvector extension
    3. Creating schema and tables
    4. Running basic queries
    """
    # Set default environment variables if not already set
    default_env = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432", 
        "POSTGRES_DB": "postgres",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres"
    }
    
    for key, value in default_env.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"Set default {key}={value}")
    
    db_conn = None
    try:
        # Step 1: Test basic connection
        logger.info("Step 1: Testing database connection...")
        config = DatabaseConfig()
        db_conn = DatabaseConnection(config)
        await db_conn.initialize()
        
        # Step 2: Test health check
        logger.info("Step 2: Testing health check...")
        health_ok = await db_conn.health_check()
        if not health_ok:
            raise Exception("Database health check failed")
        logger.info("✓ Database connection healthy")
        
        # Step 3: Check PostgreSQL version
        logger.info("Step 3: Checking PostgreSQL version...")
        version = await db_conn.fetchval("SELECT version()")
        logger.info(f"✓ PostgreSQL version: {version}")
        
        # Step 4: Check if pgvector extension is available
        logger.info("Step 4: Checking pgvector extension...")
        try:
            await db_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("✓ pgvector extension is available")
        except Exception as e:
            logger.error(f"✗ pgvector extension not available: {e}")
            logger.error("Please install pgvector extension in your PostgreSQL database")
            return False
        
        # Step 5: Test vector type
        logger.info("Step 5: Testing vector type...")
        try:
            result = await db_conn.fetchval("SELECT '[1,2,3]'::vector")
            logger.info("✓ Vector type works correctly")
        except Exception as e:
            logger.error(f"✗ Vector type not working: {e}")
            return False
        
        # Step 6: Create schema and tables
        logger.info("Step 6: Creating schema and tables...")
        await db_conn.create_schema_if_not_exists()
        logger.info("✓ Schema and tables created/verified")
        
        # Step 7: Test table exists and has correct structure
        logger.info("Step 7: Verifying table structure...")
        result = await db_conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'crawl' 
            AND table_name = 'crawled_pages'
            ORDER BY ordinal_position
        """)
        
        if not result:
            logger.error("✗ crawl.crawled_pages table not found")
            return False
        
        logger.info("✓ Table structure:")
        for row in result:
            logger.info(f"  - {row['column_name']}: {row['data_type']} ({'nullable' if row['is_nullable'] == 'YES' else 'not null'})")
        
        # Step 8: Test the search function
        logger.info("Step 8: Testing search function...")
        try:
            test_embedding = [0.1] * 1536  # Mock embedding
            # Convert to proper vector format for PostgreSQL
            search_result = await db_conn.fetch(
                "SELECT * FROM crawl.match_crawled_pages($1::vector, 1)",
                str(test_embedding)  # Convert list to string representation
            )
            logger.info("✓ Search function works correctly")
        except Exception as e:
            logger.error(f"✗ Search function error: {e}")
            return False
        
        # Step 9: Test basic CRUD operations
        logger.info("Step 9: Testing basic CRUD operations...")
        try:
            # Insert test record
            test_embedding = [0.1] * 1536
            await db_conn.execute(
                """INSERT INTO crawl.crawled_pages 
                   (url, chunk_number, content, metadata, embedding) 
                   VALUES ($1, $2, $3, $4, $5::vector)""",
                "http://test-validation.com", 0, "Test content", 
                '{"test": true}', str(test_embedding)
            )
            
            # Query test record
            result = await db_conn.fetchrow(
                "SELECT * FROM crawl.crawled_pages WHERE url = $1",
                "http://test-validation.com"
            )
            if not result:
                raise Exception("Test record not found after insert")
            
            # Delete test record
            await db_conn.execute(
                "DELETE FROM crawl.crawled_pages WHERE url = $1",
                "http://test-validation.com"
            )
            
            logger.info("✓ Basic CRUD operations work correctly")
        except Exception as e:
            logger.error(f"✗ CRUD operations error: {e}")
            return False
        
        logger.info("\nDatabase setup validation completed successfully!")
        logger.info("Your database is ready for integration tests.")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database setup validation failed: {e}")
        return False
    finally:
        if db_conn:
            await db_conn.close()


def main():
    """Main function to run database validation."""
    print("Validating database setup for mcp-crawl4ai-rag integration tests...")
    print("=" * 70)
    
    success = asyncio.run(validate_database_setup())
    
    if success:
        print("\nAll checks passed! You can now run integration tests.")
        print("\nTo run integration tests:")
        print("  pytest -m integration tests/test_utils.py::TestIntegration::test_full_workflow")
        return 0
    else:
        print("\nSome checks failed. Please fix the issues above before running integration tests.")
        print("\nCommon solutions:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Install pgvector extension: https://github.com/pgvector/pgvector")
        print("  3. Check your database connection settings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
