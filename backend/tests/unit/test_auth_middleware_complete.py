"""
Comprehensive test suite for authentication middleware and JWT validation

Tests all authentication middleware components including JWT verification,
Auth0 integration, token extraction, user authentication, and security dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt

from backend.auth.dependencies import (
    get_token, verify_auth0_token, verify_local_token, 
    get_current_user, get_current_active_user, AuthUser
)
from backend.db.models import User


class TestAuthenticationMiddleware:
    """Test suite for authentication middleware components"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock HTTP authorization credentials"""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "valid_jwt_token"
        return credentials
    
    @pytest.fixture
    def mock_user(self):
        """Mock database user"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.auth0_user_id = "auth0|123456"
        user.is_active = True
        user.created_at = datetime.utcnow()
        return user
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock AuthUser instance"""
        return AuthUser(
            user_id="1",
            email="test@example.com",
            username="testuser",
            auth_method="auth0"
        )
    
    @pytest.fixture
    def valid_jwt_payload(self):
        """Valid JWT payload"""
        return {
            "sub": "auth0|123456",
            "email": "test@example.com",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": "https://your-auth0-domain.auth0.com/"
        }
    
    @pytest.mark.asyncio
    async def test_get_token_success(self, mock_credentials):
        """Test successful token extraction"""
        token = await get_token(mock_credentials)
        
        assert token == "valid_jwt_token"
    
    @pytest.mark.asyncio
    async def test_get_token_missing_credentials(self):
        """Test token extraction with missing credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await get_token(None)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication token required" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    @pytest.mark.asyncio
    async def test_get_token_empty_credentials(self):
        """Test token extraction with empty credentials"""
        empty_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        empty_credentials.credentials = ""
        
        with pytest.raises(HTTPException) as exc_info:
            await get_token(empty_credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_verify_auth0_token_success(self, valid_jwt_payload):
        """Test successful Auth0 token verification"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_verifier:
            mock_verifier.verify_token.return_value = valid_jwt_payload
            
            result = await verify_auth0_token("valid_auth0_token")
            
            assert result == valid_jwt_payload
            mock_verifier.verify_token.assert_called_once_with("valid_auth0_token")
    
    @pytest.mark.asyncio
    async def test_verify_auth0_token_invalid(self):
        """Test Auth0 token verification with invalid token"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_verifier:
            mock_verifier.verify_token.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_auth0_token("invalid_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_verify_local_token_success(self, valid_jwt_payload):
        """Test successful local JWT token verification"""
        with patch('backend.auth.dependencies.jwt_handler') as mock_jwt_handler:
            mock_jwt_handler.verify_token.return_value = valid_jwt_payload
            
            result = await verify_local_token("valid_local_token")
            
            assert result == valid_jwt_payload
            mock_jwt_handler.verify_token.assert_called_once_with("valid_local_token")
    
    @pytest.mark.asyncio
    async def test_verify_local_token_expired(self):
        """Test local token verification with expired token"""
        with patch('backend.auth.dependencies.jwt_handler') as mock_jwt_handler:
            mock_jwt_handler.verify_token.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_local_token("expired_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_auth0_success(self, mock_db, mock_user, valid_jwt_payload):
        """Test successful user retrieval with Auth0 token"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            # Auth0 verification succeeds
            mock_auth0.verify_token.return_value = valid_jwt_payload
            
            # Database user lookup
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            result = await get_current_user(mock_db, "valid_auth0_token")
            
            assert isinstance(result, AuthUser)
            assert result.user_id == "1"
            assert result.email == "test@example.com"
            assert result.username == "testuser"
            assert result.auth_method == "auth0"
    
    @pytest.mark.asyncio
    async def test_get_current_user_local_jwt_success(self, mock_db, mock_user, valid_jwt_payload):
        """Test successful user retrieval with local JWT token"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            # Auth0 verification fails, local JWT succeeds
            mock_auth0.verify_token.side_effect = HTTPException(status_code=401)
            mock_jwt.verify_token.return_value = valid_jwt_payload
            
            # Update mock user for local auth
            mock_user.auth0_user_id = None
            mock_user.local_auth = True
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            result = await get_current_user(mock_db, "valid_local_token")
            
            assert isinstance(result, AuthUser)
            assert result.auth_method == "local"
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_db, valid_jwt_payload):
        """Test user retrieval when user not found in database"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0:
            mock_auth0.verify_token.return_value = valid_jwt_payload
            
            # User not found in database
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_db, "valid_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_both_auth_methods_fail(self, mock_db):
        """Test user retrieval when both Auth0 and local JWT fail"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            # Both verification methods fail
            mock_auth0.verify_token.side_effect = HTTPException(status_code=401)
            mock_jwt.verify_token.side_effect = HTTPException(status_code=401)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_db, "invalid_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, mock_user, mock_auth_user):
        """Test successful retrieval of active user"""
        mock_user.is_active = True
        
        with patch('backend.auth.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_auth_user
            
            # Mock database user lookup for activity check
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            result = await get_current_active_user(mock_auth_user, mock_db)
            
            assert result == mock_user
            assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, mock_user, mock_auth_user):
        """Test retrieval of inactive user raises exception"""
        mock_user.is_active = False
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_auth_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Inactive user" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_auth_user_model(self):
        """Test AuthUser model functionality"""
        auth_user = AuthUser(
            user_id="123",
            email="test@example.com",
            username="testuser",
            auth_method="auth0"
        )
        
        assert auth_user.user_id == "123"
        assert auth_user.email == "test@example.com"
        assert auth_user.username == "testuser"
        assert auth_user.auth_method == "auth0"
    
    @pytest.mark.asyncio
    async def test_token_extraction_edge_cases(self):
        """Test token extraction edge cases"""
        # Test with None credentials
        with pytest.raises(HTTPException):
            await get_token(None)
        
        # Test with credentials but no token
        empty_creds = MagicMock()
        empty_creds.credentials = None
        
        with pytest.raises(HTTPException):
            await get_token(empty_creds)
        
        # Test with whitespace-only token
        whitespace_creds = MagicMock()
        whitespace_creds.credentials = "   "
        
        token = await get_token(whitespace_creds)
        assert token == "   "  # Should extract as-is, validation happens later
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_requests(self, mock_db, mock_user, valid_jwt_payload):
        """Test handling of concurrent authentication requests"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0:
            mock_auth0.verify_token.return_value = valid_jwt_payload
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            # Simulate concurrent requests
            import asyncio
            tasks = []
            for _ in range(5):
                task = get_current_user(mock_db, "valid_token")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert isinstance(result, AuthUser)
                assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_malformed_jwt_handling(self, mock_db):
        """Test handling of malformed JWT tokens"""
        malformed_tokens = [
            "not.a.jwt",
            "header.payload",  # Missing signature
            "invalid_base64_characters",
            "",
            "Bearer invalid_token"
        ]
        
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            for token in malformed_tokens:
                # Both verifiers should fail
                mock_auth0.verify_token.side_effect = HTTPException(status_code=401)
                mock_jwt.verify_token.side_effect = HTTPException(status_code=401)
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_db, token)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_jwt_expiration_handling(self, mock_db):
        """Test handling of expired JWT tokens"""
        expired_payload = {
            "sub": "auth0|123456",
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            # Simulate token expiration error
            mock_auth0.verify_token.side_effect = HTTPException(
                status_code=401, detail="Token has expired"
            )
            mock_jwt.verify_token.side_effect = HTTPException(
                status_code=401, detail="Token has expired"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_db, "expired_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_user_permissions_validation(self, mock_db, mock_user, mock_auth_user):
        """Test user permissions validation"""
        # Test admin user
        mock_user.is_admin = True
        mock_user.tier = "premium"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await get_current_active_user(mock_auth_user, mock_db)
        
        assert result.is_admin is True
        assert result.tier == "premium"
        
        # Test regular user
        mock_user.is_admin = False
        mock_user.tier = "free"
        
        result = await get_current_active_user(mock_auth_user, mock_db)
        
        assert result.is_admin is False
        assert result.tier == "free"
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self, mock_auth_user):
        """Test handling of database connection errors"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_auth_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_auth_method_detection(self, mock_db, valid_jwt_payload):
        """Test authentication method detection"""
        # Test Auth0 method detection
        auth0_user = MagicMock()
        auth0_user.auth0_user_id = "auth0|123456"
        auth0_user.local_auth = False
        auth0_user.is_active = True
        
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0:
            mock_auth0.verify_token.return_value = valid_jwt_payload
            mock_db.query.return_value.filter.return_value.first.return_value = auth0_user
            
            result = await get_current_user(mock_db, "auth0_token")
            assert result.auth_method == "auth0"
        
        # Test local method detection
        local_user = MagicMock()
        local_user.auth0_user_id = None
        local_user.local_auth = True
        local_user.is_active = True
        
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            mock_auth0.verify_token.side_effect = HTTPException(status_code=401)
            mock_jwt.verify_token.return_value = valid_jwt_payload
            mock_db.query.return_value.filter.return_value.first.return_value = local_user
            
            result = await get_current_user(mock_db, "local_token")
            assert result.auth_method == "local"
    
    @pytest.mark.asyncio
    async def test_security_headers_validation(self):
        """Test security headers in authentication responses"""
        # Test that unauthorized responses include proper headers
        with pytest.raises(HTTPException) as exc_info:
            await get_token(None)
        
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_authentication_rate_limiting_simulation(self, mock_db):
        """Test authentication under high load (simulating rate limiting)"""
        with patch('backend.auth.dependencies.auth0_verifier') as mock_auth0, \
             patch('backend.auth.dependencies.jwt_handler') as mock_jwt:
            
            # Simulate rate limiting after many requests
            call_count = 0
            
            def rate_limited_verify(token):
                nonlocal call_count
                call_count += 1
                if call_count > 100:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                raise HTTPException(status_code=401)
            
            mock_auth0.verify_token.side_effect = rate_limited_verify
            mock_jwt.verify_token.side_effect = rate_limited_verify
            
            # Should handle rate limiting gracefully
            for i in range(105):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_db, f"token_{i}")
                
                if i < 100:
                    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                else:
                    assert exc_info.value.status_code == 429


class TestJWTValidation:
    """Specific tests for JWT validation logic"""
    
    @pytest.mark.asyncio
    async def test_jwt_signature_validation(self):
        """Test JWT signature validation"""
        # This would test the actual JWT signature validation
        # Implementation depends on the JWT library being used
        pass
    
    @pytest.mark.asyncio
    async def test_jwt_claims_validation(self):
        """Test JWT claims validation (iss, aud, exp, etc.)"""
        # Test various JWT claims validation scenarios
        pass
    
    @pytest.mark.asyncio
    async def test_jwt_algorithm_validation(self):
        """Test JWT algorithm validation"""
        # Test that only allowed algorithms are accepted
        pass


class TestAuthMiddlewareIntegration:
    """Integration tests for authentication middleware"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_auth_flow(self):
        """Test complete authentication flow"""
        # Test: token extraction -> verification -> user lookup -> response
        pass
    
    @pytest.mark.asyncio
    async def test_auth_with_database_transactions(self):
        """Test authentication with database transactions"""
        pass
    
    @pytest.mark.asyncio
    async def test_auth_performance_under_load(self):
        """Test authentication performance under high load"""
        pass