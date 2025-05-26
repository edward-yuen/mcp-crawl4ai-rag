<h1 align="center">Crawl4AI RAG MCP Server</h1>

<p align="center">
  <em>Web Crawling and RAG Capabilities for AI Agents and AI Coding Assistants</em>
</p>

A powerful implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) integrated with [Crawl4AI](https://crawl4ai.com) and PostgreSQL with pgvector for providing AI agents and AI coding assistants with advanced web crawling and RAG capabilities.

With this MCP server, you can <b>scrape anything</b> and then <b>use that knowledge anywhere</b> for RAG.

The primary goal is to bring this MCP server into [Archon](https://github.com/coleam00/Archon) as I evolve it to be more of a knowledge engine for AI coding assistants to build AI agents. This first version of the Crawl4AI/RAG MCP server will be improved upon greatly soon, especially making it more configurable so you can use different embedding models and run everything locally with Ollama.

## Overview

This MCP server provides tools that enable AI agents to crawl websites, store content in a PostgreSQL vector database with pgvector, and perform RAG over the crawled content. It follows the best practices for building MCP servers based on the [Mem0 MCP server template](https://github.com/coleam00/mcp-mem0/) I provided on my channel previously.

## Vision

The Crawl4AI RAG MCP server is just the beginning. Here's where we're headed:

1. **Integration with Archon**: Building this system directly into [Archon](https://github.com/coleam00/Archon) to create a comprehensive knowledge engine for AI coding assistants to build better AI agents.

2. **Multiple Embedding Models**: Expanding beyond OpenAI to support a variety of embedding models, including the ability to run everything locally with Ollama for complete control and privacy.

3. **Advanced RAG Strategies**: Implementing sophisticated retrieval techniques like contextual retrieval, late chunking, and others to move beyond basic "naive lookups" and significantly enhance the power and precision of the RAG system, especially as it integrates with Archon.

4. **Enhanced Chunking Strategy**: Implementing a Context 7-inspired chunking approach that focuses on examples and creates distinct, semantically meaningful sections for each chunk, improving retrieval precision.

5. **Performance Optimization**: Increasing crawling and indexing speed to make it more realistic to "quickly" index new documentation to then leverage it within the same prompt in an AI coding assistant.

## Features

- **Smart URL Detection**: Automatically detects and handles different URL types (regular webpages, sitemaps, text files)
- **Recursive Crawling**: Follows internal links to discover content
- **Parallel Processing**: Efficiently crawls multiple pages simultaneously
- **Content Chunking**: Intelligently splits content by headers and size for better processing
- **Vector Search**: Performs RAG over crawled content, optionally filtering by data source for precision
- **Source Retrieval**: Retrieve sources available for filtering to guide the RAG process
- **LightRAG Integration**: Query existing LightRAG schema data alongside crawled content
- **Multi-Schema Search**: Search across both crawl and lightrag schemas with unified results

## LightRAG Schema Integration

This MCP server can query data from both the `crawl` schema (where web-crawled data is stored) and the existing `lightrag` schema in your PostgreSQL database. This allows you to:

### Document Search
- Access pre-existing RAG data from other applications
- Combine web-crawled content with existing knowledge bases
- Search across multiple data sources simultaneously

The integration automatically detects common LightRAG table structures:
- `lightrag.documents` table with `content`, `metadata`, and `embedding` columns
- `lightrag.embeddings` table with `text`, `metadata`, and `embedding` columns

### Knowledge Graph (Apache AGE)
- Query the LightRAG knowledge graph using Cypher queries
- Explore entities and their relationships
- Find paths between entities
- Search entities by semantic similarity
- Analyze community structures
- Get comprehensive graph statistics

The knowledge graph integration requires Apache AGE extension and supports:
- Entity nodes (Person, Organization, Concept, etc.)
- Relationship edges (WORKS_AT, KNOWS, RELATED_TO, etc.)
- Community hierarchies
- Entity and relationship embeddings for semantic search

See `example_lightrag_schema.sql` for document schema and `lightrag_knowledge_graph_schema.sql` for knowledge graph schema structures.

## Tools

The server provides fourteen comprehensive web crawling, search, and knowledge graph tools:

### Crawl Schema Tools
1. **`crawl_single_page`**: Quickly crawl a single web page and store its content in the vector database
2. **`smart_crawl_url`**: Intelligently crawl a full website based on the type of URL provided (sitemap, llms-full.txt, or a regular webpage that needs to be crawled recursively)
3. **`get_available_sources`**: Get a list of all available sources (domains) in the database
4. **`perform_rag_query`**: Search for relevant content using semantic search with optional source filtering

### LightRAG Document Search Tools
5. **`query_lightrag_schema`**: Query documents from the existing LightRAG schema with optional collection filtering
6. **`get_lightrag_info`**: Get information about the LightRAG schema structure and available collections
7. **`multi_schema_search`**: Search across both crawl and lightrag schemas simultaneously with optional result combining

### LightRAG Knowledge Graph Tools (using Apache AGE)
8. **`query_graph`**: Execute Cypher queries directly on the knowledge graph
9. **`get_graph_entities`**: Retrieve entities from the knowledge graph with optional type filtering
10. **`get_entity_graph`**: Get the relationship graph for a specific entity up to a specified depth
11. **`search_graph_entities`**: Search for entities using semantic similarity on their embeddings
12. **`find_entity_path`**: Find paths between two entities in the knowledge graph
13. **`get_graph_communities`**: Retrieve community structures identified by LightRAG
14. **`get_graph_stats`**: Get statistics about the knowledge graph structure

## Prerequisites

- [Docker/Docker Desktop](https://www.docker.com/products/docker-desktop/) if running the MCP server as a container (recommended)
- [Python 3.12+](https://www.python.org/downloads/) if running the MCP server directly through uv
- [PostgreSQL](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector) extension (database for RAG)
- [Apache AGE](https://age.apache.org/) extension (optional, for LightRAG knowledge graph functionality)
- [OpenAI API key](https://platform.openai.com/api-keys) (for generating embeddings)

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/coleam00/mcp-crawl4ai-rag.git
   cd mcp-crawl4ai-rag
   ```

2. Build the Docker image:
   ```bash
   docker build -t mcp/crawl4ai-rag --build-arg PORT=8051 .
   ```

3. Create a `.env` file based on the configuration section below

### Using uv directly (no Docker)

1. Clone this repository:
   ```bash
   git clone https://github.com/coleam00/mcp-crawl4ai-rag.git
   cd mcp-crawl4ai-rag
   ```

2. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv
   .venv\Scripts\activate
   # on Mac/Linux: source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   uv pip install -e .
   crawl4ai-setup
   ```

5. Create a `.env` file based on the configuration section below

## Database Setup

Before running the server, you need to set up the PostgreSQL database with the pgvector extension and crawl schema:

1. Ensure you have PostgreSQL running with the pgvector extension installed

2. Run the schema setup script against your database:
   ```bash
   psql -h localhost -U postgres -d lightrag -f setup_crawl_schema.sql
   ```

3. Verify the schema was created successfully by checking that the `crawl.crawled_pages` table exists

## Configuration

Create a `.env` file in the project root with the following variables:

```
# MCP Server Configuration
HOST=0.0.0.0
PORT=8051
TRANSPORT=sse

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key

# PostgreSQL Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=lightrag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Running the Server

### Using Docker

```bash
docker run --env-file .env -p 8051:8051 mcp/crawl4ai-rag
```

### Using Python

```bash
uv run src/crawl4ai_mcp.py
```

The server will start and listen on the configured host and port.

## Integration with MCP Clients

### SSE Configuration

Once you have the server running with SSE transport, you can connect to it using this configuration:

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "transport": "sse",
      "url": "http://localhost:8051/sse"
    }
  }
}
```

> **Note for Windsurf users**: Use `serverUrl` instead of `url` in your configuration:
> ```json
> {
>   "mcpServers": {
>     "crawl4ai-rag": {
>       "transport": "sse",
>       "serverUrl": "http://localhost:8051/sse"
>     }
>   }
> }
> ```
>
> **Note for Docker users**: Use `host.docker.internal` instead of `localhost` if your client is running in a different container. This will apply if you are using this MCP server within n8n!

### Stdio Configuration

Add this server to your MCP configuration for Claude Desktop, Windsurf, or any other MCP client:

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "python",
      "args": ["path/to/crawl4ai-mcp/src/crawl4ai_mcp.py"],
      "env": {
        "TRANSPORT": "stdio",
        "OPENAI_API_KEY": "your_openai_api_key",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "lightrag",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres"
      }
    }
  }
}
```

### Docker with Stdio Configuration

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "-e", "OPENAI_API_KEY", 
               "-e", "POSTGRES_HOST", 
               "-e", "POSTGRES_PORT", 
               "-e", "POSTGRES_DB",
               "-e", "POSTGRES_USER",
               "-e", "POSTGRES_PASSWORD",
               "mcp/crawl4ai"],
      "env": {
        "TRANSPORT": "stdio",
        "OPENAI_API_KEY": "your_openai_api_key",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "lightrag",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres"
      }
    }
  }
}
```

## Building Your Own Server

This implementation provides a foundation for building more complex MCP servers with web crawling capabilities. To build your own:

1. Add your own tools by creating methods with the `@mcp.tool()` decorator
2. Create your own lifespan function to add your own dependencies
3. Modify the `utils.py` file for any helper functions you need
4. Extend the crawling capabilities by adding more specialized crawlers

# Example usage documentation for these new tools:
"""
## Usage Examples for Enhanced Knowledge Graph Tools

### 1. Build Knowledge Graph from Crawled Data
```python
# Process the last 50 crawled documents and extract entities/relationships
await build_knowledge_graph(ctx, limit=50)
```

### 2. Analyze Graph Structure
```python
# Get insights about graph patterns and structure
await analyze_graph_patterns(ctx)
```

### 3. Find Relationship Suggestions
```python
# Get suggestions for new relationships for "John Doe"
await suggest_entity_relationships(ctx, entity_name="John Doe")
```

### 4. Enhanced Graph Querying
```python
# Query with parameters
await enhanced_graph_query(ctx, 
    cypher_query="MATCH (p:Person {name: $name})-[r]->(o) RETURN p, r, o",
    parameters='{"name": "John Doe"}'
)
```

### 5. Check Graph Health
```python
# Verify AGE installation and graph status
await check_graph_health(ctx)
```

### 6. Explore Entity Networks
```python
# Explore 2-hop neighborhood around an entity
await explore_entity_neighborhood(ctx, 
    entity_name="OpenAI", 
    depth=2, 
    limit=15
)
```

These tools provide a complete knowledge graph experience combining traditional
RAG document search with graph-based entity and relationship exploration.