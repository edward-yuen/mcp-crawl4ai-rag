# Migration Planning: Supabase to PostgreSQL Docker

## Overview
This document outlines the plan to migrate the mcp-crawl4ai-rag repository from using Supabase as the database backend to using a local PostgreSQL database running in Docker.

## Current Architecture
- **Database**: Supabase (hosted PostgreSQL with pgvector)
- **Database Client**: Supabase Python SDK
- **Vector Search**: Supabase RPC functions
- **Embeddings**: OpenAI text-embedding-3-small
- **Schema**: crawled_pages table with vector similarity search

## Target Architecture
- **Database**: Local PostgreSQL with pgvector extension (Docker)
- **Database Client**: psycopg2 or asyncpg for direct PostgreSQL connection
- **Vector Search**: Direct SQL queries using pgvector
- **Embeddings**: OpenAI text-embedding-3-small (unchanged)
- **Schema**: Same crawled_pages table structure

## Key Changes Required

### 1. Database Connection Layer
- Replace Supabase client with PostgreSQL connection pool
- Update environment variables (remove Supabase, add PostgreSQL connection details)
- Handle connection management and pooling

### 2. Database Operations
- Convert Supabase table operations to raw SQL or ORM queries
- Replace `.rpc()` calls with direct SQL function calls
- Update vector similarity search queries
- Handle transaction management

### 3. Schema Management
- Ensure pgvector extension is installed in Docker PostgreSQL
- Create database initialization script
- Port the existing SQL schema to work with local PostgreSQL
### 4. Configuration Updates
- Update environment variables
- Modify Docker configuration if needed
- Update documentation and setup instructions

### 5. Error Handling & Logging
- Update error handling for PostgreSQL-specific exceptions
- Maintain existing functionality while improving direct database access

## Benefits of Migration
1. **Full Control**: Complete control over database configuration and performance
2. **Cost Reduction**: No external service fees
3. **Data Privacy**: All data stays local
4. **Development Flexibility**: Easier to modify schema and functions
5. **Integration**: Better integration with existing Docker infrastructure

## Potential Challenges
1. **Connection Management**: Need to handle connection pooling properly
2. **Vector Operations**: Ensure pgvector functions work identically
3. **Performance**: May need to optimize queries without Supabase's optimizations
4. **Backup/Recovery**: Need to implement own backup strategy

## Success Criteria
- All existing MCP tools work identically
- Vector search performance is maintained or improved
- Easy setup with user's existing Docker PostgreSQL
- Clean, maintainable code with proper error handling
- Comprehensive testing to ensure functionality parity