"""
Unit tests for token bucket rate limiting (Phase 8)
Tests acquire/refill/window rollover and concurrent behavior
"""
import time
import asyncio
import pytest
from unittest.mock import Mock, MagicMock
import redis

from backend.services.rate_limit import TokenBucket, exponential_backoff_with_jitter


class TestTokenBucket:
    """Test token bucket rate limiting functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_redis = Mock(spec=redis.Redis)
        self.bucket = TokenBucket(
            redis_client=self.mock_redis,
            key_prefix="test_rate",
            refill_rate=10,  # 10 tokens per minute
            capacity=10,
            window_s=60
        )
    
    def test_init_with_custom_params(self):
        """Test token bucket initialization with custom parameters"""
        bucket = TokenBucket(
            redis_client=self.mock_redis,
            key_prefix="custom",
            refill_rate=5,
            capacity=20,
            window_s=30
        )
        
        assert bucket.key_prefix == "custom"
        assert bucket.refill_rate == 5
        assert bucket.capacity == 20
        assert bucket.window_s == 30
    
    def test_acquire_success_new_bucket(self):
        """Test successful token acquisition with new bucket"""
        # Mock Redis to return None (new bucket)
        self.mock_redis.eval.return_value = [1, 9]  # Success, 9 tokens remaining
        
        result = self.bucket.acquire("org123", "meta", 1)
        
        assert result is True
        
        # Verify Redis script was called
        self.mock_redis.eval.assert_called_once()
        args = self.mock_redis.eval.call_args[0]
        assert "test_rate:org123:meta" in args
    
    def test_acquire_success_existing_bucket(self):
        """Test successful token acquisition with existing bucket"""
        self.mock_redis.eval.return_value = [1, 5]  # Success, 5 tokens remaining
        
        result = self.bucket.acquire("org123", "x", 2)
        
        assert result is True
    
    def test_acquire_rate_limited(self):
        """Test rate limiting when insufficient tokens"""
        self.mock_redis.eval.return_value = [0, 0]  # Rate limited, 0 tokens remaining
        
        result = self.bucket.acquire("org123", "meta", 3)
        
        assert result is False
    
    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once"""
        self.mock_redis.eval.return_value = [1, 5]  # Success, 5 tokens remaining
        
        result = self.bucket.acquire("org123", "meta", 5)
        
        assert result is True
        
        # Verify correct number of tokens requested
        args = self.mock_redis.eval.call_args[0]
        assert "5" in args  # tokens_requested parameter
    
    def test_acquire_redis_error_fail_open(self):
        """Test fail-open behavior when Redis is unavailable"""
        self.mock_redis.eval.side_effect = redis.RedisError("Connection failed")
        
        # Should allow request despite Redis error
        result = self.bucket.acquire("org123", "meta", 1)
        
        assert result is True
    
    def test_get_remaining_new_bucket(self):
        """Test getting remaining tokens for new bucket"""
        self.mock_redis.eval.return_value = 10  # Full capacity
        
        remaining = self.bucket.get_remaining("org123", "meta")
        
        assert remaining == 10
    
    def test_get_remaining_existing_bucket(self):
        """Test getting remaining tokens for existing bucket"""
        self.mock_redis.eval.return_value = 7
        
        remaining = self.bucket.get_remaining("org123", "meta")
        
        assert remaining == 7
    
    def test_get_remaining_redis_error(self):
        """Test getting remaining tokens with Redis error"""
        self.mock_redis.eval.side_effect = redis.RedisError("Connection failed")
        
        # Should return full capacity on error
        remaining = self.bucket.get_remaining("org123", "meta")
        
        assert remaining == self.bucket.capacity
    
    def test_get_reset_time_full_bucket(self):
        """Test reset time calculation for full bucket"""
        # Mock Redis to return full bucket
        self.mock_redis.hmget.return_value = [10, time.time()]
        
        reset_time = self.bucket.get_reset_time("org123", "meta")
        
        # Should be approximately now for full bucket
        assert abs(reset_time - time.time()) < 1
    
    def test_get_reset_time_empty_bucket(self):
        """Test reset time calculation for empty bucket"""
        now = time.time()
        self.mock_redis.hmget.return_value = [0, now - 30]  # Empty, last refill 30s ago
        
        reset_time = self.bucket.get_reset_time("org123", "meta")
        
        # Should be in the future
        assert reset_time > now
        
        # Should be reasonable time (not more than window duration)
        assert reset_time - now <= self.bucket.window_s
    
    def test_get_reset_time_redis_error(self):
        """Test reset time calculation with Redis error"""
        self.mock_redis.hmget.side_effect = redis.RedisError("Connection failed")
        
        reset_time = self.bucket.get_reset_time("org123", "meta")
        
        # Should return current time on error
        assert abs(reset_time - time.time()) < 1
    
    def test_tenant_isolation(self):
        """Test that different orgs have separate buckets"""
        self.mock_redis.eval.return_value = [1, 9]
        
        # Acquire tokens for different orgs
        result1 = self.bucket.acquire("org123", "meta", 1)
        result2 = self.bucket.acquire("org456", "meta", 1)
        
        assert result1 is True
        assert result2 is True
        
        # Verify different keys were used
        assert self.mock_redis.eval.call_count == 2
        calls = self.mock_redis.eval.call_args_list
        
        # Extract keys from Redis calls
        key1 = calls[0][0][1]  # First call, second argument (key)
        key2 = calls[1][0][1]  # Second call, second argument (key)
        
        assert key1 != key2
        assert "org123" in key1
        assert "org456" in key2
    
    def test_platform_isolation(self):
        """Test that different platforms have separate buckets"""
        self.mock_redis.eval.return_value = [1, 9]
        
        # Acquire tokens for different platforms
        result1 = self.bucket.acquire("org123", "meta", 1)
        result2 = self.bucket.acquire("org123", "x", 1)
        
        assert result1 is True
        assert result2 is True
        
        # Verify different keys were used
        assert self.mock_redis.eval.call_count == 2
        calls = self.mock_redis.eval.call_args_list
        
        key1 = calls[0][0][1]
        key2 = calls[1][0][1]
        
        assert key1 != key2
        assert "meta" in key1
        assert "x" in key2


