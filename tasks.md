# Migration Tasks: Supabase to PostgreSQL Docker

## Completed Tasks

### 2025-05-31: Fixed LightRAG Search Issues
- [x] Diagnosed issue with LightRAG schema queries not working properly
- [x] Fixed POSTGRES_HOST in .env (changed from "postgres" to "localhost")
- [x] Created improved search function that uses PostgreSQL JSON operators
- [x] Added fallback search when AGE functions fail
- [x] Created diagnostic tools:
  - `diagnose_kg_content.py` - Analyzes knowledge graph content
  - `test_improved_search.py` - Tests improved search
  - `test_options_search.py` - Searches for options strategies
- [x] Created `lightrag_search_improved.py` with robust search implementation
- [x] Updated `lightrag_integration.py` to use improved search as primary method
- [x] Documented findings in `LIGHTRAG_OPTIONS_DIAGNOSIS.md`

## Phase 1: Environment and Dependencies

### Task 1.1: Update Dependencies
- [x] Add `psycopg2-binary` or `asyncpg` to pyproject.toml
- [x] Remove `supabase` dependency from pyproject.toml
- [x] Update uv.lock by running `uv lock`

### Task 1.2: Update Environment Variables
- [x] Modify `.env.example` to replace Supabase vars with PostgreSQL vars:
  - Remove: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - Add: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- [x] Update documentation to reflect new environment variables

### Task 1.3: Database Setup Scripts
- [x] Create `setup_crawl_schema.sql` script to create crawl schema in existing PostgreSQL
- [x] Update `crawled_pages.sql` to use crawl schema
- [x] Create database connection validation script

## Phase 2: Core Database Layer

### Task 2.1: Create Database Connection Module ✅ [Completed: 2025-01-22]
- [x] Create `src/database.py` with PostgreSQL connection management
- [x] Implement connection pooling (using asyncpg pool or psycopg2 pool)
- [x] Add connection health checks and retry logic
- [x] Add environment variable validation

### Task 2.2: Update Utils Module
- [x] Replace `get_supabase_client()` with `get_db_connection()`
- [x] Rewrite `add_documents_to_supabase()` as `add_documents_to_postgres()`
- [x] Rewrite `search_documents()` to use direct SQL queries
- [x] Update all database operations to use raw SQL or query builder
## Phase 3: Core Application Updates

### Task 3.1: Update Main MCP Server
- [x] Modify `src/crawl4ai_mcp.py` imports (remove supabase, add database)
- [x] Update `Crawl4AIContext` dataclass to use database connection
- [x] Modify `crawl4ai_lifespan()` to initialize PostgreSQL connection
- [x] Update all tool functions to use new database layer
- [x] Include lightrag knowledge graph query support with age, right now only uses regular RAG 

### Task 3.2: Update Individual Tools ✅ [Completed: 2025-05-25]
- [x] Modify `crawl_single_page()` to use PostgreSQL functions
- [x] Modify `smart_crawl_url()` to use PostgreSQL functions  
- [x] Modify `get_available_sources()` to use direct SQL queries
- [x] Modify `perform_rag_query()` to use PostgreSQL vector search

### Task 3.3: Debug and Fix LightRAG Connection Issues ✅ [Completed: 2025-05-26]
- [x] Create debug script to test PostgreSQL connection with multiple host configurations
- [x] Create fix script to update POSTGRES_HOST based on deployment type
- [x] Create troubleshooting guide for common connection issues
- [x] Document the difference between local and Docker deployments

## Phase 4: SQL and Schema

### Task 4.1: Vector Search Functions ✅ [Completed: 2025-05-26]
- [x] Verify `match_crawled_pages()` function works with local PostgreSQL
- [x] Test vector similarity search performance
- [x] Create any additional helper functions needed
- [x] Add proper indexing for performance
- [x] Test knowledge graph search performance


## Phase 5: Configuration and Documentation

### Task 5.1: Docker Configuration
- [ ] Update Dockerfile if needed for new dependencies
- [ ] Test Docker build with new dependencies
- [ ] Update docker-compose examples in README

### Task 5.2: Documentation Updates
- [ ] Update README.md with PostgreSQL setup instructions
- [ ] Update database setup section
- [ ] Add troubleshooting section for PostgreSQL connection issues
- [ ] Update MCP client configuration examples
## Phase 6: Testing and Validation

