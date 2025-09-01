"""
Unit tests for token refresh service
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from backend.services.token_refresh_service import TokenRefreshService, get_token_refresh_service
from backend.db.models import SocialConnection, SocialAudit


class TestTokenRefreshService:
    """Test token refresh service functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = MagicMock()
        settings.meta_graph_version = "v18.0"
        settings.meta_app_id = "test_app_id_123"
        settings.meta_app_secret = "test_app_secret_456"
        settings.x_client_id = "test_x_client_id"
        settings.x_client_secret = "test_x_client_secret"
        return settings
    
    @pytest.fixture
    def refresh_service(self, mock_settings):
        """Create token refresh service with mock settings"""
        return TokenRefreshService(settings=mock_settings)
    
    @pytest.fixture
    def mock_meta_connection(self):
        """Create mock Meta connection"""
        connection = MagicMock(spec=SocialConnection)
        connection.id = "conn_123"
        connection.platform = "meta"
        connection.platform_account_id = "page_456"
        connection.organization_id = "org_789"
        connection.access_tokens = {
            "access_token": "encrypted_user_token",
            "page_token": "encrypted_page_token"
        }
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return connection
    
    @pytest.fixture
    def mock_x_connection(self):
        """Create mock X connection"""
        connection = MagicMock(spec=SocialConnection)
        connection.id = "conn_456"
        connection.platform = "x"
        connection.platform_account_id = "user_789"
        connection.organization_id = "org_789"
        connection.access_tokens = {
            "access_token": "encrypted_access_token",
            "refresh_token": "encrypted_refresh_token"
        }
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        return connection
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        db = MagicMock()
        return db

    def test_init_with_settings(self, mock_settings):
        """Test initialization with provided settings"""
        service = TokenRefreshService(settings=mock_settings)
        assert service.meta_app_id == "test_app_id_123"
        assert service.meta_app_secret == "test_app_secret_456"
        assert service.x_client_id == "test_x_client_id"
        assert service.x_client_secret == "test_x_client_secret"
        assert service.meta_base_url == "https://graph.facebook.com/v18.0"
    
    @patch('backend.services.token_refresh_service.get_settings')
    def test_init_without_settings(self, mock_get_settings):
        """Test initialization without provided settings"""
        mock_settings = MagicMock()
        mock_settings.meta_app_id = "default_app_id"
        mock_get_settings.return_value = mock_settings
        
        service = TokenRefreshService()
        assert service.meta_app_id == "default_app_id"


