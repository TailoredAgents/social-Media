"""
Unit tests for Meta page token service
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
import httpx

from backend.services.meta_page_token_service import (
    MetaPageTokenService, 
    get_meta_page_service
)


class TestMetaPageTokenService:
    """Test Meta page token service functionality"""
    
    @pytest.fixture
    def service(self):
        """Create MetaPageTokenService instance"""
        with patch('backend.services.meta_page_token_service.get_settings') as mock_settings:
            settings = MagicMock()
            settings.meta_graph_version = "v18.0"
            mock_settings.return_value = settings
            return MetaPageTokenService()
    
    @pytest.mark.asyncio
    async def test_list_pages_with_instagram_success(self, service):
        """Test successful page listing with Instagram accounts"""
        user_token = "user_access_token_123"
        
        # Mock Graph API response
        mock_response_data = {
            "data": [
                {
                    "id": "page_123",
                    "name": "Test Page 1",
                    "access_token": "page_token_123",
                    "instagram_business_account": {
                        "id": "ig_business_456"
                    }
                },
                {
                    "id": "page_456",
                    "name": "Test Page 2",
                    "access_token": "page_token_456"
                    # No Instagram account
                }
            ]
        }
        
        # Mock Instagram username call
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # First call for pages, second for Instagram username
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = mock_response_data
            mock_response1.raise_for_status.return_value = None
            
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {"username": "test_instagram"}
            mock_response2.raise_for_status.return_value = None
            
            mock_client.get.side_effect = [mock_response1, mock_response2]
            mock_client_class.return_value = mock_client
            
            result = await service.list_pages_with_instagram(user_token)
        
        # Verify result
        assert len(result) == 2
        
        # First page with Instagram
        page1 = result[0]
        assert page1["id"] == "page_123"
        assert page1["name"] == "Test Page 1"
        assert page1["has_instagram"] is True
        assert page1["token_available"] is True
        assert page1["instagram_business_account"]["id"] == "ig_business_456"
        assert page1["instagram_business_account"]["username"] == "test_instagram"
        
        # Second page without Instagram
        page2 = result[1]
        assert page2["id"] == "page_456"
        assert page2["name"] == "Test Page 2"
        assert page2["has_instagram"] is False
        assert page2["token_available"] is True
        assert page2["instagram_business_account"] is None
    
    @pytest.mark.asyncio
    async def test_list_pages_no_pages(self, service):
        """Test when user has no Facebook Pages"""
        user_token = "user_access_token_123"
        
        # Mock empty response
        mock_response_data = {"data": []}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await service.list_pages_with_instagram(user_token)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_pages_invalid_token(self, service):
        """Test with invalid access token"""
        user_token = "invalid_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 401 response
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid token"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Invalid or expired access token"):
                await service.list_pages_with_instagram(user_token)
    
    @pytest.mark.asyncio
    async def test_list_pages_insufficient_permissions(self, service):
        """Test with insufficient permissions"""
        user_token = "limited_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 403 response
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Insufficient permissions"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Insufficient permissions to access Facebook Pages"):
                await service.list_pages_with_instagram(user_token)
    
    @pytest.mark.asyncio
    async def test_list_pages_empty_token(self, service):
        """Test with empty token"""
        with pytest.raises(ValueError, match="User access token is required"):
            await service.list_pages_with_instagram("")
    
    @pytest.mark.asyncio
    async def test_exchange_for_page_token_success(self, service):
        """Test successful page token exchange"""
        user_token = "user_token_123"
        page_id = "page_123"
        
        # Mock successful response
        mock_response_data = {
            "access_token": "page_access_token_123",
            "name": "Test Page",
            "id": page_id
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
            
            result = await service.exchange_for_page_token(user_token, page_id)
        
        assert result["page_access_token"] == "page_access_token_123"
        assert result["page_name"] == "Test Page"
        assert result["page_id"] == page_id
    
    @pytest.mark.asyncio
    async def test_exchange_for_page_token_no_admin(self, service):
        """Test page token exchange when user is not page admin"""
        user_token = "user_token_123"
        page_id = "page_123"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 403 response
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Not page admin"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="You don't have admin access to this Facebook Page"):
                await service.exchange_for_page_token(user_token, page_id)
    
    @pytest.mark.asyncio
    async def test_exchange_for_page_token_page_not_found(self, service):
        """Test page token exchange with non-existent page"""
        user_token = "user_token_123"
        page_id = "nonexistent_page"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Page not found"
            
            mock_client.get.return_value = mock_response
            mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=MagicMock(), response=mock_response
            )
            mock_client_class.return_value = mock_client
            
            with pytest.raises(ValueError, match="Facebook Page not found or not accessible"):
                await service.exchange_for_page_token(user_token, page_id)
    
    @pytest.mark.asyncio
    async def test_exchange_for_page_token_no_token_available(self, service):
        """Test page token exchange when no token is returned"""
        user_token = "user_token_123"
        page_id = "page_123"
        
        # Mock response without access_token
        mock_response_data = {
            "name": "Test Page",
            "id": page_id
            # No access_token field
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
            
            with pytest.raises(ValueError, match="Unable to obtain page access token - you may not be a Page admin"):
                await service.exchange_for_page_token(user_token, page_id)
    
    @pytest.mark.asyncio
    async def test_exchange_for_page_token_empty_params(self, service):
        """Test page token exchange with empty parameters"""
        with pytest.raises(ValueError, match="User access token is required"):
            await service.exchange_for_page_token("", "page_123")
        
        with pytest.raises(ValueError, match="Page ID is required"):
            await service.exchange_for_page_token("token_123", "")
    
    @pytest.mark.asyncio
    async def test_validate_page_permissions_success(self, service):
        """Test successful page permissions validation"""
        page_token = "page_token_123"
        page_id = "page_123"
        
        # Mock successful response
        mock_response_data = {
            "id": page_id,
            "name": "Test Page",
            "permissions": {"ADMINISTER": True, "EDIT_PROFILE": True}
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
            
            result = await service.validate_page_permissions(page_token, page_id)
        
        assert result["valid"] is True
        assert result["page_id"] == page_id
        assert result["page_name"] == "Test Page"
        assert result["permissions"]["ADMINISTER"] is True
    
    @pytest.mark.asyncio
    async def test_validate_page_permissions_failure(self, service):
        """Test page permissions validation failure"""
        page_token = "invalid_token"
        page_id = "page_123"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock exception
            mock_client.get.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client
            
            result = await service.validate_page_permissions(page_token, page_id)
        
        assert result["valid"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_instagram_username_success(self, service):
        """Test successful Instagram username retrieval"""
        instagram_id = "ig_123"
        page_token = "page_token_123"
        
        # Mock successful response
        mock_response_data = {"username": "test_instagram_username"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await service._get_instagram_username(instagram_id, page_token)
        
        assert result == "test_instagram_username"
    
    @pytest.mark.asyncio
    async def test_get_instagram_username_no_token(self, service):
        """Test Instagram username retrieval with no page token"""
        result = await service._get_instagram_username("ig_123", "")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_instagram_username_api_error(self, service):
        """Test Instagram username retrieval with API error"""
        instagram_id = "ig_123"
        page_token = "page_token_123"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            
            # Mock exception
            mock_client.get.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client
            
            result = await service._get_instagram_username(instagram_id, page_token)
        
        assert result is None


class TestMetaPageServiceSingleton:
    """Test Meta page service singleton functionality"""
    
    def test_get_meta_page_service_singleton(self):
        """Test that get_meta_page_service returns singleton"""
        with patch('backend.services.meta_page_token_service._meta_page_service_instance', None):
            service1 = get_meta_page_service()
            service2 = get_meta_page_service()
            assert service1 is service2
    
    def test_service_initialization(self):
        """Test service initialization with settings"""
        with patch('backend.services.meta_page_token_service.get_settings') as mock_settings:
            settings = MagicMock()
            settings.meta_graph_version = "v19.0"
            mock_settings.return_value = settings
            
            service = MetaPageTokenService()
            assert service.graph_version == "v19.0"
            assert service.base_url == "https://graph.facebook.com/v19.0"