# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

A Retrieval-Augmented Generation (RAG) system for answering questions about course materials using semantic search and AI-powered responses. The application uses ChromaDB for vector storage, Anthropic's Claude Sonnet 4 for AI generation, and provides a web interface for interaction.

## Development Commands

### Installation and Setup
```bash
# Install uv package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY to the .env file
```

### Code Quality Tools
```bash
# Format code automatically
./scripts/format.sh

# Run all quality checks (format, lint, types, tests)
./scripts/quality.sh

# Development helper with multiple commands
./scripts/dev.sh [command]
# Available commands: format, check, lint, types, test, server, clean, help
```

### Running the Application
```bash
# Quick start (recommended)
chmod +x run.sh
./run.sh

# Manual start
cd backend
uv run uvicorn app:app --reload --port 8000

# Using dev script
./scripts/dev.sh server
```

Access points:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Architecture Overview

### System Flow
1. **Frontend** (`frontend/script.js`) → POST `/api/query` with query and session_id
2. **FastAPI** (`backend/app.py`) → Receives request, calls `rag_system.query()`
3. **RAG System** (`backend/rag_system.py`) → Orchestrates the query processing
4. **AI Generator** (`backend/ai_generator.py`) → Calls Claude with tool definitions
5. **Claude Decision** → Intelligently decides when to use CourseSearchTool
6. **Vector Search** (`backend/vector_store.py`) → Queries ChromaDB collections
7. **Response Generation** → Claude synthesizes results into final answer
8. **Frontend Update** → Displays response with collapsible sources section

### Key Architectural Decisions

**Tool-based RAG**: Unlike traditional RAG systems that always retrieve first, this system lets Claude intelligently decide when to search, making it more conversational and context-aware.

**Dual Vector Collections**:
- `course_catalog`: Course metadata for semantic course name resolution
- `course_content`: Document chunks for content retrieval

**Session Management**: Maintains conversation history (last 2 exchanges) per session for context-aware responses.

### Core Components

**Backend Structure**:
- `app.py`: FastAPI application with `/api/query`, `/api/courses`, `/api/stats` endpoints
- `rag_system.py`: Main orchestrator that coordinates AI generation and tool usage
- `ai_generator.py`: Anthropic Claude API integration with tool support
- `vector_store.py`: ChromaDB wrapper with course resolution and semantic search
- `search_tools.py`: Tool definitions for Claude's function calling
- `session_manager.py`: In-memory conversation history management
- `document_processor.py`: Document chunking (800 chars, 100 overlap)
- `models.py`: Pydantic models (Course, Lesson, CourseChunk)
- `config.py`: Configuration management

**Frontend Structure**:
- `index.html`: Chat interface with course statistics dashboard
- `script.js`: Handles user interactions, API calls, and UI updates
- `style.css`: Responsive chat UI styling

### Configuration Parameters

**Vector Search**:
- Chunk Size: 800 characters
- Chunk Overlap: 100 characters
- Max Results: 5 chunks per search
- Embedding Model: all-MiniLM-L6-v2 (384 dimensions)

**AI Generation**:
- Model: Claude Sonnet 4
- Temperature: 0 (deterministic)
- Max History: 2 conversation exchanges

## Important Implementation Details

### Tool Usage Pattern
The system uses Claude's tool-calling capability. When a query is received:
1. Claude receives the query with CourseSearchTool available
2. Claude decides if search is needed based on the query
3. If tool is used, results are fed back to Claude for final synthesis
4. Tool manager tracks sources for attribution

### Course Name Resolution
Partial course names are resolved using vector similarity in the course_catalog collection before searching content, allowing fuzzy matching of course references.

### Session Handling
Sessions are stored in-memory (resets on server restart). Each session maintains:
- Conversation history (user/assistant message pairs)
- Session ID for continuity
- Maximum of 2 historical exchanges for context

### Document Processing
Documents are processed on startup from `docs/` directory:
- Supports .txt and .md files
- Extracts course and lesson metadata from filename pattern
- Creates overlapping chunks for better context preservation

## Development Notes

### Code Quality Standards
- **Formatting**: Black (88 char line length)
- **Linting**: Ruff with extended ruleset (E, W, F, I, B, C4, UP)
- **Type Checking**: MyPy with strict settings
- **Testing**: Pytest with fixtures and mocks

Run `./scripts/quality.sh` before committing to ensure code meets standards.

### Current Limitations
- In-memory session storage (not persistent)
- No authentication or user management
- No rate limiting or request validation
- ChromaDB data persists in `chroma_data/` directory

### Adding New Course Materials
1. Place files in `docs/` directory
2. Follow naming convention: `{course_name}_script_lesson_{number}.txt`
3. Restart the application to reprocess documents

### Modifying Search Behavior
- Adjust chunk size/overlap in `document_processor.py`
- Modify search parameters in `vector_store.py`
- Update tool definitions in `search_tools.py`
- Change Claude's system prompt in `ai_generator.py`

### API Response Format
```python
{
    "answer": str,          # Claude's response
    "sources": List[str],   # Source references used
    "session_id": str       # Session identifier
}
```

## Dependencies

Core dependencies managed by uv:
- `chromadb==1.0.15`: Vector database
- `anthropic==0.58.2`: Claude AI API
- `sentence-transformers==5.0.0`: Text embeddings
- `fastapi==0.116.1`: Web framework
- `uvicorn==0.35.0`: ASGI server
- `python-dotenv==1.1.1`: Environment management
- always use uv to run the server do not use pip directly
- make sure to use uv to manage all dependencies
- use uv to run Python files