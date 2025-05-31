# LightRAG Schema Options Strategies - Diagnosis and Solution

## Issue Summary

When searching for "advanced options strategies in the lightrag schema", the tools are working correctly but the knowledge graph doesn't contain comprehensive options strategy information. 

## Current State

### What's Working:
1. **Database Connection**: Successfully connecting to PostgreSQL on localhost
2. **Schemas**: Both `crawl` (1744 documents) and `chunk_entity_relation` (6946 entities) schemas exist
3. **Search Tools**: The search functions are operational and returning results

### What's in the Knowledge Graph:
- **Total Entities**: 6,946
- **Finance-Related Entities**: 51 unique entities containing options/trading keywords
- **Sources**: Primarily academic PDFs like "Systematic Strategies.pdf" and "Developing and Backtesting Strategies using LLM.pdf"

### Options-Related Content Found:
- Basic concepts: "Out-of-the-Money (OTM) Call Options", "Put Spreads"
- Some strategies mentioned: "Covered Call Strategy", "Protective Put Option"
- But missing: Detailed strategies like Iron Condor, Butterfly Spread, Calendar Spreads, etc.

## The Problem

The knowledge graph was built from academic papers that mention options in passing but don't provide comprehensive options strategy information. The search is working correctly - there simply isn't detailed options strategy content to find.

## Solution

### Step 1: Crawl Options Strategy Content

Use the MCP tools to crawl websites with comprehensive options strategy information:

```
# Example: Crawl Investopedia's options section
smart_crawl_url("https://www.investopedia.com/options-basics-tutorial-4583012")

# Example: Crawl specific strategy pages
smart_crawl_url("https://www.investopedia.com/terms/i/ironcondor.asp")
smart_crawl_url("https://www.investopedia.com/terms/b/butterflyspread.asp")
```

### Step 2: Build Knowledge Graph from New Content

After crawling, use the `build_knowledge_graph` tool to extract entities and relationships from the new content.

### Step 3: Search with Improved Queries

Once the content is indexed, search will work better:

```
# These queries will return relevant results after crawling
query_lightrag_schema("iron condor strategy")
search_graph_entities("butterfly spread")
enhanced_graph_query("advanced options strategies")
```

## Fixed Search Function

I've implemented an improved search function (`lightrag_search_improved.py`) that:
- Uses PostgreSQL JSON operators for more reliable searching
- Supports multi-word queries with better matching
- Scores results by relevance
- Falls back gracefully when AGE functions aren't available

## Recommended Actions

1. **Immediate**: Use the improved search to find what's currently available
2. **Next**: Crawl options-focused educational sites to populate the knowledge graph
3. **Future**: Consider crawling broker education pages and options trading platforms

## Testing Tools Created

1. **`diagnose_kg_content.py`**: Analyzes what's in your knowledge graph
2. **`test_improved_search.py`**: Tests the improved search functionality
3. **`test_options_search.py`**: Specifically searches for options-related content

Run these to verify the fixes and understand your data better.
