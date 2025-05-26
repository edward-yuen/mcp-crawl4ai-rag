# 🔧 Pytest Error Fix Summary

## Problem
The pytest error occurs because:
1. `crawl4ai_mcp.py` creates a FastMCP instance at module level (line 118)
2. FastMCP uses pydantic Settings which validates the `port` parameter
3. The port value is being passed as an empty string `''` which can't be parsed as an integer
4. The module uses `load_dotenv(override=True)` which overrides test environment variables

## Root Cause
The error message shows:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
port
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='', input_type=str]
```

This happens because the MCP server initialization happens at import time, before test mocks can be properly set up.

## Solutions

### Solution 1: Quick Fix - Use the test runner
Run tests using the provided test runner script:
```bash
python run_tests.py tests/test_main_mcp_migration.py
```

### Solution 2: Modify the source code (Recommended for long-term)
The best long-term solution is to refactor `crawl4ai_mcp.py` to lazy-initialize the FastMCP instance:

```python
# Instead of:
mcp = FastMCP(...)

# Use lazy initialization:
_mcp = None

def get_mcp():
    global _mcp
    if _mcp is None:
        _mcp = FastMCP(
            "mcp-crawl4ai-rag",
            description="MCP server for RAG and web crawling with Crawl4AI",
            lifespan=crawl4ai_lifespan,
            host=get_host(),
            port=get_port()
        )
    return _mcp

# Then use @get_mcp().tool instead of @mcp.tool
```

### Solution 3: Use test environment file
1. The `.env.test` file has been created with proper test values
2. Tests can use this file by modifying the dotenv path during testing

### Solution 4: Current workaround in conftest.py
The updated `conftest.py`:
- Sets environment variables before any imports
- Mocks the FastMCP class before it's imported
- Uses `pytest_sessionstart` to ensure mocks are installed early

## Testing the Fix
1. Verify environment setup: `python test_setup_verification.py`
2. Run tests: `python run_tests.py -v`
3. Or run specific test: `pytest tests/test_main_mcp_migration.py -v`

## Key Files Modified
- `tests/conftest.py` - Updated with proper mocking and environment setup
- `pytest.ini` - Simplified configuration
- `run_tests.py` - Test runner that ensures proper environment
- `.env.test` - Test-specific environment variables
- `test_setup_verification.py` - Verification script

## Next Steps
If the error persists:
1. Check if `.env` file has empty PORT value
2. Ensure no other process is setting PORT to empty string
3. Consider refactoring the module to avoid module-level initialization
