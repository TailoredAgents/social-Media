"""
Unit tests for PKCE state store service
"""
import pytest
import json
import secrets
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from backend.services.pkce_state_store import (
    PKCEStateStore, 
    get_state_store, 
    create_pkce_challenge,
    consume_pkce_state
)


class TestPKCEStateStore:
    """Test PKCE state store functionality"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.info.return_value = {"used_memory_human": "1.2M"}
        return redis_mock
    
    @pytest.fixture
    def state_store(self, mock_redis):
        """Create PKCEStateStore with mocked Redis"""
        return PKCEStateStore(redis_client=mock_redis)
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        settings_mock = MagicMock()
        settings_mock.redis_url = "redis://localhost:6379"
        return settings_mock
    
    def test_initialization_with_redis_client(self, mock_redis, mock_settings):
        """Test initialization with provided Redis client"""
        with patch('backend.services.pkce_state_store.get_settings', return_value=mock_settings):
            store = PKCEStateStore(redis_client=mock_redis)
            assert store.redis is mock_redis
            assert store.ttl == 600
    
    def test_create_pkce_challenge(self, state_store, mock_redis):
        """Test PKCE challenge creation"""
        organization_id = "org_123"
        platform = "meta"
        
        # Mock Redis operations
        mock_redis.setex.return_value = True
        
        result = state_store.create(organization_id, platform)
        
        # Verify return structure
        assert "state" in result
        assert "code_challenge" in result
        assert "code_challenge_method" in result
        assert result["code_challenge_method"] == "S256"
        
        # Verify Redis call
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        redis_key = call_args[0][0]
        ttl = call_args[0][1]
        state_data_json = call_args[0][2]
        
        assert redis_key.startswith("oauth:state:")
        assert ttl == 600
        
        # Verify stored data structure
        state_data = json.loads(state_data_json)
        assert state_data["organization_id"] == organization_id
        assert state_data["platform"] == platform
        assert "code_verifier" in state_data  # Server-side only
        assert "nonce" in state_data
        assert "created_at" in state_data
        assert "expires_at" in state_data
    
    def test_create_invalid_parameters(self, state_store):
        """Test creation with invalid parameters"""
        with pytest.raises(ValueError, match="organization_id and platform are required"):
            state_store.create("", "meta")
        
        with pytest.raises(ValueError, match="organization_id and platform are required"):
            state_store.create("org_123", "")
        
        with pytest.raises(ValueError, match="Platform must be one of"):
            state_store.create("org_123", "invalid_platform")
    
    def test_consume_state_success(self, state_store, mock_redis):
        """Test successful state consumption"""
        state = "test_state_123"
        organization_id = "org_123"
        platform = "x"
        
        # Mock stored state data
        state_data = {
            "organization_id": organization_id,
            "platform": platform,
            "code_verifier": "test_verifier",
            "nonce": "test_nonce",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        }
        
        # Mock Redis pipeline
        pipeline_mock = MagicMock()
        pipeline_mock.execute.return_value = [json.dumps(state_data), 1]
        mock_redis.pipeline.return_value = pipeline_mock
        
        result = state_store.consume(state)
        
        # Verify result
        assert result["organization_id"] == organization_id
        assert result["platform"] == platform
        assert result["code_verifier"] == "test_verifier"
        
        # Verify Redis operations
        mock_redis.pipeline.assert_called_once()
        pipeline_mock.get.assert_called_once_with(f"oauth:state:{state}")
        pipeline_mock.delete.assert_called_once_with(f"oauth:state:{state}")
        pipeline_mock.execute.assert_called_once()
    
    def test_consume_state_not_found(self, state_store, mock_redis):
        """Test consuming non-existent state"""
        state = "nonexistent_state"
        
        # Mock Redis pipeline returning None
        pipeline_mock = MagicMock()
        pipeline_mock.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipeline_mock
        
        with pytest.raises(ValueError, match="State consumption failed"):
            state_store.consume(state)
    
    def test_consume_expired_state(self, state_store, mock_redis):
        """Test consuming expired state"""
        state = "expired_state"
        
        # Mock expired state data
        expired_data = {
            "organization_id": "org_123",
            "platform": "meta",
            "code_verifier": "test_verifier",
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        }
        
        # Mock Redis pipeline
        pipeline_mock = MagicMock()
        pipeline_mock.execute.return_value = [json.dumps(expired_data), 1]
        mock_redis.pipeline.return_value = pipeline_mock
        
        with pytest.raises(ValueError, match="State consumption failed"):
            state_store.consume(state)
    
    def test_consume_invalid_json(self, state_store, mock_redis):
        """Test consuming state with invalid JSON"""
        state = "invalid_json_state"
        
        # Mock Redis pipeline returning invalid JSON
        pipeline_mock = MagicMock()
        pipeline_mock.execute.return_value = ["invalid json", 1]
        mock_redis.pipeline.return_value = pipeline_mock
        
        with pytest.raises(ValueError, match="Invalid state data"):
            state_store.consume(state)
    
    def test_cache_tokens(self, state_store, mock_redis):
        """Test token caching functionality"""
        state = "test_state"
        tokens = {
            "access_token": "token_123",
            "token_type": "bearer",
            "expires_in": 3600
        }
        scopes = ["read", "write"]
        
        mock_redis.setex.return_value = True
        
        state_store.cache_tokens(state, tokens, scopes)
        
        # Verify Redis call
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        cache_key = call_args[0][0]
        ttl = call_args[0][1]
        cache_data_json = call_args[0][2]
        
        assert cache_key == f"oauth:tokens:{state}"
        assert ttl == 600
        
        # Verify cached data
        cache_data = json.loads(cache_data_json)
        assert cache_data["tokens"] == tokens
        assert cache_data["scopes"] == scopes
        assert "cached_at" in cache_data
    
    def test_read_tokens_success(self, state_store, mock_redis):
        """Test successful token reading"""
        state = "test_state"
        cached_data = {
            "tokens": {"access_token": "token_123"},
            "scopes": ["read", "write"],
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(cached_data)
        
        result = state_store.read_tokens(state)
        
        assert result == cached_data
        mock_redis.get.assert_called_once_with(f"oauth:tokens:{state}")
    
    def test_read_tokens_not_found(self, state_store, mock_redis):
        """Test reading non-existent tokens"""
        state = "nonexistent_state"
        mock_redis.get.return_value = None
        
        result = state_store.read_tokens(state)
        
        assert result is None
    
    def test_cleanup_expired(self, state_store, mock_redis):
        """Test cleanup of expired entries"""
        # Mock scan_iter to return some keys
        mock_redis.scan_iter.return_value = [
            "oauth:state:key1",
            "oauth:state:key2",
            "oauth:state:key3"
        ]
        
        # Mock exists to return False for some keys (expired)
        mock_redis.exists.side_effect = [False, True, False]
        
        count = state_store.cleanup_expired()
        
        assert count == 2  # Two expired entries
        mock_redis.scan_iter.assert_called_once_with(match="oauth:state:*")
    
    def test_get_stats(self, state_store, mock_redis):
        """Test statistics gathering"""
        # Mock scan results
        mock_redis.scan_iter.side_effect = [
            ["oauth:state:1", "oauth:state:2"],  # Active states
            ["oauth:tokens:1"]  # Cached tokens
        ]
        
        stats = state_store.get_stats()
        
        assert stats["active_states"] == 2
        assert stats["cached_tokens"] == 1
        assert stats["redis_info"]["connected"] is True
        assert "memory_used" in stats["redis_info"]
    
    def test_code_challenge_generation(self, state_store, mock_redis):
        """Test PKCE code challenge generation follows RFC 7636"""
        organization_id = "org_123"
        platform = "x"
        
        mock_redis.setex.return_value = True
        
        result = state_store.create(organization_id, platform)
        
        # Extract the stored code_verifier from Redis call
        call_args = mock_redis.setex.call_args
        state_data = json.loads(call_args[0][2])
        code_verifier = state_data["code_verifier"]
        
        # Manually calculate expected challenge
        challenge_bytes = hashlib.sha256(code_verifier.encode('ascii')).digest()
        expected_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')
        
        assert result["code_challenge"] == expected_challenge
        assert result["code_challenge_method"] == "S256"
    
    def test_different_platforms_supported(self, state_store, mock_redis):
        """Test that different platforms are properly supported"""
        organization_id = "org_123"
        mock_redis.setex.return_value = True
        
        for platform in ["meta", "x"]:
            result = state_store.create(organization_id, platform)
            
            # Verify platform is stored
            call_args = mock_redis.setex.call_args
            state_data = json.loads(call_args[0][2])
            assert state_data["platform"] == platform


class TestGlobalStateFunctions:
    """Test global convenience functions"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for global functions"""
        with patch('backend.services.pkce_state_store._state_store_instance', None):
            yield
    
    @patch('backend.services.pkce_state_store.PKCEStateStore')
    def test_get_state_store_singleton(self, mock_store_class):
        """Test that get_state_store returns singleton"""
        mock_instance = MagicMock()
        mock_store_class.return_value = mock_instance
        
        store1 = get_state_store()
        store2 = get_state_store()
        
        assert store1 is store2
        mock_store_class.assert_called_once()
    
    @patch('backend.services.pkce_state_store.get_state_store')
    def test_create_pkce_challenge_convenience(self, mock_get_store):
        """Test convenience function for creating challenges"""
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store
        mock_store.create.return_value = {"state": "test", "code_challenge": "test"}
        
        result = create_pkce_challenge("org_123", "meta")
        
        mock_store.create.assert_called_once_with("org_123", "meta")
        assert result == {"state": "test", "code_challenge": "test"}
    
    @patch('backend.services.pkce_state_store.get_state_store')
    def test_consume_pkce_state_convenience(self, mock_get_store):
        """Test convenience function for consuming state"""
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store
        mock_store.consume.return_value = {"organization_id": "org_123"}
        
        result = consume_pkce_state("test_state")
        
        mock_store.consume.assert_called_once_with("test_state")
        assert result == {"organization_id": "org_123"}


