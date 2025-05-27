#!/usr/bin/env python3
"""
Vector Index Optimization Script for Task 4.1
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.database import initialize_db_connection, close_db_connection, get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_current_indexes():
    """Analyze current vector indexes and their performance."""
    db = await get_db_connection()
    
    logger.info("Analyzing current vector indexes...")
    
    # Get existing indexes
    index_query = """
    SELECT i.relname as index_name, am.amname as index_type,
           pg_size_pretty(pg_relation_size(i.oid)) as size
    FROM pg_class i
    JOIN pg_index ix ON i.oid = ix.indexrelid
    JOIN pg_class t ON t.oid = ix.indrelid
    JOIN pg_am am ON i.relam = am.oid
    WHERE t.relname = 'crawled_pages' 
    AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'crawl')
    AND am.amname IN ('ivfflat', 'hnsw')
    """
    
    try:
        indexes = await db.fetch(index_query)
        logger.info(f"Found {len(indexes)} vector indexes")
        return indexes
    except Exception as e:
        logger.error(f"Error analyzing indexes: {e}")
        return []



async def get_table_statistics():
    """Get statistics about the crawled_pages table."""
    db = await get_db_connection()
    
    logger.info("Getting table statistics...")
    
    try:
        # Basic statistics
        stats = await db.fetchrow("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT url) as unique_urls,
                AVG(LENGTH(content)) as avg_content_length
            FROM crawl.crawled_pages
        """)
        
        if stats:
            logger.info(f"Table statistics:")
            logger.info(f"  - Total rows: {stats['total_rows']:,}")
            logger.info(f"  - Unique URLs: {stats['unique_urls']:,}")
            logger.info(f"  - Average content length: {stats['avg_content_length']:.0f} chars")
        
        return dict(stats) if stats else {}
        
    except Exception as e:
        logger.error(f"Error getting table statistics: {e}")
        return {}


async def create_optimal_vector_indexes():
    """Create optimal vector indexes based on table size and usage patterns."""
    db = await get_db_connection()
    
    # Get table statistics to determine optimal index parameters
    row_count = await db.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages")
    
    if row_count == 0:
        logger.warning("No data in table, skipping index creation")
        return []
    
    logger.info(f"Creating optimal indexes for {row_count:,} rows...")
    
    # Calculate optimal parameters
    # Rule of thumb: lists = sqrt(rows), but between 10 and 1000
    optimal_lists = max(10, min(1000, int(row_count ** 0.5)))
    
    created_indexes = []
    
    # Index configurations to create
    index_configs = [
        {
            "name": "idx_crawled_pages_embedding_cosine_optimized",
            "type": "ivfflat",
            "operator": "vector_cosine_ops",
            "lists": optimal_lists,
            "primary": True
        }
    ]


