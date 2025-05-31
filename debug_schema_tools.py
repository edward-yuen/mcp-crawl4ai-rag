#!/usr/bin/env python3
"""
Debug script to understand the schema confusion and locate options strategy data.

This script will:
1. Check what's in the knowledge graph (chunk_entity_relation schema)
2. Check if there are regular document tables (lightrag.documents, etc.)
3. Search for "options" related data across all schemas
"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
import json

# Load environment variables
load_dotenv()


async def debug_schemas():
    """Main debug function to check all schemas and find options data."""
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    
    print("=" * 80)
    print("SCHEMA DEBUGGING REPORT")
    print("=" * 80)
    
    try:
        # 1. Check what schemas exist
        print("\n1. AVAILABLE SCHEMAS:")
        schemas = await conn.fetch("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        for schema in schemas:
            print(f"  - {schema['schema_name']}")
        
        # 2. Check tables in lightrag schema (if exists)
        print("\n2. TABLES IN 'lightrag' SCHEMA:")
        lightrag_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'lightrag'
            ORDER BY table_name
        """)
        if lightrag_tables:
            for table in lightrag_tables:
                print(f"  - lightrag.{table['table_name']}")
                
                # Get row count
                count = await conn.fetchval(f"SELECT COUNT(*) FROM lightrag.{table['table_name']}")
                print(f"    Rows: {count}")
        else:
            print("  No 'lightrag' schema found or no tables in it")
        
        # 3. Check chunk_entity_relation schema (knowledge graph)
        print("\n3. KNOWLEDGE GRAPH SCHEMA (chunk_entity_relation):")
        kg_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'chunk_entity_relation'
            ORDER BY table_name
        """)
        if kg_tables:
            for table in kg_tables:
                print(f"  - chunk_entity_relation.{table['table_name']}")
                
                # Special handling for vertex table
                if table['table_name'] == '_ag_label_vertex':
                    vertex_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex"
                    )
                    print(f"    Total vertices: {vertex_count}")
                    
                    # Get entity types
                    entity_types = await conn.fetch("""
                        SELECT DISTINCT properties->>'entity_type' as entity_type, COUNT(*) as count
                        FROM chunk_entity_relation._ag_label_vertex
                        WHERE properties->>'entity_type' IS NOT NULL
                        GROUP BY properties->>'entity_type'
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    if entity_types:
                        print("    Entity types:")
                        for et in entity_types:
                            print(f"      - {et['entity_type']}: {et['count']} entities")
        else:
            print("  No 'chunk_entity_relation' schema found")
        
        # 4. Search for "options" related data in knowledge graph
        print("\n4. SEARCHING FOR 'OPTIONS' IN KNOWLEDGE GRAPH:")
        options_entities = await conn.fetch("""
            SELECT 
                properties->>'entity_id' as entity_id,
                properties->>'description' as description,
                properties->>'entity_type' as entity_type,
                properties->>'file_path' as file_path
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties->>'description' ILIKE '%option%'
               OR properties->>'entity_id' ILIKE '%option%'
            LIMIT 10
        """)
        if options_entities:
            print(f"  Found {len(options_entities)} entities related to 'options':")
            for entity in options_entities:
                print(f"\n  Entity ID: {entity['entity_id']}")
                print(f"  Type: {entity['entity_type']}")
                print(f"  Description: {entity['description'][:100]}...")
                print(f"  File Path: {entity['file_path']}")
        else:
            print("  No entities found containing 'option' in knowledge graph")
        
        # 5. Search for "options" in crawl schema
        print("\n5. SEARCHING FOR 'OPTIONS' IN CRAWL SCHEMA:")
        # Check if crawl schema exists
        crawl_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'crawl'
            )
        """)
        
        if crawl_exists:
            options_pages = await conn.fetch("""
                SELECT 
                    id,
                    url,
                    title,
                    content_preview
                FROM crawl.crawled_pages
                WHERE content ILIKE '%option%strategy%'
                   OR title ILIKE '%option%'
                LIMIT 5
            """)
            if options_pages:
                print(f"  Found {len(options_pages)} pages related to 'options':")
                for page in options_pages:
                    print(f"\n  Page ID: {page['id']}")
                    print(f"  URL: {page['url']}")
                    print(f"  Title: {page['title']}")
                    print(f"  Preview: {page['content_preview'][:100]}...")
            else:
                print("  No pages found containing 'option' in crawl schema")
        else:
            print("  No 'crawl' schema found")
        
        # 6. Check if there are any document-style tables in lightrag schema
        print("\n6. CHECKING FOR DOCUMENT TABLES IN LIGHTRAG:")
        doc_tables = ['documents', 'embeddings', 'pages', 'chunks']
        for table_name in doc_tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'lightrag' 
                    AND table_name = '{table_name}'
                )
            """)
            if exists:
                print(f"\n  Found table: lightrag.{table_name}")
                # Get sample data
                sample = await conn.fetch(f"""
                    SELECT * FROM lightrag.{table_name} 
                    LIMIT 1
                """)
                if sample:
                    print(f"  Columns: {list(sample[0].keys())}")
                
                # Search for options
                text_columns = ['content', 'text', 'description', 'chunk']
                for col in text_columns:
                    col_exists = await conn.fetchval(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = 'lightrag' 
                            AND table_name = '{table_name}'
                            AND column_name = '{col}'
                        )
                    """)
                    if col_exists:
                        options_count = await conn.fetchval(f"""
                            SELECT COUNT(*) FROM lightrag.{table_name}
                            WHERE {col} ILIKE '%option%'
                        """)
                        if options_count > 0:
                            print(f"  Found {options_count} records with 'option' in {col} column")
                            break
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print("""
The 'query_lightrag_schema' tool is searching the knowledge graph (chunk_entity_relation schema),
NOT regular document tables. This is why it might not find expected document content.

To find your options strategy data:
1. If it's in the knowledge graph, use the graph-specific tools
2. If it's web-crawled content, use 'perform_rag_query' on the crawl schema
3. If it's in separate document tables, a new tool may be needed
""")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(debug_schemas())
