"""
Test suite for the utils module.
"""
import pytest
import asyncio
import os
import json
from unittest.mock import patch, Mock, AsyncMock
from src.utils import (
    create_embedding,
    create_embeddings_batch,
    generate_contextual_embedding,
    process_chunk_with_context,
    add_documents_to_postgres,
    search_documents
)
from src.database import initialize_db_connection, close_db_connection


# Mock embedding vector for testing
MOCK_EMBEDDING = [0.1] * 1536


@pytest.fixture
async def mock_db_connection():
    """Fixture to mock database connection."""
    with patch('src.utils.get_db_connection') as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_openai():
    """Fixture to mock OpenAI API calls."""
    with patch('src.utils.openai') as mock:
        # Mock embeddings.create
        mock_response = Mock()
        mock_response.data = [Mock(embedding=MOCK_EMBEDDING)]
        mock.embeddings.create.return_value = mock_response
        
        # Mock chat completions
        mock_chat_response = Mock()
        mock_chat_response.choices = [
            Mock(message=Mock(content="This is contextual information"))
        ]
        mock.chat.completions.create.return_value = mock_chat_response
        
        yield mock


class TestEmbeddingFunctions:
    """Test embedding creation functions."""
    
    def test_create_embedding_success(self, mock_openai):
        """Test successful embedding creation."""
        result = create_embedding("test text")
        assert result == MOCK_EMBEDDING
        mock_openai.embeddings.create.assert_called_once()
    
    def test_create_embedding_failure(self, mock_openai):
        """Test embedding creation failure returns default embedding."""
        mock_openai.embeddings.create.side_effect = Exception("API Error")
        result = create_embedding("test text")
        assert len(result) == 1536
        assert all(x == 0.0 for x in result)
    
    def test_create_embeddings_batch_success(self, mock_openai):
        """Test successful batch embedding creation."""
        texts = ["text1", "text2", "text3"]
        mock_openai.embeddings.create.return_value.data = [
            Mock(embedding=MOCK_EMBEDDING) for _ in texts
        ]
        
        result = create_embeddings_batch(texts)
        assert len(result) == 3
        assert all(emb == MOCK_EMBEDDING for emb in result)
    
    def test_create_embeddings_batch_empty_input(self, mock_openai):
        """Test batch embedding with empty input."""
        result = create_embeddings_batch([])
        assert result == []
        mock_openai.embeddings.create.assert_not_called()


class TestContextualEmbedding:
    """Test contextual embedding functions."""
    
    @patch.dict(os.environ, {"MODEL_CHOICE": "gpt-4"})
    def test_generate_contextual_embedding_success(self, mock_openai):
        """Test successful contextual embedding generation."""
        full_doc = "This is a full document about AI."
        chunk = "AI is transformative."
        
        result, success = generate_contextual_embedding(full_doc, chunk)
        
        assert success is True
        assert "This is contextual information" in result
        assert chunk in result
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {"MODEL_CHOICE": "gpt-4"})
    def test_generate_contextual_embedding_failure(self, mock_openai):
        """Test contextual embedding generation failure."""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        full_doc = "This is a full document."
        chunk = "Test chunk."
        
        result, success = generate_contextual_embedding(full_doc, chunk)
        
        assert success is False
        assert result == chunk  # Should return original chunk on failure
    
    def test_process_chunk_with_context(self, mock_openai):
        """Test processing chunk with context wrapper function."""
        args = ("url", "content", "full_document")
        with patch('src.utils.generate_contextual_embedding') as mock_gen:
            mock_gen.return_value = ("contextual_content", True)
            
            result = process_chunk_with_context(args)
            
            assert result == ("contextual_content", True)
            mock_gen.assert_called_once_with("full_document", "content")


