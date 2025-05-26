# LightRAG Knowledge Graph Usage Examples

This document shows how to use the LightRAG knowledge graph tools with the MCP server.

## Basic Entity Queries

```python
# Get all Person entities
await get_graph_entities(ctx, entity_type="Person", limit=10)

# Get all entities (any type)
await get_graph_entities(ctx, limit=50)

# Search for entities by meaning
await search_graph_entities(ctx, query="artificial intelligence experts", entity_type="Person")
```

## Relationship Exploration

```python
# Get all relationships for a specific entity
await get_entity_graph(ctx, entity_name="John Doe", depth=1)

# Get specific relationship types
await get_entity_graph(ctx, entity_name="Tech Corp", relationship_type="WORKS_AT", depth=2)

# Find paths between entities
await find_entity_path(ctx, start_entity="John Doe", end_entity="Machine Learning", max_depth=3)
```

## Direct Cypher Queries

```python
# Find all people who work at tech companies
await query_graph(ctx, cypher_query="""
    MATCH (p:Person)-[:WORKS_AT]->(o:Organization)
    WHERE o.properties.industry = 'Technology'
    RETURN p.name, o.name
    LIMIT 10
""")

# Find communities of related concepts
await query_graph(ctx, cypher_query="""
    MATCH (c1:Concept)-[r:RELATED_TO]-(c2:Concept)
    RETURN c1.name, c2.name, r.strength
    ORDER BY r.strength DESC
    LIMIT 20
""")

# Complex pattern matching
await query_graph(ctx, cypher_query="""
    MATCH (p:Person)-[:EXPERT_IN]->(c:Concept)<-[:RELATED_TO]-(c2:Concept)
    WHERE p.name = 'John Doe'
    RETURN DISTINCT c2.name as related_concepts
""")
```

## Community Analysis

```python
# Get top-level communities
await get_graph_communities(ctx, level=1, limit=10)

# Get all communities
await get_graph_communities(ctx, limit=50)
```

## Graph Statistics

```python
# Get overview of the knowledge graph
await get_graph_stats(ctx)

# Returns something like:
{
    "node_counts": {
        "Person": 150,
        "Organization": 50,
        "Concept": 200,
        "Community": 20
    },
    "relationship_counts": {
        "WORKS_AT": 180,
        "KNOWS": 320,
        "EXPERT_IN": 250,
        "RELATED_TO": 500
    },
    "total_nodes": 420,
    "total_relationships": 1250
}
```

## Combined Search Examples

```python
# Search both documents and knowledge graph
await multi_schema_search(ctx, 
    query="machine learning applications in healthcare",
    schemas=["crawl", "lightrag"],
    combine=True
)

# Find entities related to search results
# First, search documents
doc_results = await query_lightrag_schema(ctx, query="quantum computing breakthroughs")

# Then, find related entities in the graph
await search_graph_entities(ctx, query="quantum computing", entity_type="Person")
await search_graph_entities(ctx, query="quantum computing", entity_type="Organization")
```

## Advanced Graph Patterns

```python
# Find experts in multiple related fields
await query_graph(ctx, cypher_query="""
    MATCH (p:Person)-[:EXPERT_IN]->(c1:Concept),
          (p)-[:EXPERT_IN]->(c2:Concept)
    WHERE c1.name = 'Machine Learning' AND c2.name = 'Data Science'
    RETURN p.name, p.properties
""")

# Find collaboration networks
await query_graph(ctx, cypher_query="""
    MATCH (p1:Person)-[:WORKS_AT]->(o:Organization)<-[:WORKS_AT]-(p2:Person)
    WHERE p1.name <> p2.name
    RETURN p1.name, p2.name, o.name as workplace
    LIMIT 20
""")

# Analyze concept hierarchies
await query_graph(ctx, cypher_query="""
    MATCH path = (c1:Concept)-[:SUBCONCEPT_OF*1..3]->(c2:Concept)
    WHERE c2.name = 'Artificial Intelligence'
    RETURN c1.name, length(path) as depth
    ORDER BY depth
""")
```

## Error Handling

All tools return JSON with a `success` field. Always check this:

```python
result = await get_entity_graph(ctx, entity_name="Unknown Entity")
# Result will be:
{
    "success": true,
    "entity": "Unknown Entity",
    "graph": {
        "entity": "Unknown Entity",
        "relationships": [],
        "connected_nodes": []
    }
}
```

If there's an error (e.g., AGE not installed):
```python
{
    "success": false,
    "error": "Error message here"
}
```
