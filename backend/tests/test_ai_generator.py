"""
Integration tests for AIGenerator
Tests tool selection and execution based on query types
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool, CourseOutlineTool


class TestAIGenerator:
    """Test suite for AIGenerator tool selection and execution"""
    
    def test_content_query_uses_search_tool(self, ai_generator, tool_manager):
        """Test that content queries trigger search_course_content tool"""
        # Mock the response to indicate tool use
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="search_course_content", 
                 id="tool_123", input={"query": "What is MCP?"})
        ]
        
        # Mock the follow-up response after tool execution
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="MCP is the Model Context Protocol.")]
        
        # Set up the mock client to return both responses
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response
        ]
        
        # Execute with a content query
        result = ai_generator.generate_response(
            query="What is MCP?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Assertions
        assert result == "MCP is the Model Context Protocol."
        assert ai_generator.client.messages.create.call_count == 2
        
        # Check that the tool was selected correctly
        first_call = ai_generator.client.messages.create.call_args_list[0]
        assert "tools" in first_call[1]
        
    def test_outline_query_uses_outline_tool(self, ai_generator, tool_manager):
        """Test that outline queries trigger get_course_outline tool"""
        # Mock the response to indicate outline tool use
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="get_course_outline",
                 id="tool_456", input={"course_name": "MCP"})
        ]
        
        # Mock the follow-up response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="The MCP course has 4 lessons.")]
        
        # Set up the mock client
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response
        ]
        
        # Execute with an outline query
        result = ai_generator.generate_response(
            query="What lessons are in the MCP course?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Assertions
        assert result == "The MCP course has 4 lessons."
        assert ai_generator.client.messages.create.call_count == 2
        
    def test_general_query_no_tools(self, ai_generator, tool_manager):
        """Test that general knowledge queries don't use tools"""
        # Mock response without tool use
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Machine learning is a subset of AI.")]
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # Execute with a general query
        result = ai_generator.generate_response(
            query="What is machine learning?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Assertions
        assert result == "Machine learning is a subset of AI."
        assert ai_generator.client.messages.create.call_count == 1
        
    def test_tool_execution_flow(self, ai_generator):
        """Test the complete tool execution flow"""
        # Create a mock tool manager
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Tool execution result"
        mock_tool_manager.get_tool_definitions.return_value = [
            {"name": "test_tool", "description": "Test tool"}
        ]
        
        # Mock initial response with tool use
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="test_tool",
                 id="tool_789", input={"param": "value"})
        ]
        
        # Mock final response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="Final answer based on tool result.")]
        
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response
        ]
        
        # Execute
        result = ai_generator.generate_response(
            query="Test query",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager
        )
        
        # Assertions
        assert result == "Final answer based on tool result."
        mock_tool_manager.execute_tool.assert_called_once_with("test_tool", param="value")
        assert ai_generator.client.messages.create.call_count == 2
        
    def test_conversation_history_handling(self, ai_generator):
        """Test that conversation history is properly included"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with context.")]
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # Execute with conversation history
        history = "User: Previous question\nAssistant: Previous answer"
        result = ai_generator.generate_response(
            query="Follow-up question",
            conversation_history=history
        )
        
        # Check that history was included in system prompt
        call_args = ai_generator.client.messages.create.call_args[1]
        assert "Previous conversation:" in call_args["system"]
        assert history in call_args["system"]
        
    def test_no_tools_provided(self, ai_generator):
        """Test behavior when no tools are provided"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response without tools.")]
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # Execute without tools
        result = ai_generator.generate_response(
            query="Question without tools"
        )
        
        # Assertions
        assert result == "Response without tools."
        call_args = ai_generator.client.messages.create.call_args[1]
        assert "tools" not in call_args
        
    def test_multiple_tool_calls(self, ai_generator):
        """Test handling of multiple tool calls in one response"""
        # Create mock tool manager
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = [
            "First tool result",
            "Second tool result"
        ]
        
        # Mock response with multiple tool uses
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="tool1", id="id1", input={"q": "query1"}),
            Mock(type="tool_use", name="tool2", id="id2", input={"q": "query2"})
        ]
        
        # Mock final response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="Combined results.")]
        
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response
        ]
        
        # Execute
        result = ai_generator.generate_response(
            query="Complex query",
            tools=[{"name": "tool1"}, {"name": "tool2"}],
            tool_manager=mock_tool_manager
        )
        
        # Assertions
        assert result == "Combined results."
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call("tool1", q="query1")
        mock_tool_manager.execute_tool.assert_any_call("tool2", q="query2")
        
    def test_tool_error_handling(self, ai_generator):
        """Test handling of tool execution errors"""
        # Create mock tool manager that raises error
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Error: Tool execution failed"
        
        # Mock response with tool use
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(type="tool_use", name="failing_tool",
                 id="tool_error", input={})
        ]
        
        # Mock final response handling the error
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="I encountered an error with the tool.")]
        
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response
        ]
        
        # Execute
        result = ai_generator.generate_response(
            query="Query that causes error",
            tools=[{"name": "failing_tool"}],
            tool_manager=mock_tool_manager
        )
        
        # Assertions
        assert "error" in result.lower()
        
    def test_system_prompt_content(self, ai_generator):
        """Test that system prompt contains expected content"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response.")]
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # Execute
        ai_generator.generate_response(query="Test query")
        
        # Check system prompt
        call_args = ai_generator.client.messages.create.call_args[1]
        system_prompt = call_args["system"]
        
        # Verify key elements are in system prompt
        assert "search_course_content" in system_prompt
        assert "get_course_outline" in system_prompt
        assert "Course outline/structure questions" in system_prompt
        assert "Content/topic questions" in system_prompt
        
    def test_temperature_setting(self, ai_generator):
        """Test that temperature is set to 0 for deterministic responses"""
        # Mock response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test.")]
        
        ai_generator.client.messages.create.return_value = mock_response
        
        # Execute
        ai_generator.generate_response(query="Test")
        
        # Check temperature
        call_args = ai_generator.client.messages.create.call_args[1]
        assert call_args["temperature"] == 0