# Migration Tasks: Supabase to PostgreSQL Docker

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

### Task 2.1: Create Database Connection Module
- [ ] Create `src/database.py` with PostgreSQL connection management
- [ ] Implement connection pooling (using asyncpg pool or psycopg2 pool)
- [ ] Add connection health checks and retry logic
- [ ] Add environment variable validation

### Task 2.2: Update Utils Module
- [ ] Replace `get_supabase_client()` with `get_db_connection()`
- [ ] Rewrite `add_documents_to_supabase()` as `add_documents_to_postgres()`
- [ ] Rewrite `search_documents()` to use direct SQL queries
- [ ] Update all database operations to use raw SQL or query builder
## Phase 3: Core Application Updates

### Task 3.1: Update Main MCP Server
- [ ] Modify `src/crawl4ai_mcp.py` imports (remove supabase, add database)
- [ ] Update `Crawl4AIContext` dataclass to use database connection
- [ ] Modify `crawl4ai_lifespan()` to initialize PostgreSQL connection
- [ ] Update all tool functions to use new database layer

### Task 3.2: Update Individual Tools
- [ ] Modify `crawl_single_page()` to use PostgreSQL functions
- [ ] Modify `smart_crawl_url()` to use PostgreSQL functions  
- [ ] Modify `get_available_sources()` to use direct SQL queries
- [ ] Modify `perform_rag_query()` to use PostgreSQL vector search

## Phase 4: SQL and Schema

### Task 4.1: Vector Search Functions
- [ ] Verify `match_crawled_pages()` function works with local PostgreSQL
- [ ] Test vector similarity search performance
- [ ] Create any additional helper functions needed
- [ ] Add proper indexing for performance

### Task 4.2: Data Migration (if needed)
- [ ] Create script to export data from existing Supabase (if applicable)
- [ ] Create script to import data into PostgreSQL
- [ ] Verify data integrity after migration

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
- [ ] Test database connection and pooling
- [ ] Test individual database operations (insert, select, delete)
- [ ] Test vector similarity search functionality
- [ ] Test embedding creation and storage

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

## Estimated Timeline
- Phase 1-2: 2-3 hours (Setup and core database layer)
- Phase 3-4: 3-4 hours (Application updates and SQL)
- Phase 5-7: 2-3 hours (Documentation, testing, cleanup)
- **Total**: 7-10 hours for complete migration