# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.

## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**

   ```bash
   uv sync
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory:

   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:

```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:

- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## System Architecture Diagram

```
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│       FRONTEND          │         │        FASTAPI          │         │      RAG SYSTEM         │
│     (script.js)         │         │       (app.py)          │         │   (rag_system.py)       │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
            │                                    │                                    │
            │     1. POST /api/query             │                                    │
            │     {query, session_id}            │                                    │
            ├────────────────────────────────────>                                    │
            │                                    │                                    │
            │                                    │     2. rag_system.query()          │
            │                                    ├────────────────────────────────────>
            │                                    │                                    │
            │                                    │                                    ▼
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│    SESSION MANAGER      │         │     AI GENERATOR        │         │     TOOL MANAGER        │
│   (session_mgr.py)      │         │   (ai_generator.py)     │         │   (search_tools.py)     │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
            ▲                                    ▲                                    │
            │     3. get_history()               │     4. generate_response()        │
            └────────────────────────────────────┼─────────────── + tools ───────────┘
                                                 │
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        CLAUDE SONNET 4                                        │
│  System: "You are an AI assistant with course search tool..."                                 │
│  Tools: [CourseSearchTool]                                                                    │
│  Query: "Answer this question about course materials: ..."                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 │ 5. Tool Decision
                                                 ▼
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│    COURSE SEARCH        │         │      VECTOR STORE       │         │       CHROMADB          │
│        TOOL             │         │   (vector_store.py)     │         │                         │
│  (search_tools.py)      │         │                         │         │                         │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
            │                                    │                                    │
            │     6. execute(query,              │                                    │
            │        course_name,                │     7. search()                    │
            │        lesson_number)              │                                    │
            ├────────────────────────────────────>                                    │
            │                                    ├────────────────────────────────────>
            │                                    │                                    │
            │                                    │  ┌───────────────────────────────┐ │
            │                                    │  │   course_catalog              │ │
            │                                    │  │   - Course resolution         │ │
            │                                    │  │                               │ │
            │                                    │  │   course_content              │ │
            │                                    │  │   - Semantic search           │ │
            │                                    │  └───────────────────────────────┘ │
            │                                    │                                    │
            │                                    │     8. SearchResults              │
            │     9. Formatted results           <────────────────────────────────────┤
            <────────────────────────────────────┤                                    │
            │                                    │                                    │
            │     10. Tool results back to Claude                                    │
            ▼                                                                         │
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        CLAUDE SONNET 4                                        │
│                     Synthesizes tool results into final answer                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 │ 11. Final response
                                                 ▼
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│      RAG SYSTEM         │         │        FASTAPI          │         │       FRONTEND          │
│                         │         │                         │         │                         │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
            │                                    │                                    │
            │     12. (response,                 │                                    │
            │         sources)                   │     13. QueryResponse              │
            ├────────────────────────────────────>     {answer, sources,              │
            │                                    │      session_id}                   │
            │                                    ├────────────────────────────────────>
            │                                    │                                    │
            │                                    │                         14. Update UI
            │                                    │                         - Add message
            │                                    │                         - Show sources
            │                                    │                         - Store session
            ▼                                    ▼                                    ▼
```


### Query Processing Steps

1. **Frontend Initiation** (`frontend/script.js:45-72`)

   - User types query and clicks send
   - Disables input controls, shows loading animation
   - Makes POST request to `/api/query` with query and session_id

2. **Backend API Endpoint** (`backend/app.py:56-74`)

   - FastAPI receives request at `/api/query`
   - Creates session ID if not provided
   - Calls `rag_system.query()` with user query and session

3. **RAG System Orchestration** (`backend/rag_system.py:102-140`)

   - Wraps query with instructions
   - Retrieves conversation history from session
   - Calls AI generator with tools enabled
   - Collects sources from tool manager

4. **Vector Search via Tools** (`backend/search_tools.py:52-86`)

   - AI decides when to search using `CourseSearchTool`
   - Calls `vector_store.search()` with optional course/lesson filters
   - Returns formatted results or "no content found"

5. **Vector Store Retrieval** (`backend/vector_store.py:61-100`)

   - Resolves course names using vector similarity
   - Builds ChromaDB filters for course/lesson
   - Queries content collection with embeddings
   - Returns top-K most relevant chunks

6. **AI Generation** (`backend/ai_generator.py:43-135`)

   - Builds system prompt with conversation context
   - Makes initial API call with tool definitions
   - If tool used: executes via tool_manager, gets results, makes follow-up call
   - Returns final generated response

7. **Response to Frontend** (`frontend/script.js:73-95`)
   - Removes loading animation
   - Parses markdown with marked.js
   - Adds assistant message bubble
   - Displays collapsible sources section

### Key Features

- **Tool-based RAG**: Claude intelligently decides when to search, making it more sophisticated than simple retrieval-first systems
- **Dual Vector Collections**: Separate collections for course metadata and content chunks
- **Semantic Course Resolution**: Partial course name matching using vector similarity
- **Session Management**: Maintains conversation context across queries
- **Source Attribution**: Tracks and displays sources for transparency

### Performance Characteristics

- **Chunk Size**: 800 characters with 100 character overlap
- **Max Results**: 5 chunks per search
- **Temperature**: 0 (deterministic responses)
- **Session History**: Last 2 conversation exchanges
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Response Time**: ~2-4 seconds typical
