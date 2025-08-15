import anthropic
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import logging

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SequentialToolState:
    """Manages state across sequential tool calling rounds"""
    current_round: int = 1
    max_rounds: int = 2
    messages: List[Dict[str, Any]] = field(default_factory=list)
    all_sources: List[Dict[str, Any]] = field(default_factory=list)
    tool_results_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_user_message(self, content: Any):
        """Add a user message to the conversation"""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: Any):
        """Add an assistant message to the conversation"""
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_results(self, results: List[Dict[str, Any]], round_num: int):
        """Add tool results and track them in history"""
        self.messages.append({"role": "user", "content": results})
        self.tool_results_history.append({
            "round": round_num,
            "results": results
        })
    
    def increment_round(self):
        """Move to the next round"""
        self.current_round += 1
    
    def can_use_tools(self) -> bool:
        """Check if more tool rounds are available"""
        return self.current_round <= self.max_rounds
    
    def get_context_summary(self) -> str:
        """Get a summary of previous tool usage for context"""
        if not self.tool_results_history:
            return ""
        
        summaries = []
        for entry in self.tool_results_history:
            round_num = entry["round"]
            results = entry["results"]
            # Extract tool types used
            tool_types = set()
            for result in results:
                # Try to infer tool type from result content
                if "Course:" in str(result.get("content", "")):
                    tool_types.add("get_course_outline")
                else:
                    tool_types.add("search_course_content")
            
            if tool_types:
                summaries.append(f"Round {round_num}: Used {', '.join(tool_types)}")
        
        return "; ".join(summaries) if summaries else ""


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Base system prompt - will be enhanced based on round number
    BASE_SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

Available Tools:
1. **search_course_content**: Search for specific content within course materials
   - Use for questions about topics, concepts, or detailed content
   - Can filter by course name and lesson number

2. **get_course_outline**: Retrieve complete course structure with lessons
   - Use for questions about course structure, lesson lists, or course overview
   - Returns course title, link, and all lessons with their numbers and titles

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **No meta-commentary**:
  - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
  - Do not mention "based on the search results" or "using the outline tool"

