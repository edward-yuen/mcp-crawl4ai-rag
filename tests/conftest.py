"""
Pytest configuration and setup for the project.

This file handles environment setup and mocking for tests.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from functools import wraps

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set up test environment variables before any imports
# This ensures they're available even if dotenv tries to load
test_env = {
    "PORT": "8051",
    "HOST": "0.0.0.0",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "OPENAI_API_KEY": "test_api_key",
    "TRANSPORT": "sse"
}

# Set all test environment variables
for key, value in test_env.items():
    os.environ[key] = value

# Mock FastMCP class
class MockFastMCP:
    def __init__(self, name, description="", lifespan=None, host="0.0.0.0", port=8051, **kwargs):
        self.name = name
        self.description = description
        self.lifespan = lifespan
        self.host = host
        # Handle port conversion
        if isinstance(port, str) and port.strip():
            self.port = int(port)
        elif isinstance(port, int):
            self.port = port
        else:
            self.port = 8051
        
        # Mock settings object
        self.settings = MagicMock()
        self.settings.host = self.host
        self.settings.port = self.port
    
    def tool(self, func=None, **kwargs):
        """Mock tool decorator."""
        if func is None:
            def decorator(f):
                return f
            return decorator
        return func
    
    def run(self):
        """Mock run method."""
        pass

# Mock Context
class MockContext:
    """Mock MCP Context."""
    pass

# Install mocks before any imports
def pytest_sessionstart(session):
    """Called after the Session object has been created and before performing collection."""
    import types
    
    # Create mock module structure
    mcp = types.ModuleType('mcp')
    mcp_server = types.ModuleType('mcp.server')
    mcp_server_fastmcp = types.ModuleType('mcp.server.fastmcp')
    
    # Set attributes
    mcp_server_fastmcp.FastMCP = MockFastMCP
    mcp_server_fastmcp.Context = MockContext
    
    # Link modules
    mcp.server = mcp_server
    mcp_server.fastmcp = mcp_server_fastmcp
    
    # Install in sys.modules
    sys.modules['mcp'] = mcp
    sys.modules['mcp.server'] = mcp_server
    sys.modules['mcp.server.fastmcp'] = mcp_server_fastmcp

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_conn.fetchone = MagicMock(return_value=None)
    mock_conn.fetchall = MagicMock(return_value=[])
    mock_conn.execute = MagicMock()
    mock_conn.commit = MagicMock()
    mock_conn.close = MagicMock()
    mock_conn.__aenter__ = MagicMock(return_value=mock_conn)
    mock_conn.__aexit__ = MagicMock(return_value=None)
    return mock_conn

@pytest.fixture
def mock_crawler():
    """Mock Crawl4AI crawler."""
    mock = MagicMock()
    mock.arun = MagicMock()
    mock.__aenter__ = MagicMock(return_value=mock)
    mock.__aexit__ = MagicMock(return_value=None)
    return mock

# Auto-use fixture to ensure mocks are set up
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure test environment is properly set up for each test."""
    # Re-ensure environment variables are set
    for key, value in test_env.items():
        os.environ[key] = value
    yield
