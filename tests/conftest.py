"""
Pytest configuration and setup for the project.

This file handles environment setup and mocking for tests.
"""
import os
import sys
import pytest
import asyncio
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
    "POSTGRES_DB": "postgres",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
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

@pytest.fixture
async def db_integration_setup():
    """
    Set up database for integration tests.
    
    This fixture:
    1. Initializes the database connection
    2. Creates the schema and tables
    3. Provides cleanup
    4. Should only be used for integration tests
    """
    # Import here to avoid circular imports
    from src.database import initialize_db_connection, close_db_connection, get_db_connection
    
    # Skip if database env vars not set
    if not all([os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_DB")]):
        pytest.skip("Database environment variables not set for integration test")
    
    db_conn = None
    try:
        # Initialize database connection
        db_conn = await initialize_db_connection()
        
        # Create schema and tables
        await db_conn.create_schema_if_not_exists()
        
        yield db_conn
        
    except Exception as e:
        pytest.skip(f"Could not set up database for integration test: {e}")
    finally:
        # Clean up
        if db_conn:
            try:
                # Clean up test data
                await db_conn.execute("DELETE FROM crawl.crawled_pages WHERE url LIKE 'http://test.com%'")
            except Exception:
                pass  # Ignore cleanup errors
            
            await close_db_connection()

@pytest.fixture
def mock_openai_for_integration():
    """
    Mock OpenAI API for integration tests.
    
    This provides realistic mock responses for embeddings
    without making actual API calls.
    """
    with patch('src.utils.openai') as mock_openai:
        def mock_create_embeddings(*args, **kwargs):
            """Mock embeddings.create that returns the right number of embeddings."""
            # Get the input texts
            input_texts = kwargs.get('input', [])
            if isinstance(input_texts, str):
                input_texts = [input_texts]
            
            # Create mock response with correct number of embeddings
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1] * 1536) for _ in input_texts
            ]
            return mock_response
        
        # Set up the mock
        mock_openai.embeddings.create.side_effect = mock_create_embeddings
        
        # Mock chat completion response
        mock_chat_response = Mock()
        mock_chat_response.choices = [
            Mock(message=Mock(content="This is contextual information"))
        ]
        mock_openai.chat.completions.create.return_value = mock_chat_response
        
        yield mock_openai

# Auto-use fixture to ensure mocks are set up
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure test environment is properly set up for each test."""
    # Re-ensure environment variables are set
    for key, value in test_env.items():
        os.environ[key] = value
    yield
