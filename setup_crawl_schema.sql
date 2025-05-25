-- Run this script against your existing PostgreSQL database to set up the crawl schema
-- You can run this with: psql -h localhost -U postgres -d lightrag -f setup_crawl_schema.sql

-- Create the crawl schema for crawl4ai data
CREATE SCHEMA IF NOT EXISTS crawl;

-- Enable the pgvector extension (should already be installed in your database)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documentation chunks table in the crawl schema
CREATE TABLE IF NOT EXISTS crawl.crawled_pages (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Add a unique constraint to prevent duplicate chunks for the same URL
    unique(url, chunk_number)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crawled_pages_embedding ON crawl.crawled_pages USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_crawled_pages_metadata ON crawl.crawled_pages USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_crawled_pages_source ON crawl.crawled_pages ((metadata->>'source'));

-- Create a function to search for documentation chunks in the crawl schema
CREATE OR REPLACE FUNCTION crawl.match_crawled_pages (
  query_embedding vector(1536),
  match_count int default 10,
  filter jsonb DEFAULT '{}'::jsonb
) returns table (
  id bigint,
  url varchar,
  chunk_number integer,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    crawled_pages.id,
    crawled_pages.url,
    crawled_pages.chunk_number,
    crawled_pages.content,
    crawled_pages.metadata,
    1 - (crawled_pages.embedding <=> query_embedding) as similarity
  from crawl.crawled_pages
  where crawled_pages.metadata @> filter
  order by crawled_pages.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Grant necessary permissions (adjust username if different)
GRANT USAGE ON SCHEMA crawl TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA crawl TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA crawl TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA crawl TO postgres;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA crawl GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA crawl GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA crawl GRANT ALL ON FUNCTIONS TO postgres;
