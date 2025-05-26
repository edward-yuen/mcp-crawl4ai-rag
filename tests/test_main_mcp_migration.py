"""
Test file for Task 3.1 - Main MCP Server PostgreSQL migration.

This test verifies that the updated crawl4ai_mcp.py file works correctly
with PostgreSQL instead of Supabase.
"""
import os
import sys
from pathlib import Path

# Ensure environment is set up before any module imports
os.environ["PORT"] = "8051"
os.environ["HOST"] = "0.0.0.0"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["OPENAI_API_KEY"] = "test_api_key"

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, List

# Now import the module - environment is already set
from src.crawl4ai_mcp import (
    Crawl4AIContext, 
    crawl4ai_lifespan,
    crawl_single_page,
    get_available_sources,
    perform_rag_query
)


class TestMainMCPServerMigration:
    """Test the main MCP server PostgreSQL migration."""
