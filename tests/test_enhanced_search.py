"""
Tests for enhanced search tools.
"""
import pytest
from src.tools.enhanced_search_tools import QueryAnalyzer


class TestQueryAnalyzer:
    """Tests for the QueryAnalyzer class."""
    
    def test_analyze_document_query(self):
        """Test analysis of document-focused queries."""
        query = "find articles about machine learning content"
        result = QueryAnalyzer.analyze_query(query)
        
        assert result['primary_type'] == 'document'
        assert result['scores']['document'] > 0
        assert 'confidence' in result
    
    def test_analyze_entity_query(self):
        """Test analysis of entity-focused queries."""
        query = "who is John Doe person organization"
        result = QueryAnalyzer.analyze_query(query)
        
        assert result['primary_type'] == 'entity'
        assert result['scores']['entity'] > 0
        assert result['patterns']['has_entities'] == True
    
    def test_analyze_cypher_query(self):
        """Test analysis of Cypher queries."""
        query = "MATCH (n:Person) RETURN n.name"
        result = QueryAnalyzer.analyze_query(query)
        
        assert result['primary_type'] == 'cypher'
        assert result['patterns']['is_cypher'] == True
    
    def test_confidence_scoring(self):
        """Test that confidence scoring works correctly."""
        query = "document content article"
        result = QueryAnalyzer.analyze_query(query)
        
        assert result['confidence'] > 0
        assert result['confidence'] <= 1.0
