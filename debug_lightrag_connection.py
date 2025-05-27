#!/usr/bin/env python3
"""
Debug script to test PostgreSQL connection and check available data in both schemas.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_connection():
    """Test basic PostgreSQL connection."""
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    
    # Get connection parameters
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "lightrag")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print()
    
    # Try different host configurations
    hosts_to_try = [host, "localhost", "127.0.0.1", "postgres", "host.docker.internal"]
    
    for test_host in hosts_to_try:
        try:
            print(f"Trying connection with host: {test_host}...")
            conn = await asyncpg.connect(
                host=test_host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            
            # Test query
            version = await conn.fetchval("SELECT version()")
            print(f"✓ SUCCESS! Connected to PostgreSQL")
            print(f"  Version: {version[:50]}...")
            
            # Get available schemas
            schemas = await conn.fetch("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """)
            print(f"\nAvailable schemas:")
            for row in schemas:
                print(f"  - {row['schema_name']}")
            
            await conn.close()
            return test_host  # Return the working host
            
        except Exception as e:
            print(f"✗ Failed with {test_host}: {str(e)}")
    
    return None


async def check_crawl_schema(host: str):
    """Check the crawl schema for available data."""
    print("\n" + "=" * 60)
    print("Checking Crawl Schema")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "lightrag"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        
        # Check if crawl schema exists
        schema_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'crawl'
            )
        """)
        
        if not schema_exists:
            print("✗ Crawl schema does not exist!")
            await conn.close()
            return
        
        print("✓ Crawl schema exists")
        
        # Check crawled_pages table
        table_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'crawl' AND table_name = 'crawled_pages'
            )
        """)
        
        if not table_exists:
            print("✗ crawled_pages table does not exist!")
            await conn.close()
            return
        
        print("✓ crawled_pages table exists")
        
        # Get row count
        count = await conn.fetchval("SELECT COUNT(*) FROM crawl.crawled_pages")
        print(f"\nTotal documents in crawl.crawled_pages: {count}")
        
        if count > 0:
            # Get sample sources
            sources = await conn.fetch("""
                SELECT DISTINCT metadata->>'source' as source, COUNT(*) as doc_count
                FROM crawl.crawled_pages
                WHERE metadata->>'source' IS NOT NULL
                GROUP BY metadata->>'source'
                ORDER BY doc_count DESC
                LIMIT 5
            """)
            
            print("\nTop 5 sources:")
            for row in sources:
                print(f"  - {row['source']}: {row['doc_count']} documents")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error checking crawl schema: {e}")


async def check_lightrag_schema(host: str):
    """Check the chunk_entity_relation schema (LightRAG knowledge graph)."""
    print("\n" + "=" * 60)
    print("Checking LightRAG Knowledge Graph")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "lightrag"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        
        # Check if chunk_entity_relation schema exists
        schema_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'chunk_entity_relation'
            )
        """)
        
        if not schema_exists:
            print("✗ chunk_entity_relation schema does not exist!")
            await conn.close()
            return
        
        print("✓ chunk_entity_relation schema exists")
        
        # Check AGE graph
        try:
            await conn.execute("LOAD 'age'")
            await conn.execute("SET search_path = ag_catalog, '$user', public")
            
            graph_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM ag_catalog.ag_graph 
                    WHERE name = 'chunk_entity_relation'
                )
            """)
            
            if graph_exists:
                print("✓ AGE graph 'chunk_entity_relation' exists")
            else:
                print("✗ AGE graph 'chunk_entity_relation' does not exist")
        except Exception as e:
            print(f"✗ Error loading AGE extension: {e}")
        
        # Check vertex table
        vertex_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'chunk_entity_relation' 
                AND table_name = '_ag_label_vertex'
            )
        """)
        
        if not vertex_exists:
            print("✗ _ag_label_vertex table does not exist!")
            await conn.close()
            return
        
        print("✓ _ag_label_vertex table exists")
        
        # Get node count
        node_count = await conn.fetchval("""
            SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex
        """)
        print(f"\nTotal nodes in knowledge graph: {node_count}")
        
        if node_count > 0:
            # Get entity type distribution
            entity_types = await conn.fetch("""
                SELECT properties::json->>'entity_type' as entity_type, COUNT(*) as count
                FROM chunk_entity_relation._ag_label_vertex
                WHERE properties::json->>'entity_type' IS NOT NULL
                GROUP BY properties::json->>'entity_type'
                ORDER BY count DESC
                LIMIT 5
            """)
            
            print("\nTop 5 entity types:")
            for row in entity_types:
                print(f"  - {row['entity_type']}: {row['count']} entities")
            
            # Get sample entities
            samples = await conn.fetch("""
                SELECT 
                    properties::json->>'entity_id' as entity_id,
                    properties::json->>'entity_type' as entity_type,
                    LEFT(properties::json->>'description', 100) as description
                FROM chunk_entity_relation._ag_label_vertex
                WHERE properties::json->>'entity_id' IS NOT NULL
                LIMIT 3
            """)
            
            print("\nSample entities:")
            for i, row in enumerate(samples, 1):
                print(f"\n  {i}. {row['entity_id']} ({row['entity_type']})")
                print(f"     {row['description']}...")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Error checking LightRAG schema: {e}")


async def test_lightrag_search(host: str):
    """Test searching the LightRAG knowledge graph."""
    print("\n" + "=" * 60)
    print("Testing LightRAG Search")
    print("=" * 60)
    
    try:
        # Import the lightrag integration module
        from src.lightrag_integration import search_lightrag_documents
        from src.database import initialize_db_connection, close_db_connection
        
        # Update environment variable with working host
        os.environ["POSTGRES_HOST"] = host
        
        # Initialize database connection
        await initialize_db_connection()
        
        # Test search
        test_query = "fusion"
        print(f"\nSearching for: '{test_query}'")
        
        results = await search_lightrag_documents(
            query=test_query,
            match_count=3
        )
        
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['id']}")
            print(f"   Content: {result['content'][:150]}...")
            print(f"   Similarity: {result['similarity']}")
        
        # Close database connection
        await close_db_connection()
        
    except Exception as e:
        print(f"✗ Error testing LightRAG search: {e}")


async def main():
    """Run all debug tests."""
    print("PostgreSQL Connection Debug Script")
    print("==================================\n")
    
    # Test connection
    working_host = await test_connection()
    
    if not working_host:
        print("\n✗ FAILED: Could not connect to PostgreSQL!")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if it's in a Docker container")
        print("3. If using Docker, ensure the container is on the correct network")
        print("4. Update POSTGRES_HOST in .env file")
        return
    
    print(f"\n✓ Using host: {working_host}")
    
    # Check schemas
    await check_crawl_schema(working_host)
    await check_lightrag_schema(working_host)
    
    # Test search
    await test_lightrag_search(working_host)
    
    # Suggest .env update if needed
    current_host = os.getenv("POSTGRES_HOST", "localhost")
    if working_host != current_host:
        print("\n" + "=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        print(f"\nUpdate your .env file:")
        print(f"Change: POSTGRES_HOST={current_host}")
        print(f"To:     POSTGRES_HOST={working_host}")


if __name__ == "__main__":
    asyncio.run(main())