class TestPKCEStateStoreErrorHandling:
    """Test error handling in PKCE state store"""
    
    @pytest.fixture
    def failing_redis(self):
        """Mock Redis client that fails operations"""
        redis_mock = MagicMock()
        redis_mock.setex.side_effect = Exception("Redis connection failed")
        redis_mock.pipeline.side_effect = Exception("Pipeline failed")
        return redis_mock
    
    def test_create_handles_redis_failure(self, failing_redis):
        """Test that creation handles Redis failures gracefully"""
        store = PKCEStateStore(redis_client=failing_redis)
        
        with pytest.raises(RuntimeError, match="PKCE state creation failed"):
            store.create("org_123", "meta")
    
    def test_consume_handles_redis_failure(self, failing_redis):
        """Test that consumption handles Redis failures gracefully"""
        store = PKCEStateStore(redis_client=failing_redis)
        
        with pytest.raises(ValueError, match="State consumption failed"):
            store.consume("test_state")
    
    def test_cache_tokens_handles_redis_failure(self, failing_redis):
        """Test that token caching handles Redis failures gracefully"""
        store = PKCEStateStore(redis_client=failing_redis)
        
        with pytest.raises(RuntimeError, match="Token caching failed"):
            store.cache_tokens("test_state", {"token": "value"}, ["scope"])