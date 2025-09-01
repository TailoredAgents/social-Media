"""
Integration tests for organization isolation (Phase 8)
Tests that one org throttled doesn't affect another; metrics reflect isolation
"""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from backend.services.publish_runner import get_publish_runner, PublishPayload
from backend.db.models import SocialConnection


@pytest.fixture
def mock_org1_connection():
    """Create mock connection for org1"""
    connection = Mock(spec=SocialConnection)
    connection.id = "org1-connection-id"
    connection.organization_id = "org1"
    connection.platform = "meta"
    connection.is_active = True
    connection.verified_for_posting = True
    connection.access_tokens = {"page_token": "encrypted_token"}
    connection.platform_metadata = {"page_id": "page1"}
    connection.token_expires_at = None
    connection.revoked_at = None
    return connection


@pytest.fixture
def mock_org2_connection():
    """Create mock connection for org2"""
    connection = Mock(spec=SocialConnection)
    connection.id = "org2-connection-id"
    connection.organization_id = "org2"
    connection.platform = "meta"
    connection.is_active = True
    connection.verified_for_posting = True
    connection.access_tokens = {"page_token": "encrypted_token"}
    connection.platform_metadata = {"page_id": "page2"}
    connection.token_expires_at = None
    connection.revoked_at = None
    return connection


@pytest.fixture
def test_payload():
    """Create test payload"""
    return PublishPayload(
        content="Test content",
        media_urls=[],
        content_hash="test_hash",
        scheduled_time=datetime.now(timezone.utc)
    )


