"""
Unit tests for CourseSearchTool
Tests the execute method with various scenarios
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool.execute() method"""

    def test_execute_with_valid_query_no_filters(self, course_search_tool):
        """Test execute with a valid query and no filters"""
        # Execute the search
        result = course_search_tool.execute(query="What is MCP?")

        # Assertions
        assert result is not None
        assert "MCP: Build Rich-Context AI Apps with Anthropic" in result
        assert "Model Context Protocol" in result
        assert len(course_search_tool.last_sources) > 0

    def test_execute_with_course_name_filter(self, course_search_tool):
        """Test execute with course name filter"""
        # Execute the search with course filter
        result = course_search_tool.execute(query="What is MCP?", course_name="MCP")

        # Assertions
        assert result is not None
        assert "MCP: Build Rich-Context AI Apps with Anthropic" in result
        assert "Model Context Protocol" in result

    def test_execute_with_lesson_number_filter(self, course_search_tool):
        """Test execute with lesson number filter"""
        # Execute the search with lesson filter
        result = course_search_tool.execute(query="What is MCP?", lesson_number=1)

        # Assertions
        assert result is not None
        assert "Lesson 1" in result
        assert "Model Context Protocol" in result

    def test_execute_with_both_filters(self, course_search_tool):
        """Test execute with both course and lesson filters"""
        # Execute the search with both filters
        result = course_search_tool.execute(
            query="What is MCP?", course_name="MCP", lesson_number=2
        )

        # Assertions
        assert result is not None
        assert "MCP: Build Rich-Context AI Apps with Anthropic" in result
        assert "Lesson 2" in result

    def test_execute_with_nonexistent_course(self, mock_vector_store):
        """Test execute with non-existent course name"""
        # Create tool with mock store
        tool = CourseSearchTool(mock_vector_store)

        # Mock the search to return error for non-existent course
        mock_vector_store.search.return_value = SearchResults.empty(
            "No course found matching 'Introduction to Python'"
        )

        # Execute the search
        result = tool.execute(
            query="What is Python?", course_name="Introduction to Python"
        )

        # Assertions
        assert "No course found matching 'Introduction to Python'" in result

    def test_execute_with_empty_results(self, course_search_tool):
        """Test execute when search returns empty results"""
        # Execute search that returns empty results
        result = course_search_tool.execute(query="empty query")

        # Assertions
        assert "No relevant content found" in result
        assert len(course_search_tool.last_sources) == 0

    def test_execute_with_empty_results_and_filters(self, mock_vector_store):
        """Test execute with empty results and filters"""
        # Create tool with mock store
        tool = CourseSearchTool(mock_vector_store)

        # Mock the search to return empty results
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[]
        )

        # Execute with course filter
        result = tool.execute(query="nonexistent content", course_name="MCP")
        assert "No relevant content found in course 'MCP'" in result

        # Execute with lesson filter
        result = tool.execute(query="nonexistent content", lesson_number=5)
        assert "No relevant content found in lesson 5" in result

        # Execute with both filters
        result = tool.execute(
            query="nonexistent content", course_name="MCP", lesson_number=5
        )
        assert "No relevant content found in course 'MCP' in lesson 5" in result

    def test_execute_with_search_error(self, course_search_tool):
        """Test execute when search returns an error"""
        # Execute search that triggers error
        result = course_search_tool.execute(query="error query")

        # Assertions
        assert "Search error" in result
        assert len(course_search_tool.last_sources) == 0

    def test_source_tracking(self, course_search_tool):
        """Test that sources are properly tracked"""
        # Execute a search
        result = course_search_tool.execute(query="What is MCP?")

        # Check sources
        sources = course_search_tool.last_sources
        assert len(sources) > 0
        assert all(isinstance(s, dict) for s in sources)
        assert all("text" in s for s in sources)

        # Check that lesson links are included when available
        for source in sources:
            if "Lesson" in source["text"]:
                # Should have a link for lessons
                assert "link" in source or source["link"] is None

    def test_result_formatting(self, course_search_tool):
        """Test that results are properly formatted"""
        # Execute a search
        result = course_search_tool.execute(query="What is MCP?")

        # Check formatting
        assert "[MCP: Build Rich-Context AI Apps with Anthropic" in result
        assert "Lesson" in result  # Should include lesson numbers
        assert "\n\n" in result  # Results should be separated

    def test_lesson_link_retrieval(self, mock_vector_store, course_search_tool):
        """Test that lesson links are retrieved when available"""
        # Execute a search for MCP content
        result = course_search_tool.execute(query="What is MCP?")

        # Check that get_lesson_link was called
        assert mock_vector_store.get_lesson_link.called

        # Check sources have links
        sources = course_search_tool.last_sources
        for source in sources:
            if "Lesson 1" in source["text"]:
                assert source.get("link") == "https://example.com/lesson1"
            elif "Lesson 2" in source["text"]:
                assert source.get("link") == "https://example.com/lesson2"

    def test_embeddings_query(self, course_search_tool):
        """Test execute with embeddings-related query"""
        # Execute search for embeddings
        result = course_search_tool.execute(query="What are embeddings?")

        # Assertions
        assert "Advanced Retrieval for AI with Chroma" in result
        assert "Embeddings are dense vector representations" in result
        assert len(course_search_tool.last_sources) > 0

    def test_multiple_results_handling(self, mock_vector_store):
        """Test handling of multiple search results"""
        # Create tool
        tool = CourseSearchTool(mock_vector_store)

        # Mock search to return multiple results
        mock_vector_store.search.return_value = SearchResults(
            documents=[
                "First result content",
                "Second result content",
                "Third result content",
            ],
            metadata=[
                {"course_title": "Course A", "lesson_number": 1, "chunk_index": 0},
                {"course_title": "Course A", "lesson_number": 2, "chunk_index": 1},
                {"course_title": "Course B", "lesson_number": 1, "chunk_index": 0},
            ],
            distances=[0.1, 0.2, 0.3],
        )

        # Execute search
        result = tool.execute(query="test query")

        # Check all results are included
        assert "First result content" in result
        assert "Second result content" in result
        assert "Third result content" in result
        assert "[Course A - Lesson 1]" in result
        assert "[Course A - Lesson 2]" in result
        assert "[Course B - Lesson 1]" in result

        # Check sources
        assert len(tool.last_sources) == 3
