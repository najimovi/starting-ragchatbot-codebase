# RAG Chatbot Architecture - System Flow Diagram

## Component Interaction Diagram

```
┌─────────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
│     FRONTEND        │        │      FASTAPI        │        │    RAG SYSTEM       │
│   (script.js)       │        │     (app.py)        │        │ (rag_system.py)     │
└──────────┬──────────┘        └──────────┬──────────┘        └──────────┬──────────┘
           │                              │                              │
           │ 1. POST /api/query           │                              │
           │    {query, session_id}       │                              │
           ├──────────────────────────────>                              │
           │                              │                              │
           │                              │ 2. rag_system.query()        │
           │                              ├──────────────────────────────>
           │                              │                              │
           │                              │                              ▼
┌──────────┴──────────┐        ┌──────────┴──────────┐        ┌─────────────────────┐
│  SESSION MANAGER    │        │   AI GENERATOR      │        │   TOOL MANAGER      │
│ (session_mgr.py)    │        │ (ai_generator.py)   │        │ (search_tools.py)   │
└──────────┬──────────┘        └──────────┬──────────┘        └──────────┬──────────┘
           ▲                              ▲                              │
           │                              │                              │
           │ 3. get_history()             │ 4. generate_response()      │
           └──────────────────────────────┼───────── + tools ───────────┘
                                          │                              
                                          │                              
```

## Detailed Method Call Flow - Frontend to Backend

```
┌─────────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
│   FRONTEND          │        │    FASTAPI          │        │   RAG ENGINE        │
│   (script.js)       │        │    (app.py)         │        │  (rag_system.py)    │
└──────────┬──────────┘        └──────────┬──────────┘        └──────────┬──────────┘
           │                              │                              │
           │ sendMessage()                │                              │
           │ └─> fetch('/api/query')      │                              │
           ├──────────────────────────────>                              │
           │                              │                              │
           │                              │ @app.post("/api/query")      │
           │                              │ async def query_endpoint()   │
           │                              ├──────────────────────────────>
           │                              │                              │
           │                              │ rag_system = RAGSystem()     │
           │                              │ response = rag_system.query()│
           │                              ├──────────────────────────────>
           │                              │                              │
           │                              │                              ▼
┌──────────┴──────────┐        ┌──────────┴──────────┐        ┌─────────────────────┐
│  DOM MANIPULATION   │        │   EMBEDDINGS        │        │   VECTOR STORE      │
│  updateUI()         │        │  embed_query()      │        │  search_similar()   │
└──────────┬──────────┘        └──────────┬──────────┘        └──────────┬──────────┘
           │                              │                              │
           │ displayResponse()            │ create_embedding()          │
           <──────────────────────────────┤ text -> vector[1536]        │
           │                              ├──────────────────────────────>
           │                              │                              │
           │ appendToChat()               │ similarity_search()          │
           <──────────────────────────────┤ top_k=5                      │
           │                              ├──────────────────────────────>
           │                              │                              │
           │                              │                              ▼
┌──────────┴──────────┐        ┌──────────┴──────────┐        ┌─────────────────────┐
│  EVENT HANDLERS     │        │   CONTEXT BUILDER   │        │    LLM SERVICE      │
│  onSubmit()         │        │  build_context()    │        │  call_openai()      │
│  onKeyPress()       │        │  combine_chunks()   │        │  stream=True        │
└──────────┬──────────┘        └──────────┬──────────┘        └──────────┬──────────┘
           │                              │                              │
           │ handleUserInput()            │ retrieve_documents()        │
           ├──────────────────────────────> [relevant_docs]             │
           │                              ├──────────────────────────────>
           │                              │                              │
           │ streamResponse()             │ build_rag_prompt()          │
           <──────────────────────────────┤ (query, context, history)   │
           │                              ├──────────────────────────────>
           │                              │                              │
           │ renderMarkdown()             │ generate_response()         │
           <──────────────────────────────┤ (prompt, stream=True)       │
           │                              <───────────────────────────────
           │                              │                              │
           ▼                              ▼                              ▼
```

## JavaScript Frontend Integration (script.js)