class TestMetaTokenRefresh:
    """Test Meta token refresh functionality"""
    
    @pytest.fixture
    def refresh_service(self):
        """Create refresh service with mock settings"""
        settings = MagicMock()
        settings.meta_app_id = "test_app_id"
        settings.meta_app_secret = "test_app_secret"
        settings.meta_graph_version = "v18.0"
        return TokenRefreshService(settings=settings)
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_refresh_meta_connection_success(self, mock_client, mock_decrypt, refresh_service):
        """Test successful Meta connection refresh"""
        # Mock connection
        connection = MagicMock()
        connection.id = "conn_123"
        connection.platform_account_id = "page_456"
        connection.organization_id = "org_123"
        connection.access_tokens = {"access_token": "encrypted_token"}
        connection.token_expires_at = None
        
        db = MagicMock()
        
        # Mock decryption
        mock_decrypt.return_value = "decrypted_user_token"
        
        # Mock HTTP responses
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        
        # Mock long-lived token exchange
        exchange_response = MagicMock()
        exchange_response.json.return_value = {
            "access_token": "new_long_lived_token",
            "expires_in": 5183999  # ~60 days
        }
        exchange_response.raise_for_status.return_value = None
        
        # Mock token validation
        validation_response = MagicMock()
        validation_response.json.return_value = {"data": {"is_valid": True}}
        validation_response.raise_for_status.return_value = None
        
        # Mock page token derivation
        page_response = MagicMock()
        page_response.json.return_value = {"access_token": "new_page_token"}
        page_response.raise_for_status.return_value = None
        
        mock_client_instance.get.side_effect = [
            exchange_response, validation_response, page_response
        ]
        
        # Execute refresh
        success, new_expiry, message = await refresh_service.refresh_meta_connection(connection, db)
        
        assert success is True
        assert new_expiry is not None
        assert "successful" in message.lower()
        
        # Verify HTTP calls
        assert mock_client_instance.get.call_count == 3
        
        # Verify connection update
        db.commit.assert_called()
        db.refresh.assert_called_with(connection)
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    async def test_refresh_meta_connection_no_credentials(self, mock_decrypt, refresh_service):
        """Test Meta refresh with missing credentials"""
        refresh_service.meta_app_id = ""
        refresh_service.meta_app_secret = ""
        
        connection = MagicMock()
        db = MagicMock()
        
        success, new_expiry, message = await refresh_service.refresh_meta_connection(connection, db)
        
        assert success is False
        assert new_expiry is None
        assert "credentials not configured" in message
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    async def test_refresh_meta_connection_no_token(self, mock_decrypt, refresh_service):
        """Test Meta refresh with no access token"""
        connection = MagicMock()
        connection.access_tokens = {}  # No access_token
        db = MagicMock()
        
        success, new_expiry, message = await refresh_service.refresh_meta_connection(connection, db)
        
        assert success is False
        assert new_expiry is None
        assert "No user access token found" in message
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_refresh_meta_connection_validation_failure(self, mock_client, mock_decrypt, refresh_service):
        """Test Meta refresh with token validation failure"""
        connection = MagicMock()
        connection.access_tokens = {"access_token": "encrypted_token"}
        db = MagicMock()
        
        mock_decrypt.return_value = "invalid_token"
        
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        
        # Mock failed validation
        validation_response = MagicMock()
        validation_response.json.return_value = {"data": {"is_valid": False}}
        validation_response.raise_for_status.return_value = None
        
        mock_client_instance.get.return_value = validation_response
        
        success, new_expiry, message = await refresh_service.refresh_meta_connection(connection, db)
        
        assert success is False
        assert "validation failed" in message


