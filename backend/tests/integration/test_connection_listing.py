"""
Integration tests for partner OAuth connection listing
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.db.models import Base, User, SocialConnection, SocialAudit
from backend.db.database import get_db
from backend.core.encryption import encrypt_token


class TestConnectionListing:
    
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
    def sample_connections(self, db_session, test_user):
        """Create sample social connections"""
        connections = []
        
        # Active Meta connection
        meta_conn = SocialConnection(
            id="conn-meta-1",
            organization_id=test_user.id,  # Using user ID as org ID
            platform="meta",
            platform_account_id="fb_page_123",
            platform_username="TestPage",
            connection_name="Test Facebook Page + @testinsta",
            access_token=encrypt_token("encrypted_user_token"),
            page_access_token=encrypt_token("encrypted_page_token"),
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
        connections.append(meta_conn)
        
        # Active X connection
        x_conn = SocialConnection(
            id="conn-x-1",
            organization_id=test_user.id,
            platform="x",
            platform_account_id="x_user_789",
            platform_username="testuser",
            connection_name="@testuser (Test User)",
            access_token=encrypt_token("encrypted_x_token"),
            refresh_token=encrypt_token("encrypted_refresh_token"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=48),  # Expiring soon
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
        connections.append(x_conn)
        
        # Expired connection (should still appear as needs_reconnect)
        expired_conn = SocialConnection(
            id="conn-meta-expired",
            organization_id=test_user.id,
            platform="meta",
            platform_account_id="fb_page_expired",
            platform_username="ExpiredPage",
            connection_name="Expired Facebook Page",
            access_token=encrypt_token("expired_token"),
            token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Already expired
            scopes=["pages_show_list"],
            platform_metadata={"page_id": "fb_page_expired", "page_name": "Expired Facebook Page"},
            webhook_subscribed=False,
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=10)
        )
        connections.append(expired_conn)
        
        # Revoked connection (should not appear)
        revoked_conn = SocialConnection(
            id="conn-revoked",
            organization_id=test_user.id,
            platform="x",
            platform_account_id="revoked_user",
            platform_username="revokeduser",
            connection_name="@revokeduser",
            access_token=encrypt_token("revoked_token"),
            scopes=["tweet.read"],
            platform_metadata={},
            webhook_subscribed=False,
            is_active=False,
            revoked_at=datetime.now(timezone.utc) - timedelta(hours=2),
            created_at=datetime.now(timezone.utc) - timedelta(days=15)
        )
        connections.append(revoked_conn)
        
        for conn in connections:
            db_session.add(conn)
        
        db_session.commit()
        return connections

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_list_connections_success(self, mock_get_user, mock_get_settings, 
                                      test_client, test_user, sample_connections, auth_headers):
        """Test successful connection listing"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make request
        response = test_client.get("/api/oauth/connections", headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "connections" in data
        connections = data["connections"]
        
        # Should return 3 active connections (not the revoked one)
        assert len(connections) == 3
        
        # Verify no tokens are returned
        for conn in connections:
            assert "access_token" not in conn
            assert "refresh_token" not in conn
            assert "page_access_token" not in conn
        
        # Find specific connections
        meta_conn = next((c for c in connections if c["platform"] == "meta" and c["id"] == "conn-meta-1"), None)
        x_conn = next((c for c in connections if c["platform"] == "x" and c["id"] == "conn-x-1"), None)
        expired_conn = next((c for c in connections if c["id"] == "conn-meta-expired"), None)
        
        assert meta_conn is not None
        assert x_conn is not None
        assert expired_conn is not None
        
        # Verify Meta connection details
        assert meta_conn["platform"] == "meta"
        assert meta_conn["platform_username"] == "TestPage"
        assert meta_conn["connection_name"] == "Test Facebook Page + @testinsta"
        assert meta_conn["webhook_subscribed"] is True
        assert meta_conn["needs_reconnect"] is False  # Expires in 30 days
        assert meta_conn["expires_in_hours"] > 24 * 29  # Should be close to 30 days
        
        # Verify X connection details
        assert x_conn["platform"] == "x"
        assert x_conn["platform_username"] == "testuser"
        assert x_conn["connection_name"] == "@testuser (Test User)"
        assert x_conn["webhook_subscribed"] is False
        assert x_conn["needs_reconnect"] is True  # Expires in 48 hours (< 72h)
        assert x_conn["expires_in_hours"] <= 48
        
        # Verify expired connection
        assert expired_conn["platform"] == "meta"
        assert expired_conn["needs_reconnect"] is True
        assert expired_conn["expires_in_hours"] <= 0  # Already expired

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_list_connections_empty(self, mock_get_user, mock_get_settings, 
                                    test_client, test_user, auth_headers):
        """Test listing when no connections exist"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make request
        response = test_client.get("/api/oauth/connections", headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "connections" in data
        assert data["connections"] == []

    @patch('backend.core.config.get_settings')
    def test_list_connections_feature_disabled(self, mock_get_settings, test_client, auth_headers):
        """Test listing when feature flag is disabled"""
        # Setup mocks
        mock_settings = type('Settings', (), {'feature_partner_oauth': False})()
        mock_get_settings.return_value = mock_settings
        
        # Make request
        response = test_client.get("/api/oauth/connections", headers=auth_headers)
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "feature_disabled"

    @patch('backend.core.config.get_settings')
    def test_list_connections_unauthorized(self, mock_get_settings, test_client):
        """Test listing without authentication"""
        # Setup mocks
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make request without auth headers
        response = test_client.get("/api/oauth/connections")
        
        # Verify response - should be unauthorized
        assert response.status_code in [401, 422]

    @patch('backend.core.config.get_settings')
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_list_connections_different_organization(self, mock_get_user, mock_get_settings, 
                                                     test_client, db_session, sample_connections, auth_headers):
        """Test that connections from other organizations are not returned"""
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
        
        # Make request
        response = test_client.get("/api/oauth/connections", headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "connections" in data
        # Should return no connections for this user
        assert data["connections"] == []

    @patch('backend.core.config.get_settings') 
    @patch('backend.auth.dependencies.get_current_active_user')
    def test_connection_health_calculations(self, mock_get_user, mock_get_settings,
                                            test_client, test_user, sample_connections, auth_headers):
        """Test that connection health calculations are correct"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_settings = type('Settings', (), {'feature_partner_oauth': True})()
        mock_get_settings.return_value = mock_settings
        
        # Make request
        response = test_client.get("/api/oauth/connections", headers=auth_headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        connections = data["connections"]
        
        # Verify health status calculations
        for conn in connections:
            if conn["expires_at"]:
                # Should have expires_in_hours calculated
                assert "expires_in_hours" in conn
                assert isinstance(conn["expires_in_hours"], int)
                
                # needs_reconnect should be true if expiring within 72 hours
                if conn["expires_in_hours"] <= 72:
                    assert conn["needs_reconnect"] is True
                else:
                    assert conn["needs_reconnect"] is False
            else:
                # Non-expiring tokens
                assert conn["expires_in_hours"] is None
                assert conn["needs_reconnect"] is False
            
            # Should have created_at timestamp
            assert "created_at" in conn
            assert conn["created_at"] is not None