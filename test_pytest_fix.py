#!/usr/bin/env python
"""
Quick test to verify the pytest fix works.
Run this to check if the module can be imported successfully.
"""
import os
import sys

# Set up test environment
print("Setting up test environment...")
test_env = {
    "PORT": "8051",
    "HOST": "0.0.0.0",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "OPENAI_API_KEY": "test_api_key"
}

for key, value in test_env.items():
    os.environ[key] = value

# Try importing the module
try:
    print("\nAttempting to import crawl4ai_mcp module...")
    from src.crawl4ai_mcp import mcp
    print("✅ SUCCESS: Module imported successfully!")
    print(f"   - MCP instance: {mcp}")
    print(f"   - Port: {mcp.port}")
    print(f"   - Host: {mcp.host}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Try running a simple pytest command
print("\n" + "="*50)
print("Now trying to run pytest...")
print("="*50)
os.system("python -m pytest tests/test_main_mcp_migration.py::TestMainMCPServerMigration::test_context_dataclass -v")