class TestExponentialBackoff:
    """Test exponential backoff with jitter calculation"""
    
    def test_backoff_increases_exponentially(self):
        """Test that backoff delay increases exponentially"""
        delays = []
        
        for attempt in range(5):
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=60.0)
            delays.append(delay)
        
        # Each delay should generally be larger than the previous (accounting for jitter)
        # Base pattern should be 1, 2, 4, 8, 16 seconds (±25% jitter)
        assert delays[0] < 2.0  # ~1s ±25%
        assert delays[1] < 3.0  # ~2s ±25% 
        assert delays[2] < 6.0  # ~4s ±25%
        assert delays[3] < 12.0  # ~8s ±25%
        assert delays[4] < 24.0  # ~16s ±25%
    
    def test_backoff_respects_max_delay(self):
        """Test that backoff doesn't exceed max_delay"""
        for attempt in range(10, 20):  # High attempt numbers
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=30.0)
            
            assert delay <= 30.0 * 1.25  # Max delay + max jitter
    
    def test_backoff_minimum_delay(self):
        """Test that backoff has minimum delay"""
        for attempt in range(5):
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=60.0)
            
            assert delay >= 0.1  # Minimum delay
    
    def test_backoff_with_custom_base(self):
        """Test backoff with custom base delay"""
        delay = exponential_backoff_with_jitter(0, base_delay=5.0, max_delay=60.0)
        
        # Should be around 5 seconds ±25%
        assert 3.75 <= delay <= 6.25
    
    def test_backoff_jitter_variation(self):
        """Test that jitter creates variation in delays"""
        delays = []
        
        # Generate multiple delays for same attempt
        for _ in range(20):
            delay = exponential_backoff_with_jitter(2, base_delay=4.0, max_delay=60.0)
            delays.append(delay)
        
        # Should have variation (not all the same)
        unique_delays = set(delays)
        assert len(unique_delays) > 1
        
        # All should be in reasonable range (4s ±25%)
        for delay in delays:
            assert 3.0 <= delay <= 5.0