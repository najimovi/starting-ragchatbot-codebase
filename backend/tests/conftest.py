"""
Shared test fixtures and configuration for all tests
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ai_generator import AIGenerator
from config import Config
from rag_system import RAGSystem
from search_tools import CourseOutlineTool, CourseSearchTool, ToolManager
from vector_store import VectorStore

from tests.fixtures.mock_data import (
    SAMPLE_TOOL_RESPONSES,
    create_sample_search_results,
)


# Fixtures for VectorStore
@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing"""
    mock_store = Mock(spec=VectorStore)

    # Mock the search method
    def mock_search(query, course_name=None, lesson_number=None, limit=None):
        if "error" in query.lower():
            return create_sample_search_results("error")
        elif "empty" in query.lower():
            return create_sample_search_results("empty")
        elif "mcp" in query.lower():
            return create_sample_search_results("mcp")
        elif "embedding" in query.lower():
            return create_sample_search_results("embeddings")
        else:
            return create_sample_search_results("default")

    mock_store.search.side_effect = mock_search

    # Mock the _resolve_course_name method (for CourseOutlineTool)
    def mock_resolve_course_name(course_name):
        if "mcp" in course_name.lower():
            return "MCP: Build Rich-Context AI Apps with Anthropic"
        elif "advanced" in course_name.lower() or "retrieval" in course_name.lower():
            return "Advanced Retrieval for AI with Chroma"
        elif "python" in course_name.lower():
            return None  # Course not found
        else:
            return None

    mock_store._resolve_course_name.side_effect = mock_resolve_course_name

    # Mock get_lesson_link method
    def mock_get_lesson_link(course_title, lesson_number):
        if "MCP" in course_title:
            if lesson_number < 4:
                return f"https://example.com/lesson{lesson_number}"
        elif "Advanced" in course_title:
            if lesson_number < 3:
                return f"https://example.com/ar-lesson{lesson_number}"
        return None

    mock_store.get_lesson_link.side_effect = mock_get_lesson_link

    # Mock course_catalog for CourseOutlineTool
    mock_catalog = Mock()

    def mock_catalog_get(ids=None):
        if ids and ids[0] == "MCP: Build Rich-Context AI Apps with Anthropic":
            return {
                "metadatas": [
                    {
                        "title": "MCP: Build Rich-Context AI Apps with Anthropic",
                        "course_link": "https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/",
                        "lessons_json": '[{"lesson_number": 0, "lesson_title": "Introduction", "lesson_link": "https://example.com/lesson0"}, {"lesson_number": 1, "lesson_title": "Why MCP", "lesson_link": "https://example.com/lesson1"}, {"lesson_number": 2, "lesson_title": "MCP Architecture", "lesson_link": "https://example.com/lesson2"}, {"lesson_number": 3, "lesson_title": "Chatbot Example", "lesson_link": "https://example.com/lesson3"}]',
                    }
                ]
            }
        elif ids and ids[0] == "Advanced Retrieval for AI with Chroma":
            return {
                "metadatas": [
                    {
                        "title": "Advanced Retrieval for AI with Chroma",
                        "course_link": "https://www.deeplearning.ai/short-courses/advanced-retrieval-for-ai/",
                        "lessons_json": '[{"lesson_number": 0, "lesson_title": "Introduction", "lesson_link": "https://example.com/ar-lesson0"}, {"lesson_number": 1, "lesson_title": "Overview Of Embeddings Based Retrieval", "lesson_link": "https://example.com/ar-lesson1"}, {"lesson_number": 2, "lesson_title": "Pitfalls Of Retrieval", "lesson_link": "https://example.com/ar-lesson2"}]',
                    }
                ]
            }
        return None

    mock_catalog.get.side_effect = mock_catalog_get
    mock_store.course_catalog = mock_catalog

    # Mock other methods as needed
    mock_store.get_existing_course_titles.return_value = [
        "MCP: Build Rich-Context AI Apps with Anthropic",
        "Advanced Retrieval for AI with Chroma",
    ]
    mock_store.get_course_count.return_value = 2

    return mock_store


# Fixtures for search tools
@pytest.fixture
def course_search_tool(mock_vector_store):
    """Create a CourseSearchTool with mocked vector store"""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def course_outline_tool(mock_vector_store):
    """Create a CourseOutlineTool with mocked vector store"""
    return CourseOutlineTool(mock_vector_store)


@pytest.fixture
def tool_manager(course_search_tool, course_outline_tool):
    """Create a ToolManager with registered tools"""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    manager.register_tool(course_outline_tool)
    return manager


# Fixtures for AI Generator
@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    mock_client = Mock()

    # Create mock response
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [Mock(text="This is a test response about MCP.")]

    mock_client.messages.create.return_value = mock_response

    return mock_client


@pytest.fixture
def ai_generator(mock_anthropic_client):
    """Create an AIGenerator with mocked Anthropic client"""
    with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value = mock_anthropic_client
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-test")
        return generator


# Fixtures for RAG System
@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock(spec=Config)
    config.ANTHROPIC_API_KEY = "test-key"
    config.ANTHROPIC_MODEL = "claude-sonnet-test"
    config.EMBEDDING_MODEL = "test-embeddings"
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.CHROMA_PATH = "./test_chroma_db"
    return config


@pytest.fixture
def rag_system(mock_config, mock_vector_store, ai_generator):
    """Create a RAG system with mocked components"""
    with patch("rag_system.VectorStore") as mock_vs_class:
        with patch("rag_system.AIGenerator") as mock_ai_class:
            mock_vs_class.return_value = mock_vector_store
            mock_ai_class.return_value = ai_generator

            system = RAGSystem(mock_config)
            return system


# Utility fixtures
@pytest.fixture
def sample_search_results():
    """Provide sample search results for testing"""
    return {
        "mcp": create_sample_search_results("mcp"),
        "embeddings": create_sample_search_results("embeddings"),
        "empty": create_sample_search_results("empty"),
        "error": create_sample_search_results("error"),
    }


@pytest.fixture
def sample_tool_responses():
    """Provide sample tool responses for testing"""
    return SAMPLE_TOOL_RESPONSES
