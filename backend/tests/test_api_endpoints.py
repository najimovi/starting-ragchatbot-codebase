"""
API endpoint tests for the FastAPI application
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pydantic import BaseModel
from typing import List, Optional, Union, Dict


# Define models locally to avoid import issues
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Union[str, Dict[str, str]]]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


class ClearSessionRequest(BaseModel):
    """Request model for clearing a session"""
    session_id: str


class ClearSessionResponse(BaseModel):
    """Response model for clear session"""
    success: bool
    message: str


def create_test_app(rag_system_mock):
    """
    Create a test FastAPI application with API endpoints only
    This avoids issues with static file mounting during tests
    """
    app = FastAPI(title="Course Materials RAG System Test")
    
    # Store the mock in the app for endpoint access
    app.state.rag_system = rag_system_mock
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        from fastapi import HTTPException
        try:
            session_id = request.session_id
            if not session_id:
                session_id = app.state.rag_system.session_manager.create_session()
            
            answer, sources = app.state.rag_system.query(request.query, session_id)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        from fastapi import HTTPException
        try:
            analytics = app.state.rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/session/clear", response_model=ClearSessionResponse)
    async def clear_session(request: ClearSessionRequest):
        """Clear a specific session's conversation history"""
        try:
            app.state.rag_system.session_manager.clear_session(request.session_id)
            
            return ClearSessionResponse(
                success=True,
                message=f"Session {request.session_id} cleared successfully"
            )
        except Exception as e:
            return ClearSessionResponse(
                success=False,
                message=f"Failed to clear session: {str(e)}"
            )
    
    @app.get("/")
    async def read_root():
        """Root endpoint for health check"""
        return {"status": "healthy", "service": "Course Materials RAG System"}
    
    return app


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system for API testing"""
    mock_rag = Mock()
    
    # Mock session manager
    mock_session_manager = Mock()
    mock_session_manager.create_session.return_value = "test-session-123"
    mock_session_manager.clear_session.return_value = None
    mock_rag.session_manager = mock_session_manager
    
    # Mock query method
    def mock_query(query, session_id):
        if "error" in query.lower():
            raise Exception("Test error during query processing")
        elif "mcp" in query.lower():
            return (
                "MCP is a protocol for AI applications to communicate with external systems.",
                [
                    {"text": "MCP: Build Rich-Context AI Apps", "link": "https://example.com/lesson1"},
                    "Additional context from lesson 2"
                ]
            )
        else:
            return (
                "This is a test response.",
                ["Source 1", "Source 2"]
            )
    
    mock_rag.query = mock_query
    
    # Use Mock for get_course_analytics so it can be modified in tests
    mock_rag.get_course_analytics = Mock(return_value={
        "total_courses": 2,
        "course_titles": [
            "MCP: Build Rich-Context AI Apps with Anthropic",
            "Advanced Retrieval for AI with Chroma"
        ]
    })
    
    return mock_rag


@pytest.fixture
def test_app(mock_rag_system):
    """Create a test FastAPI app"""
    return create_test_app(mock_rag_system)


@pytest.fixture
def test_client(test_app):
    """Create a test client with the test app"""
    return TestClient(test_app)


class TestQueryEndpoint:
    """Tests for the /api/query endpoint"""
    
    def test_query_success_with_new_session(self, test_client):
        """Test successful query without providing session ID"""
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
        assert data["answer"] == "This is a test response."
        assert len(data["sources"]) == 2
    
    def test_query_success_with_existing_session(self, test_client):
        """Test successful query with existing session ID"""
        response = test_client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "session_id": "existing-session-456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing-session-456"
    
    def test_query_with_mcp_content(self, test_client):
        """Test query that returns mixed source formats"""
        response = test_client.post(
            "/api/query",
            json={"query": "Tell me about MCP"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "MCP is a protocol" in data["answer"]
        assert len(data["sources"]) == 2
        # First source should be a dict with text and link
        assert isinstance(data["sources"][0], dict)
        assert "text" in data["sources"][0]
        assert "link" in data["sources"][0]
        # Second source should be a string
        assert isinstance(data["sources"][1], str)
    
    def test_query_error_handling(self, test_client):
        """Test error handling in query endpoint"""
        response = test_client.post(
            "/api/query",
            json={"query": "This will cause an error"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]
    
    def test_query_invalid_request(self, test_client):
        """Test query with invalid request body"""
        response = test_client.post(
            "/api/query",
            json={}  # Missing required 'query' field
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_query_empty_query(self, test_client):
        """Test query with empty query string"""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )
        
        # Empty string is still a valid string, so this should work
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data


class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint"""
    
    def test_get_courses_success(self, test_client):
        """Test successful retrieval of course statistics"""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
        assert "MCP: Build Rich-Context AI Apps with Anthropic" in data["course_titles"]
        assert "Advanced Retrieval for AI with Chroma" in data["course_titles"]
    
    def test_get_courses_error_handling(self, test_app, test_client):
        """Test error handling in courses endpoint"""
        # Get the mock from the app state
        mock_rag = test_app.state.rag_system
        # Make the method raise an exception
        mock_rag.get_course_analytics.side_effect = Exception("Database error")
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database error" in data["detail"]
    
    def test_get_courses_empty_result(self, test_app, test_client):
        """Test courses endpoint with no courses available"""
        # Get the mock from the app state
        mock_rag = test_app.state.rag_system
        # Reset the side effect first
        mock_rag.get_course_analytics.side_effect = None
        # Mock empty analytics
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []


class TestClearSessionEndpoint:
    """Tests for the /api/session/clear endpoint"""
    
    def test_clear_session_success(self, test_client):
        """Test successful session clearing"""
        response = test_client.post(
            "/api/session/clear",
            json={"session_id": "test-session-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleared successfully" in data["message"]
        assert "test-session-123" in data["message"]
    
    def test_clear_session_failure(self, test_app, test_client):
        """Test session clearing with error"""
        # Get the mock from the app state
        mock_rag = test_app.state.rag_system
        # Make the clear_session method raise an exception
        mock_rag.session_manager.clear_session.side_effect = Exception("Session not found")
        
        response = test_client.post(
            "/api/session/clear",
            json={"session_id": "non-existent-session"}
        )
        
        assert response.status_code == 200  # Still returns 200 but with success=False
        data = response.json()
        assert data["success"] is False
        assert "Failed to clear session" in data["message"]
        assert "Session not found" in data["message"]
    
    def test_clear_session_invalid_request(self, test_client):
        """Test clear session with invalid request body"""
        response = test_client.post(
            "/api/session/clear",
            json={}  # Missing required 'session_id' field
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_clear_session_empty_id(self, test_client):
        """Test clear session with empty session ID"""
        response = test_client.post(
            "/api/session/clear",
            json={"session_id": ""}
        )
        
        # Empty string is still a valid string
        assert response.status_code == 200
        data = response.json()
        # The actual behavior depends on the session manager implementation


class TestRootEndpoint:
    """Tests for the root / endpoint"""
    
    def test_root_health_check(self, test_client):
        """Test root endpoint returns health status"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert "RAG System" in data["service"]
    
    def test_root_method_not_allowed(self, test_client):
        """Test that POST to root is not allowed"""
        response = test_client.post("/", json={})
        
        assert response.status_code == 405  # Method not allowed


class TestAPIIntegration:
    """Integration tests for multiple endpoint interactions"""
    
    def test_query_then_clear_session(self, test_client):
        """Test creating a session with query then clearing it"""
        # First, make a query to create a session
        query_response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        
        assert query_response.status_code == 200
        session_id = query_response.json()["session_id"]
        
        # Then clear the session
        clear_response = test_client.post(
            "/api/session/clear",
            json={"session_id": session_id}
        )
        
        assert clear_response.status_code == 200
        assert clear_response.json()["success"] is True
    
    def test_multiple_queries_same_session(self, test_client):
        """Test multiple queries using the same session"""
        session_id = "persistent-session-789"
        
        # First query
        response1 = test_client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "session_id": session_id
            }
        )
        
        assert response1.status_code == 200
        assert response1.json()["session_id"] == session_id
        
        # Second query with same session
        response2 = test_client.post(
            "/api/query",
            json={
                "query": "Tell me more about MCP",
                "session_id": session_id
            }
        )
        
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
        assert "MCP is a protocol" in response2.json()["answer"]
    
    def test_concurrent_endpoint_access(self, test_client):
        """Test that different endpoints can be accessed independently"""
        # Get courses
        courses_response = test_client.get("/api/courses")
        assert courses_response.status_code == 200
        
        # Make a query
        query_response = test_client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        assert query_response.status_code == 200
        
        # Check health
        health_response = test_client.get("/")
        assert health_response.status_code == 200
        
        # All endpoints should work independently
        assert courses_response.json()["total_courses"] == 2
        assert "answer" in query_response.json()
        assert health_response.json()["status"] == "healthy"


# Performance and edge case tests
class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_long_query(self, test_client):
        """Test handling of very long query strings"""
        long_query = "What is " + "Python " * 1000  # Very long query
        
        response = test_client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
    
    def test_special_characters_in_query(self, test_client):
        """Test queries with special characters"""
        special_queries = [
            "What is 🐍 Python?",
            "Tell me about <script>alert('xss')</script>",
            "Query with \n newlines \t and tabs",
            "Query with 中文 characters",
            "Query with émojis 🎉 and àccents"
        ]
        
        for query in special_queries:
            response = test_client.post(
                "/api/query",
                json={"query": query}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
    
    def test_null_session_id(self, test_client):
        """Test explicit null session_id"""
        response = test_client.post(
            "/api/query",
            json={
                "query": "Test query",
                "session_id": None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"  # Should create new session
    
    def test_malformed_json(self, test_client):
        """Test handling of malformed JSON requests"""
        response = test_client.post(
            "/api/query",
            data='{"query": "test"',  # Malformed JSON (missing closing brace)
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable entity
    
    def test_wrong_content_type(self, test_client):
        """Test request with wrong content type"""
        response = test_client.post(
            "/api/query",
            data="query=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 422  # Should expect JSON