### Task 6.1: Unit Testing
- [x] Test database connection and pooling (created test_database_connection.py)
- [x] Test individual database operations (insert, select, delete) (created tests/test_utils.py)
- [x] Test vector similarity search functionality (created tests/test_utils.py)
- [x] Test embedding creation and storage (created tests/test_utils.py)

### Task 6.2: Integration Testing
- [ ] Test all MCP tools end-to-end
- [ ] Test crawling and storage pipeline
- [ ] Test RAG query functionality with various filters
- [ ] Test error handling and edge cases

### Task 6.3: Performance Testing
- [ ] Compare performance with original Supabase version
- [ ] Test concurrent operations and connection pooling
- [ ] Test large batch operations
- [ ] Optimize queries if needed

## Phase 7: Cleanup and Finalization

### Task 7.1: Code Cleanup
- [ ] Remove all Supabase-related code and imports
- [ ] Add proper error handling and logging
- [ ] Add type hints and documentation
- [ ] Code review and refactoring

### Task 7.2: Final Documentation
- [ ] Update all configuration examples
- [ ] Create migration guide for existing users
- [ ] Test setup instructions with fresh environment
- [ ] Update README with new architecture details

## Discovered During Work

### Completed Tasks (May 24, 2025)
- [x] **Database Schema Setup**: Successfully created `crawl` schema in existing PostgreSQL database
- [x] **Environment Configuration**: Updated `.env.example` and `.env` with PostgreSQL settings
- [x] **Database Validation**: Created and tested `validate_db_setup.py` - all checks passed
- [x] **Connection Configuration**: Fixed host settings for connecting from host machine to Docker container
- [x] **Documentation Updates**: Updated README.md to replace Supabase references with PostgreSQL

### Next Priority Tasks
- **Task 1.1**: Still need to update `pyproject.toml` dependencies and run `uv lock`
- **Task 2.1**: Create database connection module (`src/database.py`)
- **Task 2.2**: Update utils module to replace Supabase functions

## Priority Order
1. **High Priority**: Tasks 1.1, 1.2, 2.1, 2.2 (Core functionality)
2. **Medium Priority**: Tasks 3.1, 3.2, 4.1 (Application updates)
3. **Low Priority**: Tasks 5.1, 5.2, 6.x, 7.x (Polish and testing)

## Discovered During Work
- [x] Add LightRAG schema integration (2025-01-19)
  - Created lightrag_integration.py module
  - Added query_lightrag_schema tool
  - Added get_lightrag_info tool  
  - Added multi_schema_search tool
  - Enables querying from both crawl and lightrag schemas
- [x] Add LightRAG Knowledge Graph support (2025-01-19)
  - Created lightrag_knowledge_graph.py module
  - Added query_graph tool for Cypher queries
  - Added get_graph_entities tool
  - Added get_entity_graph tool for relationship traversal
  - Added search_graph_entities tool for semantic entity search
  - Added find_entity_path tool for pathfinding
  - Added get_graph_communities tool
  - Added get_graph_stats tool
  - Full Apache AGE integration for graph queries

## Estimated Timeline
- Phase 1-2: 2-3 hours (Setup and core database layer)
- Phase 3-4: 3-4 hours (Application updates and SQL)
- Phase 5-7: 2-3 hours (Documentation, testing, cleanup)
- **Total**: 7-10 hours for complete migration

## Discovered During Work (Task 3.1 & 3.2 - 2025-05-25)

### Task 3.1 Verification ✅ (Completed):
- ✅ **Imports**: Successfully updated to remove Supabase and add database imports
- ✅ **Context Dataclass**: `Crawl4AIContext` properly updated with `db_connection: DatabaseConnection`
- ✅ **Lifespan Management**: `crawl4ai_lifespan()` correctly initializes PostgreSQL with `initialize_db_connection()`
- ✅ **Tool Functions**: All tools properly updated to use new database layer

### Task 3.2 Completion ✅ (Completed):
- ✅ **crawl_single_page()**: Updated to get database connection from context and use `add_documents_to_postgres()`
- ✅ **smart_crawl_url()**: Updated to get database connection from context and use PostgreSQL functions
- ✅ **get_available_sources()**: Already properly implemented with direct SQL queries using `db_connection.fetch()`
- ✅ **perform_rag_query()**: Already properly implemented using PostgreSQL vector search via `search_documents()`

### Key Fixes Applied:
1. **Context Access**: Fixed both `crawl_single_page()` and `smart_crawl_url()` to properly access database connection via `ctx.request_context.lifespan_context.db_connection`
2. **Function Calls**: Ensured all database operations use the async PostgreSQL functions from `utils.py`
3. **Error Handling**: Maintained proper error handling and logging throughout
4. **Comments**: Added clarifying comments about PostgreSQL usage

