"""
Script to fix pytest setup issues for mcp-crawl4ai-rag project.
This script will help install missing dependencies and verify the setup.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command, shell=True):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Success: {command}")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Failed: {command}")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"✗ Exception running {command}: {e}")
        return False

def main():
    print("=== Fixing pytest setup for mcp-crawl4ai-rag ===\n")
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check Python version
    print(f"1. Python version: {sys.version}")
    if sys.version_info < (3, 12):
        print("Warning: Project requires Python 3.12+, but you have an older version.")
        print("The project might still work, but consider upgrading Python.")
    
    print("\n2. Installing dependencies...")
    
    # Try to install with uv first (if available)
    if run_command("uv --version"):
        print("\n   Using uv to install dependencies...")
        if run_command("uv sync"):
            print("   ✓ Dependencies installed with uv")
        else:
            print("   ✗ uv sync failed, trying uv pip install...")
            run_command("uv pip install -e .")
    else:
        # Fallback to pip
        print("\n   uv not found, using pip...")
        print("   Installing from pyproject.toml...")
        
        # Install the package in editable mode
        if run_command(f"{sys.executable} -m pip install -e ."):
            print("   ✓ Package installed in editable mode")
        else:
            # Try installing individual dependencies
            print("   Trying to install individual dependencies...")
            deps = [
                "crawl4ai==0.6.2",
                "mcp==1.7.1", 
                "asyncpg==0.30.0",
                "openai==1.71.0",
                "python-dotenv==1.0.0"  # Note: corrected package name
            ]
            for dep in deps:
                run_command(f"{sys.executable} -m pip install {dep}")
    
    print("\n3. Verifying imports...")
    
    # Test basic imports
    test_imports = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

try:
    import mcp
    print("   ✓ mcp module imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import mcp: {e}")

try:
    import openai  
    print("   ✓ openai module imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import openai: {e}")

try:
    import asyncpg
    print("   ✓ asyncpg module imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import asyncpg: {e}")

try:
    from src.database import get_db_connection
    print("   ✓ src.database imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import src.database: {e}")

try:
    from src.utils import create_embedding
    print("   ✓ src.utils imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import src.utils: {e}")
"""
    
    run_command(f"{sys.executable} -c \"{test_imports}\"")
    
    print("\n4. Running pytest to check if issues are resolved...")
    run_command("pytest tests/ -v --tb=short")
    
    print("\n=== Setup complete ===")
    print("\nIf you still see errors:")
    print("1. Make sure you have PostgreSQL running with the correct schema")
    print("2. Check your .env file has the correct database credentials")
    print("3. Try running: python -m pytest tests/ -v")

if __name__ == "__main__":
    main()