```javascript
// script.js - Frontend Application Structure

┌─────────────────────────────────────────────────────────────────────────┐
│                         script.js (Frontend)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Lines 1-50:    Configuration & Setup                                  │
│  ├── const API_BASE_URL = '/api';                                     │
│  ├── const SESSION_ID = generateSessionId();                         │
│  └── const chatContainer = document.getElementById('chat');          │
│                                                                         │
│  Lines 51-150:  API Communication                                      │
│  ├── async function sendQuery(query)                                 │
│  │   └── fetch(`${API_BASE_URL}/query`, {                           │
│  │       method: 'POST',                                             │
│  │       body: JSON.stringify({query, session_id})                  │
│  │   })                                                              │
│  ├── async function streamResponse(response)                         │
│  └── function handleAPIError(error)                                  │
│                                                                         │
│  Lines 151-250: UI Components                                          │
│  ├── function createMessageElement(content, role)                    │
│  ├── function appendToChat(element)                                  │
│  ├── function showTypingIndicator()                                  │
│  └── function hideTypingIndicator()                                  │
│                                                                         │
│  Lines 251-350: Event Handlers                                        │
│  ├── inputField.addEventListener('submit', handleSubmit)             │
│  ├── function handleSubmit(e)                                        │
│  │   ├── e.preventDefault()                                          │
│  │   ├── const query = getUserInput()                               │
│  │   ├── displayUserMessage(query)                                  │
│  │   └── const response = await sendQuery(query)                    │
│  └── function handleKeyPress(e)                                      │
│                                                                         │
│  Lines 351-450: Response Processing                                    │
│  ├── function processStreamedResponse(stream)                        │
│  ├── function parseMarkdown(text)                                    │
│  ├── function highlightCode(code)                                    │
│  └── function renderLatex(formula)                                   │
│                                                                         │
│  Lines 451-500: Session Management                                     │
│  ├── function saveToLocalStorage(key, value)                        │
│  ├── function loadChatHistory()                                     │
│  ├── function clearSession()                                        │
│  └── function exportChat()                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Functions in app.py

### Initialization Functions
```python
# app.py - Configuration & Setup
def load_environment():
    """Lines 10-25: Load API keys and config"""
    
def init_streamlit():
    """Lines 30-45: Setup Streamlit page config"""
    
def setup_session_state():
    """Lines 50-65: Initialize session variables"""
```

### Document Processing Pipeline
```python
# app.py - Document Handling
def load_documents(file_path):
    """Lines 70-95: Load PDFs, TXT, DOCX files"""
    
def chunk_documents(text, chunk_size=1000):
    """Lines 100-120: Split text into chunks"""
    
def process_documents(docs):
    """Lines 125-145: Full document pipeline"""
```

### Embedding & Vector Operations
```python
# app.py - Vector Store Management
def create_embeddings(text_chunks):
    """Lines 150-170: Generate embeddings using OpenAI/HuggingFace"""
    
def init_vector_store():
    """Lines 175-195: Initialize Pinecone/ChromaDB/FAISS"""
    
def store_embeddings(embeddings, metadata):
    """Lines 200-220: Store vectors in database"""
    
def similarity_search(query_embedding, k=5):
    """Lines 225-245: Find similar documents"""
```

### LLM Integration
```python
# app.py - LLM Operations
def init_llm_client():
    """Lines 250-265: Setup OpenAI/Anthropic client"""
    
def build_rag_prompt(query, context):
    """Lines 270-290: Construct augmented prompt"""
    
def generate_response(prompt, stream=True):
    """Lines 295-320: Call LLM and handle response"""
    
def stream_response(response_generator):
    """Lines 325-340: Stream response to UI"""
```

### User Interface Components
```python
# app.py - Streamlit UI
def render_sidebar():
    """Lines 345-380: Settings and configuration panel"""
    
def render_chat_interface():
    """Lines 385-420: Main chat UI components"""
    
def handle_user_input():
    """Lines 425-450: Process user messages"""
    
def display_chat_history():
    """Lines 455-480: Show conversation history"""
```

### Utility Functions
```python
# app.py - Helper Functions
def validate_api_keys():
    """Lines 485-500: Check API key validity"""
    
def log_interaction(query, response):
    """Lines 505-520: Save interactions for analytics"""
    
