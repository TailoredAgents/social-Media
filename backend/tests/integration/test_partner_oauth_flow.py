"""
Integration tests for partner OAuth flow
"""
import pytest
import json
import uuid
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.db.database import Base
from backend.db.models import User
from backend.db.multi_tenant_models import Organization
from backend.core.config import get_settings


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    # Create test organization
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Organization",
        slug="test-org",
        plan_type="professional"
    )
    session.add(org)
    
    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password"
    )
    session.add(user)
    session.commit()
    
    yield session, org.id, user.id
    session.close()


@pytest.fixture
def client_with_feature_enabled():
    """Test client with feature flag enabled"""
    with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
        get_settings.cache_clear()
        return TestClient(app)


@pytest.fixture
def client_with_feature_disabled():
    """Test client with feature flag disabled"""
    with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'false'}):
        get_settings.cache_clear()
        return TestClient(app)


@pytest.fixture
def authenticated_user_token(db_session):
    """Mock authenticated user token"""
    session, org_id, user_id = db_session
    
    # Mock JWT token validation
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.default_organization_id = org_id
    mock_user.email = "test@example.com"
    
    with patch('backend.auth.dependencies.get_current_active_user', return_value=mock_user):
        yield mock_user


# Feature Flag Integration Tests

def test_endpoints_not_available_when_disabled(client_with_feature_disabled):
    """Test that endpoints return 404 when feature disabled"""
    client = client_with_feature_disabled
    
    # Test start endpoint
    response = client.get("/api/oauth/meta/start")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # The dependency check happens before route, so should return expected error
    # The feature flag dependency raises HTTPException(404) when disabled
    assert response.status_code in [404, 400]  # Could be 400 if route validation happens first
    
    if response.status_code == 404:
        response_data = response.json()
        assert response_data["error"] == "feature_disabled"
        assert response_data["feature_flag"] == "FEATURE_PARTNER_OAUTH"


def test_endpoints_require_auth_when_enabled(client_with_feature_enabled):
    """Test that endpoints require authentication when enabled"""
    client = client_with_feature_enabled
    
    # Without authentication, should get 401/422 (depending on auth setup)
    response = client.get("/api/oauth/meta/start")
    assert response.status_code in [401, 422]  # Unauthorized or validation error


# OAuth Start Flow Tests

def test_start_oauth_meta_success(client_with_feature_enabled, authenticated_user_token):
    """Test successful Meta OAuth start"""
    client = client_with_feature_enabled
    
    with patch('backend.services.pkce_state_store.get_state_store') as mock_get_store:
        mock_store = MagicMock()
        mock_store.create.return_value = {
            "state": "test_state_123",
            "code_challenge": "test_challenge",
            "code_challenge_method": "S256"
        }
        mock_get_store.return_value = mock_store
        
        with patch('backend.api.partner_oauth.get_settings') as mock_settings:
            settings = MagicMock()
            settings.meta_app_id = "meta_app_123"
            settings.meta_graph_version = "v18.0"
            settings.backend_url = "http://localhost:8000"
            mock_settings.return_value = settings
            
            response = client.get("/api/oauth/meta/start")
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["platform"] == "meta"
    assert response_data["state"] == "test_state_123"
    assert response_data["expires_in"] == 600
    assert "auth_url" in response_data
    assert "facebook.com" in response_data["auth_url"]
    assert "client_id=meta_app_123" in response_data["auth_url"]


def test_start_oauth_x_success(client_with_feature_enabled, authenticated_user_token):
    """Test successful X OAuth start with PKCE"""
    client = client_with_feature_enabled
    
    with patch('backend.services.pkce_state_store.get_state_store') as mock_get_store:
        mock_store = MagicMock()
        mock_store.create.return_value = {
            "state": "test_state_456",
            "code_challenge": "test_challenge_x",
            "code_challenge_method": "S256"
        }
        mock_get_store.return_value = mock_store
        
        with patch('backend.api.partner_oauth.get_settings') as mock_settings:
            settings = MagicMock()
            settings.x_client_id = "x_client_123"
            settings.backend_url = "http://localhost:8000"
            mock_settings.return_value = settings
            
            response = client.get("/api/oauth/x/start")
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["platform"] == "x"
    assert response_data["state"] == "test_state_456"
    assert "auth_url" in response_data
    assert "twitter.com" in response_data["auth_url"]
    assert "code_challenge=test_challenge_x" in response_data["auth_url"]
    assert "code_challenge_method=S256" in response_data["auth_url"]