async def get_table_statistics():
    """Get statistics about the crawled_pages table."""
    db = await get_db_connection()
    
    logger.info("Getting table statistics...")
    
    try:
        # Basic statistics
        stats = await db.fetchrow("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT url) as unique_urls,
                AVG(LENGTH(content)) as avg_content_length
            FROM crawl.crawled_pages
        """)
        
        if stats:
            logger.info(f"Total rows: {stats['total_rows']:,}")
            logger.info(f"Unique URLs: {stats['unique_urls']:,}")
        
        return dict(stats) if stats else {}
        
    except Exception as e:
        logger.error(f"Error getting table statistics: {e}")
        return {}



async def create_optimal_vector_indexes():
    """Create optimal vector indexes based on table size and usage patterns."""
    db = await get_db_connection()
    
    # Get table statistics to determine optimal index parameters
    row_count = await db.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages")
    
    if row_count == 0:
        logger.warning("No data in table, skipping index creation")
        return []
    
    logger.info(f"Creating optimal indexes for {row_count:,} rows...")
    
    # Calculate optimal parameters
    # Rule of thumb: lists = sqrt(rows), but between 10 and 1000
    optimal_lists = max(10, min(1000, int(row_count ** 0.5)))
    
    created_indexes = []
    
    try:
        # Drop existing index if it exists
        await db.execute("DROP INDEX IF EXISTS crawl.idx_crawled_pages_embedding_cosine_optimized")
        
        # Create the new index
        create_sql = f"""
        CREATE INDEX CONCURRENTLY idx_crawled_pages_embedding_cosine_optimized 
        ON crawl.crawled_pages 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = {optimal_lists})
        """
        
        logger.info("Creating optimized cosine index...")
        await db.execute(create_sql)
        created_indexes.append("idx_crawled_pages_embedding_cosine_optimized")
        logger.info("✓ Successfully created optimized index")
        
    except Exception as e:
        logger.error(f"✗ Failed to create optimized index: {e}")
    
    return created_indexes



async def test_index_performance():
    """Test the performance of the created indexes."""
    db = await get_db_connection()
    
    logger.info("Testing index performance...")
    
    # Test vector search if we have data
    row_count = await db.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages WHERE embedding IS NOT NULL")
    
    if row_count > 0:
        # Test vector similarity search
        test_embedding = "[" + ",".join(["0.1"] * 1536) + "]"
        
        try:
            import time
            start_time = time.time()
            
            result = await db.fetchval(f"""
                SELECT COUNT(*) FROM crawl.match_crawled_pages(
                    '{test_embedding}'::vector,
                    10,
                    '{{}}'::jsonb
                )
            """)
            
            query_time = time.time() - start_time
            logger.info(f"Vector search test: {query_time:.3f}s ({result} results)")
            
        except Exception as e:
            logger.error(f"Error testing vector search: {e}")
    else:
        logger.warning("No vector data available for performance test")


async def optimize_vacuum_and_analyze():
    """Run VACUUM and ANALYZE to optimize table statistics."""
    db = await get_db_connection()
    
    logger.info("Running VACUUM and ANALYZE...")
    
    try:
        # VACUUM to reclaim space and update statistics
        await db.execute("VACUUM ANALYZE crawl.crawled_pages")
        logger.info("✓ VACUUM ANALYZE completed")
        
    except Exception as e:
        logger.error(f"Error during VACUUM/ANALYZE: {e}")



async def test_index_performance():
    """Test the performance of the created indexes."""
    db = await get_db_connection()
    
    logger.info("Testing index performance...")
    
    # Test vector search if we have data
    row_count = await db.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages WHERE embedding IS NOT NULL")
    
    if row_count > 0:
        # Test vector similarity search
        test_embedding = "[" + ",".join(["0.1"] * 1536) + "]"
        
        try:
            import time
            start_time = time.time()
            
            result = await db.fetchval(f"""
                SELECT COUNT(*) FROM crawl.match_crawled_pages(
                    '{test_embedding}'::vector,
                    10,
                    '{{}}'::jsonb
                )
            """)
            
            query_time = time.time() - start_time
            logger.info(f"Vector search test: {query_time:.3f}s ({result} results)")
            
        except Exception as e:
            logger.error(f"Error testing vector search: {e}")
    else:
        logger.warning("No vector data available for performance test")



async def optimize_vacuum_and_analyze():
    """Run VACUUM and ANALYZE to optimize table statistics."""
    db = await get_db_connection()
    
    logger.info("Running VACUUM and ANALYZE...")
    
    try:
        # VACUUM to reclaim space and update statistics
        await db.execute("VACUUM ANALYZE crawl.crawled_pages")
        logger.info("✓ VACUUM ANALYZE completed")
        
    except Exception as e:
        logger.error(f"Error during VACUUM/ANALYZE: {e}")


async def main():
    """Main optimization function."""
    try:
        # Initialize database connection
        await initialize_db_connection()
        
        logger.info("Starting vector index optimization...")
        
        # Step 1: Analyze current state
        await analyze_current_indexes()
        await get_table_statistics()
        
        # Step 2: Create optimal indexes
        vector_indexes = await create_optimal_vector_indexes()
        
        # Step 3: Optimize with VACUUM/ANALYZE
        await optimize_vacuum_and_analyze()
        
        # Step 4: Test performance
        await test_index_performance()
        
        logger.info("✓ Vector index optimization completed successfully!")
        
        if vector_indexes:
            logger.info(f"Created {len(vector_indexes)} vector indexes")
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise
    finally:
        await close_db_connection()


if __name__ == "__main__":
    asyncio.run(main())