When presenting course outlines:
- Include the course title and link (if available)
- List all lessons with their numbers and titles
- Format clearly with proper indentation

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str, max_tool_rounds: int = 2):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tool_rounds = max_tool_rounds
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None,
                         max_tool_rounds: Optional[int] = None) -> str:
        """
        Generate AI response with optional sequential tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_tool_rounds: Override default max rounds for this query
            
        Returns:
            Generated response as string
        """
        # Use provided max_rounds or fall back to instance default
        max_rounds = max_tool_rounds if max_tool_rounds is not None else self.max_tool_rounds
        
        # If no tools or tool_manager, fall back to simple response
        if not tools or not tool_manager:
            return self._generate_simple_response(query, conversation_history)
        
        # Initialize state for sequential tool calling
        state = SequentialToolState(max_rounds=max_rounds)
        state.add_user_message(query)
        
        # Execute sequential tool calling loop
        return self._execute_sequential_tools(
            state=state,
            conversation_history=conversation_history,
            tools=tools,
            tool_manager=tool_manager
        )
    
    def _generate_simple_response(self, query: str, conversation_history: Optional[str] = None) -> str:
        """Generate a response without any tool usage"""
        system_content = self._build_system_prompt(
            conversation_history=conversation_history,
            round_number=0,
            max_rounds=0
        )
        
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        response = self.client.messages.create(**api_params)
        return response.content[0].text
    
    def _execute_sequential_tools(self, state: SequentialToolState, 
                                 conversation_history: Optional[str],
                                 tools: List,
                                 tool_manager) -> str:
        """
        Execute tool calling loop with support for multiple sequential rounds.
        
        Returns:
            Final response text after all tool rounds
        """
        
        while state.can_use_tools():
            # Build system prompt for current round
            system_prompt = self._build_system_prompt(
                conversation_history=conversation_history,
                round_number=state.current_round,
                max_rounds=state.max_rounds,
                context_summary=state.get_context_summary()
            )
            
            # Prepare API parameters with tools
            api_params = {
                **self.base_params,
                "messages": state.messages.copy(),
                "system": system_prompt,
                "tools": tools,
                "tool_choice": {"type": "auto"}
            }
            
            try:
                # Make API call
                response = self.client.messages.create(**api_params)
                
                # Check if Claude used tools
                if response.stop_reason != "tool_use":
                    # Claude chose not to use tools - return response
                    return response.content[0].text
                
                # Handle tool execution
                state.add_assistant_message(response.content)
                
                # Execute tools and collect results
                tool_results = self._execute_tools(response, tool_manager)
                
                if tool_results:
                    state.add_tool_results(tool_results, state.current_round)
                    
                    # Collect sources from this round
                    if hasattr(tool_manager, 'get_last_sources'):
                        round_sources = tool_manager.get_last_sources()
                        state.all_sources.extend(round_sources)
                        tool_manager.reset_sources()
                
                # Move to next round
                state.increment_round()
                
            except Exception as e:
                logger.error(f"Error in round {state.current_round}: {str(e)}")
                # Try to generate response with what we have so far
                if state.messages:
                    return self._generate_final_response(state, system_prompt)
                else:
                    return f"I encountered an error while processing your request: {str(e)}"
        
        # Max rounds reached - generate final response without tools
        return self._generate_final_response(
            state, 
            self._build_system_prompt(
                conversation_history=conversation_history,
                round_number=state.max_rounds + 1,  # Indicates final round
                max_rounds=state.max_rounds,
                context_summary=state.get_context_summary(),
                final_round=True
            )
        )
    
    def _execute_tools(self, response, tool_manager) -> List[Dict[str, Any]]:
        """
        Execute all tool calls from a response and return results.
        
        Args:
            response: Claude's response containing tool use blocks
            tool_manager: Tool manager to execute tools
            
        Returns:
            List of tool results
        """
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    # Validate tool name is a string
                    tool_name = content_block.name
                    if not isinstance(tool_name, str):
                        tool_name = str(tool_name) if tool_name else "unknown_tool"
                        logger.warning(f"Tool name was not a string: {content_block.name}")
                    
                    # Execute tool
                    tool_result = tool_manager.execute_tool(
                        tool_name,
                        **content_block.input
                    )
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                    
                except Exception as e:
                    logger.error(f"Error executing tool {content_block.name}: {str(e)}")
                    # Add error result so Claude knows the tool failed
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Tool execution failed: {str(e)}"
                    })
        
        return tool_results
    
    def _generate_final_response(self, state: SequentialToolState, system_prompt: str) -> str:
        """
        Generate final response after all tool rounds are complete.
        
        Args:
            state: Current state with all messages
            system_prompt: System prompt for final response
            
        Returns:
            Final response text
        """
        final_params = {
            **self.base_params,
            "messages": state.messages,
            "system": system_prompt
        }
        
        # No tools in final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
    
    def _build_system_prompt(self, conversation_history: Optional[str] = None,
                            round_number: int = 1,
                            max_rounds: int = 2,
                            context_summary: str = "",
                            final_round: bool = False) -> str:
        """
        Build system prompt appropriate for the current round.
        
        Args:
            conversation_history: Previous conversation context
            round_number: Current round number (1-based)
            max_rounds: Maximum number of tool rounds allowed
            context_summary: Summary of previous tool usage
            final_round: Whether this is the final response (no more tools)
            
        Returns:
            System prompt string
        """
        prompt_parts = [self.BASE_SYSTEM_PROMPT]
        
        # Add conversation history if provided
        if conversation_history:
            prompt_parts.append(f"\nPrevious conversation:\n{conversation_history}")
        
        # Add round-specific guidance
        if final_round:
            prompt_parts.append("""
FINAL RESPONSE PHASE:
- You have completed all tool usage rounds
- Synthesize all tool results into a comprehensive answer
- Provide a complete, standalone answer based on all gathered information
""")
        elif round_number > 0 and max_rounds > 0:
            if round_number == 1:
                prompt_parts.append(f"""
SEQUENTIAL TOOL USAGE - Round {round_number} of {max_rounds}:
- You can use tools to gather information
- If you need additional related information after seeing initial results, you can use tools again in the next round
- Examples of multi-round scenarios:
  * User asks about "courses covering similar topics to X" → Round 1: get outline or search X, Round 2: search for related topics
  * User asks for "comparison between course A and B" → Round 1: get outline of A, Round 2: get outline of B
  * User asks "what courses cover topic X and what are their structures" → Round 1: search for topic X, Round 2: get outlines of found courses
- Focus on gathering the most important information first
- You have {max_rounds - round_number + 1} round(s) remaining for tool usage
""")
            else:
                prompt_parts.append(f"""
SEQUENTIAL TOOL USAGE - Round {round_number} of {max_rounds}:
- Previous tool usage: {context_summary}
- You have {max_rounds - round_number + 1} round(s) remaining for tool usage
- Use tools only if you need additional information to complete the user's request
- If you have sufficient information from previous rounds, provide your final answer without using tools
- Consider using complementary tools (e.g., if you searched in round 1, consider getting outlines in round 2)
""")
        
        return "\n".join(prompt_parts)
    
    # Backward compatibility: keep the old _handle_tool_execution method signature
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Legacy method for single-round tool execution.
        Maintained for backward compatibility.
        """
        # Use the new sequential system with max_rounds=1
        state = SequentialToolState(max_rounds=1)
        
        # Reconstruct state from base_params
        state.messages = base_params["messages"].copy()
        state.add_assistant_message(initial_response.content)
        
        # Execute tools
        tool_results = self._execute_tools(initial_response, tool_manager)
        
        if tool_results:
            state.add_tool_results(tool_results, 1)
        
        # Generate final response
        return self._generate_final_response(
            state,
            base_params["system"]
        )