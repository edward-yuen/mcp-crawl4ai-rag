#!/usr/bin/env python3
"""
Vector Search Function Verification for Task 4.1
"""
import asyncio
import logging
import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.database import initialize_db_connection, close_db_connection, get_db_connection
from src.utils import search_documents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_match_function_exists():
    """Test that the match_crawled_pages function exists and is callable."""
    db = await get_db_connection()
    
    logger.info("Testing match_crawled_pages function existence...")
    
    try:
        func_exists = await db.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_proc p 
                JOIN pg_namespace n ON p.pronamespace = n.oid 
                WHERE n.nspname = 'crawl' 
                AND p.proname = 'match_crawled_pages'
            )
        """)
        
        if func_exists:
            logger.info("✓ match_crawled_pages function exists")
            return True
        else:
            logger.error("✗ match_crawled_pages function not found")
            return False
            
    except Exception as e:
        logger.error(f"Error checking function existence: {e}")
        return False



async def test_basic_vector_search():
    """Test basic vector search functionality."""
    db = await get_db_connection()
    
    logger.info("Testing basic vector search...")
    
    try:
        # Create a test embedding (1536 dimensions for OpenAI)
        test_embedding = "[" + ",".join([str(0.1 * i % 1) for i in range(1536)]) + "]"
        
        # Test the match function directly
        start_time = time.time()
        results = await db.fetch("""
            SELECT * FROM crawl.match_crawled_pages(
                $1::vector,
                5,
                '{}'::jsonb
            )
        """, test_embedding)
        query_time = time.time() - start_time
        
        logger.info(f"✓ Direct function call: {len(results)} results in {query_time:.3f}s")
        
        # Test via utils search_documents function
        start_time = time.time()
        utils_results = await search_documents("test query", match_count=5)
        utils_time = time.time() - start_time
        
        logger.info(f"✓ Utils search function: {len(utils_results)} results in {utils_time:.3f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Vector search test failed: {e}")
        return False



async def test_vector_search_performance():
    """Test vector search performance with multiple queries."""
    logger.info("Testing vector search performance...")
    
    test_queries = [
        "Python programming language",
        "machine learning algorithms", 
        "web development frameworks",
        "database management systems",
        "artificial intelligence research"
    ]
    
    query_times = []
    total_results = 0
    
    try:
        for i, query in enumerate(test_queries):
            start_time = time.time()
            results = await search_documents(query, match_count=10)
            query_time = time.time() - start_time
            
            query_times.append(query_time)
            total_results += len(results)
            
            logger.info(f"Query {i+1}: {query_time:.3f}s ({len(results)} results)")
        
        avg_time = sum(query_times) / len(query_times)
        
        logger.info(f"✓ Performance test completed:")
        logger.info(f"  Average query time: {avg_time:.3f}s")
        logger.info(f"  Total results: {total_results}")
        logger.info(f"  Queries per second: {1/avg_time:.1f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance test failed: {e}")
        return False



async def main():
    """Main test function."""
    try:
        # Initialize database connection
        await initialize_db_connection()
        
        logger.info("="*50)
        logger.info("VECTOR SEARCH FUNCTION VERIFICATION")
        logger.info("="*50)
        
        # Run all tests
        tests = [
            ("Function Existence", test_match_function_exists()),
            ("Basic Vector Search", test_basic_vector_search()),
            ("Performance Test", test_vector_search_performance())
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_coro in tests:
            logger.info(f"\n--- {test_name} ---")
            result = await test_coro
            if result:
                passed += 1
        
        logger.info("="*50)
        logger.info(f"RESULTS: {passed}/{total} tests passed")
        logger.info("="*50)
        
        if passed == total:
            logger.info("✓ All vector search tests passed!")
        else:
            logger.warning(f"✗ {total - passed} tests failed")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise
    finally:
        await close_db_connection()


if __name__ == "__main__":
    asyncio.run(main())
