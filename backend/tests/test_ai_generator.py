"""
Integration tests for AIGenerator
Tests tool selection and execution based on query types
Including sequential tool calling support
"""

import os
import sys
from unittest.mock import Mock

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from search_tools import ToolManager


class TestAIGenerator:
    """Test suite for AIGenerator tool selection and execution"""

    def test_content_query_uses_search_tool(self, ai_generator, tool_manager):
        """Test that content queries trigger search_course_content tool"""
        # Mock the response to indicate tool use
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                name="search_course_content",
                id="tool_123",
                input={"query": "What is MCP?"},
            )
        ]

        # Mock the follow-up response after tool execution
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="MCP is the Model Context Protocol.")]

        # Set up the mock client to return both responses
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response,
        ]

        # Execute with a content query
        result = ai_generator.generate_response(
            query="What is MCP?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
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
            Mock(
                type="tool_use",
                name="get_course_outline",
                id="tool_456",
                input={"course_name": "MCP"},
            )
        ]

        # Mock the follow-up response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="The MCP course has 4 lessons.")]

        # Set up the mock client
        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response,
        ]

        # Execute with an outline query
        result = ai_generator.generate_response(
            query="What lessons are in the MCP course?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
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
            tool_manager=tool_manager,
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
        content_block = Mock()
        content_block.type = "tool_use"
        content_block.name = "test_tool"  # Ensure it's a string
        content_block.id = "tool_789"
        content_block.input = {"param": "value"}
        mock_response.content = [content_block]

        # Mock final response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="Final answer based on tool result.")]

        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response,
        ]

        # Execute
        result = ai_generator.generate_response(
            query="Test query",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
        )

        # Assertions
        assert result == "Final answer based on tool result."
        mock_tool_manager.execute_tool.assert_called_once_with(
            "test_tool", param="value"
        )
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
            query="Follow-up question", conversation_history=history
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
        result = ai_generator.generate_response(query="Question without tools")

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
            "Second tool result",
        ]

        # Mock response with multiple tool uses
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"

        # Create proper content blocks
        content_block1 = Mock()
        content_block1.type = "tool_use"
        content_block1.name = "tool1"
        content_block1.id = "id1"
        content_block1.input = {"q": "query1"}

        content_block2 = Mock()
        content_block2.type = "tool_use"
        content_block2.name = "tool2"
        content_block2.id = "id2"
        content_block2.input = {"q": "query2"}

        mock_response.content = [content_block1, content_block2]

        # Mock final response
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [Mock(text="Combined results.")]

        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response,
        ]

        # Execute
        result = ai_generator.generate_response(
            query="Complex query",
            tools=[{"name": "tool1"}, {"name": "tool2"}],
            tool_manager=mock_tool_manager,
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
        content_block = Mock()
        content_block.type = "tool_use"
        content_block.name = "failing_tool"
        content_block.id = "tool_error"
        content_block.input = {}
        mock_response.content = [content_block]

        # Mock final response handling the error
        mock_final_response = Mock()
        mock_final_response.stop_reason = "end_turn"
        mock_final_response.content = [
            Mock(text="I encountered an error with the tool.")
        ]

        ai_generator.client.messages.create.side_effect = [
            mock_response,
            mock_final_response,
        ]

        # Execute
        result = ai_generator.generate_response(
            query="Query that causes error",
            tools=[{"name": "failing_tool"}],
            tool_manager=mock_tool_manager,
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


class TestSequentialToolCalling:
    """Test suite for sequential tool calling functionality"""

    def test_sequential_two_rounds(self, ai_generator):
        """Test two sequential tool calls"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = [
            "First tool result: Found MCP course",
            "Second tool result: Course has 4 lessons",
        ]
        mock_tool_manager.get_tool_definitions.return_value = [
            {"name": "search_course_content"},
            {"name": "get_course_outline"},
        ]
        mock_tool_manager.get_last_sources.return_value = []

        # First round: search
        mock_round1 = Mock()
        mock_round1.stop_reason = "tool_use"
        content1 = Mock()
        content1.type = "tool_use"
        content1.name = "search_course_content"
        content1.id = "tool1"
        content1.input = {"query": "MCP"}
        mock_round1.content = [content1]

        # Second round: get outline
        mock_round2 = Mock()
        mock_round2.stop_reason = "tool_use"
        content2 = Mock()
        content2.type = "tool_use"
        content2.name = "get_course_outline"
        content2.id = "tool2"
        content2.input = {"course_name": "MCP"}
        mock_round2.content = [content2]

        # Final response
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="MCP course found with 4 lessons.")]

        ai_generator.client.messages.create.side_effect = [
            mock_round1,
            mock_round2,
            mock_final,
        ]

        result = ai_generator.generate_response(
            query="Find MCP course and tell me its structure",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
            max_tool_rounds=2,
        )

        assert result == "MCP course found with 4 lessons."
        assert ai_generator.client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2

    def test_early_termination_no_second_tool(self, ai_generator):
        """Test Claude choosing not to use tools in second round"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Found the information"
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "test_tool"}]
        mock_tool_manager.get_last_sources.return_value = []

        # First round: use tool
        mock_round1 = Mock()
        mock_round1.stop_reason = "tool_use"
        content1 = Mock()
        content1.type = "tool_use"
        content1.name = "test_tool"
        content1.id = "tool1"
        content1.input = {"param": "value"}
        mock_round1.content = [content1]

        # Second round: no tool use
        mock_round2 = Mock()
        mock_round2.stop_reason = "end_turn"
        mock_round2.content = [Mock(text="Here's the answer based on the search.")]

        ai_generator.client.messages.create.side_effect = [mock_round1, mock_round2]

        result = ai_generator.generate_response(
            query="Test query",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
            max_tool_rounds=2,
        )

        assert result == "Here's the answer based on the search."
        assert ai_generator.client.messages.create.call_count == 2

    def test_max_rounds_reached(self, ai_generator):
        """Test behavior when max rounds is reached"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Tool result"
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "test_tool"}]
        mock_tool_manager.get_last_sources.return_value = []

        # Create tool use responses for max rounds
        mock_tool_response = Mock()
        mock_tool_response.stop_reason = "tool_use"
        content = Mock()
        content.type = "tool_use"
        content.name = "test_tool"
        content.id = "tool_id"
        content.input = {}
        mock_tool_response.content = [content]

        # Final response after max rounds
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="Final answer after 2 rounds.")]

        ai_generator.client.messages.create.side_effect = [
            mock_tool_response,  # Round 1
            mock_tool_response,  # Round 2
            mock_final,  # Final response (no tools)
        ]

        result = ai_generator.generate_response(
            query="Test",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
            max_tool_rounds=2,
        )

        assert result == "Final answer after 2 rounds."
        assert ai_generator.client.messages.create.call_count == 3

        # Verify final call has no tools
        final_call = ai_generator.client.messages.create.call_args_list[-1]
        assert "tools" not in final_call[1]

    def test_configurable_max_rounds(self, ai_generator):
        """Test that max_rounds can be configured per query"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Result"
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "tool"}]
        mock_tool_manager.get_last_sources.return_value = []

        # Create 3 tool use responses
        mock_tool_response = Mock()
        mock_tool_response.stop_reason = "tool_use"
        content = Mock()
        content.type = "tool_use"
        content.name = "tool"
        content.id = "id"
        content.input = {}
        mock_tool_response.content = [content]

        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="Done after 3 rounds.")]

        ai_generator.client.messages.create.side_effect = [
            mock_tool_response,  # Round 1
            mock_tool_response,  # Round 2
            mock_tool_response,  # Round 3
            mock_final,
        ]

        result = ai_generator.generate_response(
            query="Test",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
            max_tool_rounds=3,  # Override default
        )

        assert result == "Done after 3 rounds."
        assert mock_tool_manager.execute_tool.call_count == 3

    def test_error_recovery_in_round(self, ai_generator):
        """Test error handling during a tool round"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "failing_tool"}]

        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        content = Mock()
        content.type = "tool_use"
        content.name = "failing_tool"
        content.id = "id"
        content.input = {}
        mock_response.content = [content]

        # Claude handles the error gracefully
        mock_recovery = Mock()
        mock_recovery.stop_reason = "end_turn"
        mock_recovery.content = [Mock(text="Tool failed but here's what I know.")]

        ai_generator.client.messages.create.side_effect = [mock_response, mock_recovery]

        result = ai_generator.generate_response(
            query="Test",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
        )

        assert "Tool failed but here's what I know." in result

    def test_source_accumulation_across_rounds(self, ai_generator):
        """Test that sources are accumulated from all rounds"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "tool"}]

        # Mock source tracking
        sources_round1 = [{"text": "Source 1", "link": "link1"}]
        sources_round2 = [{"text": "Source 2", "link": "link2"}]
        mock_tool_manager.get_last_sources.side_effect = [
            sources_round1,
            sources_round2,
        ]

        # Create responses for 2 rounds
        mock_round1 = Mock()
        mock_round1.stop_reason = "tool_use"
        content1 = Mock()
        content1.type = "tool_use"
        content1.name = "tool"
        content1.id = "id1"
        content1.input = {}
        mock_round1.content = [content1]

        mock_round2 = Mock()
        mock_round2.stop_reason = "tool_use"
        content2 = Mock()
        content2.type = "tool_use"
        content2.name = "tool"
        content2.id = "id2"
        content2.input = {}
        mock_round2.content = [content2]

        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [Mock(text="Final answer.")]

        ai_generator.client.messages.create.side_effect = [
            mock_round1,
            mock_round2,
            mock_final,
        ]

        result = ai_generator.generate_response(
            query="Test",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
        )

        assert result == "Final answer."
        # Verify reset_sources was called after each round
        assert mock_tool_manager.reset_sources.call_count == 2

    def test_system_prompt_evolution(self, ai_generator):
        """Test that system prompts change appropriately between rounds"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.return_value = "Result"
        mock_tool_manager.get_tool_definitions.return_value = [{"name": "tool"}]
        mock_tool_manager.get_last_sources.return_value = []

        # Capture all API calls
        api_calls = []

        def capture_call(**kwargs):
            api_calls.append(kwargs)
            # Return appropriate response based on call number
            if len(api_calls) <= 2:
                # Tool use responses
                mock_response = Mock()
                mock_response.stop_reason = "tool_use"
                content = Mock()
                content.type = "tool_use"
                content.name = "tool"
                content.id = f"id{len(api_calls)}"
                content.input = {}
                mock_response.content = [content]
                return mock_response
            else:
                # Final response
                mock_response = Mock()
                mock_response.stop_reason = "end_turn"
                mock_response.content = [Mock(text="Done.")]
                return mock_response

        ai_generator.client.messages.create.side_effect = capture_call

        result = ai_generator.generate_response(
            query="Test",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
            max_tool_rounds=2,
        )

        # Check round 1 prompt
        assert "Round 1 of 2" in api_calls[0]["system"]
        assert "You have 2 round(s) remaining" in api_calls[0]["system"]

        # Check round 2 prompt
        assert "Round 2 of 2" in api_calls[1]["system"]
        assert "You have 1 round(s) remaining" in api_calls[1]["system"]

        # Check final prompt
        assert "FINAL RESPONSE PHASE" in api_calls[2]["system"]

    def test_comparison_query_two_outlines(self, ai_generator):
        """Test a realistic comparison query requiring two outline calls"""
        mock_tool_manager = Mock(spec=ToolManager)
        mock_tool_manager.execute_tool.side_effect = [
            "MCP Course: 4 lessons on Model Context Protocol",
            "Advanced Retrieval: 6 lessons on vector search",
        ]
        mock_tool_manager.get_tool_definitions.return_value = [
            {"name": "get_course_outline"}
        ]
        mock_tool_manager.get_last_sources.return_value = []

        # Round 1: Get MCP outline
        mock_round1 = Mock()
        mock_round1.stop_reason = "tool_use"
        content1 = Mock()
        content1.type = "tool_use"
        content1.name = "get_course_outline"
        content1.id = "outline1"
        content1.input = {"course_name": "MCP"}
        mock_round1.content = [content1]

        # Round 2: Get Advanced Retrieval outline
        mock_round2 = Mock()
        mock_round2.stop_reason = "tool_use"
        content2 = Mock()
        content2.type = "tool_use"
        content2.name = "get_course_outline"
        content2.id = "outline2"
        content2.input = {"course_name": "Advanced Retrieval"}
        mock_round2.content = [content2]

        # Final: Compare the two
        mock_final = Mock()
        mock_final.stop_reason = "end_turn"
        mock_final.content = [
            Mock(text="MCP has 4 lessons while Advanced Retrieval has 6 lessons.")
        ]

        ai_generator.client.messages.create.side_effect = [
            mock_round1,
            mock_round2,
            mock_final,
        ]

        result = ai_generator.generate_response(
            query="Compare the structure of MCP and Advanced Retrieval courses",
            tools=mock_tool_manager.get_tool_definitions(),
            tool_manager=mock_tool_manager,
        )

        assert "4 lessons" in result
        assert "6 lessons" in result
        assert mock_tool_manager.execute_tool.call_count == 2
