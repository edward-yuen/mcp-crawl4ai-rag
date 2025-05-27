"""Quick test to verify pytest fixes."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing imports after fixes...")

try:
    # Test fixed imports
    from src.lightrag_integration import search_lightrag_documents
    print("✓ src.lightrag_integration imports correctly")
    
    from src.crawl4ai_mcp import Crawl4AIContext
    print("✓ src.crawl4ai_mcp imports correctly")
    
    from src.utils import create_embedding
    print("✓ src.utils imports correctly")
    
    print("\nAll imports successful! Pytest should now work.")
    
except ImportError as e:
    print(f"✗ Import still failing: {e}")
    print("\nMake sure to install dependencies:")
    print("  pip install -e .")
    print("or")
    print("  uv sync")
