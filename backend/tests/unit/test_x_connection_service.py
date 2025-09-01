"""
Unit tests for X connection service
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx

from backend.services.x_connection_service import (
    XConnectionService,
    get_x_connection_service
)


class TestXConnectionService:
    """Test X connection service functionality"""
    
    @pytest.fixture
    def service(self):
        """Create XConnectionService instance"""
        return XConnectionService()
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, service):
        """Test successful user profile retrieval"""
        tokens = {"access_token": "bearer_token_123"}
        
        # Mock X API response
        mock_response_data = {
            "data": {
                "id": "12345",
                "username": "testuser",
                "name": "Test User",
                "verified": True,
                "created_at": "2020-01-01T00:00:00.000Z",
                "public_metrics": {
                    "followers_count": 1000,
                    "following_count": 500,
                    "tweet_count": 2000
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await service.get_me(tokens)
        
        # Verify result
        assert result["id"] == "12345"
        assert result["username"] == "testuser"
        assert result["name"] == "Test User"
        assert result["verified"] is True
        assert result["created_at"] == "2020-01-01T00:00:00.000Z"
        assert result["public_metrics"]["followers_count"] == 1000
    
    @pytest.mark.asyncio
    async def test_get_me_minimal_data(self, service):
        """Test user profile with minimal data"""
        tokens = {"access_token": "bearer_token_123"}
        
        # Mock minimal response
        mock_response_data = {
            "data": {
                "id": "12345",
                "username": "testuser"
                # Missing name, verified, etc.
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await service.get_me(tokens)
        
        assert result["id"] == "12345"
        assert result["username"] == "testuser"
        assert result["name"] == "testuser"  # Falls back to username
        assert result["verified"] is False  # Default value
        assert result["public_metrics"] == {}  # Default value
    
    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, service):
        """Test with invalid access token"""
        tokens = {"access_token": "invalid_token"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 401 response
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Invalid or expired X access token"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_get_me_insufficient_permissions(self, service):
        """Test with insufficient permissions"""
        tokens = {"access_token": "limited_token"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 403 response
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Forbidden"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Insufficient permissions to access user profile"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_get_me_rate_limit(self, service):
        """Test rate limit handling"""
        tokens = {"access_token": "bearer_token_123"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 429 response
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="X API rate limit exceeded - please try again later"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_get_me_no_access_token(self, service):
        """Test with missing access token"""
        tokens = {}
        
        with pytest.raises(ValueError, match="Access token is required"):
            await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_get_me_empty_response(self, service):
        """Test with empty API response"""
        tokens = {"access_token": "bearer_token_123"}
        
        # Mock empty response
        mock_response_data = {}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="No user data returned from X API"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_get_me_invalid_user_data(self, service):
        """Test with invalid user data (missing ID or username)"""
        tokens = {"access_token": "bearer_token_123"}
        
        # Mock response with missing username
        mock_response_data = {
            "data": {
                "id": "12345"
                # Missing username
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Invalid user data: missing ID or username"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_validate_tokens_success(self, service):
        """Test successful token validation"""
        tokens = {
            "access_token": "bearer_token_123",
            "scope": "tweet.read tweet.write users.read",
            "expires_at": "2024-12-31T23:59:59Z"
        }
        
        # Mock get_me call
        with patch.object(service, 'get_me') as mock_get_me:
            mock_get_me.return_value = {
                "id": "12345",
                "username": "testuser",
                "name": "Test User"
            }
            
            result = await service.validate_tokens(tokens)
        
        assert result["valid"] is True
        assert result["user_id"] == "12345"
        assert result["username"] == "testuser"
        assert result["name"] == "Test User"
        assert result["scopes"] == ["tweet.read", "tweet.write", "users.read"]
        assert result["expires_at"] == "2024-12-31T23:59:59Z"
    
    @pytest.mark.asyncio
    async def test_validate_tokens_failure(self, service):
        """Test token validation failure"""
        tokens = {"access_token": "invalid_token"}
        
        # Mock get_me failure
        with patch.object(service, 'get_me') as mock_get_me:
            mock_get_me.side_effect = ValueError("Invalid token")
            
            result = await service.validate_tokens(tokens)
        
        assert result["valid"] is False
        assert result["error"] == "Invalid token"
    
    def test_extract_scopes_string(self, service):
        """Test scope extraction from string"""
        tokens = {"scope": "tweet.read tweet.write users.read offline.access"}
        
        scopes = service._extract_scopes(tokens)
        
        assert scopes == ["tweet.read", "tweet.write", "users.read", "offline.access"]
    
    def test_extract_scopes_list(self, service):
        """Test scope extraction from list"""
        tokens = {"scope": ["tweet.read", "tweet.write", "users.read"]}
        
        scopes = service._extract_scopes(tokens)
        
        assert scopes == ["tweet.read", "tweet.write", "users.read"]
    
    def test_extract_scopes_fallback(self, service):
        """Test scope extraction fallback"""
        tokens = {}  # No scope field
        
        scopes = service._extract_scopes(tokens)
        
        # Should return default expected scopes
        expected = ["tweet.read", "tweet.write", "users.read", "offline.access"]
        assert scopes == expected
    
    def test_extract_scopes_empty_string(self, service):
        """Test scope extraction from empty string"""
        tokens = {"scope": ""}
        
        scopes = service._extract_scopes(tokens)
        
        # Should return default expected scopes
        expected = ["tweet.read", "tweet.write", "users.read", "offline.access"]
        assert scopes == expected
    
    @pytest.mark.asyncio
    async def test_get_user_context_success(self, service):
        """Test successful user context retrieval"""
        tokens = {"access_token": "bearer_token_123"}
        
        # Mock get_me call
        with patch.object(service, 'get_me') as mock_get_me:
            mock_get_me.return_value = {
                "id": "12345",
                "username": "testuser",
                "name": "Test User",
                "verified": True,
                "created_at": "2020-01-01T00:00:00.000Z",
                "public_metrics": {
                    "followers_count": 1000,
                    "following_count": 500,
                    "tweet_count": 2000
                }
            }
            
            result = await service.get_user_context(tokens)
        
        assert result["user_id"] == "12345"
        assert result["username"] == "testuser"
        assert result["display_name"] == "Test User"
        
        metadata = result["metadata"]
        assert metadata["since_id"] is None
        assert metadata["verified"] is True
        assert metadata["created_at"] == "2020-01-01T00:00:00.000Z"
        assert metadata["followers_count"] == 1000
        assert metadata["following_count"] == 500
        assert metadata["tweet_count"] == 2000
        assert metadata["last_connected"] is None
    
    @pytest.mark.asyncio
    async def test_get_user_context_failure(self, service):
        """Test user context retrieval failure"""
        tokens = {"access_token": "invalid_token"}
        
        # Mock get_me failure
        with patch.object(service, 'get_me') as mock_get_me:
            mock_get_me.side_effect = ValueError("Invalid token")
            
            with pytest.raises(ValueError, match="Failed to get user context: Invalid token"):
                await service.get_user_context(tokens)
    
    @pytest.mark.asyncio
    async def test_api_error_with_json_response(self, service):
        """Test API error handling with JSON error response"""
        tokens = {"access_token": "bearer_token_123"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 400 response with JSON error
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_response.json.return_value = {"detail": "Invalid request format"}
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "400 Bad Request", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="X API error: Invalid request format"):
                await service.get_me(tokens)
    
    @pytest.mark.asyncio
    async def test_api_error_without_json_response(self, service):
        """Test API error handling without JSON error response"""
        tokens = {"access_token": "bearer_token_123"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 500 response without JSON
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_response.json.side_effect = Exception("Not JSON")
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="X API error: 500"):
                await service.get_me(tokens)


class TestXConnectionServiceSingleton:
    """Test X connection service singleton functionality"""
    
    def test_get_x_connection_service_singleton(self):
        """Test that get_x_connection_service returns singleton"""
        with patch('backend.services.x_connection_service._x_connection_service_instance', None):
            service1 = get_x_connection_service()
            service2 = get_x_connection_service()
            assert service1 is service2
    
    def test_service_initialization(self):
        """Test service initialization"""
        service = XConnectionService()
        assert service.base_url == "https://api.twitter.com/2"