"""
Shared test fixtures and configuration for all tests
"""
import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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


# API Testing Fixtures
@pytest.fixture
def mock_session_manager():
    """Create a mock session manager for API testing"""
    manager = Mock()
    manager.create_session.return_value = "test-session-123"
    manager.get_session.return_value = {
        "session_id": "test-session-123",
        "history": []
    }
    manager.add_to_history.return_value = None
    manager.clear_session.return_value = None
    manager.sessions = {}
    return manager

@pytest.fixture
def mock_document_processor():
    """Create a mock document processor for testing"""
    processor = Mock()
    processor.process_file.return_value = (
        Mock(title="Test Course", course_link="https://test.com"),
        [Mock(text="Chunk 1", metadata={"lesson": 1})]
    )
    processor.process_folder.return_value = (1, 10)
    return processor

@pytest.fixture
def api_test_data():
    """Provide test data for API testing"""
    return {
        "valid_query": {
            "query": "What is Python?",
            "session_id": "test-123"
        },
        "query_without_session": {
            "query": "Tell me about MCP"
        },
        "empty_query": {
            "query": "",
            "session_id": "test-456"
        },
        "special_chars_query": {
            "query": "What about 🐍 Python & <script>?",
            "session_id": "test-789"
        },
        "course_analytics": {
            "total_courses": 5,
            "course_titles": [
                "Python Basics",
                "Advanced Python",
                "MCP: Build Rich-Context AI Apps",
                "Machine Learning Fundamentals",
                "Data Science with Python"
            ]
        }
    }

@pytest.fixture
def mock_fastapi_dependencies():
    """Mock FastAPI dependencies for testing"""
    deps = {
        "config": Mock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-test",
            CHROMA_PATH="./test_db"
        ),
        "vector_store": Mock(spec=VectorStore),
        "ai_generator": Mock(spec=AIGenerator),
        "rag_system": Mock()
    }
    
    # Setup RAG system mock
    deps["rag_system"].query.return_value = (
        "Test response",
        ["Source 1", "Source 2"]
    )
    deps["rag_system"].get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course 1", "Course 2"]
    }
    deps["rag_system"].session_manager = Mock()
    deps["rag_system"].session_manager.create_session.return_value = "new-session-id"
    
    return deps

@pytest.fixture
def async_mock_client():
    """Create an async mock for HTTP client testing"""
    mock = AsyncMock()
    mock.post.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value={
            "answer": "Test answer",
            "sources": [],
            "session_id": "test-session"
        })
    )
    mock.get.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value={
            "total_courses": 2,
            "course_titles": ["Course 1", "Course 2"]
        })
    )
    return mock

# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

@pytest.fixture
def cleanup_chroma_db():
    """Cleanup ChromaDB test data after tests"""
    yield
    # Cleanup test database if it exists
    import shutil
    test_db_path = "./test_chroma_db"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)

# Async test support
@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock external services
@pytest.fixture
def mock_anthropic_service():
    """Mock Anthropic API service"""
    with patch('anthropic.Anthropic') as mock_anthropic:
        client = Mock()
        client.messages.create.return_value = Mock(
            content=[Mock(text="Mocked AI response")],
            stop_reason="end_turn"
        )
        mock_anthropic.return_value = client
        yield client

@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client"""
    with patch('chromadb.Client') as mock_client:
        client = Mock()
        collection = Mock()
        collection.add.return_value = None
        collection.query.return_value = {
            'documents': [["Doc 1", "Doc 2"]],
            'metadatas': [[{"source": "test1"}, {"source": "test2"}]],
            'distances': [[0.1, 0.2]]
        }
        collection.get.return_value = {
            'documents': ["Doc 1"],
            'metadatas': [{"source": "test"}]
        }
        client.get_or_create_collection.return_value = collection
        mock_client.return_value = client
        yield client

# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Fixture for measuring test performance"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 1 second")
    config.addinivalue_line("markers", "requires_api_key: Tests that require API keys")
