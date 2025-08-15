"""
End-to-end tests for RAG System
Tests the complete flow of content query handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rag_system import RAGSystem
from search_tools import ToolManager
from tests.fixtures.mock_data import SAMPLE_QUERIES


class TestRAGSystem:
    """Test suite for RAG system end-to-end content query handling"""
    
    def test_content_search_query(self, rag_system):
        """Test handling of content search queries"""
        # Mock the AI generator to simulate tool use and response
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 id="tool_1", input={"query": "What is MCP?"})
        ]
        
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="MCP is the Model Context Protocol that enables AI integration.")]
        
        rag_system.ai_generator.client.messages.create.side_effect = [
            mock_response, mock_final
        ]
        
        # Execute query
        response, sources = rag_system.query("What is MCP?")
        
        # Assertions
        assert "Model Context Protocol" in response
        assert isinstance(sources, list)
        assert len(sources) > 0
        
    def test_filtered_search_query(self, rag_system):
        """Test handling of filtered search queries"""
        # Mock the AI generator to use search with filters
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 id="tool_2", input={
                     "query": "architecture",
                     "course_name": "MCP",
                     "lesson_number": 2
                 })
        ]
        
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="Lesson 2 of MCP covers the architecture components.")]
        
        rag_system.ai_generator.client.messages.create.side_effect = [
            mock_response, mock_final
        ]
        
        # Execute filtered query
        response, sources = rag_system.query("What is covered in lesson 2 of MCP?")
        
        # Assertions
        assert "architecture" in response.lower() or "lesson 2" in response.lower()
        
    def test_course_specific_query(self, rag_system):
        """Test handling of course-specific queries"""
        # Mock the AI generator
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 id="tool_3", input={
                     "query": "course content",
                     "course_name": "Advanced Retrieval"
                 })
        ]
        
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="The Advanced Retrieval course teaches embeddings and vector search.")]
        
        rag_system.ai_generator.client.messages.create.side_effect = [
            mock_response, mock_final
        ]
        
        # Execute query
        response, sources = rag_system.query("What does the Advanced Retrieval course teach?")
        
        # Assertions
        assert "embeddings" in response.lower() or "retrieval" in response.lower()
        
    def test_session_management(self, rag_system):
        """Test session management and conversation history"""
        # Mock responses for multiple queries
        responses = [
            Mock(stop_reason="end_turn", content=[Mock(text="First response about MCP.")]),
            Mock(stop_reason="end_turn", content=[Mock(text="Second response with context.")])
        ]
        
        rag_system.ai_generator.client.messages.create.side_effect = responses
        
        # First query with session
        response1, _ = rag_system.query("What is MCP?", session_id="test_session")
        assert "First response" in response1
        
        # Second query with same session - should have history
        response2, _ = rag_system.query("Tell me more", session_id="test_session")
        assert "Second response" in response2
        
        # Verify conversation history was passed
        second_call = rag_system.ai_generator.client.messages.create.call_args_list[1]
        assert second_call is not None
        
    def test_source_attribution(self, rag_system):
        """Test that sources are properly tracked and returned"""
        # Set up mock tool manager with sources
        rag_system.tool_manager.get_last_sources.return_value = [
            {"text": "MCP Course - Lesson 1", "link": "https://example.com/lesson1"},
            {"text": "MCP Course - Lesson 2", "link": "https://example.com/lesson2"}
        ]
        
        # Mock AI response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with sources.")]
        
        rag_system.ai_generator.client.messages.create.return_value = mock_response
        
        # Execute query
        response, sources = rag_system.query("Query for sources")
        
        # Assertions
        assert len(sources) == 2
        assert sources[0]["text"] == "MCP Course - Lesson 1"
        assert sources[0]["link"] == "https://example.com/lesson1"
        
        # Verify sources were reset after retrieval
        rag_system.tool_manager.reset_sources.assert_called_once()
        
    def test_empty_results_handling(self, rag_system):
        """Test handling when search returns no results"""
        # Mock tool execution to return no results
        rag_system.tool_manager.execute_tool.return_value = "No relevant content found."
        
        # Mock AI response handling empty results
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 id="tool_4", input={"query": "nonexistent topic"})
        ]
        
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="I couldn't find information about that topic.")]
        
        rag_system.ai_generator.client.messages.create.side_effect = [
            mock_response, mock_final
        ]
        
        # Execute query
        response, sources = rag_system.query("Tell me about nonexistent topic")
        
        # Assertions
        assert "couldn't find" in response.lower() or "no" in response.lower()
        assert len(sources) == 0 or sources == []
        
    def test_query_without_session(self, rag_system):
        """Test query execution without session ID"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response without session.")]
        
        rag_system.ai_generator.client.messages.create.return_value = mock_response
        
        # Execute without session
        response, sources = rag_system.query("Query without session")
        
        # Assertions
        assert response == "Response without session."
        # Verify no session methods were called
        assert not rag_system.session_manager.get_conversation_history.called
        assert not rag_system.session_manager.add_exchange.called
        
    def test_prompt_formatting(self, rag_system):
        """Test that queries are properly formatted as prompts"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response.")]
        
        rag_system.ai_generator.client.messages.create.return_value = mock_response
        
        # Execute query
        rag_system.query("Simple question")
        
        # Check prompt formatting
        call_args = rag_system.ai_generator.generate_response.call_args
        assert "Answer this question about course materials:" in call_args[1]["query"]
        assert "Simple question" in call_args[1]["query"]
        
    def test_tool_definitions_passed(self, rag_system):
        """Test that tool definitions are passed to AI generator"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response.")]
        
        rag_system.ai_generator.client.messages.create.return_value = mock_response
        
        # Execute query
        rag_system.query("Test query")
        
        # Check tool definitions were passed
        call_args = rag_system.ai_generator.generate_response.call_args[1]
        assert "tools" in call_args
        tools = call_args["tools"]
        
        # Verify both tools are present
        tool_names = [tool["name"] for tool in tools]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names
        
    def test_error_propagation(self, rag_system):
        """Test that errors are properly handled and don't crash the system"""
        # Mock AI generator to raise an exception
        rag_system.ai_generator.generate_response.side_effect = Exception("API Error")
        
        # Execute query - should handle error gracefully
        with pytest.raises(Exception) as exc_info:
            rag_system.query("Query that causes error")
        
        assert "API Error" in str(exc_info.value)
        
    def test_multiple_queries_different_types(self, rag_system):
        """Test handling of different query types in sequence"""
        # Mock different response types
        responses = [
            # Content query response
            Mock(stop_reason="tool_use", content=[
                Mock(type="tool_use", name="search_course_content",
                     id="t1", input={"query": "MCP"})
            ]),
            Mock(stop_reason="end_turn", content=[Mock(text="MCP is a protocol.")]),
            
            # Outline query response
            Mock(stop_reason="tool_use", content=[
                Mock(type="tool_use", name="get_course_outline",
                     id="t2", input={"course_name": "MCP"})
            ]),
            Mock(stop_reason="end_turn", content=[Mock(text="MCP has 4 lessons.")]),
            
            # General query response (no tools)
            Mock(stop_reason="end_turn", content=[Mock(text="Machine learning is AI.")])
        ]
        
        rag_system.ai_generator.client.messages.create.side_effect = responses
        
        # Execute different query types
        response1, _ = rag_system.query("What is MCP?")
        assert "protocol" in response1.lower()
        
        response2, _ = rag_system.query("What lessons are in MCP?")
        assert "4 lessons" in response2.lower()
        
        response3, _ = rag_system.query("What is machine learning?")
        assert "AI" in response3
        
    def test_course_analytics_integration(self, rag_system):
        """Test that course analytics work with the RAG system"""
        # Get analytics
        analytics = rag_system.get_course_analytics()
        
        # Assertions
        assert "total_courses" in analytics
        assert "course_titles" in analytics
        assert analytics["total_courses"] == 2
        assert len(analytics["course_titles"]) == 2