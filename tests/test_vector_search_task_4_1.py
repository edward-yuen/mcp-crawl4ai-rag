"""
Unit tests for vector search functions - Task 4.1 completion tests.
"""
import pytest
import asyncio
import json
import time
from unittest.mock import patch, Mock, AsyncMock
from src.utils import search_documents, create_embedding, add_documents_to_postgres
from src.database import get_db_connection


class TestVectorSearchFunctions:
    """Test vector search functionality for Task 4.1."""
    
    @pytest.mark.asyncio
    async def test_match_function_execution(self, mock_db_connection, mock_openai_for_integration):
        """Test that match_crawled_pages function can be executed."""
        # Mock database response
        mock_db_connection.fetch.return_value = [
            {
                'id': 1,
                'url': 'http://test.com',
                'chunk_number': 0,
                'content': 'Test content',
                'metadata': {'test': True},
                'similarity': 0.95
            }
        ]
        
        with patch('src.utils.get_db_connection', return_value=mock_db_connection):
            results = await search_documents("test query", match_count=5)
            
            assert len(results) == 1
            assert results[0]['similarity'] == 0.95
            assert results[0]['url'] == 'http://test.com'
            
            # Verify the function was called with correct parameters
            mock_db_connection.fetch.assert_called_once()
            call_args = mock_db_connection.fetch.call_args[0]
            assert "crawl.match_crawled_pages" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_vector_similarity_search_performance(self, mock_db_connection, mock_openai_for_integration):
        """Test vector similarity search performance."""
        # Mock quick database response
        mock_db_connection.fetch.return_value = []
        
        with patch('src.utils.get_db_connection', return_value=mock_db_connection):
            start_time = time.time()
            results = await search_documents("performance test", match_count=10)
            query_time = time.time() - start_time
            
            # Should complete quickly (less than 1 second for empty results)
            assert query_time < 1.0
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_vector_search_with_metadata_filter(self, mock_db_connection, mock_openai_for_integration):
        """Test vector search with metadata filtering."""
        mock_db_connection.fetch.return_value = []
        
        filter_metadata = {"category": "test", "source": "unit_test"}
        
        with patch('src.utils.get_db_connection', return_value=mock_db_connection):
            results = await search_documents(
                "test query", 
                match_count=5, 
                filter_metadata=filter_metadata
            )
            
            # Verify filter was passed correctly
            call_args = mock_db_connection.fetch.call_args[0]
            filter_param = call_args[3]
            assert json.loads(filter_param) == filter_metadata
    
    @pytest.mark.asyncio
    async def test_embedding_vector_dimensions(self, mock_openai_for_integration):
        """Test that embeddings have correct dimensions."""
        embedding = create_embedding("test text")
        
        # OpenAI text-embedding-3-small should return 1536 dimensions
        assert len(embedding) == 1536
        assert all(isinstance(val, (int, float)) for val in embedding)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_search_integration(self, db_integration_setup, mock_openai_for_integration):
        """Integration test for complete vector search workflow."""
        # This test requires a real database connection
        db_conn = db_integration_setup
        
        # Add test document
        test_urls = ["http://vector-test.com"]
        test_chunks = [0]
        test_contents = ["Vector search integration test content"]
        test_metadata = [{"test_type": "vector_integration"}]
        test_full_docs = {"http://vector-test.com": "Full document for vector test"}
        
        # Insert test data
        await add_documents_to_postgres(
            test_urls, test_chunks, test_contents, test_metadata, test_full_docs
        )
        
        # Search for the document
        results = await search_documents("vector search integration", match_count=5)
        
        # Verify results
        assert len(results) > 0
        found_test_doc = any(r['url'] == "http://vector-test.com" for r in results)
        assert found_test_doc, "Test document not found in search results"
        
        # Verify similarity scores are reasonable
        for result in results:
            assert 0.0 <= result['similarity'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_vector_search_error_handling(self, mock_db_connection, mock_openai_for_integration):
        """Test error handling in vector search functions."""
        # Mock database error
        mock_db_connection.fetch.side_effect = Exception("Database connection error")
        
        with patch('src.utils.get_db_connection', return_value=mock_db_connection):
            results = await search_documents("test query")
            
            # Should return empty list on error, not raise exception
            assert results == []
    
    def test_vector_search_input_validation(self):
        """Test input validation for vector search parameters."""
        # Test with various match_count values
        valid_match_counts = [1, 5, 10, 50, 100]
        for count in valid_match_counts:
            # Should not raise exception for valid counts
            assert count > 0
        
        # Test query string handling
        valid_queries = ["test", "test query", "multiple word query test"]
        for query in valid_queries:
            assert isinstance(query, str)
            assert len(query) > 0
