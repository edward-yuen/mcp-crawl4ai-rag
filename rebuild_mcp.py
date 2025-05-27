#!/usr/bin/env python3
"""
Script to rebuild and test the MCP server with proper transport configuration.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def main():
    """Main function to rebuild the MCP server."""
    project_root = Path(__file__).parent
    
    print("Rebuilding MCP Crawl4AI RAG Server...")
    print("=" * 50)
    
    # Step 1: Stop existing containers
    print("\n1. Stopping existing containers...")
    run_command("docker-compose down", cwd=project_root)
    
    # Step 2: Remove existing image to force rebuild
    print("\n2. Removing existing image...")
    run_command("docker rmi mcp-crawl4ai-rag-mcp-crawl4ai-rag 2>/dev/null || true", cwd=project_root)
    
    # Step 3: Build new image
    print("\n3. Building new Docker image...")
    if not run_command("docker-compose build --no-cache", cwd=project_root):
        print("[ERROR] Failed to build Docker image")
        return False
    
    # Step 4: Start the container
    print("\n4. Starting the container...")
    if not run_command("docker-compose up -d", cwd=project_root):
        print("[ERROR] Failed to start container")
        return False    
    # Step 5: Check container status
    print("\n5. Checking container status...")
    run_command("docker-compose ps", cwd=project_root)
    
    # Step 6: Show logs
    print("\n6. Showing recent logs...")
    run_command("docker-compose logs --tail=20 mcp-crawl4ai-rag", cwd=project_root)
    
    print("\n[SUCCESS] MCP server rebuild complete!")
    print("\n[NEXT STEPS]:")
    print("1. The server is now configured for stdio transport (MCP clients)")
    print("2. Add the server to your Claude Desktop configuration")
    print("3. Test the connection")
    print("\n[CONFIGURATION] To switch to SSE transport (web clients):")
    print("   - Set TRANSPORT=sse in .env")
    print("   - Uncomment the web service in docker-compose.yml")
    print("   - Rebuild with this script")

if __name__ == "__main__":
    main()