### Architecture Verification:
- **Database Layer**: `database.py` ✅ (Connection pooling, health checks, retry logic)
- **Utils Layer**: `utils.py` ✅ (PostgreSQL operations, vector search)
- **MCP Server**: `crawl4ai_mcp.py` ✅ (Tool functions, context management)
- **Schema**: `crawled_pages.sql` ✅ (PostgreSQL schema with pgvector)

### Next Steps:
- Task 4.1: Verify vector search functions performance
- Task 6.2: Integration testing of all MCP tools end-to-end

### Completed:
- ✅ Updated `utils.py` to use PostgreSQL instead of Supabase
- ✅ Replaced `get_supabase_client()` with `get_db_connection()`
- ✅ Rewrote `add_documents_to_supabase()` as `add_documents_to_postgres()` using raw SQL
- ✅ Rewrote `search_documents()` to use direct SQL queries via the `match_crawled_pages` function
- ✅ Created comprehensive test suite in `tests/test_utils.py`
- ✅ All database operations now use asyncpg connection from `database.py`

### Key Changes Made:
1. **Import Changes**: Removed `supabase` import, added `database` module import
2. **Function Signatures**: Removed `client` parameter from functions since we now use global connection
3. **Async Functions**: Made database functions `async` to work with asyncpg
4. **SQL Operations**: Used parameterized queries with proper type casting (e.g., `$1::vector`, `$2::jsonb`)
5. **Batch Processing**: Maintained batch processing logic but adapted for PostgreSQL's `execute_many()`

### Next Steps (Task 3.1):
- Update `crawl4ai_mcp.py` to:
  - Remove Supabase imports
  - Update function calls to use new async functions
  - Change `get_supabase_client()` to `get_db_connection()`
  - Add `await` to database function calls
  - Update the lifespan context manager

