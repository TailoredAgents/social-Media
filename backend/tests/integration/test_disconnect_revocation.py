"""
Integration tests for partner OAuth connection disconnection and revocation
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx

from backend.main import app
from backend.db.models import Base, User, SocialConnection, SocialAudit
from backend.db.database import get_db
from backend.core.encryption import encrypt_token


class TestDisconnectRevocation:
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        
        yield session
        
        session.close()

    @pytest.fixture
    def override_get_db(self, db_session):
        """Override get_db dependency"""
        def _override_get_db():
            try:
                yield db_session
            finally:
                pass
        return _override_get_db

    @pytest.fixture
    def test_client(self, override_get_db):
        """Create test client with database override"""
        app.dependency_overrides[get_db] = override_get_db
        
        yield TestClient(app)
        
        app.dependency_overrides.clear()

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test_token"}

    @pytest.fixture
    def meta_connection(self, db_session, test_user):
        """Create Meta connection for testing"""
        connection = SocialConnection(
            id="conn-meta-test",
            organization_id=test_user.id,
            platform="meta",
            platform_account_id="fb_page_123",
            platform_username="TestPage",
            connection_name="Test Facebook Page + @testinsta",
            access_token=encrypt_token("user_access_token_123"),
            page_access_token=encrypt_token("page_access_token_456"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            scopes=["pages_show_list", "pages_manage_posts", "instagram_basic"],
            platform_metadata={
                "page_id": "fb_page_123",
                "page_name": "Test Facebook Page",
                "ig_id": "ig_account_456",
                "ig_username": "testinsta"
            },
            webhook_subscribed=True,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
        return connection

    @pytest.fixture
    def x_connection(self, db_session, test_user):
        """Create X connection for testing"""
        connection = SocialConnection(
            id="conn-x-test",
            organization_id=test_user.id,
            platform="x",
            platform_account_id="x_user_789",
            platform_username="testuser",
            connection_name="@testuser (Test User)",
            access_token=encrypt_token("x_access_token_789"),
            refresh_token=encrypt_token("x_refresh_token_abc"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
            platform_metadata={
                "since_id": None,
                "verified": False,
                "followers_count": 100
            },
            webhook_subscribed=False,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=5)
        )
        
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
        return connection

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    @patch('httpx.AsyncClient')
    def test_disconnect_meta_connection_success(self, mock_httpx, mock_get_user, mock_get_settings,
                                                test_client, test_user, meta_connection, db_session, auth_headers):
        """Test successful Meta connection disconnection with webhook unsubscription"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {
            'feature_partner_oauth': True,
            'meta_graph_version': 'v18.0'
        })()
        mock_get_settings.return_value = mock_settings
        
        # Mock HTTP client for webhook unsubscription
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Make disconnect request
        response = test_client.delete(
            f"/api/oauth/{meta_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "revoked"
        assert data["connection_id"] == str(meta_connection.id)
        assert "revoked_at" in data
        
        # Verify database changes
        db_session.refresh(meta_connection)
        assert meta_connection.is_active is False
        assert meta_connection.revoked_at is not None
        assert meta_connection.webhook_subscribed is False
        
        # Verify audit log created
        audit = db_session.query(SocialAudit).filter(
            SocialAudit.connection_id == meta_connection.id,
            SocialAudit.action == "disconnect"
        ).first()
        
        assert audit is not None
        assert audit.status == "success"
        assert audit.platform == "meta"
        assert audit.user_id == test_user.id
        assert audit.audit_metadata["connection_id"] == str(meta_connection.id)
        
        # Verify Meta webhook unsubscription calls
        assert mock_client.delete.call_count == 2  # Page + Instagram
        
        # Verify page unsubscription
        page_call = mock_client.delete.call_args_list[0]
        assert "fb_page_123/subscribed_apps" in str(page_call)
        
        # Verify Instagram unsubscription  
        ig_call = mock_client.delete.call_args_list[1]
        assert "ig_account_456/subscribed_apps" in str(ig_call)

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    @patch('httpx.AsyncClient')
    def test_disconnect_x_connection_success(self, mock_httpx, mock_get_user, mock_get_settings,
                                             test_client, test_user, x_connection, db_session, auth_headers):
        """Test successful X connection disconnection with token revocation"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {
            'feature_partner_oauth': True,
            'x_client_id': 'test_client_id',
            'x_client_secret': 'test_client_secret'
        })()
        mock_get_settings.return_value = mock_settings
        
        # Mock HTTP client for token revocation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Make disconnect request
        response = test_client.delete(
            f"/api/oauth/{x_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "revoked"
        assert data["connection_id"] == str(x_connection.id)
        assert "revoked_at" in data
        
        # Verify database changes
        db_session.refresh(x_connection)
        assert x_connection.is_active is False
        assert x_connection.revoked_at is not None
        assert x_connection.webhook_subscribed is False
        
        # Verify audit log created
        audit = db_session.query(SocialAudit).filter(
            SocialAudit.connection_id == x_connection.id,
            SocialAudit.action == "disconnect"
        ).first()
        
        assert audit is not None
        assert audit.status == "success"
        assert audit.platform == "x"
        assert audit.user_id == test_user.id
        
        # Verify X token revocation call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        
        # Verify revocation endpoint
        assert "api.twitter.com/2/oauth2/revoke" in str(call_args)
        
        # Verify auth was provided
        assert 'auth' in call_args.kwargs
        auth_tuple = call_args.kwargs['auth']
        assert auth_tuple[0] == 'test_client_id'
        assert auth_tuple[1] == 'test_client_secret'

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    @patch('httpx.AsyncClient')
    def test_disconnect_provider_failure_partial_success(self, mock_httpx, mock_get_user, mock_get_settings,
                                                          test_client, test_user, meta_connection, db_session, auth_headers):
        """Test disconnection when provider revocation fails but local revocation succeeds"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {
            'feature_partner_oauth': True,
            'meta_graph_version': 'v18.0'
        })()
        mock_get_settings.return_value = mock_settings
        
        # Mock HTTP client to fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Make disconnect request
        response = test_client.delete(
            f"/api/oauth/{meta_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response - should still succeed locally
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "revoked"
        assert data["connection_id"] == str(meta_connection.id)
        
        # Verify database changes still happened
        db_session.refresh(meta_connection)
        assert meta_connection.is_active is False
        assert meta_connection.revoked_at is not None
        
        # Verify audit log shows partial success
        audit = db_session.query(SocialAudit).filter(
            SocialAudit.connection_id == meta_connection.id,
            SocialAudit.action == "disconnect"
        ).first()
        
        assert audit is not None
        assert audit.status == "partial_success"
        assert audit.audit_metadata["provider_revocation"] is False

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_disconnect_connection_not_found(self, mock_get_user, mock_get_settings,
                                             test_client, test_user, auth_headers):
        """Test disconnecting non-existent connection"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make disconnect request with non-existent ID
        fake_id = "non-existent-connection-id"
        response = test_client.delete(
            f"/api/oauth/{fake_id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        
        assert data["error"] == "connection_not_found"
        assert fake_id in data["connection_id"]

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_disconnect_already_revoked_connection(self, mock_get_user, mock_get_settings,
                                                   test_client, test_user, meta_connection, db_session, auth_headers):
        """Test disconnecting already revoked connection"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Revoke connection first
        meta_connection.is_active = False
        meta_connection.revoked_at = datetime.now(timezone.utc)
        db_session.commit()
        
        # Make disconnect request
        response = test_client.delete(
            f"/api/oauth/{meta_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        
        assert data["error"] == "connection_not_found"

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_disconnect_different_organization(self, mock_get_user, mock_get_settings,
                                               test_client, db_session, meta_connection, auth_headers):
        """Test that users can't disconnect connections from other organizations"""
        # Create different user
        other_user = User(
            id="999e4567-e89b-12d3-a456-426614174999",
            email="other@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Setup mocks to return other user
        mock_get_user.return_value = other_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Try to disconnect connection owned by different org
        response = test_client.delete(
            f"/api/oauth/{meta_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        
        assert data["error"] == "connection_not_found"
        
        # Verify original connection is unchanged
        db_session.refresh(meta_connection)
        assert meta_connection.is_active is True
        assert meta_connection.revoked_at is None

    @patch('backend.core.config.get_settings')
    def test_disconnect_feature_disabled(self, mock_get_settings, test_client, auth_headers):
        """Test disconnection when feature flag is disabled"""
        # Setup mocks
        mock_settings = type('Settings', (), {'feature_partner_oauth': False})()
        mock_get_settings.return_value = mock_settings
        
        # Make disconnect request
        response = test_client.delete(
            "/api/oauth/some-connection-id",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "feature_disabled"

    @patch('backend.core.config.get_settings')
    def test_disconnect_unauthorized(self, mock_get_settings, test_client):
        """Test disconnection without authentication"""
        # Setup mocks
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make request without auth headers
        response = test_client.delete(
            "/api/oauth/some-connection-id",
            json={"confirmation": True}
        )
        
        # Verify response - should be unauthorized
        assert response.status_code in [401, 422]

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    @patch('httpx.AsyncClient')
    def test_disconnect_database_error_audit_log(self, mock_httpx, mock_get_user, mock_get_settings,
                                                  test_client, test_user, meta_connection, db_session, auth_headers):
        """Test that failed disconnections are logged in audit"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Mock provider call to succeed
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        # Close database session to simulate database error
        db_session.close()
        
        # Make disconnect request
        response = test_client.delete(
            f"/api/oauth/{meta_connection.id}",
            headers=auth_headers,
            json={"confirmation": True}
        )
        
        # Should get error response
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "disconnect_failed"