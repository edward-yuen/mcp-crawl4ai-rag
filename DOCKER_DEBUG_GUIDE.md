# Running Debug Scripts with Docker MCP

## Option 1: Use the Docker Debug Script (Recommended)

Run the bash script I created:

```bash
# On Windows (Git Bash or WSL)
bash debug_docker.sh

# Or make it executable first
chmod +x debug_docker.sh
./debug_docker.sh
```

## Option 2: Run Python Debug Script Inside Container

Copy and run the debug script inside the MCP container:

```bash
# Copy the debug script into the container
docker cp debug_lightrag_connection.py mcp-crawl4ai-rag:/app/

# Run it inside the container
docker exec -it mcp-crawl4ai-rag python /app/debug_lightrag_connection.py
```

## Option 3: Test from Outside Container

If your PostgreSQL is accessible from the host (port 5432 exposed), you can modify the debug script to test from outside:

```bash
# First, check if PostgreSQL port is exposed
docker ps | grep postgres

# If you see "0.0.0.0:5432->5432/tcp", then run:
python debug_lightrag_connection.py
```

## Option 4: Interactive Container Shell

Get a shell inside the MCP container for debugging:

```bash
# Enter the container
docker exec -it mcp-crawl4ai-rag /bin/bash

# Inside the container, run Python interactively
python
```

Then test the connection:

```python
import asyncio
import asyncpg
import os

async def test():
    conn = await asyncpg.connect(
        host='postgres',  # Container name
        port=5432,
        database='lightrag',
        user='postgres',
        password='postgres'
    )
    print("Connected!")
    print(await conn.fetchval("SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex"))
    await conn.close()

asyncio.run(test())
```

## Common Docker Issues

### Container Not Running
```bash
# Start the container
docker-compose up -d mcp-crawl4ai-rag

# Or if using docker run
docker start mcp-crawl4ai-rag
```

### Network Issues
```bash
# List all networks
docker network ls

# Inspect the network
docker network inspect ai-lightrag_lightrag-network

# Manually connect containers
docker network connect ai-lightrag_lightrag-network postgres
docker network connect ai-lightrag_lightrag-network mcp-crawl4ai-rag
```

### View Container Logs
```bash
# Check MCP container logs
docker logs mcp-crawl4ai-rag --tail 50

# Check PostgreSQL logs
docker logs <postgres-container-name> --tail 50
```

## Quick Test Command

Run this one-liner to quickly test the connection:

```bash
docker exec mcp-crawl4ai-rag python -c "import asyncio; import asyncpg; asyncio.run(asyncpg.connect('postgresql://postgres:postgres@postgres:5432/lightrag').close()); print('✓ Connection successful!')"
```

If this works, your MCP server should be able to connect to the LightRAG knowledge graph!