class TestXTokenRefresh:
    """Test X token refresh functionality"""
    
    @pytest.fixture
    def refresh_service(self):
        """Create refresh service with mock settings"""
        settings = MagicMock()
        settings.x_client_id = "test_x_client_id"
        settings.x_client_secret = "test_x_client_secret"
        return TokenRefreshService(settings=settings)
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_refresh_x_connection_success(self, mock_client, mock_decrypt, refresh_service):
        """Test successful X connection refresh"""
        # Mock connection
        connection = MagicMock()
        connection.id = "conn_456"
        connection.organization_id = "org_123"
        connection.access_tokens = {"refresh_token": "encrypted_refresh_token"}
        
        db = MagicMock()
        
        # Mock decryption
        mock_decrypt.return_value = "decrypted_refresh_token"
        
        # Mock HTTP response
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        refresh_response = MagicMock()
        refresh_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 7200
        }
        refresh_response.raise_for_status.return_value = None
        mock_client_instance.post.return_value = refresh_response
        
        # Execute refresh
        success, new_expiry, message = await refresh_service.refresh_x_connection(connection, db)
        
        assert success is True
        assert new_expiry is not None
        assert "successful" in message.lower()
        
        # Verify HTTP call
        mock_client_instance.post.assert_called_once()
        
        # Check authorization header
        call_args = mock_client_instance.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"].startswith("Basic ")
        
        # Verify connection update
        db.commit.assert_called()
        db.refresh.assert_called_with(connection)
    
    async def test_refresh_x_connection_no_credentials(self, refresh_service):
        """Test X refresh with missing credentials"""
        refresh_service.x_client_id = ""
        refresh_service.x_client_secret = ""
        
        connection = MagicMock()
        db = MagicMock()
        
        success, new_expiry, message = await refresh_service.refresh_x_connection(connection, db)
        
        assert success is False
        assert new_expiry is None
        assert "credentials not configured" in message
    
    async def test_refresh_x_connection_no_refresh_token(self, refresh_service):
        """Test X refresh with no refresh token"""
        connection = MagicMock()
        connection.access_tokens = {}  # No refresh_token
        db = MagicMock()
        
        success, new_expiry, message = await refresh_service.refresh_x_connection(connection, db)
        
        assert success is False
        assert new_expiry is None
        assert "No refresh token found" in message
    
    @patch('backend.services.token_refresh_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_refresh_x_connection_api_error(self, mock_client, mock_decrypt, refresh_service):
        """Test X refresh with API error"""
        connection = MagicMock()
        connection.access_tokens = {"refresh_token": "encrypted_refresh_token"}
        db = MagicMock()
        
        mock_decrypt.return_value = "invalid_refresh_token"
        
        # Mock HTTP error
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        from httpx import HTTPStatusError, Response, Request
        
        mock_request = Request("POST", "http://test.com")
        mock_response = Response(400, request=mock_request)
        mock_client_instance.post.side_effect = HTTPStatusError(
            "400 Bad Request", request=mock_request, response=mock_response
        )
        
        success, new_expiry, message = await refresh_service.refresh_x_connection(connection, db)
        
        assert success is False
        assert "API call failed" in message


class TestHelperMethods:
    """Test helper methods"""
    
    @pytest.fixture
    def refresh_service(self):
        """Create refresh service"""
        return TokenRefreshService()
    
    def test_now_utc(self, refresh_service):
        """Test _now_utc helper"""
        now = refresh_service._now_utc()
        assert isinstance(now, datetime)
        assert now.tzinfo == timezone.utc
    
    def test_update_connection(self, refresh_service):
        """Test _update_connection helper"""
        connection = MagicMock()
        db = MagicMock()
        
        updates = {"last_checked_at": datetime.now(timezone.utc)}
        refresh_service._update_connection(db, connection, updates)
        
        # Verify attributes were set
        for field, value in updates.items():
            assert hasattr(connection, field)
        
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(connection)
    
    async def test_create_refresh_audit_success(self, refresh_service):
        """Test successful audit creation"""
        connection = MagicMock()
        connection.id = "conn_123"
        connection.organization_id = "org_456"
        connection.platform = "meta"
        
        db = MagicMock()
        
        await refresh_service._create_refresh_audit(
            db, connection, "refresh", "success", {"test": "data"}
        )
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
    
    async def test_create_refresh_audit_failure(self, refresh_service):
        """Test audit creation with database error"""
        connection = MagicMock()
        db = MagicMock()
        db.add.side_effect = Exception("DB error")
        
        # Should not raise exception
        await refresh_service._create_refresh_audit(
            db, connection, "refresh", "failure", {"error": "test"}
        )


class TestTokenRefreshServiceSingleton:
    """Test token refresh service singleton"""
    
    @patch('backend.services.token_refresh_service.get_settings')
    def test_get_token_refresh_service_singleton(self, mock_get_settings):
        """Test that get_token_refresh_service returns singleton"""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Reset singleton
        import backend.services.token_refresh_service
        backend.services.token_refresh_service._token_refresh_service = None
        
        service1 = get_token_refresh_service()
        service2 = get_token_refresh_service()
        
        assert service1 is service2
        mock_get_settings.assert_called_once()
    
    def test_get_token_refresh_service_with_settings(self):
        """Test get_token_refresh_service with provided settings"""
        settings = MagicMock()
        settings.meta_app_id = "test_app_id"
        
        # Reset singleton
        import backend.services.token_refresh_service
        backend.services.token_refresh_service._token_refresh_service = None
        
        service = get_token_refresh_service(settings=settings)
        assert service.meta_app_id == "test_app_id"