"""
Test script to verify the pytest environment setup is working correctly.
"""
import os
import sys
from pathlib import Path

# Add the tests directory to the path so we can import conftest
sys.path.insert(0, str(Path(__file__).parent / "tests"))

# Import conftest first to set up all the mocks
import conftest

# Now try importing the actual module
try:
    print("Attempting to import crawl4ai_mcp...")
    from src.crawl4ai_mcp import mcp
    print("✓ Successfully imported crawl4ai_mcp")
    print(f"  mcp instance: {mcp}")
    print(f"  mcp.port: {mcp.port}")
    print(f"  mcp.host: {mcp.host}")
except Exception as e:
    print(f"✗ Failed to import crawl4ai_mcp: {e}")
    import traceback
    traceback.print_exc()

# Check environment variables
print("\nEnvironment variables:")
for key in ["PORT", "HOST", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "OPENAI_API_KEY"]:
    value = os.environ.get(key, "NOT SET")
    print(f"  {key}: {value}")

print("\nTest setup verification complete.")
