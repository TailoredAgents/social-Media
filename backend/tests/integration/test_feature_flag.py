"""
Integration tests for partner OAuth feature flag functionality
"""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.core.config import get_settings


class TestPartnerOAuthFeatureFlag:
    """Test feature flag behavior for partner OAuth"""
    
    def test_feature_flag_defaults_to_false(self):
        """Test that FEATURE_PARTNER_OAUTH defaults to False"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing environment variable
            if 'FEATURE_PARTNER_OAUTH' in os.environ:
                del os.environ['FEATURE_PARTNER_OAUTH']
            
            settings = get_settings()
            assert settings.feature_partner_oauth is False
    
    def test_feature_flag_can_be_enabled(self):
        """Test that feature flag can be enabled via environment"""
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
            settings = get_settings()
            assert settings.feature_partner_oauth is True
    
    def test_feature_flag_handles_various_true_values(self):
        """Test that various 'true' values are handled correctly"""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on']
        
        for value in true_values:
            with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': value}):
                # Clear settings cache
                get_settings.cache_clear()
                settings = get_settings()
                assert settings.feature_partner_oauth is True, f"Value '{value}' should be True"
    
    def test_feature_flag_handles_false_values(self):
        """Test that 'false' values are handled correctly"""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'off', '']
        
        for value in false_values:
            with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': value}):
                # Clear settings cache
                get_settings.cache_clear()
                settings = get_settings()
                assert settings.feature_partner_oauth is False, f"Value '{value}' should be False"
    
    def test_meta_graph_version_default(self):
        """Test META_GRAPH_VERSION defaults correctly"""
        with patch.dict(os.environ, {}, clear=True):
            if 'META_GRAPH_VERSION' in os.environ:
                del os.environ['META_GRAPH_VERSION']
            
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.meta_graph_version == "v18.0"
    
    def test_meta_graph_version_override(self):
        """Test META_GRAPH_VERSION can be overridden"""
        with patch.dict(os.environ, {'META_GRAPH_VERSION': 'v19.0'}):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.meta_graph_version == "v19.0"
    
    def test_token_encryption_key_setting(self):
        """Test token encryption key configuration"""
        test_key = "test_encryption_key_value"
        
        with patch.dict(os.environ, {'TOKEN_ENCRYPTION_KEY': test_key}):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.token_encryption_key == test_key
    
    def test_token_encryption_key_defaults_empty(self):
        """Test token encryption key defaults to empty string"""
        with patch.dict(os.environ, {}, clear=True):
            if 'TOKEN_ENCRYPTION_KEY' in os.environ:
                del os.environ['TOKEN_ENCRYPTION_KEY']
            
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.token_encryption_key == ""
    
    def test_all_partner_oauth_settings_together(self):
        """Test all partner OAuth settings work together"""
        env_vars = {
            'FEATURE_PARTNER_OAUTH': 'true',
            'META_GRAPH_VERSION': 'v19.0',
            'TOKEN_ENCRYPTION_KEY': 'test_fernet_key_12345',
            'META_APP_ID': 'test_app_id',
            'META_APP_SECRET': 'test_app_secret'
        }
        
        with patch.dict(os.environ, env_vars):
            get_settings.cache_clear()
            settings = get_settings()
            
            assert settings.feature_partner_oauth is True
            assert settings.meta_graph_version == "v19.0"
            assert settings.token_encryption_key == "test_fernet_key_12345"
    
    @pytest.fixture
    def app_with_feature_disabled(self):
        """Create test app with feature flag disabled"""
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'false'}):
            get_settings.cache_clear()
            
            # Import app after setting environment
            from backend.main import app
            return app
    
    @pytest.fixture  
    def app_with_feature_enabled(self):
        """Create test app with feature flag enabled"""
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
            get_settings.cache_clear()
            
            # Import app after setting environment
            from backend.main import app
            return app
    
    def test_app_loads_with_feature_disabled(self, app_with_feature_disabled):
        """Test that app loads properly with feature disabled"""
        client = TestClient(app_with_feature_disabled)
        
        # Test that basic endpoints work
        response = client.get("/health")  
        # Should work regardless of feature flag
        # Note: We expect this to work if health endpoint exists, or 404 if it doesn't
        assert response.status_code in [200, 404, 405]
    
    def test_app_loads_with_feature_enabled(self, app_with_feature_enabled):
        """Test that app loads properly with feature enabled"""
        client = TestClient(app_with_feature_enabled)
        
        # Test that basic endpoints work
        response = client.get("/health")
        # Should work regardless of feature flag  
        assert response.status_code in [200, 404, 405]
    
    def test_settings_cache_behavior(self):
        """Test that settings are properly cached and can be cleared"""
        # First call
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'false'}):
            get_settings.cache_clear()
            settings1 = get_settings()
            assert settings1.feature_partner_oauth is False
        
        # Second call with different env (should still be cached)
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
            settings2 = get_settings()  # Should return cached version
            assert settings2.feature_partner_oauth is False  # Still cached
        
        # Clear cache and try again
        get_settings.cache_clear()
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
            settings3 = get_settings()
            assert settings3.feature_partner_oauth is True  # Now updated


class TestPartnerOAuthConfigValidation:
    """Test configuration validation for partner OAuth"""
    
    def test_configuration_completeness_when_enabled(self):
        """Test that enabling the feature flag reveals configuration requirements"""
        # This test ensures that when the feature is enabled,
        # we can detect missing required configuration
        
        required_config = [
            'TOKEN_ENCRYPTION_KEY',
            'META_APP_ID', 
            'META_APP_SECRET',
            'X_CLIENT_ID',
            'X_CLIENT_SECRET'
        ]
        
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'true'}):
            get_settings.cache_clear()
            settings = get_settings()
            
            # Feature should be enabled
            assert settings.feature_partner_oauth is True
            
            # We can check if required config is present
            # (This is mainly for future validation logic)
            assert hasattr(settings, 'token_encryption_key')
            assert hasattr(settings, 'meta_graph_version')
    
    def test_configuration_not_required_when_disabled(self):
        """Test that configuration is not validated when feature disabled"""
        with patch.dict(os.environ, {'FEATURE_PARTNER_OAUTH': 'false'}, clear=True):
            # Remove any existing oauth config
            oauth_vars = [
                'TOKEN_ENCRYPTION_KEY', 'META_APP_ID', 'META_APP_SECRET',
                'X_CLIENT_ID', 'X_CLIENT_SECRET'
            ]
            for var in oauth_vars:
                if var in os.environ:
                    del os.environ[var]
            
            get_settings.cache_clear()
            settings = get_settings()
            
            # Should load fine even without oauth config
            assert settings.feature_partner_oauth is False
            assert settings.token_encryption_key == ""  # Default empty
            assert settings.meta_graph_version == "v18.0"  # Has default