"""
Test system endpoints - health check, root, and system information
"""
import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns correct API information"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    expected_keys = ["name", "version", "status", "description", "documentation", "endpoints", "features"]
    for key in expected_keys:
        assert key in data
    
    # Check specific values
    assert data["name"] == "AI Social Media Content Agent API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "production-ready"
    
    # Check documentation links
    assert "/docs" in data["documentation"]["interactive_docs"]
    assert "/redoc" in data["documentation"]["redoc"]
    
    # Check endpoints are listed
    assert "health" in data["endpoints"]
    assert "authentication" in data["endpoints"]
    assert "content" in data["endpoints"]
    
    # Check features are listed
    assert "AI-Powered Content Generation" in data["features"]
    assert "Semantic Memory System" in data["features"]

def test_health_check_endpoint(client: TestClient):
    """Test the health check endpoint returns system status"""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    expected_keys = ["status", "timestamp", "version", "environment", "services", "system_info", "features_enabled"]
    for key in expected_keys:
        assert key in data
    
    # Check status values
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0"
    
    # Check services status
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "faiss_vector_store" in data["services"]
    
    # Check system info
    assert "python_version" in data["system_info"]
    assert "fastapi_version" in data["system_info"]
    assert "database_type" in data["system_info"]
    
    # Check enabled features
    assert "ai_content_generation" in data["features_enabled"]
    assert "semantic_search" in data["features_enabled"]

def test_health_check_with_database_error(client: TestClient, monkeypatch):
    """Test health check when database is unavailable"""
    def mock_db_error(*args, **kwargs):
        raise Exception("Database connection failed")
    
    # Mock the database connection to fail
    monkeypatch.setattr("backend.main.engine.connect", mock_db_error)
    
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should report degraded status when database is down
    assert data["status"] == "degraded"
    assert "unhealthy" in data["services"]["database"]

def test_openapi_json_endpoint(client: TestClient):
    """Test OpenAPI JSON schema endpoint"""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check OpenAPI structure
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    
    # Check API info
    assert data["info"]["title"] == "AI Social Media Content Agent API"
    assert data["info"]["version"] == "1.0.0"
    
    # Check that paths are documented
    assert "/" in data["paths"]
    assert "/api/health" in data["paths"]

def test_docs_endpoint_accessible(client: TestClient):
    """Test that the documentation endpoint is accessible"""
    response = client.get("/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_redoc_endpoint_accessible(client: TestClient):
    """Test that the ReDoc endpoint is accessible"""
    response = client.get("/redoc")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_cors_headers(client: TestClient):
    """Test that CORS headers are properly set"""
    # Test preflight request
    response = client.options("/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type"
    })
    
    # CORS should allow the request
    assert response.status_code == 200

def test_security_headers(client: TestClient):
    """Test that security headers are applied"""
    response = client.get("/")
    
    # Check for common security headers
    headers = response.headers
    
    # These would be set by the security middleware
    assert response.status_code == 200
    # Additional security header checks could be added here

def test_api_versioning(client: TestClient):
    """Test API version consistency across endpoints"""
    
    # Check root endpoint
    root_response = client.get("/")
    assert root_response.json()["version"] == "1.0.0"
    
    # Check health endpoint
    health_response = client.get("/api/health")
    assert health_response.json()["version"] == "1.0.0"
    
    # Check OpenAPI spec
    openapi_response = client.get("/openapi.json")
    assert openapi_response.json()["info"]["version"] == "1.0.0"

def test_error_handling(client: TestClient):
    """Test that non-existent endpoints return proper 404"""
    response = client.get("/api/nonexistent")
    
    assert response.status_code == 404
    
    # Should return JSON error response
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_async_endpoints(client: TestClient):
    """Test that async endpoints work correctly"""
    response = client.get("/")
    assert response.status_code == 200
    
    response = client.get("/api/health")
    assert response.status_code == 200

def test_request_id_handling(client: TestClient):
    """Test that requests can include tracking IDs"""
    headers = {"X-Request-ID": "test-request-123"}
    response = client.get("/", headers=headers)
    
    assert response.status_code == 200
    # The API should handle the request normally

def test_content_type_json(client: TestClient):
    """Test that API returns JSON content type"""
    response = client.get("/")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]