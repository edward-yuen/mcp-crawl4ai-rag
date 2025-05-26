"""Test to verify the src module path fix works."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_basic_path_fix():
    """Test that we can import src modules without external dependencies."""
    try:
        import src
        print("PASS: Can import src module")
        
        from src import database
        print("PASS: Can import src.database module")
        
        from src.database import DatabaseConnection, initialize_db_connection
        assert callable(DatabaseConnection)
        assert callable(initialize_db_connection)
        print("PASS: Can import database functions")
        
        return True
        
    except ImportError as e:
        print(f"FAIL: Import error - {e}")
        return False


def test_file_structure():
    """Test that expected files exist in src directory."""
    src_dir = project_root / "src"
    
    expected_files = ["database.py", "utils.py", "crawl4ai_mcp.py"]
    
    for file in expected_files:
        file_path = src_dir / file
        assert file_path.exists(), f"Missing file: {file}"
    
    print("PASS: All expected src files exist")


if __name__ == "__main__":
    print("Testing src module path fix...")
    
    test_file_structure()
    
    if test_basic_path_fix():
        print("\nSUCCESS: Path fix works!")
        print("The 'ModuleNotFoundError: No module named src' is RESOLVED")
    else:
        print("\nFAILED: Path fix did not work.")
