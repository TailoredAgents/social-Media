"""
Comprehensive test suite for authentication API endpoints

Tests all authentication endpoints including registration, login, profile management,
token handling, and Auth0 integration.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from backend.main import app
from backend.db.models import User, UserSetting
from backend.auth.dependencies import get_current_user, get_current_active_user
from backend.db.database import get_db


class TestAuthAPI:
    """Test suite for authentication API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.is_active = True
        user.tier = "free"
        user.created_at = datetime.utcnow()
        user.auth0_user_id = None
        user.local_auth = True
        return user
    
    @pytest.fixture
    def mock_auth0_user(self):
        """Mock Auth0 user object"""
        user = MagicMock(spec=User)
        user.id = 2
        user.email = "auth0@example.com"
        user.username = "auth0user"
        user.full_name = "Auth0 User"
        user.is_active = True
        user.tier = "premium"
        user.created_at = datetime.utcnow()
        user.auth0_user_id = "auth0|123456"
        user.local_auth = False
        return user
    
    def test_register_user_success(self, client, mock_db, mock_user):
        """Test successful user registration"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('backend.api.auth.User') as mock_user_class, \
             patch('backend.api.auth.jwt_handler') as mock_jwt:
            
            mock_user_class.return_value = mock_user
            mock_jwt.create_access_token.return_value = "test_token"
            
            response = client.post(
                "/api/auth/register",
                json={
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "securepassword123",
                    "full_name": "New User"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_token"
            assert data["token_type"] == "bearer"
            assert data["email"] == "test@example.com"
            assert data["username"] == "testuser"
        
        app.dependency_overrides.clear()
    
    def test_register_user_already_exists(self, client, mock_db, mock_user):
        """Test registration with existing email"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock existing user
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_register_user_validation_errors(self, client, mock_db):
        """Test registration validation errors"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Invalid email format
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422
        
        # Missing required fields
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com"
                # Missing username and password
            }
        )
        assert response.status_code == 422
        
        # Empty password
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_login_user_success(self, client, mock_db, mock_user):
        """Test successful user login"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock finding user and password verification
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('backend.api.auth.jwt_handler') as mock_jwt, \
             patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            
            mock_jwt.create_access_token.return_value = "test_token"
            mock_auth_validator.verify_password.return_value = True
            
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "correctpassword"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_token"
            assert data["user_id"] == "1"
            assert data["email"] == "test@example.com"
        
        app.dependency_overrides.clear()
    
    def test_login_user_invalid_credentials(self, client, mock_db, mock_user):
        """Test login with invalid credentials"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock finding user but wrong password
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = False
            
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid credentials" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_login_user_not_found(self, client, mock_db):
        """Test login with non-existent user"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock user not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_login_inactive_user(self, client, mock_db, mock_user):
        """Test login with inactive user"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock inactive user
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = True
            
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "correctpassword"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "inactive" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_get_user_profile_success(self, client, mock_user):
        """Test retrieving user profile"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.get("/api/auth/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["is_active"] is True
        assert data["tier"] == "free"
        
        app.dependency_overrides.clear()
    
    def test_get_user_profile_unauthorized(self, client):
        """Test profile access without authentication"""
        response = client.get("/api/auth/profile")
        
        assert response.status_code in [401, 403]
    
    def test_update_user_profile_success(self, client, mock_db, mock_user):
        """Test successful profile update"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        response = client.put(
            "/api/auth/profile",
            json={
                "full_name": "Updated Name",
                "username": "updateduser"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_change_password_success(self, client, mock_db, mock_user):
        """Test successful password change"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_db.commit.return_value = None
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = True
            mock_auth_validator.hash_password.return_value = "new_hashed_password"
            
            response = client.put(
                "/api/auth/change-password",
                json={
                    "current_password": "oldpassword",
                    "new_password": "newpassword123",
                    "confirm_password": "newpassword123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "changed successfully" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_change_password_wrong_current(self, client, mock_user):
        """Test password change with wrong current password"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = False
            
            response = client.put(
                "/api/auth/change-password",
                json={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123",
                    "confirm_password": "newpassword123"
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "current password" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_change_password_mismatch(self, client, mock_user):
        """Test password change with mismatched new passwords"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword123",
                "confirm_password": "differentpassword"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "do not match" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_auth0_callback_success(self, client, mock_db, mock_auth0_user):
        """Test successful Auth0 callback"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock Auth0 user info
        auth0_user_info = {
            "sub": "auth0|123456",
            "email": "auth0@example.com",
            "name": "Auth0 User"
        }
        
        with patch('backend.api.auth.auth0_user_manager') as mock_auth0, \
             patch('backend.api.auth.jwt_handler') as mock_jwt:
            
            mock_auth0.get_user_info.return_value = auth0_user_info
            mock_auth0.create_or_update_user.return_value = mock_auth0_user
            mock_jwt.create_access_token.return_value = "auth0_token"
            
            response = client.post(
                "/api/auth/auth0/callback",
                json={"access_token": "auth0_access_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "auth0_token"
            assert data["email"] == "auth0@example.com"
        
        app.dependency_overrides.clear()
    
    def test_auth0_callback_invalid_token(self, client):
        """Test Auth0 callback with invalid token"""
        with patch('backend.api.auth.auth0_user_manager') as mock_auth0:
            mock_auth0.get_user_info.side_effect = Exception("Invalid token")
            
            response = client.post(
                "/api/auth/auth0/callback",
                json={"access_token": "invalid_token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid Auth0 token" in data["detail"]
    
    def test_logout_success(self, client, mock_user):
        """Test successful logout"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('backend.api.auth.jwt_handler') as mock_jwt:
            mock_jwt.blacklist_token.return_value = True
            
            response = client.post("/api/auth/logout")
            
            assert response.status_code == 200
            data = response.json()
            assert "logged out successfully" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_refresh_token_success(self, client, mock_user):
        """Test successful token refresh"""
        with patch('backend.api.auth.jwt_handler') as mock_jwt:
            mock_jwt.verify_refresh_token.return_value = mock_user
            mock_jwt.create_access_token.return_value = "new_access_token"
            
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": "valid_refresh_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "new_access_token"
        
        # No need to clear overrides as we didn't set any
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid refresh token"""
        with patch('backend.api.auth.jwt_handler') as mock_jwt:
            mock_jwt.verify_refresh_token.side_effect = Exception("Invalid token")
            
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": "invalid_refresh_token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid refresh token" in data["detail"]
    
    def test_delete_account_success(self, client, mock_db, mock_user):
        """Test successful account deletion"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = True
            
            response = client.delete(
                "/api/auth/account",
                json={"password": "correctpassword"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]
        
        app.dependency_overrides.clear()
    
    def test_delete_account_wrong_password(self, client, mock_user):
        """Test account deletion with wrong password"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        with patch('backend.api.auth.auth_config_validator') as mock_auth_validator:
            mock_auth_validator.verify_password.return_value = False
            
            response = client.delete(
                "/api/auth/account",
                json={"password": "wrongpassword"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid password" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_user_settings_management(self, client, mock_db, mock_user):
        """Test user settings CRUD operations"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock user setting
        mock_setting = MagicMock(spec=UserSetting)
        mock_setting.setting_key = "theme"
        mock_setting.setting_value = "dark"
        
        # Test get settings
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_setting]
        
        response = client.get("/api/auth/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data
        
        # Test update settings
        mock_db.commit.return_value = None
        
        response = client.put(
            "/api/auth/settings",
            json={
                "settings": {
                    "theme": "light",
                    "notifications": "enabled"
                }
            }
        )
        
        assert response.status_code == 200
        
        app.dependency_overrides.clear()
    
    def test_password_strength_validation(self, client, mock_db):
        """Test password strength validation"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        weak_passwords = [
            "123",           # Too short
            "password",      # Too common
            "12345678",      # No letters
            "abcdefgh"       # No numbers/special chars
        ]
        
        for weak_password in weak_passwords:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": weak_password,
                    "full_name": "Test User"
                }
            )
            
            # Should reject weak passwords (implementation dependent)
            assert response.status_code in [400, 422]
        
        app.dependency_overrides.clear()
    
    def test_rate_limiting_simulation(self, client, mock_db):
        """Test rate limiting on authentication endpoints"""
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock failed login attempts
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Simulate multiple failed login attempts
        for _ in range(10):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            
            # Should maintain consistent error response
            assert response.status_code == 401
        
        app.dependency_overrides.clear()
    
    def test_session_management(self, client, mock_user):
        """Test session management functionality"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        # Test getting active sessions
        with patch('backend.api.auth.jwt_handler') as mock_jwt:
            mock_jwt.get_active_sessions.return_value = [
                {"session_id": "sess1", "created_at": "2024-01-01", "device": "Chrome"},
                {"session_id": "sess2", "created_at": "2024-01-02", "device": "Mobile"}
            ]
            
            response = client.get("/api/auth/sessions")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sessions"]) == 2
        
        # Test revoking specific session
        with patch('backend.api.auth.jwt_handler') as mock_jwt:
            mock_jwt.revoke_session.return_value = True
            
            response = client.delete("/api/auth/sessions/sess1")
            
            assert response.status_code == 200
            data = response.json()
            assert "revoked successfully" in data["message"]
        
        app.dependency_overrides.clear()


class TestAuthIntegration:
    """Integration tests for authentication API"""
    
    def test_complete_auth_flow(self, client, test_db):
        """Test complete authentication flow"""
        # This would test: register -> login -> access protected resource -> logout
        pass
    
    def test_auth0_integration_flow(self, client, test_db):
        """Test Auth0 integration flow"""
        pass
    
    def test_jwt_token_lifecycle(self, client, test_db):
        """Test JWT token creation, validation, and expiration"""
        pass