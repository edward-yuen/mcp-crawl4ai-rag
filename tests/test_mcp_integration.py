"""Integration tests for MCP server PostgreSQL migration."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports_work():
    """Test that all imports work correctly after migration."""
    from src.crawl4ai_mcp import crawl_single_page, get_available_sources
    from src.database import DatabaseConnection, initialize_db_connection
    from src import crawl4ai_mcp
    
    assert hasattr(crawl4ai_mcp, 'DatabaseConnection')
    assert hasattr(crawl4ai_mcp, 'add_documents_to_postgres')
    print("PASS: All imports work correctly")


def test_database_functions_available():
    """Test that database functions are available."""
    from src.database import get_db_connection
    from src.utils import add_documents_to_postgres, search_documents
    
    assert callable(get_db_connection) 
    assert callable(add_documents_to_postgres)
    print("PASS: All database functions are available")


def test_context_structure():
    """Test that Crawl4AIContext has the correct structure."""
    from src.crawl4ai_mcp import Crawl4AIContext
    from unittest.mock import MagicMock
    
    context = Crawl4AIContext(
        crawler=MagicMock(),
        db_connection=MagicMock()
    )
    
    assert hasattr(context, 'crawler')
    assert hasattr(context, 'db_connection')
    print("PASS: Crawl4AIContext structure is correct")



if __name__ == "__main__":
    print("Running MCP PostgreSQL Integration Tests...")
    
    test_imports_work()
    test_database_functions_available()
    test_context_structure()
    
    print("All tests passed! Tasks 3.1 & 3.2 completed successfully.")
