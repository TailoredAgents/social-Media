"""
Unit tests for X mentions service
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from backend.services.x_mentions_service import XMentionsService, get_x_mentions_service
from backend.db.models import SocialConnection


class TestXMentionsService:
    """Test X mentions service functionality"""
    
    @pytest.fixture
    def mentions_service(self):
        """Create X mentions service"""
        return XMentionsService()
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock X connection"""
        connection = MagicMock(spec=SocialConnection)
        connection.id = "conn_123"
        connection.platform = "x"
        connection.platform_account_id = "user_456"
        connection.organization_id = "org_789"
        connection.access_tokens = {"access_token": "encrypted_token"}
        connection.platform_metadata = {"mentions_since_id": "12345"}
        connection.last_checked_at = datetime.now(timezone.utc) - timedelta(hours=1)
        # Add SQLAlchemy-like attributes
        connection._sa_instance_state = MagicMock()
        return connection
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        db = MagicMock()
        return db

    def test_init_default(self, mentions_service):
        """Test initialization with default settings"""
        assert mentions_service.base_url == "https://api.twitter.com/2"
        assert mentions_service.max_results == 100
        assert mentions_service.base_backoff_seconds == 60
        assert len(mentions_service._processed_tweet_ids) == 0
    
    def test_session_management(self, mentions_service):
        """Test session cache management"""
        # Add some test IDs
        mentions_service._processed_tweet_ids.add("123")
        mentions_service._processed_tweet_ids.add("456")
        
        assert len(mentions_service._processed_tweet_ids) == 2
        
        # Reset cache
        mentions_service.reset_session_cache()
        assert len(mentions_service._processed_tweet_ids) == 0
        
        # Get stats
        stats = mentions_service.get_session_stats()
        assert stats["processed_tweet_ids_count"] == 0
        assert "session_start_time" in stats

    @patch('backend.services.x_mentions_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_poll_mentions_success(self, mock_client, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test successful mentions polling"""
        # Mock decryption
        mock_decrypt.return_value = "bearer_token_123"
        
        # Mock API response
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "98765",
                    "text": "Hey @user_456 check this out!",
                    "author_id": "author_123",
                    "created_at": "2025-01-01T12:00:00.000Z"
                },
                {
                    "id": "98766", 
                    "text": "Another mention @user_456",
                    "author_id": "author_456",
                    "created_at": "2025-01-01T12:01:00.000Z"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        
        # Execute polling
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is True
        assert result["new_mentions"] == 2
        assert result["total_fetched"] == 2
        assert result["since_id"] == "98766"  # Highest ID
        assert len(result["processed_ids"]) == 2
        
        # Verify API call
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        assert "user_456/mentions" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer bearer_token_123"
        assert call_args[1]["params"]["since_id"] == "12345"
        
        # Verify database updates
        mock_db_session.commit.assert_called()
    
    @patch('backend.services.x_mentions_service.decrypt_token')
    async def test_poll_mentions_no_token(self, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test polling with no access token"""
        mock_connection.access_tokens = {}  # No access_token
        
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is False
        assert "No access token found" in result["error"]
    
    @patch('backend.services.x_mentions_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_poll_mentions_rate_limited(self, mock_client, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test polling with rate limit (429)"""
        mock_decrypt.return_value = "bearer_token_123"
        
        # Mock rate limit response
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        from httpx import HTTPStatusError, Response, Request
        
        mock_request = Request("GET", "http://test.com")
        mock_response = Response(429, request=mock_request, headers={"x-rate-limit-reset": "1640995200"})
        mock_client_instance.get.side_effect = HTTPStatusError(
            "429 Rate Limited", request=mock_request, response=mock_response
        )
        
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is False
        assert result["error"] == "rate_limited"
        assert "backoff_seconds" in result
        assert "retry_after" in result
    
    @patch('backend.services.x_mentions_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_poll_mentions_http_error(self, mock_client, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test polling with HTTP error (not 429)"""
        mock_decrypt.return_value = "bearer_token_123"
        
        # Mock HTTP error
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        from httpx import HTTPStatusError, Response, Request
        
        mock_request = Request("GET", "http://test.com")
        mock_response = Response(401, request=mock_request)
        mock_client_instance.get.side_effect = HTTPStatusError(
            "401 Unauthorized", request=mock_request, response=mock_response
        )
        
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is False
        assert "HTTP 401" in result["error"]
    
    @patch('backend.services.x_mentions_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_poll_mentions_no_new_mentions(self, mock_client, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test polling with no new mentions"""
        mock_decrypt.return_value = "bearer_token_123"
        
        # Mock API response with no data
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is True
        assert result["new_mentions"] == 0
        assert result["total_fetched"] == 0
        assert result["since_id"] == "12345"  # Unchanged
    
    @patch('backend.services.x_mentions_service.decrypt_token')
    @patch('httpx.AsyncClient')
    async def test_poll_mentions_duplicate_in_session(self, mock_client, mock_decrypt, mentions_service, mock_connection, mock_db_session):
        """Test polling with duplicates already processed in session"""
        mock_decrypt.return_value = "bearer_token_123"
        
        # Add tweet to processed cache
        mentions_service._processed_tweet_ids.add("98765")
        
        # Mock API response with duplicate
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "98765",  # Already processed
                    "text": "Hey @user_456 check this out!",
                    "author_id": "author_123",
                    "created_at": "2025-01-01T12:00:00.000Z"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        
        result = await mentions_service.poll_mentions(mock_connection, mock_db_session)
        
        assert result["success"] is True
        assert result["new_mentions"] == 0  # Duplicate skipped
        assert result["total_fetched"] == 1
        assert len(result["processed_ids"]) == 0  # Not processed again

    async def test_fetch_mentions_params(self, mentions_service):
        """Test _fetch_mentions parameter construction"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status.return_value = None
            mock_client_instance.get.return_value = mock_response
            
            await mentions_service._fetch_mentions("user_123", "token_456", "since_id_789")
            
            # Verify request parameters
            call_args = mock_client_instance.get.call_args
            assert "user_123/mentions" in call_args[0][0]
            
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer token_456"
            
            params = call_args[1]["params"]
            assert params["max_results"] == 100
            assert params["since_id"] == "since_id_789"
            assert "tweet.fields" in params

    async def test_process_mention(self, mentions_service):
        """Test _process_mention method"""
        tweet = {
            "id": "123456",
            "text": "Hello @user mention",
            "author_id": "author_789",
            "created_at": "2025-01-01T12:00:00.000Z"
        }
        
        connection = MagicMock()
        connection.id = "conn_123"
        
        # Should not raise exception (stub implementation)
        await mentions_service._process_mention(tweet, connection)
    
    def test_calculate_rate_limit_backoff_with_headers(self, mentions_service):
        """Test backoff calculation with rate limit headers"""
        import time
        
        # Mock response with rate limit headers
        response = MagicMock()
        current_time = int(time.time())
        reset_time = current_time + 300  # 5 minutes from now
        response.headers = {"x-rate-limit-reset": str(reset_time)}
        
        backoff = mentions_service._calculate_rate_limit_backoff(response)
        
        assert backoff >= 300  # At least the reset time
        assert backoff <= 330   # Reset time + max jitter
    
    def test_calculate_rate_limit_backoff_no_headers(self, mentions_service):
        """Test backoff calculation without rate limit headers"""
        response = MagicMock()
        response.headers = {}  # No rate limit headers
        
        backoff = mentions_service._calculate_rate_limit_backoff(response)
        
        assert backoff >= mentions_service.base_backoff_seconds
        assert backoff <= mentions_service.base_backoff_seconds + mentions_service.jitter_max_seconds
    
    async def test_update_since_id_new_metadata(self, mentions_service):
        """Test _update_since_id with new metadata"""
        connection = MagicMock()
        connection.platform_metadata = None  # No existing metadata
        
        db = MagicMock()
        
        await mentions_service._update_since_id(connection, db, "new_since_id_123")
        
        assert connection.platform_metadata == {"mentions_since_id": "new_since_id_123"}
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(connection)
    
    async def test_update_since_id_existing_metadata(self, mentions_service):
        """Test _update_since_id with existing metadata"""
        connection = MagicMock()
        connection.platform_metadata = {"other_key": "other_value"}
        
        db = MagicMock()
        
        await mentions_service._update_since_id(connection, db, "new_since_id_456")
        
        expected_metadata = {
            "other_key": "other_value",
            "mentions_since_id": "new_since_id_456"
        }
        assert connection.platform_metadata == expected_metadata
        db.commit.assert_called_once()


class TestXMentionsServiceSingleton:
    """Test X mentions service singleton"""
    
    @patch('backend.services.x_mentions_service.get_settings')
    def test_get_x_mentions_service_singleton(self, mock_get_settings):
        """Test that get_x_mentions_service returns singleton"""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Reset singleton
        import backend.services.x_mentions_service
        backend.services.x_mentions_service._x_mentions_service = None
        
        service1 = get_x_mentions_service()
        service2 = get_x_mentions_service()
        
        assert service1 is service2
        mock_get_settings.assert_called_once()
    
    def test_get_x_mentions_service_with_settings(self):
        """Test get_x_mentions_service with provided settings"""
        settings = MagicMock()
        
        # Reset singleton
        import backend.services.x_mentions_service
        backend.services.x_mentions_service._x_mentions_service = None
        
        service = get_x_mentions_service(settings=settings)
        assert service.settings == settings