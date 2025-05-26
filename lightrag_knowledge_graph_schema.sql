-- LightRAG Knowledge Graph Schema using Apache AGE
-- This shows the expected graph structure for the knowledge graph integration

-- First, ensure AGE extension is installed
CREATE EXTENSION IF NOT EXISTS age;

-- Load the AGE extension
LOAD 'age';

-- Set the search path to include ag_catalog
SET search_path = ag_catalog, "$user", public;

-- Create the LightRAG knowledge graph
SELECT ag_catalog.create_graph('lightrag_graph');

-- Example of creating entity types and relationships
-- Note: In AGE, you create nodes and relationships using Cypher queries

-- Create Person entities
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
CREATE (n:Person {
    name: 'John Doe',
    description: 'Software engineer specializing in AI',
    entity_type: 'Person',
    properties: {
        'role': 'engineer',
        'expertise': ['AI', 'Machine Learning']
    }
})
$$) as (n agtype);

-- Create Organization entities
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
CREATE (n:Organization {
    name: 'Tech Corp',
    description: 'Leading technology company',
    entity_type: 'Organization',
    properties: {
        'industry': 'Technology',
        'size': 'Large'
    }
})
$$) as (n agtype);

-- Create Concept entities
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
CREATE (n:Concept {
    name: 'Machine Learning',
    description: 'Branch of AI focused on learning from data',
    entity_type: 'Concept',
    properties: {
        'field': 'Artificial Intelligence',
        'importance': 'High'
    }
})
$$) as (n agtype);

-- Create Community entities (for hierarchical grouping)
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
CREATE (n:Community {
    id: 'comm_1',
    name: 'AI Research Community',
    level: 1,
    size: 150,
    description: 'Community of AI researchers and practitioners'
})
$$) as (n agtype);

-- Create relationships
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
MATCH (p:Person {name: 'John Doe'}), (o:Organization {name: 'Tech Corp'})
CREATE (p)-[r:WORKS_AT {since: 2020, position: 'Senior Engineer'}]->(o)
$$) as (r agtype);

SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
MATCH (p:Person {name: 'John Doe'}), (c:Concept {name: 'Machine Learning'})
CREATE (p)-[r:EXPERT_IN {level: 'Advanced'}]->(c)
$$) as (r agtype);

-- Entity embeddings table (for semantic search on entities)
CREATE TABLE IF NOT EXISTS lightrag.entity_embeddings (
    entity_id bigserial PRIMARY KEY,
    entity_name varchar NOT NULL,
    entity_type varchar NOT NULL,
    properties jsonb DEFAULT '{}'::jsonb,
    embedding vector(1536),  -- OpenAI embeddings
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_entity_embeddings_embedding 
    ON lightrag.entity_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_entity_embeddings_type 
    ON lightrag.entity_embeddings (entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_embeddings_name 
    ON lightrag.entity_embeddings (entity_name);

-- Relationship embeddings table (optional, for semantic search on relationships)
CREATE TABLE IF NOT EXISTS lightrag.relationship_embeddings (
    relationship_id bigserial PRIMARY KEY,
    start_entity varchar NOT NULL,
    end_entity varchar NOT NULL,
    relationship_type varchar NOT NULL,
    properties jsonb DEFAULT '{}'::jsonb,
    embedding vector(1536),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_relationship_embeddings_embedding 
    ON lightrag.relationship_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Example queries that the integration supports:

-- 1. Get all Person entities
-- SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
-- MATCH (n:Person) RETURN n
-- $$) as (n agtype);

-- 2. Find relationships for an entity
-- SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
-- MATCH (n {name: 'John Doe'})-[r]-(m)
-- RETURN n, r, m
-- $$) as (n agtype, r agtype, m agtype);

-- 3. Find shortest path between entities
-- SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
-- MATCH path = shortestPath((a {name: 'John Doe'})-[*]-(b {name: 'Machine Learning'}))
-- RETURN path
-- $$) as (path agtype);

-- 4. Get community members
-- SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
-- MATCH (c:Community {id: 'comm_1'})-[:CONTAINS]->(n)
-- RETURN c, n
-- $$) as (c agtype, n agtype);
