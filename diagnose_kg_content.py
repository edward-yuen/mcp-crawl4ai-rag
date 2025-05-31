#!/usr/bin/env python3
"""
Diagnostic tool for LightRAG Knowledge Graph content.
Helps understand what entities are available and how to search effectively.
"""
import asyncio
import os
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.database import initialize_db_connection, close_db_connection, get_db_connection


async def analyze_knowledge_graph():
    """Analyze the content of the knowledge graph."""
    print("=" * 80)
    print("LightRAG Knowledge Graph Analysis")
    print("=" * 80)
    
    await initialize_db_connection()
    db = await get_db_connection()
    
    # 1. Get total entity count
    total_count = await db.fetchval("""
        SELECT COUNT(*) FROM chunk_entity_relation._ag_label_vertex
    """)
    print(f"\nTotal entities in knowledge graph: {total_count}")
    
    # 2. Get entity type distribution
    print("\nEntity Type Distribution:")
    entity_types = await db.fetch("""
        SELECT properties::json->>'entity_type' as entity_type, COUNT(*) as count
        FROM chunk_entity_relation._ag_label_vertex
        WHERE properties::json->>'entity_type' IS NOT NULL
        GROUP BY properties::json->>'entity_type'
        ORDER BY count DESC
    """)
    
    for row in entity_types:
        print(f"  {row['entity_type']}: {row['count']} entities")
    
    # 3. Search for finance/trading related entities
    print("\n" + "=" * 80)
    print("Finance/Trading Related Entities")
    print("=" * 80)
    
    finance_keywords = [
        'option', 'call', 'put', 'spread', 'straddle', 'strangle', 
        'butterfly', 'condor', 'collar', 'strategy', 'trading', 
        'derivative', 'hedge', 'volatility', 'premium', 'strike'
    ]
    
    all_finance_entities = []
    
    for keyword in finance_keywords:
        results = await db.fetch(f"""
            SELECT 
                properties::json->>'entity_id' as entity_id,
                properties::json->>'description' as description,
                properties::json->>'entity_type' as entity_type
            FROM chunk_entity_relation._ag_label_vertex
            WHERE properties::json->>'entity_id' ILIKE '%{keyword}%'
               OR properties::json->>'description' ILIKE '%{keyword}%'
            LIMIT 20
        """)
        
        if results:
            print(f"\nEntities containing '{keyword}':")
            for row in results[:5]:  # Show top 5 for each keyword
                all_finance_entities.append(row)
                print(f"  - {row['entity_id']} ({row['entity_type']})")
                desc = row['description'] or ''
                if desc:
                    print(f"    {desc[:100]}...")
    
    # 4. Get source files
    print("\n" + "=" * 80)
    print("Source Files in Knowledge Graph")
    print("=" * 80)
    
    sources = await db.fetch("""
        SELECT DISTINCT properties::json->>'file_path' as file_path, COUNT(*) as entity_count
        FROM chunk_entity_relation._ag_label_vertex
        WHERE properties::json->>'file_path' IS NOT NULL
        GROUP BY properties::json->>'file_path'
        ORDER BY entity_count DESC
        LIMIT 10
    """)
    
    print("\nTop source files by entity count:")
    for row in sources:
        if row['file_path']:
            print(f"  {row['file_path']}: {row['entity_count']} entities")
    
    # 5. Analyze relationships
    print("\n" + "=" * 80)
    print("Relationship Analysis")
    print("=" * 80)
    
    edge_count = await db.fetchval("""
        SELECT COUNT(*) FROM chunk_entity_relation._ag_label_edge
    """)
    print(f"\nTotal relationships: {edge_count}")
    
    # Get relationship types
    rel_types = await db.fetch("""
        SELECT properties::json->>'relationship' as rel_type, COUNT(*) as count
        FROM chunk_entity_relation._ag_label_edge
        WHERE properties::json->>'relationship' IS NOT NULL
        GROUP BY properties::json->>'relationship'
        ORDER BY count DESC
        LIMIT 10
    """)
    
    if rel_types:
        print("\nTop relationship types:")
        for row in rel_types:
            if row['rel_type']:
                print(f"  {row['rel_type']}: {row['count']}")
    
    # 6. Provide search recommendations
    print("\n" + "=" * 80)
    print("Search Recommendations")
    print("=" * 80)
    
    # Deduplicate finance entities
    unique_finance_entities = {}
    for entity in all_finance_entities:
        entity_id = entity['entity_id']
        if entity_id not in unique_finance_entities:
            unique_finance_entities[entity_id] = entity
    
    if unique_finance_entities:
        print(f"\nFound {len(unique_finance_entities)} unique finance-related entities.")
        print("\nRecommended search queries based on available data:")
        
        # Group by entity type
        by_type = Counter(e['entity_type'] for e in unique_finance_entities.values())
        
        for entity_type, count in by_type.most_common():
            print(f"\n{entity_type.title()}s ({count} found):")
            examples = [e for e in unique_finance_entities.values() if e['entity_type'] == entity_type]
            for example in examples[:3]:
                print(f"  - Search for: '{example['entity_id']}'")
    else:
        print("\nNo specific options/trading strategy entities found.")
        print("The knowledge graph appears to contain general entities but not")
        print("specific options trading strategies.")
        print("\nTo add options strategies content:")
        print("1. Crawl websites with options trading content")
        print("2. Build knowledge graph from the crawled data")
        print("3. Then search for specific strategies")
    
    await close_db_connection()


async def suggest_crawl_sources():
    """Suggest sources to crawl for options strategies content."""
    print("\n" + "=" * 80)
    print("Suggested Sources for Options Strategies Content")
    print("=" * 80)
    
    print("\nTo populate your knowledge graph with options strategies, consider crawling:")
    print("\n1. Educational sites:")
    print("   - Investopedia options section")
    print("   - CBOE education center")
    print("   - Options Industry Council (OIC)")
    
    print("\n2. Broker education pages:")
    print("   - Interactive Brokers options education")
    print("   - TD Ameritrade options courses")
    print("   - Fidelity options learning center")
    
    print("\n3. Options-focused sites:")
    print("   - OptionAlpha educational content")
    print("   - TastyTrade learn center")
    print("   - Options Playbook")
    
    print("\nExample crawl command:")
    print("   Use the 'smart_crawl_url' tool with URLs like:")
    print("   - https://www.investopedia.com/options-basics-tutorial-4583012")
    print("   - https://www.optionseducation.org/strategies")


async def main():
    """Run the analysis."""
    await analyze_knowledge_graph()
    await suggest_crawl_sources()


if __name__ == "__main__":
    asyncio.run(main())
