"""
Test runner script that ensures proper environment setup before running tests.

This script sets up the environment variables and then runs pytest.
"""
import os
import sys
import subprocess

# Set up environment variables BEFORE running pytest
env_vars = {
    "PORT": "8051",
    "HOST": "0.0.0.0",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "OPENAI_API_KEY": "test_api_key"
}

# Set environment variables
for key, value in env_vars.items():
    os.environ[key] = value

# Run pytest with the remaining command line arguments
if __name__ == "__main__":
    # Get any additional arguments passed to this script
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest"] + args
    
    # Run pytest
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    # Exit with the same code as pytest
    sys.exit(result.returncode)