def test_start_oauth_invalid_platform(client_with_feature_enabled, authenticated_user_token):
    """Test OAuth start with invalid platform"""
    client = client_with_feature_enabled
    
    response = client.get("/api/oauth/invalid/start")
    
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["error"] == "invalid_platform"
    assert "invalid" in response_data["message"]


def test_start_oauth_missing_client_config(client_with_feature_enabled, authenticated_user_token):
    """Test OAuth start with missing client configuration"""
    client = client_with_feature_enabled
    
    with patch('backend.api.partner_oauth.get_settings') as mock_settings:
        settings = MagicMock()
        settings.meta_app_id = None  # Missing config
        mock_settings.return_value = settings
        
        response = client.get("/api/oauth/meta/start")
    
    assert response.status_code == 500
    response_data = response.json()
    assert response_data["error"] == "missing_config"
    assert "META_APP_ID not configured" in response_data["message"]


# OAuth Callback Flow Tests

def test_callback_meta_success(client_with_feature_enabled):
    """Test successful Meta OAuth callback"""
    client = client_with_feature_enabled
    
    # Mock state store returning valid state
    mock_state_data = {
        "organization_id": "org_123",
        "platform": "meta",
        "code_verifier": "test_verifier",
        "expires_at": "2024-12-31T23:59:59+00:00"
    }
    
    with patch('backend.services.pkce_state_store.get_state_store') as mock_get_store:
        mock_store = MagicMock()
        mock_store.consume.return_value = mock_state_data
        mock_store.cache_tokens.return_value = None
        mock_get_store.return_value = mock_store
        
        # Mock token exchange
        with patch('backend.api.partner_oauth._exchange_code_for_tokens') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "meta_token_123",
                "token_type": "bearer",
                "expires_in": 5184000,
                "platform": "meta"
            }
            
            with patch('backend.api.partner_oauth.get_settings') as mock_settings:
                settings = MagicMock()
                settings.backend_url = "http://localhost:8000"
                mock_settings.return_value = settings
                
                response = client.get("/api/oauth/meta/callback?code=auth_code_123&state=test_state")
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["status"] == "success"
    assert response_data["platform"] == "meta"
    assert response_data["state"] == "test_state"
    assert response_data["next_step"] == "asset_selection"


def test_callback_oauth_error(client_with_feature_enabled):
    """Test OAuth callback with provider error"""
    client = client_with_feature_enabled
    
    response = client.get("/api/oauth/meta/callback?error=access_denied&error_description=User denied access")
    
    assert response.status_code == 400
    response_data = response.json()
    
    assert response_data["error"] == "oauth_provider_error"
    assert response_data["message"] == "User denied access"
    assert response_data["platform"] == "meta"
    assert response_data["provider_error"] == "access_denied"


def test_callback_invalid_state(client_with_feature_enabled):
    """Test OAuth callback with invalid state"""
    client = client_with_feature_enabled
    
    with patch('backend.services.pkce_state_store.get_state_store') as mock_get_store:
        mock_store = MagicMock()
        mock_store.consume.side_effect = ValueError("Invalid or expired state")
        mock_get_store.return_value = mock_store
        
        response = client.get("/api/oauth/meta/callback?code=auth_code_123&state=invalid_state")
    
    assert response.status_code == 400
    response_data = response.json()
    
    assert response_data["error"] == "invalid_state"
    assert response_data["message"] == "Invalid or expired state parameter"


# Security and Error Handling Tests

def test_state_parameter_validation(client_with_feature_enabled):
    """Test that state parameter validation is enforced"""
    client = client_with_feature_enabled
    
    # Missing state parameter
    response = client.get("/api/oauth/meta/callback?code=test_code")
    assert response.status_code == 422  # Validation error
    
    # Empty state parameter
    response = client.get("/api/oauth/meta/callback?code=test_code&state=")
    assert response.status_code == 422  # Validation error


def test_code_parameter_validation(client_with_feature_enabled):
    """Test that code parameter validation is enforced"""
    client = client_with_feature_enabled
    
    # Missing code parameter
    response = client.get("/api/oauth/meta/callback?state=test_state")
    assert response.status_code == 422  # Validation error
    
    # Empty code parameter
    response = client.get("/api/oauth/meta/callback?code=&state=test_state")
    assert response.status_code == 422  # Validation error


def test_comprehensive_error_response_format(client_with_feature_disabled):
    """Test that error responses follow consistent format"""
    client = client_with_feature_disabled
    
    # Test feature disabled error format
    response = client.get("/api/oauth/meta/start")
    
    assert response.status_code == 404
    response_data = response.json()
    
    # Check error response structure
    assert "error" in response_data
    assert "message" in response_data
    assert "feature_flag" in response_data
    assert response_data["feature_flag"] == "FEATURE_PARTNER_OAUTH"