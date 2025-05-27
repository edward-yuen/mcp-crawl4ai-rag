# Claude Desktop MCP Configuration

This file contains the configuration needed to connect Claude Desktop to your MCP server.

## Configuration Location

Add this configuration to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Configuration for Docker Container (stdio transport)

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "docker",
      "args": [
        "exec", "-i", "mcp-crawl4ai-rag", 
        "python", "src/crawl4ai_mcp.py"
      ],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

## Configuration for Local Python Installation

If you're running the server locally without Docker:

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "python",
      "args": ["C:/Users/shopb/Documents/AI/mcp-crawl4ai-rag/src/crawl4ai_mcp.py"],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```
## Troubleshooting

1. **Container not running**: Make sure the Docker container is running:
   ```bash
   docker-compose ps
   ```

2. **Connection issues**: Check the container logs:
   ```bash
   docker-compose logs mcp-crawl4ai-rag
   ```

3. **Transport mismatch**: Ensure TRANSPORT=stdio in .env file

4. **Restart Claude Desktop** after making configuration changes