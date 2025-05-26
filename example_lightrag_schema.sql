-- Example LightRAG schema structure that is compatible with the integration
-- This shows the expected table structures that the lightrag_integration module searches for

-- Option 1: Documents table structure
CREATE TABLE IF NOT EXISTS lightrag.documents (
    id bigserial PRIMARY KEY,
    content text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    embedding vector(1536),  -- OpenAI embeddings
    collection_name varchar,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_lightrag_documents_embedding 
    ON lightrag.documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_lightrag_documents_collection 
    ON lightrag.documents (collection_name);
CREATE INDEX IF NOT EXISTS idx_lightrag_documents_metadata 
    ON lightrag.documents USING gin (metadata);

-- Option 2: Alternative embeddings table structure
CREATE TABLE IF NOT EXISTS lightrag.embeddings (
    id bigserial PRIMARY KEY,
    text text NOT NULL,  -- Note: uses 'text' instead of 'content'
    metadata jsonb DEFAULT '{}'::jsonb,
    embedding vector(1536),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_lightrag_embeddings_embedding 
    ON lightrag.embeddings USING ivfflat (embedding vector_cosine_ops);

-- Optional: Collections table for managing document collections
CREATE TABLE IF NOT EXISTS lightrag.collections (
    id bigserial PRIMARY KEY,
    name varchar NOT NULL UNIQUE,
    description text,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- The integration will automatically detect and adapt to either structure
-- It first tries the 'documents' table, then falls back to 'embeddings' table