class TestDatabaseOperations:
    """Test database operations."""
    
    @pytest.mark.asyncio
    async def test_add_documents_to_postgres_basic(self, mock_db_connection, mock_openai):
        """Test basic document addition to PostgreSQL."""
        urls = ["http://example.com"]
        chunk_numbers = [0]
        contents = ["Test content"]
        metadatas = [{"source": "test"}]
        url_to_full_document = {"http://example.com": "Full document"}
        
        await add_documents_to_postgres(
            urls, chunk_numbers, contents, metadatas, url_to_full_document
        )
        
        # Verify delete was called
        mock_db_connection.execute.assert_called()
        # Verify insert was called via execute_many
        mock_db_connection.execute_many.assert_called()
    
    @pytest.mark.asyncio
    async def test_add_documents_to_postgres_batch_processing(self, mock_db_connection, mock_openai):
        """Test batch processing of documents."""
        # Create 25 documents to test batch processing (batch_size=20)
        urls = [f"http://example.com/{i}" for i in range(25)]
        chunk_numbers = list(range(25))
        contents = [f"Content {i}" for i in range(25)]
        metadatas = [{"index": i} for i in range(25)]
        url_to_full_document = {url: f"Full doc {i}" for i, url in enumerate(urls)}
        
        # Mock batch embeddings
        mock_openai.embeddings.create.return_value.data = [
            Mock(embedding=MOCK_EMBEDDING) for _ in range(20)
        ]
        
        await add_documents_to_postgres(
            urls, chunk_numbers, contents, metadatas, url_to_full_document, batch_size=20
        )
        
        # Should be called twice (20 + 5)
        assert mock_db_connection.execute_many.call_count == 2

    
    @pytest.mark.asyncio
    async def test_search_documents_basic(self, mock_db_connection, mock_openai):
        """Test basic document search."""
        # Mock database response
        mock_db_connection.fetch.return_value = [
            {
                'id': 1,
                'url': 'http://example.com',
                'chunk_number': 0,
                'content': 'Test content',
                'metadata': {'source': 'test'},
                'similarity': 0.95
            }
        ]
        
        results = await search_documents("search query", match_count=5)
        
        assert len(results) == 1
        assert results[0]['url'] == 'http://example.com'
        assert results[0]['similarity'] == 0.95
        mock_db_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_documents_with_filter(self, mock_db_connection, mock_openai):
        """Test document search with metadata filter."""
        mock_db_connection.fetch.return_value = []
        
        filter_metadata = {"source": "specific_source"}
        results = await search_documents("query", filter_metadata=filter_metadata)
        
        # Verify the filter was passed correctly
        call_args = mock_db_connection.fetch.call_args[0]
        assert json.loads(call_args[3]) == filter_metadata
    
    @pytest.mark.asyncio
    async def test_search_documents_error_handling(self, mock_db_connection, mock_openai):
        """Test search error handling."""
        mock_db_connection.fetch.side_effect = Exception("Database error")
        
        results = await search_documents("query")
        
        assert results == []  # Should return empty list on error


class TestIntegration:
    """Integration tests with real database (requires PostgreSQL with pgvector)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow(self):
        """Test complete workflow: add documents and search them."""
        # Skip if no database connection
        if not all([os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_DB")]):
            pytest.skip("Database environment variables not set")
        
        # Initialize real database connection
        await initialize_db_connection()
        
        try:
            # Add test documents
            urls = ["http://test.com/1", "http://test.com/2"]
            chunk_numbers = [0, 0]
            contents = ["Python is a programming language", "JavaScript is also a programming language"]
            metadatas = [{"lang": "python"}, {"lang": "javascript"}]
            url_to_full_document = {
                "http://test.com/1": "Full Python document",
                "http://test.com/2": "Full JavaScript document"
            }
            
            await add_documents_to_postgres(
                urls, chunk_numbers, contents, metadatas, url_to_full_document
            )
            
            # Search for documents
            results = await search_documents("programming language", match_count=2)
            
            assert len(results) > 0
            assert all('programming language' in r['content'] for r in results)
            
        finally:
            # Clean up
            await close_db_connection()
