"""
Unit tests for partner OAuth router
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from backend.api.partner_oauth import (
    router,
    is_partner_oauth_enabled,
    require_partner_oauth_enabled,
    get_user_organization_id,
    _get_client_id,
    _get_redirect_uri,
    _exchange_code_for_tokens,
    PLATFORM_CONFIGS
)


class TestFeatureFlagGating:
    """Test feature flag gating functionality"""
    
    def test_is_partner_oauth_enabled_default_false(self):
        """Test that feature flag defaults to False"""
        with patch('backend.api.partner_oauth.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(feature_partner_oauth=False)
            assert is_partner_oauth_enabled() is False
    
    def test_is_partner_oauth_enabled_when_true(self):
        """Test that feature flag can be enabled"""
        with patch('backend.api.partner_oauth.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(feature_partner_oauth=True)
            assert is_partner_oauth_enabled() is True
    
    def test_is_partner_oauth_enabled_missing_attribute(self):
        """Test handling when attribute is missing"""
        with patch('backend.api.partner_oauth.get_settings') as mock_settings:
            settings_mock = MagicMock()
            del settings_mock.feature_partner_oauth  # Remove attribute
            mock_settings.return_value = settings_mock
            
            # Should default to False when attribute missing
            assert is_partner_oauth_enabled() is False
    
    def test_require_partner_oauth_enabled_passes_when_enabled(self):
        """Test dependency passes when feature enabled"""
        with patch('backend.api.partner_oauth.is_partner_oauth_enabled', return_value=True):
            # Should not raise exception
            require_partner_oauth_enabled()
    
    def test_require_partner_oauth_enabled_raises_when_disabled(self):
        """Test dependency raises HTTPException when feature disabled"""
        with patch('backend.api.partner_oauth.is_partner_oauth_enabled', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                require_partner_oauth_enabled()
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail["error"] == "feature_disabled"
            assert exc_info.value.detail["feature_flag"] == "FEATURE_PARTNER_OAUTH"


class TestUserOrganizationMapping:
    """Test user to organization mapping"""
    
    def test_get_user_organization_id_with_default_org(self):
        """Test getting organization ID when user has default org"""
        user_mock = MagicMock()
        user_mock.default_organization_id = "org_123"
        user_mock.id = 456
        
        org_id = get_user_organization_id(user_mock)
        assert org_id == "org_123"
    
    def test_get_user_organization_id_fallback_to_user_id(self):
        """Test fallback to user ID when no default org"""
        user_mock = MagicMock()
        user_mock.default_organization_id = None
        user_mock.id = 456
        
        org_id = get_user_organization_id(user_mock)
        assert org_id == "456"
    
    def test_get_user_organization_id_no_default_org_attribute(self):
        """Test fallback when default_organization_id attribute missing"""
        user_mock = MagicMock()
        del user_mock.default_organization_id  # Remove attribute
        user_mock.id = 456
        
        org_id = get_user_organization_id(user_mock)
        assert org_id == "456"


class TestPlatformConfiguration:
    """Test platform configuration constants"""
    
    def test_meta_platform_config(self):
        """Test Meta platform configuration"""
        config = PLATFORM_CONFIGS["meta"]
        
        assert config["name"] == "Meta (Facebook & Instagram)"
        assert config["auth_base"] == "https://www.facebook.com/{version}/dialog/oauth"
        assert config["requires_pkce"] is False
        assert config["next_step"] == "asset_selection"
        
        # Check required scopes
        expected_scopes = [
            "pages_show_list",
            "pages_manage_posts", 
            "pages_read_engagement",
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_insights"
        ]
        for scope in expected_scopes:
            assert scope in config["scopes"]
    
    def test_x_platform_config(self):
        """Test X (Twitter) platform configuration"""
        config = PLATFORM_CONFIGS["x"]
        
        assert config["name"] == "X (Twitter)"
        assert config["auth_base"] == "https://twitter.com/i/oauth2/authorize"
        assert config["requires_pkce"] is True
        assert config["next_step"] == "connection_confirm"
        
        # Check required scopes
        expected_scopes = [
            "tweet.read",
            "tweet.write",
            "users.read", 
            "offline.access"
        ]
        for scope in expected_scopes:
            assert scope in config["scopes"]


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_client_id_meta(self):
        """Test getting Meta client ID"""
        settings_mock = MagicMock()
        settings_mock.meta_app_id = "meta_app_123"
        
        client_id = _get_client_id("meta", settings_mock)
        assert client_id == "meta_app_123"
    
    def test_get_client_id_x(self):
        """Test getting X client ID"""
        settings_mock = MagicMock()
        settings_mock.x_client_id = "x_client_123"
        
        client_id = _get_client_id("x", settings_mock)
        assert client_id == "x_client_123"
    
    def test_get_client_id_meta_missing(self):
        """Test Meta client ID missing raises exception"""
        settings_mock = MagicMock()
        settings_mock.meta_app_id = None
        
        with pytest.raises(HTTPException) as exc_info:
            _get_client_id("meta", settings_mock)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["error"] == "missing_config"
        assert exc_info.value.detail["message"] == "META_APP_ID not configured"
    
    def test_get_client_id_x_missing(self):
        """Test X client ID missing raises exception"""
        settings_mock = MagicMock()
        settings_mock.x_client_id = None
        
        with pytest.raises(HTTPException) as exc_info:
            _get_client_id("x", settings_mock)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["error"] == "missing_config"
        assert exc_info.value.detail["message"] == "X_CLIENT_ID not configured"
    
    def test_get_client_id_unsupported_platform(self):
        """Test unsupported platform raises ValueError"""
        settings_mock = MagicMock()
        
        with pytest.raises(ValueError, match="Unsupported platform: invalid"):
            _get_client_id("invalid", settings_mock)
    
    def test_get_redirect_uri_default(self):
        """Test redirect URI generation with default backend URL"""
        settings_mock = MagicMock()
        settings_mock.backend_url = None  # Test default fallback
        
        with patch('backend.api.partner_oauth.getattr', side_effect=lambda obj, name, default: default if name == 'backend_url' else getattr(obj, name)):
            uri = _get_redirect_uri("meta", settings_mock)
            assert uri == "http://localhost:8000/api/oauth/meta/callback"
    
    def test_get_redirect_uri_custom(self):
        """Test redirect URI generation with custom backend URL"""
        settings_mock = MagicMock()
        settings_mock.backend_url = "https://api.example.com"
        
        uri = _get_redirect_uri("x", settings_mock)
        assert uri == "https://api.example.com/api/oauth/x/callback"


class TestTokenExchange:
    """Test token exchange functionality"""
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_meta_success(self):
        """Test successful Meta token exchange"""
        oauth_manager = MagicMock()
        settings_mock = MagicMock()
        settings_mock.meta_graph_version = "v18.0"
        settings_mock.meta_app_secret = "meta_secret"
        
        # Mock httpx response
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "access_token": "meta_access_token",
            "token_type": "bearer",
            "expires_in": 5184000
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = response_mock
            mock_client_class.return_value = mock_client
            
            with patch('backend.api.partner_oauth._get_client_id', return_value="meta_app_id"):
                result = await _exchange_code_for_tokens(
                    oauth_manager=oauth_manager,
                    platform="meta",
                    code="auth_code_123",
                    redirect_uri="http://localhost:8000/api/oauth/meta/callback",
                    code_verifier=None,
                    settings=settings_mock
                )
        
        assert result["access_token"] == "meta_access_token"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 5184000
        assert result["platform"] == "meta"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_x_success(self):
        """Test successful X token exchange with PKCE"""
        oauth_manager = MagicMock()
        settings_mock = MagicMock()
        settings_mock.x_client_secret = "x_secret"
        
        # Mock httpx response
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "access_token": "x_access_token",
            "token_type": "bearer",
            "expires_in": 7200,
            "refresh_token": "x_refresh_token",
            "scope": "tweet.read tweet.write users.read offline.access"
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = response_mock
            mock_client_class.return_value = mock_client
            
            with patch('backend.api.partner_oauth._get_client_id', return_value="x_client_id"):
                result = await _exchange_code_for_tokens(
                    oauth_manager=oauth_manager,
                    platform="x",
                    code="auth_code_123",
                    redirect_uri="http://localhost:8000/api/oauth/x/callback",
                    code_verifier="test_verifier",
                    settings=settings_mock
                )
        
        assert result["access_token"] == "x_access_token"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 7200
        assert result["refresh_token"] == "x_refresh_token"
        assert result["scope"] == "tweet.read tweet.write users.read offline.access"
        assert result["platform"] == "x"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_meta_failure(self):
        """Test Meta token exchange failure"""
        oauth_manager = MagicMock()
        settings_mock = MagicMock()
        settings_mock.meta_graph_version = "v18.0"
        settings_mock.meta_app_secret = "meta_secret"
        
        # Mock failed httpx response
        response_mock = MagicMock()
        response_mock.status_code = 400
        response_mock.text = "Invalid authorization code"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = response_mock
            mock_client_class.return_value = mock_client
            
            with patch('backend.api.partner_oauth._get_client_id', return_value="meta_app_id"):
                with pytest.raises(Exception, match="Meta token exchange failed"):
                    await _exchange_code_for_tokens(
                        oauth_manager=oauth_manager,
                        platform="meta",
                        code="invalid_code",
                        redirect_uri="http://localhost:8000/api/oauth/meta/callback",
                        code_verifier=None,
                        settings=settings_mock
                    )
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_x_failure(self):
        """Test X token exchange failure"""
        oauth_manager = MagicMock()
        settings_mock = MagicMock()
        settings_mock.x_client_secret = "x_secret"
        
        # Mock failed httpx response
        response_mock = MagicMock()
        response_mock.status_code = 401
        response_mock.text = "Invalid client credentials"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = response_mock
            mock_client_class.return_value = mock_client
            
            with patch('backend.api.partner_oauth._get_client_id', return_value="x_client_id"):
                with pytest.raises(Exception, match="X token exchange failed"):
                    await _exchange_code_for_tokens(
                        oauth_manager=oauth_manager,
                        platform="x",
                        code="invalid_code",
                        redirect_uri="http://localhost:8000/api/oauth/x/callback",
                        code_verifier="test_verifier",
                        settings=settings_mock
                    )
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_unsupported_platform(self):
        """Test unsupported platform raises ValueError"""
        oauth_manager = MagicMock()
        settings_mock = MagicMock()
        
        with pytest.raises(ValueError, match="Unsupported platform: invalid"):
            await _exchange_code_for_tokens(
                oauth_manager=oauth_manager,
                platform="invalid",
                code="code",
                redirect_uri="uri",
                code_verifier=None,
                settings=settings_mock
            )


class TestRouterResponses:
    """Test router response models"""
    
    def test_oauth_start_response_model(self):
        """Test OAuthStartResponse model validation"""
        from backend.api.partner_oauth import OAuthStartResponse
        
        response = OAuthStartResponse(
            auth_url="https://example.com/oauth/authorize",
            state="test_state_123",
            platform="meta",
            expires_in=600
        )
        
        assert response.auth_url == "https://example.com/oauth/authorize"
        assert response.state == "test_state_123"
        assert response.platform == "meta"
        assert response.expires_in == 600
    
    def test_oauth_callback_response_model(self):
        """Test OAuthCallbackResponse model validation"""
        from backend.api.partner_oauth import OAuthCallbackResponse
        
        response = OAuthCallbackResponse(
            status="success",
            platform="x",
            state="test_state_123",
            next_step="connection_confirm",
            expires_in=600
        )
        
        assert response.status == "success"
        assert response.platform == "x"
        assert response.state == "test_state_123"
        assert response.next_step == "connection_confirm"
        assert response.expires_in == 600
    
    def test_disabled_feature_response_model(self):
        """Test DisabledFeatureResponse model validation"""
        from backend.api.partner_oauth import DisabledFeatureResponse
        
        response = DisabledFeatureResponse()
        
        assert response.error == "feature_disabled"
        assert response.message == "Partner OAuth feature is not enabled"
        assert response.feature_flag == "FEATURE_PARTNER_OAUTH"


class TestRouterDependencies:
    """Test router dependency behavior"""
    
    def test_router_has_correct_prefix(self):
        """Test that router has correct prefix"""
        assert router.prefix == "/api/oauth"
    
    def test_router_has_correct_tags(self):
        """Test that router has correct tags"""
        assert "partner-oauth" in router.tags
    
    def test_router_has_feature_flag_dependency(self):
        """Test that router includes feature flag dependency"""
        # Check that the dependency is included in the router
        assert len(router.dependencies) > 0
        
        # The dependency should be the require_partner_oauth_enabled function
        # This is a bit tricky to test directly, but we can verify behavior
        with patch('backend.api.partner_oauth.is_partner_oauth_enabled', return_value=False):
            with pytest.raises(HTTPException):
                require_partner_oauth_enabled()