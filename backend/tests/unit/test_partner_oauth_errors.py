"""
Unit tests for partner OAuth error handling
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from backend.api.partner_oauth import (
    get_meta_assets,
    connect_meta_account,
    connect_x_account,
    MetaConnectRequest,
    XConnectRequest
)


class TestPartnerOAuthErrorHandling:
    """Test error handling in partner OAuth endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = MagicMock()
        user.id = 123
        user.default_organization_id = "org_456"
        return user
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        db = MagicMock()
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None
        return db
    
    @pytest.mark.asyncio
    async def test_get_meta_assets_invalid_state(self, mock_user):
        """Test Meta assets endpoint with invalid state"""
        state = "invalid_state"
        
        # Mock state store returning None (expired/invalid state)
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = None
            mock_get_store.return_value = mock_store
            
            with pytest.raises(HTTPException) as exc_info:
                await get_meta_assets(state=state, current_user=mock_user)
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail["error"] == "invalid_state"
            assert "State not found or expired" in exc_info.value.detail["message"]
    
    @pytest.mark.asyncio
    async def test_get_meta_assets_api_failure(self, mock_user):
        """Test Meta assets endpoint with API failure"""
        state = "valid_state"
        
        # Mock valid state but API failure
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "user_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.list_pages_with_instagram = AsyncMock()
                mock_service.list_pages_with_instagram.side_effect = Exception("Graph API Error")
                mock_get_service.return_value = mock_service
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_meta_assets(state=state, current_user=mock_user)
                
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail["error"] == "assets_fetch_failed"
                assert "Failed to retrieve Facebook Pages" in exc_info.value.detail["message"]
    
    @pytest.mark.asyncio
    async def test_connect_meta_account_invalid_state(self, mock_user, mock_db_session):
        """Test Meta connect endpoint with invalid state"""
        request = MetaConnectRequest(state="invalid_state", page_id="page_123")
        
        # Mock state store returning None
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = None
            mock_get_store.return_value = mock_store
            
            with pytest.raises(HTTPException) as exc_info:
                await connect_meta_account(
                    request=request,
                    current_user=mock_user,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail["error"] == "invalid_state"
    
    @pytest.mark.asyncio
    async def test_connect_meta_account_not_page_admin(self, mock_user, mock_db_session):
        """Test Meta connect endpoint when user is not page admin"""
        request = MetaConnectRequest(state="valid_state", page_id="page_123")
        
        # Mock valid state but page admin failure
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "user_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.exchange_for_page_token = AsyncMock()
                mock_service.exchange_for_page_token.side_effect = ValueError(
                    "You don't have admin access to this Facebook Page"
                )
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with pytest.raises(HTTPException) as exc_info:
                        await connect_meta_account(
                            request=request,
                            current_user=mock_user,
                            db=mock_db_session
                        )
                
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail["error"] == "connection_failed"
                assert "admin access" in exc_info.value.detail["message"]
                assert exc_info.value.detail["page_id"] == "page_123"
                
                # Verify audit log was created
                mock_db_session.add.assert_called()
                mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_connect_meta_account_database_error(self, mock_user, mock_db_session):
        """Test Meta connect endpoint with database error"""
        request = MetaConnectRequest(state="valid_state", page_id="page_123")
        
        # Mock successful token exchange but database error
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "user_token_123"},
                "scopes": ["pages_manage_posts"]
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.exchange_for_page_token = AsyncMock()
                mock_service.exchange_for_page_token.return_value = {
                    "page_access_token": "page_token_123",
                    "page_name": "Test Page",
                    "page_id": "page_123"
                }
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with patch('backend.api.partner_oauth.encrypt_token', return_value="encrypted_token"):
                        # Make database commit fail
                        mock_db_session.commit.side_effect = Exception("Database connection error")
                        
                        with pytest.raises(HTTPException) as exc_info:
                            await connect_meta_account(
                                request=request,
                                current_user=mock_user,
                                db=mock_db_session
                            )
                        
                        assert exc_info.value.status_code == 500
                        assert exc_info.value.detail["error"] == "connection_failed"
                        assert "Failed to create connection" in exc_info.value.detail["message"]
    
    @pytest.mark.asyncio
    async def test_connect_x_account_invalid_state(self, mock_user, mock_db_session):
        """Test X connect endpoint with invalid state"""
        request = XConnectRequest(state="invalid_state")
        
        # Mock state store returning None
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = None
            mock_get_store.return_value = mock_store
            
            with pytest.raises(HTTPException) as exc_info:
                await connect_x_account(
                    request=request,
                    current_user=mock_user,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail["error"] == "invalid_state"
    
    @pytest.mark.asyncio
    async def test_connect_x_account_api_error(self, mock_user, mock_db_session):
        """Test X connect endpoint with API error"""
        request = XConnectRequest(state="valid_state")
        
        # Mock valid state but X API failure
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "bearer_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_x_connection_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.get_user_context = AsyncMock()
                mock_service.get_user_context.side_effect = ValueError("Invalid or expired X access token")
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with pytest.raises(HTTPException) as exc_info:
                        await connect_x_account(
                            request=request,
                            current_user=mock_user,
                            db=mock_db_session
                        )
                
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail["error"] == "connection_failed"
                assert "expired X access token" in exc_info.value.detail["message"]
    
    @pytest.mark.asyncio
    async def test_connect_x_account_database_error(self, mock_user, mock_db_session):
        """Test X connect endpoint with database error"""
        request = XConnectRequest(state="valid_state")
        
        # Mock successful API call but database error
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "bearer_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_x_connection_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.get_user_context = AsyncMock()
                mock_service.get_user_context.return_value = {
                    "user_id": "12345",
                    "username": "testuser",
                    "display_name": "Test User",
                    "metadata": {"verified": True}
                }
                mock_service._extract_scopes.return_value = ["tweet.read", "tweet.write"]
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with patch('backend.api.partner_oauth.encrypt_token', return_value="encrypted_token"):
                        # Make database commit fail
                        mock_db_session.commit.side_effect = Exception("Database error")
                        
                        with pytest.raises(HTTPException) as exc_info:
                            await connect_x_account(
                                request=request,
                                current_user=mock_user,
                                db=mock_db_session
                            )
                        
                        assert exc_info.value.status_code == 500
                        assert exc_info.value.detail["error"] == "connection_failed"
    
    @pytest.mark.asyncio
    async def test_expired_state_handling(self, mock_user):
        """Test handling of expired OAuth state"""
        state = "expired_state"
        
        # Test different scenarios where state might be invalid/expired
        scenarios = [
            None,  # State not found
            {},    # Empty cached data
            {"tokens": {}},  # Missing access token
        ]
        
        for scenario in scenarios:
            with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
                mock_store = MagicMock()
                mock_store.read_tokens.return_value = scenario
                mock_get_store.return_value = mock_store
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_meta_assets(state=state, current_user=mock_user)
                
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail["error"] == "invalid_state"
    
    @pytest.mark.asyncio
    async def test_missing_scope_error_handling(self, mock_user, mock_db_session):
        """Test handling when user lacks required scopes"""
        request = MetaConnectRequest(state="valid_state", page_id="page_123")
        
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "user_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.exchange_for_page_token = AsyncMock()
                mock_service.exchange_for_page_token.side_effect = ValueError(
                    "Insufficient permissions to access Facebook Pages"
                )
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with pytest.raises(HTTPException) as exc_info:
                        await connect_meta_account(
                            request=request,
                            current_user=mock_user,
                            db=mock_db_session
                        )
                
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail["error"] == "connection_failed"
                assert "Insufficient permissions" in exc_info.value.detail["message"]
    
    @pytest.mark.asyncio
    async def test_audit_log_creation_on_errors(self, mock_user, mock_db_session):
        """Test that audit logs are created even when operations fail"""
        request = MetaConnectRequest(state="valid_state", page_id="page_123")
        
        # Mock scenario that should create a failed audit log
        with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
            mock_store = MagicMock()
            mock_store.read_tokens.return_value = {
                "tokens": {"access_token": "user_token_123"}
            }
            mock_get_store.return_value = mock_store
            
            with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                mock_service = MagicMock()
                mock_service.exchange_for_page_token = AsyncMock()
                mock_service.exchange_for_page_token.side_effect = ValueError("Page not found")
                mock_get_service.return_value = mock_service
                
                with patch('backend.api.partner_oauth.get_user_organization_id', return_value="org_456"):
                    with pytest.raises(HTTPException):
                        await connect_meta_account(
                            request=request,
                            current_user=mock_user,
                            db=mock_db_session
                        )
                
                # Verify that audit log was attempted to be created
                # The mock_db_session.add should have been called for the audit log
                assert mock_db_session.add.called
                assert mock_db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_friendly_error_messages(self, mock_user):
        """Test that error messages are user-friendly and actionable"""
        state = "test_state"
        
        # Test various error scenarios and their messages
        error_scenarios = [
            {
                "exception": ValueError("You don't have admin access to this Facebook Page"),
                "expected_message": "You don't have admin access to this Facebook Page"
            },
            {
                "exception": ValueError("Facebook Page not found or not accessible"),
                "expected_message": "Facebook Page not found or not accessible"
            },
            {
                "exception": ValueError("Invalid or expired access token"),
                "expected_message": "Invalid or expired access token"
            },
        ]
        
        for scenario in error_scenarios:
            with patch('backend.api.partner_oauth.get_state_store') as mock_get_store:
                mock_store = MagicMock()
                mock_store.read_tokens.return_value = {
                    "tokens": {"access_token": "user_token_123"}
                }
                mock_get_store.return_value = mock_store
                
                with patch('backend.api.partner_oauth.get_meta_page_service') as mock_get_service:
                    mock_service = MagicMock()
                    mock_service.list_pages_with_instagram = AsyncMock()
                    mock_service.list_pages_with_instagram.side_effect = scenario["exception"]
                    mock_get_service.return_value = mock_service
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await get_meta_assets(state=state, current_user=mock_user)
                    
                    assert exc_info.value.status_code == 500
                    assert scenario["expected_message"] in str(exc_info.value.detail)