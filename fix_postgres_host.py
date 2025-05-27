#!/usr/bin/env python3
"""
Quick fix script to update PostgreSQL host in .env file based on your setup.
"""
import os
import shutil
from pathlib import Path


def update_env_file():
    """Update the .env file with the correct PostgreSQL host."""
    env_path = Path(".env")
    env_backup_path = Path(".env.backup")
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return
    
    # Create backup
    shutil.copy(env_path, env_backup_path)
    print(f"✓ Created backup: {env_backup_path}")
    
    # Read current content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Ask user about their setup
    print("\nHow are you running the MCP server?")
    print("1. Locally (not in Docker)")
    print("2. In Docker container")
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        # Running locally - need to connect to localhost
        new_host = "localhost"
        print("\n✓ Setting POSTGRES_HOST=localhost for local development")
    elif choice == "2":
        # Running in Docker - connect to postgres service
        new_host = "postgres"
        print("\n✓ Setting POSTGRES_HOST=postgres for Docker networking")
    else:
        print("❌ Invalid choice!")
        return
    
    # Update the lines
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("POSTGRES_HOST="):
            new_lines.append(f"POSTGRES_HOST={new_host}\n")
            updated = True
            print(f"✓ Updated: POSTGRES_HOST={new_host}")
        else:
            new_lines.append(line)
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    if updated:
        print("\n✓ Successfully updated .env file!")
        print(f"  Old file backed up to: {env_backup_path}")
    else:
        print("\n⚠️  POSTGRES_HOST not found in .env file")
        print("  You may need to add it manually")
    
    # Additional setup tips
    print("\n" + "="*60)
    print("SETUP TIPS:")
    print("="*60)
    
    if choice == "1":
        print("\nFor local development:")
        print("1. Make sure PostgreSQL is accessible on localhost:5432")
        print("2. If using Docker PostgreSQL, ensure port 5432 is exposed")
        print("3. Check that the 'lightrag' database exists")
        print("4. Run: python debug_lightrag_connection.py to test")
    else:
        print("\nFor Docker deployment:")
        print("1. Ensure both containers are on the same network")
        print("2. The network should be: ai-lightrag_lightrag-network")
        print("3. PostgreSQL container should be named 'postgres'")
        print("4. Run: docker-compose up mcp-crawl4ai-rag")


if __name__ == "__main__":
    update_env_file()
