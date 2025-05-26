#!/usr/bin/env python3
"""
Integration test runner for mcp-crawl4ai-rag project.

This script runs integration tests with proper database setup validation.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def main():
    """Main test runner function."""
    os.chdir(Path(__file__).parent)
    
    print("mcp-crawl4ai-rag Integration Test Runner")
    print("=" * 50)
    
    # Step 1: Validate database setup
    print("\n1. Validating database setup...")
    if not run_command("python test_db_setup.py"):
        print("Database setup validation failed!")
        print("Please fix database issues before running integration tests.")
        return 1
    
    # Step 2: Run unit tests first
    print("\n2. Running unit tests...")
    if not run_command("pytest tests/test_utils.py::TestEmbeddingFunctions -v"):
        print("Unit tests failed!")
        return 1
    
    if not run_command("pytest tests/test_utils.py::TestDatabaseOperations -v"):
        print("Database unit tests failed!")
        return 1
    
    # Step 3: Run integration tests
    print("\n3. Running integration tests...")
    if not run_command("pytest tests/test_utils.py::TestIntegration::test_full_workflow -v -s"):
        print("Integration test failed!")
        return 1
    
    print("\nAll tests passed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
