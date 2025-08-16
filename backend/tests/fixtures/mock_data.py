"""
Mock data for testing the RAG system components
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from models import Course, CourseChunk, Lesson
from vector_store import SearchResults

# Sample courses for testing
SAMPLE_COURSES = {
    "mcp": Course(
        title="MCP: Build Rich-Context AI Apps with Anthropic",
        course_link="https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/",
        instructor="Anthropic Team",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Introduction",
                lesson_link="https://example.com/lesson0",
            ),
            Lesson(
                lesson_number=1,
                title="Why MCP",
                lesson_link="https://example.com/lesson1",
            ),
            Lesson(
                lesson_number=2,
                title="MCP Architecture",
                lesson_link="https://example.com/lesson2",
            ),
            Lesson(
                lesson_number=3,
                title="Chatbot Example",
                lesson_link="https://example.com/lesson3",
            ),
        ],
    ),
    "advanced_retrieval": Course(
        title="Advanced Retrieval for AI with Chroma",
        course_link="https://www.deeplearning.ai/short-courses/advanced-retrieval-for-ai/",
        instructor="Chroma Team",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Introduction",
                lesson_link="https://example.com/ar-lesson0",
            ),
            Lesson(
                lesson_number=1,
                title="Overview Of Embeddings Based Retrieval",
                lesson_link="https://example.com/ar-lesson1",
            ),
            Lesson(
                lesson_number=2,
                title="Pitfalls Of Retrieval",
                lesson_link="https://example.com/ar-lesson2",
            ),
        ],
    ),
}

# Sample course chunks for testing
SAMPLE_CHUNKS = [
    CourseChunk(
        content="The Model Context Protocol (MCP) is an open protocol that enables seamless integration between AI assistants and external data sources and tools.",
        course_title="MCP: Build Rich-Context AI Apps with Anthropic",
        lesson_number=1,
        chunk_index=0,
    ),
    CourseChunk(
        content="MCP provides a standardized way for AI models to interact with local services, APIs, and data stores through a simple client-server architecture.",
        course_title="MCP: Build Rich-Context AI Apps with Anthropic",
        lesson_number=2,
        chunk_index=1,
    ),
    CourseChunk(
        content="Embeddings are dense vector representations of text that capture semantic meaning, allowing for similarity comparisons in vector space.",
        course_title="Advanced Retrieval for AI with Chroma",
        lesson_number=1,
        chunk_index=0,
    ),
    CourseChunk(
        content="Common retrieval pitfalls include semantic drift, where similar words have different meanings in context, and the vocabulary mismatch problem.",
        course_title="Advanced Retrieval for AI with Chroma",
        lesson_number=2,
        chunk_index=1,
    ),
]


# Sample search results for testing
def create_sample_search_results(query_type: str = "mcp") -> SearchResults:
    """Create sample search results based on query type"""

    if query_type == "mcp":
        return SearchResults(
            documents=[
                "The Model Context Protocol (MCP) is an open protocol that enables seamless integration between AI assistants and external data sources and tools.",
                "MCP provides a standardized way for AI models to interact with local services, APIs, and data stores through a simple client-server architecture.",
            ],
            metadata=[
                {
                    "course_title": "MCP: Build Rich-Context AI Apps with Anthropic",
                    "lesson_number": 1,
                    "chunk_index": 0,
                },
                {
                    "course_title": "MCP: Build Rich-Context AI Apps with Anthropic",
                    "lesson_number": 2,
                    "chunk_index": 1,
                },
            ],
            distances=[0.1, 0.2],
        )

    elif query_type == "embeddings":
        return SearchResults(
            documents=[
                "Embeddings are dense vector representations of text that capture semantic meaning, allowing for similarity comparisons in vector space."
            ],
            metadata=[
                {
                    "course_title": "Advanced Retrieval for AI with Chroma",
                    "lesson_number": 1,
                    "chunk_index": 0,
                }
            ],
            distances=[0.15],
        )

    elif query_type == "empty":
        return SearchResults(documents=[], metadata=[], distances=[])

    elif query_type == "error":
        return SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="Search error: Connection failed",
        )

    else:
        return SearchResults(
            documents=["Generic content about AI and machine learning."],
            metadata=[
                {
                    "course_title": "Unknown Course",
                    "lesson_number": None,
                    "chunk_index": 0,
                }
            ],
            distances=[0.5],
        )


# Sample tool responses for testing
SAMPLE_TOOL_RESPONSES = {
    "search_course_content": {
        "mcp_query": "[MCP: Build Rich-Context AI Apps with Anthropic - Lesson 1]\nThe Model Context Protocol (MCP) is an open protocol that enables seamless integration.\n\n[MCP: Build Rich-Context AI Apps with Anthropic - Lesson 2]\nMCP provides a standardized way for AI models to interact with local services.",
        "embeddings_query": "[Advanced Retrieval for AI with Chroma - Lesson 1]\nEmbeddings are dense vector representations of text that capture semantic meaning.",
        "no_results": "No relevant content found.",
        "with_course_filter": "No relevant content found in course 'Introduction to Python'.",
        "with_lesson_filter": "No relevant content found in lesson 5.",
    },
    "get_course_outline": {
        "mcp": "Course: MCP: Build Rich-Context AI Apps with Anthropic\nCourse Link: https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/\nTotal Lessons: 4\n\nLessons:\n  Lesson 0: Introduction (https://example.com/lesson0)\n  Lesson 1: Why MCP (https://example.com/lesson1)\n  Lesson 2: MCP Architecture (https://example.com/lesson2)\n  Lesson 3: Chatbot Example (https://example.com/lesson3)",
        "advanced_retrieval": "Course: Advanced Retrieval for AI with Chroma\nCourse Link: https://www.deeplearning.ai/short-courses/advanced-retrieval-for-ai/\nTotal Lessons: 3\n\nLessons:\n  Lesson 0: Introduction (https://example.com/ar-lesson0)\n  Lesson 1: Overview Of Embeddings Based Retrieval (https://example.com/ar-lesson1)\n  Lesson 2: Pitfalls Of Retrieval (https://example.com/ar-lesson2)",
        "not_found": "No course found matching 'Introduction to Python'",
    },
}

# Sample queries for testing
SAMPLE_QUERIES = {
    "content_queries": [
        "What is MCP?",
        "Explain embeddings",
        "How does the Model Context Protocol work?",
        "What are retrieval pitfalls?",
        "Describe the MCP architecture",
    ],
    "outline_queries": [
        "What lessons are in the MCP course?",
        "Show me the outline of Advanced Retrieval",
        "What is the structure of the MCP course?",
        "List all lessons in Advanced Retrieval for AI",
    ],
    "general_queries": [
        "What is machine learning?",
        "How does Python work?",
        "Explain neural networks",
    ],
    "filtered_queries": [
        "What is covered in lesson 2 of MCP?",
        "What does lesson 1 of Advanced Retrieval teach?",
        "Explain MCP architecture from lesson 2",
    ],
}

# Mock ChromaDB collection responses
MOCK_CHROMA_RESPONSES = {
    "course_catalog_query": {
        "documents": [["MCP: Build Rich-Context AI Apps with Anthropic"]],
        "metadatas": [
            [
                {
                    "title": "MCP: Build Rich-Context AI Apps with Anthropic",
                    "instructor": "Anthropic Team",
                    "course_link": "https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/",
                    "lessons_json": '[{"lesson_number": 0, "lesson_title": "Introduction", "lesson_link": "https://example.com/lesson0"}]',
                    "lesson_count": 4,
                }
            ]
        ],
        "distances": [[0.1]],
    },
    "course_content_query": {
        "documents": [["The Model Context Protocol (MCP) is an open protocol..."]],
        "metadatas": [
            [
                {
                    "course_title": "MCP: Build Rich-Context AI Apps with Anthropic",
                    "lesson_number": 1,
                    "chunk_index": 0,
                }
            ]
        ],
        "distances": [[0.1]],
    },
}
