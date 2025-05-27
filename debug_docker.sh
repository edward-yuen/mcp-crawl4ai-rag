#!/bin/bash
# Debug script for Docker deployment

echo "==================================="
echo "Docker MCP Debug Script"
echo "==================================="
echo ""

# Check if containers are running
echo "1. Checking Docker containers..."
echo "--------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}" | grep -E "NAME|postgres|mcp-crawl4ai-rag|lightrag"
echo ""

# Check network
echo "2. Checking Docker network..."
echo "-----------------------------"
docker network inspect ai-lightrag_lightrag-network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' 2>/dev/null || echo "Network not found!"
echo ""

# Test connection from MCP container
echo "3. Testing PostgreSQL connection from MCP container..."
echo "------------------------------------------------------"
docker exec mcp-crawl4ai-rag python -c "
import asyncio
import asyncpg
import os

async def test():
    try:
        # Try with environment variables
        host = os.getenv('POSTGRES_HOST', 'postgres')
        print(f'Trying to connect to PostgreSQL at {host}...')
        
        conn = await asyncpg.connect(
            host=host,
            port=5432,
            database='lightrag',
            user='postgres',
            password='postgres'
        )
        
        version = await conn.fetchval('SELECT version()')
        print(f'✓ Connected successfully!')
        print(f'  PostgreSQL version: {version[:50]}...')
        
        # Check schemas
        schemas = await conn.fetch('''
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('crawl', 'chunk_entity_relation')
        ''')
        
        print(f'\nAvailable schemas:')
        for s in schemas:
            print(f'  - {s[\"schema_name\"]}')
        
        # Check data
        crawl_count = await conn.fetchval('SELECT COUNT(*) FROM crawl.crawled_pages')
        print(f'\nCrawl schema: {crawl_count} documents')
        
        kg_count = await conn.fetchval('SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex')
        print(f'Knowledge graph: {kg_count} nodes')
        
        await conn.close()
        
    except Exception as e:
        print(f'✗ Connection failed: {e}')

asyncio.run(test())
" 2>&1

echo ""
echo "4. Quick fixes if connection fails:"
echo "-----------------------------------"
echo "a) Ensure PostgreSQL container is running:"
echo "   docker start <postgres-container-name>"
echo ""
echo "b) Connect containers to the same network:"
echo "   docker network connect ai-lightrag_lightrag-network <postgres-container-name>"
echo "   docker network connect ai-lightrag_lightrag-network mcp-crawl4ai-rag"
echo ""
echo "c) Rebuild and restart MCP container:"
echo "   docker-compose up --build mcp-crawl4ai-rag"
