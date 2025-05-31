"""
Integration test for enhanced search tools.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.enhanced_search_tools import QueryAnalyzer


async def test_query_analyzer():
    """Test the QueryAnalyzer functionality."""
    print("Testing QueryAnalyzer...")
    
    # Test different query types
    test_queries = [
        ("find articles about Python programming", "document"),
        ("who is John Doe", "entity"),
        ("how are entities connected", "relationship"),
        ("MATCH (n) RETURN n", "cypher"),
        ("graph traversal community", "graph")
    ]
    
    for query, expected_type in test_queries:
        result = QueryAnalyzer.analyze_query(query)
        print(f"Query: '{query}' -> Type: {result['primary_type']} (Expected: {expected_type})")
        assert result['primary_type'] == expected_type, f"Expected {expected_type}, got {result['primary_type']}"
    
    print("PASS: QueryAnalyzer tests passed!")


async def main():
    """Run basic tests."""
    print("=== Enhanced Search Basic Tests ===\n")
    await test_query_analyzer()
    print("\n=== Tests completed! ===")


if __name__ == "__main__":
    asyncio.run(main())
