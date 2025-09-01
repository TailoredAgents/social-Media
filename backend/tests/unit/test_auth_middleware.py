"""
Unit tests for Authentication middleware

Tests authentication and authorization middleware including:
- JWT token validation
- Auth0 integration
- User authentication and authorization
- Protected route access control
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock, MagicMock
from fastapi import status
import jwt

from backend.auth.middleware import jwt_middleware
from backend.auth.dependencies import get_current_user, get_optional_user
from backend.db.models import User


class TestJWTMiddleware:
    """Test JWT authentication middleware"""
    
    def test_valid_jwt_token(self, client, test_user, db_session):
        """Test request with valid JWT token"""
        # Create a valid JWT token
        payload = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "aud": "test_audience",
            "iss": "test.auth0.com"
        }
        
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            with patch('backend.auth.middleware.verify_jwt_token', return_value=payload):
                response = client.get("/api/content/list", headers=headers)
        
        # Should not be blocked by middleware
        assert response.status_code \!= status.HTTP_401_UNAUTHORIZED
    
    def test_expired_jwt_token(self, client, test_user):
        """Test request with expired JWT token"""
        # Create an expired JWT token
        payload = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "aud": "test_audience",
            "iss": "test.auth0.com"
        }
        
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/content/list", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_jwt_token(self, client):
        """Test request with invalid JWT token"""
        headers = {"Authorization": "Bearer invalid_token_format"}
        
        response = client.get("/api/content/list", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_authorization_header(self, client):
        """Test request without Authorization header"""
        response = client.get("/api/content/list")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_malformed_authorization_header(self, client):
        """Test request with malformed Authorization header"""
        test_cases = [
            {"Authorization": "InvalidFormat token"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": ""},  # Empty header
            {"Authorization": "Basic username:password"}  # Wrong auth type
        ]
        
        for headers in test_cases:
            response = client.get("/api/content/list", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_public_endpoints_no_auth(self, client):
        """Test that public endpoints don't require authentication"""
        public_endpoints = [
            "/",
            "/api/health",
            "/api/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # Should not return 401 (may return other status codes)
            assert response.status_code \!= status.HTTP_401_UNAUTHORIZED
    
    def test_auth0_jwks_validation(self, client, test_user):
        """Test Auth0 JWKS token validation"""
        # Mock Auth0 JWKS response
        mock_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test_key_id",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "mock_n_value",
                    "e": "AQAB"
                }
            ]
        }
        
        # Mock Auth0 JWT payload
        auth0_payload = {
            "sub": "auth0|test_user_123",
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "aud": "test_audience",
            "iss": "https://test.auth0.com/"
        }
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_jwks
            mock_get.return_value.status_code = 200
            
            with patch('jwt.decode', return_value=auth0_payload):
                with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                    headers = {"Authorization": "Bearer mock_auth0_token"}
                    response = client.get("/api/content/list", headers=headers)
        
        assert response.status_code \!= status.HTTP_401_UNAUTHORIZED
    
    def test_auth0_jwks_fetch_failure(self, client):
        """Test handling of Auth0 JWKS fetch failures"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("JWKS fetch failed")
            
            headers = {"Authorization": "Bearer auth0_token"}
            response = client.get("/api/content/list", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_creation_from_jwt(self, client, db_session):
        """Test automatic user creation from JWT payload"""
        new_user_payload = {
            "sub": "auth0|new_user_456",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/avatar.jpg",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "aud": "test_audience",
            "iss": "https://test.auth0.com/"
        }
        
        with patch('backend.auth.middleware.verify_jwt_token', return_value=new_user_payload):
            with patch('backend.db.database.get_db', return_value=db_session):
                headers = {"Authorization": "Bearer new_user_token"}
                response = client.get("/api/content/list", headers=headers)
        
        # User should be created automatically
        user = db_session.query(User).filter(User.user_id == "auth0|new_user_456").first()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
    
    def test_middleware_performance(self, client, test_user, performance_timer):
        """Test middleware performance under load"""
        payload = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "aud": "test_audience",
            "iss": "test.auth0.com"
        }
        
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            with patch('backend.auth.middleware.verify_jwt_token', return_value=payload):
                performance_timer.start()
                
                # Make multiple requests to test performance
                for _ in range(10):
                    response = client.get("/api/health", headers=headers)
                    assert response.status_code == status.HTTP_200_OK
                
                elapsed = performance_timer.stop()
        
        # Middleware should be fast (< 100ms for 10 requests)
        assert elapsed < 0.1
    
    def test_cors_headers_in_middleware(self, client):
        """Test that CORS headers are properly set by middleware"""
        response = client.options("/api/content/list")
        
        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_security_headers_middleware(self, client):
        """Test security headers added by middleware"""
        response = client.get("/api/health")
        
        # Check for security headers
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        for header in expected_headers:
            assert header in response.headers


class TestAuthDependencies:
    """Test authentication dependency functions"""
    
    def test_get_current_user_success(self, test_user, db_session):
        """Test successful user retrieval from token"""
        mock_token = {
            "sub": test_user.user_id,
            "email": test_user.email
        }
        
        with patch('backend.auth.dependencies.get_token_payload', return_value=mock_token):
            with patch('backend.db.database.get_db', return_value=db_session):
                # Add user to session
                db_session.add(test_user)
                db_session.commit()
                
                from backend.auth.dependencies import get_current_user
                
                # Mock the database query
                with patch.object(db_session, 'query') as mock_query:
                    mock_query.return_value.filter.return_value.first.return_value = test_user
                    
                    result = get_current_user(token=mock_token, db=db_session)
                    assert result.user_id == test_user.user_id
                    assert result.email == test_user.email
    
    def test_get_current_user_not_found(self, db_session):
        """Test user not found in database"""
        mock_token = {
            "sub": "nonexistent_user",
            "email": "nonexistent@example.com"
        }
        
        with patch('backend.auth.dependencies.get_token_payload', return_value=mock_token):
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = None
                
                from backend.auth.dependencies import get_current_user
                
                with pytest.raises(Exception):  # Should raise authentication error
                    get_current_user(token=mock_token, db=db_session)
    
    def test_get_optional_user_with_token(self, test_user, db_session):
        """Test optional user dependency with valid token"""
        mock_token = {
            "sub": test_user.user_id,
            "email": test_user.email
        }
        
        with patch('backend.auth.dependencies.get_token_payload', return_value=mock_token):
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = test_user
                
                from backend.auth.dependencies import get_optional_user
                
                result = get_optional_user(token=mock_token, db=db_session)
                assert result is not None
                assert result.user_id == test_user.user_id
    
    def test_get_optional_user_without_token(self, db_session):
        """Test optional user dependency without token"""
        from backend.auth.dependencies import get_optional_user
        
        result = get_optional_user(token=None, db=db_session)
        assert result is None
    
    def test_role_based_access_control(self, test_user, db_session):
        """Test role-based access control"""
        # Set user role
        test_user.profile_data = {
            "role": "admin",
            "permissions": ["read", "write", "delete"]
        }
        
        mock_token = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "role": "admin"
        }
        
        with patch('backend.auth.dependencies.get_token_payload', return_value=mock_token):
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = test_user
                
                from backend.auth.dependencies import require_role
                
                # Should not raise exception for admin role
                require_role("admin")(user=test_user)
                
                # Should raise exception for unauthorized role
                with pytest.raises(Exception):
                    require_role("super_admin")(user=test_user)


class TestTokenValidation:
    """Test JWT token validation logic"""
    
    def test_token_signature_validation(self):
        """Test JWT signature validation"""
        from backend.auth.middleware import verify_jwt_token
        
        # Valid token
        payload = {
            "sub": "test_user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        valid_token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        with patch('backend.core.config.settings.SECRET_KEY', "test_secret"):
            result = verify_jwt_token(valid_token)
            assert result["sub"] == "test_user"
        
        # Invalid signature
        invalid_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        with patch('backend.core.config.settings.SECRET_KEY', "test_secret"):
            with pytest.raises(jwt.InvalidTokenError):
                verify_jwt_token(invalid_token)
    
    def test_token_expiration_validation(self):
        """Test JWT expiration validation"""
        from backend.auth.middleware import verify_jwt_token
        
        # Expired token
        expired_payload = {
            "sub": "test_user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        
        with patch('backend.core.config.settings.SECRET_KEY', "test_secret"):
            with pytest.raises(jwt.ExpiredSignatureError):
                verify_jwt_token(expired_token)
    
    def test_token_audience_validation(self):
        """Test JWT audience validation"""
        from backend.auth.middleware import verify_jwt_token
        
        # Token with wrong audience
        payload = {
            "sub": "test_user",
            "aud": "wrong_audience",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        with patch('backend.core.config.settings.SECRET_KEY', "test_secret"):
            with patch('backend.core.config.settings.AUTH0_AUDIENCE', "correct_audience"):
                with pytest.raises(jwt.InvalidAudienceError):
                    verify_jwt_token(token)
    
    def test_token_issuer_validation(self):
        """Test JWT issuer validation"""
        from backend.auth.middleware import verify_jwt_token
        
        # Token with wrong issuer
        payload = {
            "sub": "test_user",
            "iss": "https://wrong.auth0.com/",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        with patch('backend.core.config.settings.SECRET_KEY', "test_secret"):
            with patch('backend.core.config.settings.AUTH0_DOMAIN', "correct.auth0.com"):
                with pytest.raises(jwt.InvalidIssuerError):
                    verify_jwt_token(token)


class TestAuthenticationMetrics:
    """Test authentication metrics and monitoring"""
    
    def test_authentication_success_metrics(self, client, test_user):
        """Test tracking of successful authentications"""
        payload = {
            "sub": test_user.user_id,
            "email": test_user.email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('backend.auth.middleware.track_auth_metric') as mock_metric:
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.get("/api/content/list", headers=headers)
        
        mock_metric.assert_called_with("auth_success", user_id=test_user.user_id)
    
    def test_authentication_failure_metrics(self, client):
        """Test tracking of failed authentications"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        with patch('backend.auth.middleware.track_auth_metric') as mock_metric:
            response = client.get("/api/content/list", headers=headers)
        
        mock_metric.assert_called_with("auth_failure", reason="invalid_token")
    
    def test_auth_middleware_statistics(self, client):
        """Test authentication middleware statistics endpoint"""
        response = client.get("/api/auth/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "auth_system" in data
        assert "middleware_stats" in data
        assert "jwks_status" in data
EOF < /dev/null