class TestOrganizationIsolation:
    """Test that rate limiting and circuit breaking are isolated per organization"""
    
    def setup_method(self):
        """Set up test environment"""
        self.runner = get_publish_runner()
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_rate_limit_isolation_between_orgs(self, mock_redis, mock_org1_connection, mock_org2_connection, test_payload):
        """Test that rate limiting is isolated between organizations"""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock Redis eval calls for rate limiting
        # First org is rate limited, second org is allowed
        mock_redis_client.eval.side_effect = [
            1,  # Org1 circuit breaker allows
            [0, 0],  # Org1 rate limiter blocks (no tokens)
            1,  # Org2 circuit breaker allows
            [1, 9]  # Org2 rate limiter allows (9 tokens remaining)
        ]
        
        # Mock reset time calculation for org1
        mock_redis_client.hmget.return_value = [0, 1234567890.0]
        
        mock_db = Mock()
        
        # Test org1 - should be rate limited
        result1 = await self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0)
        
        assert result1.success is False
        assert result1.should_retry is True
        assert "Rate limited" in result1.error_message
        
        # Test org2 - should succeed (isolated from org1)
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "post_123", None))
            
            result2 = await self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0)
            
            assert result2.success is True
            assert result2.platform_post_id == "post_123"
        
        # Verify different Redis keys were used for rate limiting
        eval_calls = mock_redis_client.eval.call_args_list
        
        # Extract Redis keys from the calls
        org1_keys = [call[0][1] for call in eval_calls[:2]]  # First 2 calls for org1
        org2_keys = [call[0][1] for call in eval_calls[2:]]  # Next 2 calls for org2
        
        # Verify org isolation in keys
        for key in org1_keys:
            assert "org1" in key
            assert "org2" not in key
            
        for key in org2_keys:
            assert "org2" in key  
            assert "org1" not in key
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_circuit_breaker_isolation_between_orgs(self, mock_redis, mock_org1_connection, mock_org2_connection, test_payload):
        """Test that circuit breakers are isolated between organizations"""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock circuit breaker responses
        # Org1 circuit breaker is open (blocks), org2 is closed (allows)
        mock_redis_client.eval.side_effect = [
            0,  # Org1 circuit breaker blocks (open)
            1,  # Org2 circuit breaker allows (closed)
            [1, 9]  # Org2 rate limiter allows
        ]
        
        # Mock circuit breaker state for org1 (open)
        mock_redis_client.hmget.return_value = [b'5', b'1234567890.0', b'open']
        
        mock_db = Mock()
        
        # Test org1 - should be blocked by circuit breaker
        result1 = await self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0)
        
        assert result1.success is False
        assert result1.should_retry is True
        assert "Circuit breaker open" in result1.error_message
        
        # Test org2 - should succeed (isolated circuit breaker)
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "post_456", None))
            
            result2 = await self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0)
            
            assert result2.success is True
            assert result2.platform_post_id == "post_456"
        
        # Verify different Redis keys were used for circuit breakers
        eval_calls = mock_redis_client.eval.call_args_list
        org1_cb_key = eval_calls[0][0][1]  # First call - org1 circuit breaker
        org2_cb_key = eval_calls[1][0][1]  # Second call - org2 circuit breaker
        
        assert "org1" in org1_cb_key
        assert "org2" in org2_cb_key
        assert org1_cb_key != org2_cb_key
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_platform_isolation_within_org(self, mock_redis, test_payload):
        """Test that different platforms are isolated within same organization"""
        # Create connections for same org, different platforms
        meta_connection = Mock(spec=SocialConnection)
        meta_connection.id = "meta-conn-id"
        meta_connection.organization_id = "org1"
        meta_connection.platform = "meta"
        meta_connection.is_active = True
        meta_connection.verified_for_posting = True
        meta_connection.access_tokens = {"page_token": "encrypted_token"}
        meta_connection.platform_metadata = {"page_id": "page1"}
        meta_connection.token_expires_at = None
        meta_connection.revoked_at = None
        
        x_connection = Mock(spec=SocialConnection)
        x_connection.id = "x-conn-id"
        x_connection.organization_id = "org1"  # Same org
        x_connection.platform = "x"  # Different platform
        x_connection.is_active = True
        x_connection.verified_for_posting = True
        x_connection.access_tokens = {"access_token": "encrypted_token"}
        x_connection.platform_metadata = {}
        x_connection.token_expires_at = None
        x_connection.revoked_at = None
        
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock responses - meta is rate limited, x is allowed
        mock_redis_client.eval.side_effect = [
            1,  # Meta circuit breaker allows
            [0, 0],  # Meta rate limiter blocks
            1,  # X circuit breaker allows  
            [1, 9]  # X rate limiter allows
        ]
        
        mock_redis_client.hmget.return_value = [0, 1234567890.0]
        
        mock_db = Mock()
        
        # Test Meta platform - should be rate limited
        result_meta = await self.runner.run_publish(meta_connection, test_payload, mock_db, attempt=0)
        
        assert result_meta.success is False
        assert "Rate limited" in result_meta.error_message
        
        # Test X platform - should succeed (different platform bucket)
        with patch.object(self.runner, 'x_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "tweet_789", None))
            
            result_x = await self.runner.run_publish(x_connection, test_payload, mock_db, attempt=0)
            
            assert result_x.success is True
            assert result_x.platform_post_id == "tweet_789"
        
        # Verify different Redis keys were used for different platforms
        eval_calls = mock_redis_client.eval.call_args_list
        
        # Check that platform names appear in keys
        meta_keys = [call[0][1] for call in eval_calls[:2]]  # First 2 calls for meta
        x_keys = [call[0][1] for call in eval_calls[2:]]  # Next 2 calls for x
        
        for key in meta_keys:
            assert "meta" in key
            
        for key in x_keys:
            assert "x" in key
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_metrics_reflect_organization_isolation(self, mock_redis, mock_org1_connection, mock_org2_connection, test_payload):
        """Test that metrics properly reflect per-organization behavior"""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock org1 rate limited, org2 successful
        mock_redis_client.eval.side_effect = [
            1,  # Org1 circuit breaker allows
            [0, 0],  # Org1 rate limiter blocks
            1,  # Org2 circuit breaker allows
            [1, 9]  # Org2 rate limiter allows
        ]
        
        mock_redis_client.hmget.return_value = [0, 1234567890.0]
        
        mock_db = Mock()
        
        # Test org1 - rate limited
        result1 = await self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0)
        
        # Test org2 - successful
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "post_123", None))
            
            result2 = await self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0)
        
        # Verify metrics reflect correct org isolation
        assert result1.metrics['org_id'] == "org1"
        assert result1.metrics['result'] == "rate_limited"
        
        assert result2.metrics['org_id'] == "org2"
        assert result2.metrics['result'] == "success"
        assert result2.metrics['platform_post_id'] == "post_123"
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_concurrent_org_requests(self, mock_redis, mock_org1_connection, mock_org2_connection, test_payload):
        """Test concurrent requests from different organizations"""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock responses for concurrent requests
        mock_redis_client.eval.side_effect = [
            # Org1 requests
            1, [1, 9],  # Success
            1, [1, 8],  # Success
            # Org2 requests  
            1, [1, 9],  # Success
            1, [1, 8],  # Success
        ]
        
        mock_db = Mock()
        
        # Mock successful adapter responses
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            mock_adapter.publish = AsyncMock(return_value=(True, "success_post", None))
            
            # Create concurrent tasks
            tasks = [
                self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0),
                self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0),
                self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0),
                self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0),
            ]
            
            results = await asyncio.gather(*tasks)
        
        # All should succeed (sufficient tokens for both orgs)
        for result in results:
            assert result.success is True
            
        # Verify metrics show correct org isolation
        org1_results = [r for r in results if r.metrics['org_id'] == "org1"]
        org2_results = [r for r in results if r.metrics['org_id'] == "org2"]
        
        assert len(org1_results) == 2
        assert len(org2_results) == 2
    
    @pytest.mark.asyncio
    @patch('backend.services.rate_limit.get_redis_client')
    async def test_failure_isolation_circuit_breaker(self, mock_redis, mock_org1_connection, mock_org2_connection, test_payload):
        """Test that circuit breaker failures in one org don't affect another"""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Mock circuit breaker and rate limiter allowing requests
        mock_redis_client.eval.side_effect = [
            1, [1, 9],  # Org1 allowed
            1, [1, 9],  # Org2 allowed  
        ]
        
        mock_db = Mock()
        
        # Mock org1 adapter to fail, org2 to succeed
        with patch.object(self.runner, 'meta_adapter') as mock_adapter:
            # Alternate between failure for org1 and success for org2
            def adapter_side_effect(connection, content, media_urls):
                if connection.organization_id == "org1":
                    return asyncio.coroutine(lambda: (False, None, "Server error"))()
                else:
                    return asyncio.coroutine(lambda: (True, "success_post", None))()
            
            mock_adapter.publish = AsyncMock(side_effect=adapter_side_effect)
            
            result1 = await self.runner.run_publish(mock_org1_connection, test_payload, mock_db, attempt=0)
            result2 = await self.runner.run_publish(mock_org2_connection, test_payload, mock_db, attempt=0)
        
        # Org1 should fail, org2 should succeed
        assert result1.success is False
        assert result1.should_retry is True
        
        assert result2.success is True
        assert result2.platform_post_id == "success_post"
        
        # Verify metrics reflect isolation
        assert result1.metrics['org_id'] == "org1"
        assert result1.metrics['result'] == "failure"
        
        assert result2.metrics['org_id'] == "org2" 
        assert result2.metrics['result'] == "success"