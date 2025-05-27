# LightRAG MCP Connection Troubleshooting Guide

## Common Issues and Solutions

### 1. Connection Refused Error
**Symptom**: `connection refused` error when trying to connect to PostgreSQL

**Solutions**:
- If running MCP locally and PostgreSQL in Docker:
  - Set `POSTGRES_HOST=localhost` in .env
  - Ensure PostgreSQL container exposes port 5432: `-p 5432:5432`
  
- If running both in Docker:
  - Set `POSTGRES_HOST=postgres` in .env
  - Ensure both containers are on the same network
  - Check network name matches: `ai-lightrag_lightrag-network`

### 2. Database Not Found
**Symptom**: `database "lightrag" does not exist`

**Solution**:
- Ensure the LightRAG PostgreSQL container is running
- Check if you have the correct database name in .env

### 3. No Data in LightRAG
**Symptom**: Tools return empty results

**Solution**:
- The LightRAG knowledge graph needs to be populated first
- Check if `chunk_entity_relation._ag_label_vertex` table has data
- Run the debug script to verify data exists

### 4. Network Issues (Docker)
**Symptom**: `could not translate host name "postgres" to address`

**Solution**:
```bash
# Check if the network exists
docker network ls | grep lightrag

# If not, create it
docker network create ai-lightrag_lightrag-network

# Ensure your PostgreSQL container is on this network
docker network connect ai-lightrag_lightrag-network <postgres-container-name>
```

### 5. AGE Extension Not Loaded
**Symptom**: `extension "age" does not exist`

**Solution**:
- The LightRAG PostgreSQL image should have AGE pre-installed
- If using a custom PostgreSQL, install AGE extension

## Quick Diagnostic Commands

```bash
# Test PostgreSQL connection from command line
psql -h localhost -p 5432 -U postgres -d lightrag -c "SELECT 1"

# Check Docker containers
docker ps | grep -E "postgres|lightrag"

# Check Docker networks
docker network inspect ai-lightrag_lightrag-network

# Test from inside MCP container (if using Docker)
docker exec -it mcp-crawl4ai-rag python -c "
import asyncio
import asyncpg
asyncio.run(asyncpg.connect('postgresql://postgres:postgres@postgres:5432/lightrag'))
"
```

## Environment Variable Reference

For **local development** (MCP running on host):
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=lightrag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

For **Docker deployment** (MCP in container):
```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=lightrag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```
