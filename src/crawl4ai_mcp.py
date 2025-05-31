"""
MCP server for web crawling with Crawl4AI.

This server provides tools to crawl websites using Crawl4AI, automatically detecting
the appropriate crawl method based on URL type (sitemap, txt file, or regular webpage).
"""
from mcp.server.fastmcp import FastMCP

# Import server configuration and context
from src.server.config import get_server_config
from src.server.context import crawl4ai_lifespan
from src.server.registry import register_all_tools


# Initialize FastMCP server with configuration
mcp = FastMCP(
    "mcp-crawl4ai-rag",
    description="MCP server for RAG and web crawling with Crawl4AI",
    lifespan=crawl4ai_lifespan,
    **get_server_config()
)

# Register all tools from modules
register_all_tools(mcp)


if __name__ == "__main__":
    # FastMCP automatically detects transport mode from environment variables
    # TRANSPORT=stdio for stdin/stdout or TRANSPORT=sse for HTTP server
    # Use mcp.run() directly - it internally handles the event loop
    mcp.run()
