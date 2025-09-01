"""
Authentication configuration validator
"""
from typing import Dict, List, Any
from backend.core.config import get_settings

class AuthConfigValidator:
    """Validate authentication configuration"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def validate_auth0_config(self) -> Dict[str, Any]:
        """Validate Auth0 configuration"""
        config_status = {
            "auth0_domain": bool(self.settings.auth0_domain),
            "auth0_client_id": bool(self.settings.auth0_client_id),
            "auth0_client_secret": bool(self.settings.auth0_client_secret),
            "auth0_audience": bool(self.settings.auth0_audience),
        }
        
        config_status["auth0_enabled"] = all(config_status.values())
        
        return config_status
    
    def validate_jwt_config(self) -> Dict[str, Any]:
        """Validate JWT configuration"""
        config_status = {
            "secret_key": bool(self.settings.secret_key and self.settings.secret_key != "your-secret-key-change-this"),
            "algorithm": self.settings.algorithm == "HS256",
            "token_expire_minutes": self.settings.access_token_expire_minutes > 0,
        }
        
        config_status["jwt_enabled"] = all(config_status.values())
        
        return config_status
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get overall authentication status"""
        auth0_status = self.validate_auth0_config()
        jwt_status = self.validate_jwt_config()
        
        return {
            "auth0": auth0_status,
            "jwt": jwt_status,
            "available_methods": self._get_available_methods(auth0_status, jwt_status),
            "recommendations": self._get_recommendations(auth0_status, jwt_status)
        }
    
    def _get_available_methods(self, auth0_status: Dict, jwt_status: Dict) -> List[str]:
        """Get list of available authentication methods"""
        methods = []
        
        if jwt_status["jwt_enabled"]:
            methods.append("local")
        
        if auth0_status["auth0_enabled"]:
            methods.append("auth0")
        
        return methods
    
    def _get_recommendations(self, auth0_status: Dict, jwt_status: Dict) -> List[str]:
        """Get configuration recommendations"""
        recommendations = []
        
        if not jwt_status["secret_key"]:
            recommendations.append("Set a secure SECRET_KEY in environment variables")
        
        if not auth0_status["auth0_enabled"]:
            recommendations.append("Configure Auth0 settings for enterprise authentication")
        
        if not any([auth0_status["auth0_enabled"], jwt_status["jwt_enabled"]]):
            recommendations.append("Critical: No authentication method is properly configured")
        
        return recommendations

# Global instance
auth_config_validator = AuthConfigValidator()