"""
Tests for response formatting utilities.
"""
import pytest
import json
from datetime import datetime
from src.models.responses import (
    format_success_response,
    format_error_response,
    format_crawl_response,
    format_search_response,
    format_graph_response,
    format_list_response,
    format_batch_response,
    sanitize_response_data
)


class TestResponseFormatting:
    """Test suite for response formatting utilities."""

    def test_format_success_response(self):
        """Test basic success response formatting."""
        data = {"key": "value", "count": 42}
        response = format_success_response(data)
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["key"] == "value"
        assert result["count"] == 42
        assert "error" not in result

    def test_format_success_response_with_message(self):
        """Test success response with message."""
        data = {"result": "test"}
        response = format_success_response(data, message="Operation completed")
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["message"] == "Operation completed"
        assert result["result"] == "test"

    def test_format_error_response(self):
        """Test error response formatting."""
        response = format_error_response("Something went wrong")
        result = json.loads(response)
        
        assert result["success"] is False
        assert result["error"] == "Something went wrong"

    def test_format_error_response_with_exception(self):
        """Test error response with Exception object."""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            response = format_error_response(e)
            result = json.loads(response)
            
            assert result["success"] is False
            assert "Test exception" in result["error"]

    def test_format_error_response_with_context(self):
        """Test error response with context."""
        context = {"url": "https://example.com", "attempt": 3}
        response = format_error_response("Failed to connect", context=context)
        result = json.loads(response)
        
        assert result["success"] is False
        assert result["error"] == "Failed to connect"
        assert result["url"] == "https://example.com"
        assert result["attempt"] == 3

    def test_format_crawl_response_success(self):
        """Test successful crawl response."""
        response = format_crawl_response(
            url="https://example.com",
            success=True,
            pages_crawled=10,
            chunks_created=25,
            processing_time=3.14159
        )
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["pages_crawled"] == 10
        assert result["chunks_created"] == 25
        assert result["processing_time_seconds"] == 3.14

    def test_format_crawl_response_failure(self):
        """Test failed crawl response."""
        response = format_crawl_response(
            url="https://example.com",
            success=False,
            error="404 Not Found"
        )
        result = json.loads(response)
        
        assert result["success"] is False
        assert result["url"] == "https://example.com"
        assert result["error"] == "404 Not Found"

    def test_format_search_response(self):
        """Test search response formatting."""
        results = [
            {"title": "Result 1", "score": 0.95},
            {"title": "Result 2", "score": 0.87}
        ]
        response = format_search_response(
            query="test query",
            results=results,
            total_matches=100,
            source_filter="example.com",
            processing_time=0.123
        )
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["query"] == "test query"
        assert len(result["results"]) == 2
        assert result["result_count"] == 2
        assert result["total_matches"] == 100
        assert result["source_filter"] == "example.com"
        assert result["processing_time_seconds"] == 0.12

    def test_format_graph_response(self):
        """Test graph operation response."""
        response = format_graph_response(
            operation="find_path",
            result={"path": ["A", "B", "C"]},
            entity_count=3,
            relationship_count=2
        )
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["operation"] == "find_path"
        assert result["result"]["path"] == ["A", "B", "C"]
        assert result["entity_count"] == 3
        assert result["relationship_count"] == 2

    def test_format_list_response(self):
        """Test list response formatting."""
        items = ["source1.com", "source2.org", "source3.net"]
        response = format_list_response("sources", items)
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["sources"] == items
        assert result["sources_count"] == 3

    def test_format_batch_response(self):
        """Test batch operation response."""
        errors = ["Error 1", "Error 2", "Error 3"]
        response = format_batch_response(
            operation="bulk_import",
            total_items=100,
            successful_items=97,
            failed_items=3,
            errors=errors,
            processing_time=45.67
        )
        result = json.loads(response)
        
        assert result["success"] is True
        assert result["operation"] == "bulk_import"
        assert result["total_items"] == 100
        assert result["successful_items"] == 97
        assert result["failed_items"] == 3
        assert result["success_rate"] == 97.0
        assert result["errors"] == errors
        assert result["processing_time_seconds"] == 45.67

    def test_format_batch_response_error_truncation(self):
        """Test batch response with error truncation."""
        errors = [f"Error {i}" for i in range(20)]
        response = format_batch_response(
            operation="bulk_process",
            total_items=20,
            successful_items=0,
            failed_items=20,
            errors=errors
        )
        result = json.loads(response)
        
        assert len(result["errors"]) == 10  # Should truncate to 10
        assert result["errors_truncated"] is True
        assert result["total_errors"] == 20

    def test_sanitize_response_data(self):
        """Test data sanitization for JSON compatibility."""
        # Test datetime conversion
        now = datetime.now()
        data = {
            "timestamp": now,
            "bytes": b"hello world",
            "set": {1, 2, 3},
            "tuple": (4, 5, 6),
            "nested": {
                "datetime": now,
                "list": [b"bytes", now, None]
            }
        }
        
        sanitized = sanitize_response_data(data)
        
        assert isinstance(sanitized["timestamp"], str)
        assert sanitized["timestamp"] == now.isoformat()
        assert sanitized["bytes"] == "hello world"
        assert sanitized["set"] == [1, 2, 3]
        assert sanitized["tuple"] == [4, 5, 6]
        assert isinstance(sanitized["nested"]["datetime"], str)
        assert sanitized["nested"]["list"][0] == "bytes"
        assert sanitized["nested"]["list"][2] is None

    def test_json_serialization(self):
        """Test that all formatted responses are valid JSON."""
        # Test various response types
        responses = [
            format_success_response({"test": True}),
            format_error_response("error"),
            format_crawl_response("url", True, 1, 2),
            format_search_response("query", []),
            format_graph_response("op", {}),
            format_list_response("items", []),
            format_batch_response("op", 10, 8, 2)
        ]
        
        for response in responses:
            # Should not raise JSONDecodeError
            result = json.loads(response)
            assert isinstance(result, dict)
            assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