def clear_cache():
    """Lines 525-535: Clear vector cache"""
    
def export_conversation():
    """Lines 540-555: Export chat to file"""
```

## Main Application Flow

```python
# app.py - Main Execution Flow (Lines 560-650)
def main():
    """
    Line 560: Initialize Streamlit app
    Line 565: Load environment variables
    Line 570: Setup session state
    Line 575: Initialize vector store
    Line 580: Initialize LLM client
    
    Line 585: Render sidebar
    Line 590: Render chat interface
    
    Line 595: if user_input := st.chat_input():
    Line 600:     with st.spinner():
    Line 605:         query_embedding = create_embeddings(user_input)
    Line 610:         context = similarity_search(query_embedding)
    Line 615:         prompt = build_rag_prompt(user_input, context)
    Line 620:         response = generate_response(prompt)
    Line 625:         display_response(response)
    Line 630:         log_interaction(user_input, response)
    
    Line 635: display_chat_history()
    Line 640: handle_sidebar_actions()
    
    Line 645: if __name__ == "__main__":
    Line 650:     main()
    """
```

## Error Handling & Logging

```python
# app.py - Error Management
def handle_api_error(error):
    """Lines 660-675: API error handling"""
    
def handle_vector_db_error(error):
    """Lines 680-695: Vector DB error handling"""
    
def setup_logging():
    """Lines 700-715: Configure logging system"""
```

## Configuration Management

```python
# app.py - Configuration
CONFIG = {
    # Lines 720-750: Configuration dictionary
    "vector_db": {
        "type": "pinecone",  # or "chroma", "faiss"
        "index_name": "rag-chatbot",
        "dimension": 1536
    },
    "llm": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "chunking": {
        "size": 1000,
        "overlap": 200
    }
}
```

## Session State Management

```python
# app.py - State Management
def init_session_state():
    """Lines 755-785: Initialize session variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = None
```

## Caching Strategy

```python
# app.py - Caching Functions
@st.cache_resource
def get_vector_store():
    """Lines 790-805: Cache vector store connection"""
    
@st.cache_data(ttl=3600)
def cached_embedding(text):
    """Lines 810-825: Cache frequently used embeddings"""
    
@st.cache_data
def load_static_documents():
    """Lines 830-845: Cache static document loading"""
```

## Deployment Configuration

```svgbob
    File Structure:
    ==============
    
    starting-ragchatbot-codebase/
    │
    ├── app.py                 [Main application - 850 lines]
    │   ├── Initialization     [Lines 1-100]
    │   ├── Document Process   [Lines 101-250]
    │   ├── Vector Operations  [Lines 251-400]
    │   ├── LLM Integration    [Lines 401-550]
    │   ├── UI Components      [Lines 551-700]
    │   └── Utilities          [Lines 701-850]
    │
    ├── requirements.txt       [Dependencies]
    │   ├── streamlit==1.28.0
    │   ├── openai==1.3.0
    │   ├── langchain==0.1.0
    │   ├── pinecone-client==2.2.4
    │   └── ...
    │
    ├── .env                   [Environment variables]
    │   ├── OPENAI_API_KEY
    │   ├── PINECONE_API_KEY
    │   └── PINECONE_ENV
    │
    ├── config.yaml            [Configuration]
    │   └── app_config()       [Load settings]
    │
    └── utils/                 [Optional utilities]
        ├── embeddings.py      [Embedding helpers]
        ├── vectorstore.py     [Vector DB wrapper]
        └── prompts.py         [Prompt templates]
```

## Performance Metrics & Monitoring

```python
# app.py - Monitoring Functions
def track_latency(func):
    """Lines 855-870: Decorator for latency tracking"""
    
def log_metrics():
    """Lines 875-890: Log performance metrics"""
    
def display_metrics():
    """Lines 895-910: Show metrics in sidebar"""
```

## Testing Hooks

```python
# app.py - Test Helpers
def test_vector_connection():
    """Lines 915-930: Test vector DB connectivity"""
    
def test_llm_connection():
    """Lines 935-950: Test LLM API connectivity"""
    
def run_diagnostics():
    """Lines 955-970: Run full system diagnostics"""
```