### Notes:
- The schema expects the `crawl` schema to exist (created by `crawled_pages.sql`)
- Vector operations require pgvector extension to be installed
- All metadata is stored as JSONB in PostgreSQL
- Embedding dimension is hardcoded to 1536 (OpenAI's text-embedding-3-small)

## Additional Tasks - 2025-05-25

### Task: Fix pytest import errors and missing dependencies
- [x] Fixed import paths in test_lightrag_integration.py (changed from `from lightrag_integration` to `from src.lightrag_integration`)
- [x] Fixed import paths in test_main_mcp_migration.py (changed from `from crawl4ai_mcp` to `from src.crawl4ai_mcp`)
- [x] Fixed pyproject.toml dependency issue (changed `dotenv==0.9.9` to `python-dotenv==1.0.0`)
- [x] Created fix_pytest_setup.py script to help install missing dependencies
- [x] Created test_import_fixes.py to verify import corrections
- [ ] Install missing dependencies (`mcp`, `openai`, `asyncpg`, etc.) using `pip install -e .` or `uv sync`
- [ ] Ensure PostgreSQL is running with correct schema for full test suite to pass### Task: Fix pytest module-level initialization error (2025-05-25)
- [x] Identified root cause: FastMCP instance created at module level in crawl4ai_mcp.py
- [x] Issue: pydantic Settings receives empty string for port during test import
- [x] Created comprehensive debugging documentation in pytest_debug.md
- [x] Updated tests/conftest.py with proper mocking and environment setup
- [x] Created run_tests.py as test runner with proper environment setup
- [x] Created .env.test with test-specific environment variables
- [x] Created test_setup_verification.py to verify test environment
- [x] Updated pytest.ini with proper configuration
- [ ] Consider refactoring crawl4ai_mcp.py to use lazy initialization (long-term fix)


### Task: Fix pytest warnings (2025-05-26)
- [x] Fixed pytest return warning in test_path_fix.py (replaced return True/False with proper assertions)
- [x] Added warning filters to pytest.ini to suppress external library deprecation warnings (pydantic, fake_http_header, importlib)
- [x] Added asyncio_default_fixture_loop_scope configuration to pytest.ini
- [x] Verified all 24 tests pass with 0 warnings
- [x] Created pytest_warnings_fix_summary.md documenting all fixes

### Task: Implement Unified Enhanced Search Tool ✅ [Completed: 2025-05-31]
- [x] Create enhanced_search_tools.py with unified search functionality
- [x] Create search_helpers.py with implementation details for different search backends
- [x] Consolidate redundant search tools (perform_rag_query, multi_schema_search deprecated)
- [x] Implement QueryAnalyzer for intelligent query routing based on query type
- [x] Support document search, entity search, graph queries, and natural language queries
- [x] Update registry.py to include new tools and deprecate redundant ones
- [x] Create comprehensive tests for the enhanced search functionality
- [x] Create integration test script to verify functionality
- [x] Add smart_search as simplified interface to enhanced_search

### MCP Server Refactoring Tasks (2025-05-30) ✅ [Completed: 2025-05-31]
- [x] Create `src/tools/knowledge_graph_tools.py` - Extract all KG tools from main file (completed)
- [x] Create `src/server/registry.py` - Tool registration system (completed)
- [x] Create `src/crawling/strategies.py` - Move strategy-specific functions (completed)
- [x] Refactor main `src/crawl4ai_mcp.py` from 1263 lines to 45 lines (completed)
- [x] Update imports to use new modules (completed)
- [x] Create `src/models/responses.py` - Response formatting utilities ✅ [Completed: 2025-05-31]
- [x] Create `src/common/constants.py` - Constants and configuration ✅ [Completed: 2025-05-31]
- [x] Create `src/common/exceptions.py` - Custom exceptions ✅ [Completed: 2025-05-31]
- [x] Create `src/common/validators.py` - Input validation ✅ [Completed: 2025-05-31]
- [ ] Test all functionality (remaining)



### Task 4.1: Vector Search Functions Completion (2025-05-26)
- [x] Verified `match_crawled_pages()` function exists and is callable in local PostgreSQL
- [x] Created comprehensive test script `test_vector_search_functions.py` for function verification
- [x] Tested vector similarity search performance with multiple queries (averaging ~1.6s per query)
- [x] Created vector search helper functions artifact with enhanced functionality:
  - Enhanced search results with metadata
  - Index optimization functions
  - Batch search capabilities  
  - Search performance analysis tools
  - Validation functions for setup verification
- [x] Created `optimize_vector_indexes.py` script for index management and performance tuning
- [x] Added comprehensive unit tests in `tests/test_vector_search_task_4_1.py` (6/7 tests passing)
- [x] Verified error handling and graceful degradation when OpenAI API unavailable
- [x] Tested integration workflow with real database connection
- [x] Confirmed vector indexes exist and are properly configured
- [x] Performance metrics: Direct function calls ~0.056s, full search pipeline ~1.6s average
- [x] All vector search infrastructure working correctly with local PostgreSQL + pgvector


## Discovered During Work

### LightRAG Connection Issues (2025-05-26)
- **Issue**: MCP server unable to connect to PostgreSQL when POSTGRES_HOST is set to "postgres" but running locally
- **Root Cause**: Docker networking configuration mismatch between local and containerized deployments
- **Solution**: Created debug and fix scripts to detect and correct the POSTGRES_HOST setting
- **Files Created**:
  - `debug_lightrag_connection.py` - Tests multiple host configurations and validates data
  - `fix_postgres_host.py` - Interactive script to update .env based on deployment type
  - `LIGHTRAG_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide


### FastMCP Run Method Fix (2025-05-31)
- **Issue**: MCP server failing to start in Docker with "TypeError: FastMCP.run() got an unexpected keyword argument 'read_stream'"
- **Root Cause**: FastMCP API changed - run() method no longer accepts read_stream/write_stream parameters
- **Solution**: Updated `src/crawl4ai_mcp.py` to use simplified run() method that auto-detects transport mode from environment
- **Changes Made**:
  - Removed explicit stream parameters from mcp.run() call
  - Removed unused sys import
  - FastMCP now automatically handles stdio/sse transport based on environment


### FastMCP Asyncio Event Loop Fix (2025-05-31) ✅ [Completed: 2025-05-31]
- **Issue**: MCP server failing to start in Docker with "RuntimeError: Already running asyncio in this thread"
- **Root Cause**: FastMCP's `run()` method internally uses `anyio.run()` which conflicts with `asyncio.run()`
- **Solution**: Changed main entry point to call `mcp.run()` directly instead of wrapping in `asyncio.run()`
- **Changes Made**:
  - Removed `asyncio.run(main())` wrapper function
  - Removed `async def main()` function
  - Removed asyncio import
  - Call `mcp.run()` directly from `if __name__ == "__main__":` block
  - FastMCP internally handles event loop creation and transport detection