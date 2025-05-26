"""
Test file for LightRAG schema integration.

This test verifies the lightrag_integration module and new MCP tools.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import json

from src.lightrag_integration import (
    search_lightrag_documents,
    get_lightrag_collections,
    get_lightrag_schema_info,
    search_multi_schema
)
from src.crawl4ai_mcp import (
    query_lightrag_schema,
    get_lightrag_info,
    multi_schema_search
)


class TestLightRAGIntegration:
    """Test the LightRAG schema integration functionality."""
    
    @pytest.mark.asyncio
    @patch('src.lightrag_integration.get_db_connection')
    @patch('src.lightrag_integration.create_embedding')
    async def test_search_lightrag_documents(self, mock_create_embedding, mock_get_db):
        """Test searching documents in lightrag schema."""
        # Setup mocks
        mock_embedding = [0.1] * 1536
        mock_create_embedding.return_value = mock_embedding
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock database results
        mock_results = [
            {
                'id': 1,
                'content': 'Test document 1',
                'metadata': {'source': 'test'},
                'similarity': 0.95
            },
            {
                'id': 2,
                'content': 'Test document 2',
                'metadata': {'source': 'test'},
                'similarity': 0.85
            }
        ]
        mock_db.fetch.return_value = mock_results
        
        # Test search
        results = await search_lightrag_documents("test query", match_count=5)
        
        # Verify
        assert len(results) == 2
        assert results[0]['content'] == 'Test document 1'
        assert results[0]['similarity'] == 0.95
        mock_create_embedding.assert_called_once_with("test query")
        mock_db.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.lightrag_integration.get_db_connection')
    async def test_get_lightrag_collections(self, mock_get_db):
        """Test retrieving collections from lightrag schema."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock database results
        mock_results = [
            {'collection_name': 'documents'},
            {'collection_name': 'knowledge_base'},
            {'collection_name': 'research'}
        ]
        mock_db.fetch.return_value = mock_results
        
        # Test get collections
        collections = await get_lightrag_collections()
        
        # Verify
        assert len(collections) == 3
        assert 'documents' in collections
        assert 'knowledge_base' in collections
        assert 'research' in collections
    
    @pytest.mark.asyncio
    @patch('src.lightrag_integration.get_db_connection')
    async def test_get_lightrag_schema_info(self, mock_get_db):
        """Test retrieving schema information."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock table results
        mock_tables = [
            {'table_name': 'documents'},
            {'table_name': 'embeddings'}
        ]
        
        # Mock column results
        mock_columns = [
            {
                'column_name': 'id',
                'data_type': 'bigint',
                'is_nullable': 'NO'
            },
            {
                'column_name': 'content',
                'data_type': 'text',
                'is_nullable': 'NO'
            },
            {
                'column_name': 'embedding',
                'data_type': 'USER-DEFINED',
                'is_nullable': 'YES'
            }
        ]
        
        # Set up mock to return different results based on query
        mock_db.fetch.side_effect = [mock_tables, mock_columns, mock_columns]
        
        # Test get schema info
        schema_info = await get_lightrag_schema_info()
        
        # Verify
        assert 'tables' in schema_info
        assert len(schema_info['tables']) == 2
        assert 'documents' in schema_info['tables']
        assert 'table_details' in schema_info
    
    @pytest.mark.asyncio
    @patch('src.lightrag_integration.get_db_connection')
    @patch('src.lightrag_integration.create_embedding')
    async def test_search_multi_schema(self, mock_create_embedding, mock_get_db):
        """Test searching across multiple schemas."""
        # Setup mocks
        mock_embedding = [0.1] * 1536
        mock_create_embedding.return_value = mock_embedding
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock crawl schema results
        mock_crawl_results = [
            {
                'id': 1,
                'url': 'https://example.com',
                'content': 'Crawled content',
                'metadata': {},
                'similarity': 0.9
            }
        ]
        
        # Mock lightrag results (called by search_lightrag_documents)
        mock_lightrag_results = [
            {
                'id': 2,
                'content': 'LightRAG content',
                'metadata': {},
                'similarity': 0.95
            }
        ]
        
        # Set up mock to return different results based on query
        mock_db.fetch.side_effect = [mock_crawl_results, mock_lightrag_results]
        
        # Test multi-schema search
        results = await search_multi_schema(
            "test query",
            schemas=["crawl", "lightrag"],
            match_count=5,
            combine_results=True
        )
        
        # Verify
        assert 'combined' in results
        assert 'by_schema' in results
        assert len(results['by_schema']) == 2
        assert 'crawl' in results['by_schema']
        assert 'lightrag' in results['by_schema']
        
        # Check combined results are sorted by similarity
        combined = results['combined']
        if len(combined) > 1:
            for i in range(len(combined) - 1):
                assert combined[i]['similarity'] >= combined[i+1]['similarity']


class TestLightRAGMCPTools:
    """Test the MCP tool functions for LightRAG integration."""
    
    @pytest.mark.asyncio
    @patch('src.crawl4ai_mcp.search_lightrag_documents')
    async def test_query_lightrag_schema_tool(self, mock_search):
        """Test the query_lightrag_schema MCP tool."""
        # Setup mock
        mock_search.return_value = [
            {
                'id': 1,
                'content': 'Test content',
                'metadata': {'source': 'test'},
                'similarity': 0.95
            }
        ]
        
        # Create mock context
        mock_ctx = Mock()
        
        # Test tool
        result = await query_lightrag_schema(
            mock_ctx,
            query="test query",
            collection="documents",
            match_count=5
        )
        
        # Parse result
        result_data = json.loads(result)
        
        # Verify
        assert result_data['success'] is True
        assert result_data['query'] == "test query"
        assert result_data['schema'] == "lightrag"
        assert result_data['collection_filter'] == "documents"
        assert len(result_data['results']) == 1
        assert result_data['results'][0]['content'] == 'Test content'
    
    @pytest.mark.asyncio
    @patch('src.crawl4ai_mcp.get_lightrag_schema_info')
    @patch('src.crawl4ai_mcp.get_lightrag_collections')
    async def test_get_lightrag_info_tool(self, mock_get_collections, mock_get_schema):
        """Test the get_lightrag_info MCP tool."""
        # Setup mocks
        mock_get_schema.return_value = {
            'tables': ['documents', 'embeddings'],
            'table_details': {}
        }
        mock_get_collections.return_value = ['documents', 'knowledge_base']
        
        # Create mock context
        mock_ctx = Mock()
        
        # Test tool
        result = await get_lightrag_info(mock_ctx)
        
        # Parse result
        result_data = json.loads(result)
        
        # Verify
        assert result_data['success'] is True
        assert 'schema_info' in result_data
        assert 'collections' in result_data
        assert len(result_data['collections']) == 2
        assert 'documents' in result_data['collections']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
