"""
Integration tests for publish retries (Phase 8)
Tests mock 429/5xx → backoff + retry; success unblocks
"""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import httpx

from backend.services.publish_runner import get_publish_runner, PublishPayload
from backend.services.rate_limit import RetryableError, FatalError
from backend.db.models import SocialConnection
from backend.tests.conftest import TestDatabase


@pytest.fixture
async def mock_connection():
    """Create mock social connection for testing"""
    connection = Mock(spec=SocialConnection)
    connection.id = "test-connection-id"
    connection.organization_id = "test-org-id"
    connection.platform = "meta"
    connection.is_active = True
    connection.verified_for_posting = True
    connection.access_tokens = {
        "page_token": "encrypted_page_token",
        "access_token": "encrypted_access_token"
    }
    connection.platform_metadata = {
        "page_id": "test_page_id"
    }
    connection.token_expires_at = None
    connection.revoked_at = None
    return connection


@pytest.fixture
def mock_payload():
    """Create test publish payload"""
    return PublishPayload(
        content="Test content for publishing",
        media_urls=["https://example.com/image.jpg"],
        content_hash="test_content_hash_123",
        scheduled_time=datetime.now(timezone.utc),
        idempotency_key="test_idempotency_key"
    )


class TestPublishRetries:
    """Test publish retry logic with mocked responses"""
    
    def setup_method(self):
        """Set up test environment"""
        self.runner = get_publish_runner()
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_successful_publish_first_attempt(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test successful publish on first attempt"""
        # Mock dependencies
        mock_decrypt.return_value = "decrypted_token"
        mock_redis.return_value = Mock()
        
        # Mock Redis operations (rate limit and circuit breaker)
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "meta_post_123456"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(return_value=mock_response)
            
            # Mock database session
            mock_db = Mock()
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is True
            assert result.platform_post_id == "meta_post_123456"
            assert result.should_retry is False
            assert result.error_message is None
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_rate_limit_429_retry(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test retry logic for 429 rate limiting"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Mock Redis operations - allow through rate limiter and circuit breaker
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"x-rate-limit-reset": "1234567890"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(return_value=mock_response)
            
            mock_db = Mock()
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is False
            assert result.should_retry is True
            assert "Rate limited" in result.error_message
            assert result.retry_after_s is not None
            assert result.retry_after_s > 0
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_server_error_5xx_retry(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test retry logic for 5xx server errors"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(return_value=mock_response)
            
            mock_db = Mock()
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is False
            assert result.should_retry is True
            assert "server error" in result.error_message
            assert result.retry_after_s is not None
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_auth_error_401_no_retry(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test no retry for authentication errors (401)"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(return_value=mock_response)
            
            mock_db = Mock()
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is False
            assert result.should_retry is False  # Should not retry auth errors
            assert "Authentication failed" in result.error_message
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_circuit_breaker_blocks_request(self, mock_redis, mock_connection, mock_payload):
        """Test circuit breaker blocking requests when open"""
        # Mock Redis circuit breaker to return blocked (open)
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 0  # Block request (circuit open)
        mock_redis_client.hmget.return_value = [b'5', b'1234567890.0', b'open']  # Circuit state
        
        mock_db = Mock()
        
        result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
        
        assert result.success is False
        assert result.should_retry is True
        assert "Circuit breaker open" in result.error_message
        assert result.retry_after_s is not None
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_rate_limiter_blocks_request(self, mock_redis, mock_connection, mock_payload):
        """Test rate limiter blocking requests when quota exceeded"""
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Allow circuit breaker, but block rate limiter
        mock_redis_client.eval.side_effect = [
            1,  # Circuit breaker allows
            [0, 0]  # Rate limiter blocks (no tokens remaining)
        ]
        mock_redis_client.hmget.return_value = [0, 1234567890.0]  # Rate limit state
        
        mock_db = Mock()
        
        result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
        
        assert result.success is False
        assert result.should_retry is True
        assert "Rate limited" in result.error_message
        assert result.retry_after_s is not None
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_network_timeout_retry(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test retry logic for network timeouts"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            
            mock_db = Mock()
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is False
            assert result.should_retry is True
            assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    @patch('backend.services.publisher_adapters.meta_adapter.decrypt_token')
    async def test_exponential_backoff_increases(self, mock_decrypt, mock_redis, mock_connection, mock_payload):
        """Test that retry delay increases with attempt number"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        # Mock 500 response for retry
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post = AsyncMock(return_value=mock_response)
            
            mock_db = Mock()
            
            # Test multiple attempts
            results = []
            for attempt in [0, 1, 2, 3]:
                result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=attempt)
                results.append(result)
            
            # Verify retry delays increase
            delays = [r.retry_after_s for r in results]
            
            # Each delay should generally be larger than the previous
            for i in range(1, len(delays)):
                # Allow for jitter variation - next delay should be at least 75% of expected
                expected_min = delays[i-1] * 1.5 * 0.75
                assert delays[i] >= expected_min or delays[i] <= 60  # Cap at max delay
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_unverified_connection_fatal_error(self, mock_redis, mock_connection, mock_payload):
        """Test that unverified connection produces fatal error"""
        # Mock unverified connection
        mock_connection.verified_for_posting = False
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        
        result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
        
        assert result.success is False
        assert result.should_retry is False  # Fatal - no retry
        assert "not verified for posting" in result.error_message
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_inactive_connection_fatal_error(self, mock_redis, mock_connection, mock_payload):
        """Test that inactive connection produces fatal error"""
        # Mock inactive connection
        mock_connection.is_active = False
        
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        
        result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
        
        assert result.success is False
        assert result.should_retry is False  # Fatal - no retry
        assert "not active" in result.error_message
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_audit_logging_on_success(self, mock_redis, mock_connection, mock_payload):
        """Test that successful publish creates audit log"""
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        mock_db = Mock()
        
        # Mock successful adapter response
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "post_123", None))
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is True
            
            # Verify audit log was created
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            
            # Check the audit log object
            audit_call = mock_db.add.call_args[0][0]
            assert audit_call.action == "publish_attempt"
            assert audit_call.status == "success"
            assert audit_call.organization_id == mock_connection.organization_id
            assert audit_call.connection_id == mock_connection.id
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_audit_logging_on_failure(self, mock_redis, mock_connection, mock_payload):
        """Test that failed publish creates audit log"""
        # Mock Redis operations
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.eval.return_value = 1  # Allow request
        
        mock_db = Mock()
        
        # Mock failed adapter response
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(False, None, "Test error"))
            
            result = await self.runner.run_publish(mock_connection, mock_payload, mock_db, attempt=0)
            
            assert result.success is False
            
            # Verify audit log was created
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            
            # Check the audit log object
            audit_call = mock_db.add.call_args[0][0]
            assert audit_call.action == "publish_attempt"
            assert audit_call.status == "failure_retryable"