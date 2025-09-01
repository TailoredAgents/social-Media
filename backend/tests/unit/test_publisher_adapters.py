"""
Unit tests for Phase 7: Publisher adapters
Tests the Meta/X adapter stubs and idempotency functionality
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from backend.services.connection_publisher_service import ConnectionPublisherService
from backend.db.models import SocialConnection, SocialAudit


class TestPublisherAdapters:
    """Unit tests for connection publisher service adapters"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = MagicMock()
        settings.meta_graph_version = "v18.0"
        return settings
    
    @pytest.fixture
    def publisher_service(self, mock_settings):
        """Create publisher service with mock settings"""
        return ConnectionPublisherService(settings=mock_settings)
    
    @pytest.fixture
    def mock_meta_connection(self):
        """Create mock Meta connection"""
        connection = MagicMock(spec=SocialConnection)
        connection.id = "conn_123"
        connection.platform = "meta"
        connection.organization_id = "org_456"
        connection.is_active = True
        connection.verified_for_posting = True
        connection.access_tokens = {"page_token": "encrypted_page_token"}
        connection.platform_metadata = {"page_id": "123456789"}
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        return connection
    
    @pytest.fixture
    def mock_x_connection(self):
        """Create mock X connection"""
        connection = MagicMock(spec=SocialConnection)
        connection.id = "conn_789"
        connection.platform = "x"
        connection.organization_id = "org_456"
        connection.is_active = True
        connection.verified_for_posting = True
        connection.access_tokens = {"access_token": "encrypted_access_token"}
        connection.platform_metadata = {}
        connection.token_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        return connection
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        db = MagicMock()
        return db
    
    def test_init_with_settings(self, mock_settings):
        """Test initialization with provided settings"""
        service = ConnectionPublisherService(settings=mock_settings)
        assert service.settings == mock_settings
        assert service.meta_base_url == "https://graph.facebook.com/v18.0"
        assert service.x_base_url == "https://api.twitter.com/2"
    
    def test_init_without_settings(self):
        """Test initialization without provided settings"""
        with patch('backend.services.connection_publisher_service.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.meta_graph_version = "v20.0"
            mock_get_settings.return_value = mock_settings
            
            service = ConnectionPublisherService()
            assert service.meta_base_url == "https://graph.facebook.com/v20.0"
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_publish_to_meta_success(self, mock_decrypt, publisher_service, mock_meta_connection, mock_db_session):
        """Test successful Meta publishing"""
        mock_decrypt.return_value = "decrypted_page_token"
        
        content = "Test content for Meta"
        media_urls = ["https://example.com/image.jpg"]
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_meta_connection, content, media_urls, mock_db_session
        )
        
        # Should succeed with mock implementation
        assert success is True
        assert post_id is not None
        assert post_id.startswith("meta_post_")
        assert error == "Published to Meta successfully"
        
        # Verify token was decrypted
        mock_decrypt.assert_called_once_with("encrypted_page_token")
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_publish_to_x_success(self, mock_decrypt, publisher_service, mock_x_connection, mock_db_session):
        """Test successful X publishing"""
        mock_decrypt.return_value = "decrypted_access_token"
        
        content = "Test tweet content"
        media_urls = []
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_x_connection, content, media_urls, mock_db_session
        )
        
        # Should succeed with mock implementation
        assert success is True
        assert post_id is not None
        assert post_id.startswith("x_tweet_")
        assert error == "Published to X successfully"
        
        # Verify token was decrypted
        mock_decrypt.assert_called_once_with("encrypted_access_token")
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    async def test_publish_inactive_connection(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test publishing to inactive connection fails"""
        mock_meta_connection.is_active = False
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_meta_connection, "test", [], mock_db_session
        )
        
        assert success is False
        assert post_id is None
        assert "not active" in error
    
    async def test_publish_unverified_connection(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test publishing to unverified connection fails"""
        mock_meta_connection.verified_for_posting = False
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_meta_connection, "test", [], mock_db_session
        )
        
        assert success is False
        assert post_id is None
        assert "not verified" in error
        assert "test draft" in error.lower()
    
    async def test_publish_unsupported_platform(self, publisher_service, mock_db_session):
        """Test publishing to unsupported platform"""
        unsupported_connection = MagicMock(spec=SocialConnection)
        unsupported_connection.platform = "linkedin"
        unsupported_connection.is_active = True
        unsupported_connection.verified_for_posting = True
        
        success, post_id, error = await publisher_service.publish_to_connection(
            unsupported_connection, "test", [], mock_db_session
        )
        
        assert success is False
        assert post_id is None
        assert "Unsupported platform" in error
    
    async def test_publish_meta_no_page_token(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test Meta publishing without page token"""
        mock_meta_connection.access_tokens = {"access_token": "user_token_only"}
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_meta_connection, "test", [], mock_db_session
        )
        
        assert success is False
        assert post_id is None
        assert "No page access token" in error
    
    async def test_publish_meta_no_page_id(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test Meta publishing without page ID in metadata"""
        mock_meta_connection.platform_metadata = {}  # No page_id
        
        with patch('backend.services.connection_publisher_service.decrypt_token', return_value="token"):
            success, post_id, error = await publisher_service.publish_to_connection(
                mock_meta_connection, "test", [], mock_db_session
            )
        
        assert success is False
        assert post_id is None
        assert "No page ID" in error
    
    async def test_publish_x_no_access_token(self, publisher_service, mock_x_connection, mock_db_session):
        """Test X publishing without access token"""
        mock_x_connection.access_tokens = {"refresh_token": "refresh_only"}
        
        success, post_id, error = await publisher_service.publish_to_connection(
            mock_x_connection, "test", [], mock_db_session
        )
        
        assert success is False
        assert post_id is None
        assert "No access token" in error
    
    def test_generate_content_hash_basic(self, publisher_service):
        """Test basic content hash generation"""
        content = "Test content"
        media_urls = ["https://example.com/image.jpg"]
        
        hash1 = publisher_service.generate_content_hash(content, media_urls)
        hash2 = publisher_service.generate_content_hash(content, media_urls)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_generate_content_hash_different_content(self, publisher_service):
        """Test that different content produces different hashes"""
        hash1 = publisher_service.generate_content_hash("Content A", [])
        hash2 = publisher_service.generate_content_hash("Content B", [])
        
        assert hash1 != hash2
    
    def test_generate_content_hash_different_media(self, publisher_service):
        """Test that different media produces different hashes"""
        content = "Same content"
        hash1 = publisher_service.generate_content_hash(content, ["image1.jpg"])
        hash2 = publisher_service.generate_content_hash(content, ["image2.jpg"])
        
        assert hash1 != hash2
    
    def test_generate_content_hash_media_order(self, publisher_service):
        """Test that media URL order doesn't affect hash (sorted)"""
        content = "Test content"
        hash1 = publisher_service.generate_content_hash(content, ["b.jpg", "a.jpg"])
        hash2 = publisher_service.generate_content_hash(content, ["a.jpg", "b.jpg"])
        
        # Should be same because URLs are sorted
        assert hash1 == hash2
    
    def test_generate_idempotency_key(self, publisher_service):
        """Test idempotency key generation"""
        org_id = "org_123"
        conn_id = "conn_456"
        content_hash = "abcd1234"
        scheduled_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        key = publisher_service.generate_idempotency_key(
            org_id, conn_id, content_hash, scheduled_time
        )
        
        expected = f"content_schedule:{org_id}:{conn_id}:{content_hash}:2024-01-01T12:00:00+00:00"
        assert key == expected
    
    def test_generate_idempotency_key_immediate(self, publisher_service):
        """Test idempotency key for immediate publishing"""
        org_id = "org_123"
        conn_id = "conn_456"
        content_hash = "abcd1234"
        
        key = publisher_service.generate_idempotency_key(
            org_id, conn_id, content_hash, None
        )
        
        expected = f"content_schedule:{org_id}:{conn_id}:{content_hash}:immediate"
        assert key == expected
    
    @patch('backend.services.connection_publisher_service.get_token_refresh_service')
    async def test_ensure_token_fresh_no_expiry(self, mock_get_refresh, publisher_service, mock_meta_connection, mock_db_session):
        """Test token freshness check when no expiry is set"""
        mock_meta_connection.token_expires_at = None
        
        # Should not attempt refresh
        await publisher_service._ensure_token_fresh(mock_meta_connection, mock_db_session)
        
        mock_get_refresh.assert_not_called()
    
    @patch('backend.services.connection_publisher_service.get_token_refresh_service')
    async def test_ensure_token_fresh_not_expiring(self, mock_get_refresh, publisher_service, mock_meta_connection, mock_db_session):
        """Test token freshness when token is not expiring soon"""
        # Token expires in 2 hours (not within 1 hour threshold)
        mock_meta_connection.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        
        await publisher_service._ensure_token_fresh(mock_meta_connection, mock_db_session)
        
        # Should not attempt refresh
        mock_get_refresh.assert_not_called()
    
    @patch('backend.services.connection_publisher_service.get_token_refresh_service')
    async def test_ensure_token_fresh_expiring_soon(self, mock_get_refresh, publisher_service, mock_meta_connection, mock_db_session):
        """Test token freshness when token is expiring soon"""
        # Token expires in 30 minutes (within 1 hour threshold)
        mock_meta_connection.token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        # Mock refresh service
        mock_refresh_service = MagicMock()
        mock_get_refresh.return_value = mock_refresh_service
        
        # Mock successful refresh
        new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
        mock_refresh_service.refresh_meta_connection = AsyncMock(
            return_value=(True, new_expiry, "Refresh successful")
        )
        
        await publisher_service._ensure_token_fresh(mock_meta_connection, mock_db_session)
        
        # Should attempt refresh
        mock_get_refresh.assert_called_once()
        mock_refresh_service.refresh_meta_connection.assert_called_once_with(mock_meta_connection, mock_db_session)
    
    @patch('backend.services.connection_publisher_service.get_token_refresh_service')
    async def test_ensure_token_fresh_refresh_failure(self, mock_get_refresh, publisher_service, mock_meta_connection, mock_db_session):
        """Test token freshness when refresh fails"""
        mock_meta_connection.token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        mock_refresh_service = MagicMock()
        mock_get_refresh.return_value = mock_refresh_service
        
        # Mock failed refresh
        mock_refresh_service.refresh_meta_connection = AsyncMock(
            return_value=(False, None, "Refresh failed")
        )
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await publisher_service._ensure_token_fresh(mock_meta_connection, mock_db_session)
        
        assert "Token refresh failed" in str(exc_info.value)
    
    async def test_create_audit_log_success(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test successful audit log creation"""
        await publisher_service._create_audit_log(
            mock_db_session, mock_meta_connection, "test_action", "success", {"key": "value"}
        )
        
        # Verify audit log was created
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # Check the audit log content
        added_audit = mock_db_session.add.call_args[0][0]
        assert isinstance(added_audit, SocialAudit)
        assert added_audit.organization_id == mock_meta_connection.organization_id
        assert added_audit.connection_id == mock_meta_connection.id
        assert added_audit.platform == "meta"
        assert added_audit.action == "test_action"
        assert added_audit.status == "success"
        assert added_audit.metadata == {"key": "value"}
    
    async def test_create_audit_log_failure_handled(self, publisher_service, mock_meta_connection, mock_db_session):
        """Test that audit log creation failures don't break publishing"""
        # Mock database error
        mock_db_session.add.side_effect = Exception("DB error")
        
        # Should not raise exception
        await publisher_service._create_audit_log(
            mock_db_session, mock_meta_connection, "test_action", "success", {}
        )
        
        # Should have attempted to add
        mock_db_session.add.assert_called_once()
    
    def test_singleton_behavior(self):
        """Test that get_connection_publisher_service returns singleton"""
        from backend.services.connection_publisher_service import get_connection_publisher_service
        
        service1 = get_connection_publisher_service()
        service2 = get_connection_publisher_service()
        
        assert service1 is service2
    
    def test_singleton_with_settings(self, mock_settings):
        """Test singleton behavior with provided settings"""
        from backend.services.connection_publisher_service import get_connection_publisher_service
        
        # Reset singleton
        import backend.services.connection_publisher_service
        backend.services.connection_publisher_service._connection_publisher_service = None
        
        service = get_connection_publisher_service(settings=mock_settings)
        assert service.settings == mock_settings