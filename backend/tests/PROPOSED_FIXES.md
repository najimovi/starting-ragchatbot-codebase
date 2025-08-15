# Proposed Code Fixes Based on Test Results

## Critical Issue 1: AIGenerator Tool Name Validation

### Current Code (ai_generator.py:127-129):
```python
tool_result = tool_manager.execute_tool(
    content_block.name, 
    **content_block.input
)
```

### Proposed Fix:
```python
# Add validation for tool name
tool_name = content_block.name
if not isinstance(tool_name, str):
    tool_name = str(tool_name) if tool_name else "unknown_tool"
    
tool_result = tool_manager.execute_tool(
    tool_name, 
    **content_block.input
)
```

## Critical Issue 2: Source Tracking Robustness

### Current Implementation:
Sources are stored as instance attributes on tools and can be lost.

### Proposed Enhancement for ToolManager:
```python
class ToolManager:
    def __init__(self):
        self.tools = {}
        self._sources_stack = []  # Track sources from all tool calls
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        result = self.tools[tool_name].execute(**kwargs)
        
        # Collect sources if the tool tracks them
        tool = self.tools[tool_name]
        if hasattr(tool, 'last_sources') and tool.last_sources:
            self._sources_stack.extend(tool.last_sources)
        
        return result
    
    def get_all_sources(self) -> list:
        """Get all sources from all tool executions"""
        return self._sources_stack.copy()
    
    def reset_sources(self):
        """Reset all tracked sources"""
        self._sources_stack.clear()
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []
```

## Critical Issue 3: Error Handling in CourseSearchTool

### Current Code (search_tools.py:73-74):
```python
if results.error:
    return results.error
```

### Proposed Fix:
```python
if results.error:
    # Log the error for debugging
    import logging
    logging.error(f"Search error in CourseSearchTool: {results.error}")
    
    # Return user-friendly message
    if "No course found" in results.error:
        return results.error  # This is already user-friendly
    else:
        return "An error occurred while searching. Please try again."
```

## Critical Issue 4: RAGSystem Query Error Handling

### Current Code (rag_system.py:124-129):
```python
response = self.ai_generator.generate_response(
    query=prompt,
    conversation_history=history,
    tools=self.tool_manager.get_tool_definitions(),
    tool_manager=self.tool_manager
)
```

### Proposed Fix:
```python
try:
    response = self.ai_generator.generate_response(
        query=prompt,
        conversation_history=history,
        tools=self.tool_manager.get_tool_definitions(),
        tool_manager=self.tool_manager
    )
except Exception as e:
    # Log the error
    import logging
    logging.error(f"Error generating response: {str(e)}")
    
    # Return a user-friendly error message
    response = "I encountered an error while processing your request. Please try rephrasing your question."
    sources = []
    return response, sources
```

## Critical Issue 5: VectorStore Search Validation

### Add input validation to vector_store.py:
```python
def search(self, 
           query: str,
           course_name: Optional[str] = None,
           lesson_number: Optional[int] = None,
           limit: Optional[int] = None) -> SearchResults:
    
    # Input validation
    if not query or not isinstance(query, str):
        return SearchResults.empty("Invalid query: must be a non-empty string")
    
    if lesson_number is not None and not isinstance(lesson_number, int):
        return SearchResults.empty("Invalid lesson number: must be an integer")
    
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        return SearchResults.empty("Invalid limit: must be a positive integer")
    
    # Rest of the existing code...
```

## Test Infrastructure Fixes

### Fix for conftest.py mock_vector_store:
```python
@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing"""
    mock_store = Mock(spec=VectorStore)
    
    # Create a more robust mock_search function
    def mock_search(query, course_name=None, lesson_number=None, limit=None):
        # Check for specific test scenarios
        if course_name == "Introduction to Python":
            return SearchResults.empty(f"No course found matching '{course_name}'")
        elif "error" in query.lower():
            return create_sample_search_results("error")
        elif "empty" in query.lower() or "nonexistent" in query.lower():
            return create_sample_search_results("empty")
        elif "mcp" in query.lower():
            return create_sample_search_results("mcp")
        elif "embedding" in query.lower():
            return create_sample_search_results("embeddings")
        else:
            return create_sample_search_results("default")
    
    # Set the side_effect
    mock_store.search = Mock(side_effect=mock_search)
    
    # Rest of the mock setup...
```

### Fix for test_ai_generator.py mock content blocks:
```python
# Instead of:
Mock(type="tool_use", name="search_course_content", ...)

# Use:
content_block = Mock()
content_block.type = "tool_use"
content_block.name = "search_course_content"  # Ensure it's a string
content_block.id = "tool_123"
content_block.input = {"query": "What is MCP?"}
```

## Implementation Priority

1. **Immediate**: Fix test infrastructure (conftest.py and test mocks)
2. **High**: Add input validation and error handling to production code
3. **Medium**: Improve source tracking architecture
4. **Low**: Add comprehensive logging throughout the system

## Testing After Fixes

After implementing these fixes:
1. Re-run the test suite
2. Add regression tests for each fixed issue
3. Add integration tests to catch interaction issues
4. Consider adding property-based testing for input validation