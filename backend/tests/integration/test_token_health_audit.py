"""
Integration tests for token health audit
Tests the complete token health audit flow with database integration
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.db.models import SocialConnection, SocialAudit, Organization, User
from backend.tasks.token_health_tasks import audit_all_tokens, refresh_connection, _find_connections_needing_refresh
from backend.tests.conftest import TestingSessionLocal


class TestTokenHealthAuditIntegration:
    """Integration tests for token health audit"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture
    def test_organization(self, db_session):
        """Create test organization"""
        org = Organization(name="Test Org", is_active=True)
        db_session.add(org)
        db_session.commit()
        return org
    
    @pytest.fixture
    def test_user(self, db_session, test_organization):
        """Create test user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
            organization_id=test_organization.id
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    @pytest.fixture
    def expiring_meta_connection(self, db_session, test_organization):
        """Create Meta connection that's expiring soon"""
        expiry_time = datetime.now(timezone.utc) + timedelta(hours=48)  # Within 72h threshold
        
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="page_123",
            platform_username="TestPage",
            access_tokens={
                "access_token": "encrypted_user_token",
                "page_token": "encrypted_page_token"
            },
            token_expires_at=expiry_time,
            is_active=True,
            connection_metadata={}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def expiring_x_connection(self, db_session, test_organization):
        """Create X connection that's expiring soon"""
        expiry_time = datetime.now(timezone.utc) + timedelta(hours=24)  # Within 72h threshold
        
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="x",
            platform_account_id="user_456",
            platform_username="TestUser",
            access_tokens={
                "access_token": "encrypted_access_token",
                "refresh_token": "encrypted_refresh_token"
            },
            token_expires_at=expiry_time,
            is_active=True,
            connection_metadata={}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def unknown_expiry_connection(self, db_session, test_organization):
        """Create connection with unknown expiry date"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="page_789",
            platform_username="UnknownPage",
            access_tokens={
                "access_token": "encrypted_token"
            },
            token_expires_at=None,  # Unknown expiry
            is_active=True,
            connection_metadata={}
        )
        db_session.add(connection)
        db_session.commit()
        return connection

    def test_find_connections_needing_refresh(self, db_session, expiring_meta_connection, expiring_x_connection, unknown_expiry_connection):
        """Test finding connections that need token refresh"""
        # Create a healthy connection that shouldn't be included
        healthy_connection = SocialConnection(
            organization_id=expiring_meta_connection.organization_id,
            platform="meta",
            platform_account_id="healthy_page",
            platform_username="HealthyPage",
            access_tokens={"access_token": "encrypted_token"},
            token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),  # Far in future
            is_active=True,
            connection_metadata={}
        )
        db_session.add(healthy_connection)
        db_session.commit()
        
        # Find connections needing refresh
        connections = _find_connections_needing_refresh(db_session)
        
        # Should find the expiring and unknown expiry connections
        connection_ids = [str(conn.id) for conn in connections]
        
        assert str(expiring_meta_connection.id) in connection_ids
        assert str(expiring_x_connection.id) in connection_ids
        assert str(unknown_expiry_connection.id) in connection_ids
        assert str(healthy_connection.id) not in connection_ids
        
        # Check platform distribution
        platforms = [conn.platform for conn in connections]
        assert "meta" in platforms
        assert "x" in platforms

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    def test_audit_all_tokens_feature_disabled(self, mock_feature_enabled):
        """Test audit when feature is disabled"""
        mock_feature_enabled.return_value = False
        
        result = audit_all_tokens()
        
        assert result["status"] == "skipped"
        assert result["reason"] == "feature_disabled"

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    @patch('backend.tasks.token_health_tasks.get_token_refresh_service')
    @patch('backend.tasks.token_health_tasks.get_db')
    def test_audit_all_tokens_success(
        self, 
        mock_get_db, 
        mock_get_refresh_service,
        mock_feature_enabled,
        db_session,
        expiring_meta_connection,
        expiring_x_connection
    ):
        """Test successful token audit with refreshes"""
        mock_feature_enabled.return_value = True
        mock_get_db.return_value = iter([db_session])
        
        # Mock refresh service
        mock_refresh_service = MagicMock()
        mock_get_refresh_service.return_value = mock_refresh_service
        
        # Mock successful refreshes
        new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
        mock_refresh_service.refresh_meta_connection = AsyncMock(
            return_value=(True, new_expiry, "Meta refresh successful")
        )
        mock_refresh_service.refresh_x_connection = AsyncMock(
            return_value=(True, new_expiry, "X refresh successful")
        )
        
        result = audit_all_tokens()
        
        assert result["connections_checked"] >= 2
        assert result["refresh_attempts"] >= 2
        assert result["refresh_successes"] >= 2
        assert result["refresh_failures"] == 0
        assert result["platforms"]["meta"] >= 1
        assert result["platforms"]["x"] >= 1
        assert len(result["errors"]) == 0
        
        # Verify refresh methods were called
        mock_refresh_service.refresh_meta_connection.assert_called()
        mock_refresh_service.refresh_x_connection.assert_called()

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    @patch('backend.tasks.token_health_tasks.get_token_refresh_service')
    @patch('backend.tasks.token_health_tasks.get_db')
    def test_audit_all_tokens_with_failures(
        self,
        mock_get_db,
        mock_get_refresh_service,
        mock_feature_enabled,
        db_session,
        expiring_meta_connection
    ):
        """Test token audit with some refresh failures"""
        mock_feature_enabled.return_value = True
        mock_get_db.return_value = iter([db_session])
        
        # Mock refresh service with failure
        mock_refresh_service = MagicMock()
        mock_get_refresh_service.return_value = mock_refresh_service
        
        mock_refresh_service.refresh_meta_connection = AsyncMock(
            return_value=(False, None, "Token validation failed")
        )
        
        result = audit_all_tokens()
        
        assert result["refresh_failures"] >= 1
        assert len(result["errors"]) >= 1
        
        # Check error details
        error = result["errors"][0]
        assert error["platform"] == "meta"
        assert "Token validation failed" in error["error"]

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    @patch('backend.tasks.token_health_tasks.get_token_refresh_service')
    @patch('backend.tasks.token_health_tasks.get_db')
    def test_refresh_connection_task_success(
        self,
        mock_get_db,
        mock_get_refresh_service,
        mock_feature_enabled,
        db_session,
        expiring_meta_connection
    ):
        """Test individual connection refresh task"""
        mock_feature_enabled.return_value = True
        mock_get_db.return_value = iter([db_session])
        
        # Mock refresh service
        mock_refresh_service = MagicMock()
        mock_get_refresh_service.return_value = mock_refresh_service
        
        new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
        mock_refresh_service.refresh_meta_connection = AsyncMock(
            return_value=(True, new_expiry, "Refresh successful")
        )
        
        result = refresh_connection(str(expiring_meta_connection.id))
        
        assert result["status"] == "success"
        assert result["connection_id"] == str(expiring_meta_connection.id)
        assert result["platform"] == "meta"
        assert "successful" in result["message"]
        assert result["new_expiry"] is not None
        
        mock_refresh_service.refresh_meta_connection.assert_called_once()

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    @patch('backend.tasks.token_health_tasks.get_db')
    def test_refresh_connection_not_found(self, mock_get_db, mock_feature_enabled, db_session):
        """Test refresh task with non-existent connection"""
        mock_feature_enabled.return_value = True
        mock_get_db.return_value = iter([db_session])
        
        result = refresh_connection("nonexistent-connection-id")
        
        assert result["status"] == "failed"
        assert "not found" in result["error"]

    @patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled')
    @patch('backend.tasks.token_health_tasks.get_token_refresh_service')
    @patch('backend.tasks.token_health_tasks.get_db')
    def test_refresh_connection_unsupported_platform(
        self,
        mock_get_db,
        mock_get_refresh_service,
        mock_feature_enabled,
        db_session,
        test_organization
    ):
        """Test refresh task with unsupported platform"""
        mock_feature_enabled.return_value = True
        mock_get_db.return_value = iter([db_session])
        
        # Create connection with unsupported platform
        unsupported_connection = SocialConnection(
            organization_id=test_organization.id,
            platform="linkedin",  # Not supported for token refresh
            platform_account_id="linkedin_123",
            platform_username="LinkedInUser",
            access_tokens={"access_token": "token"},
            is_active=True,
            connection_metadata={}
        )
        db_session.add(unsupported_connection)
        db_session.commit()
        
        result = refresh_connection(str(unsupported_connection.id))
        
        assert result["status"] == "failed"
        assert "Unsupported platform" in result["error"]

    def test_audit_logs_creation(self, db_session, expiring_meta_connection):
        """Test that audit logs are properly created during refresh"""
        # Get initial audit count
        initial_audit_count = db_session.query(SocialAudit).count()
        
        with patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled', return_value=True):
            with patch('backend.tasks.token_health_tasks.get_db', return_value=iter([db_session])):
                with patch('backend.tasks.token_health_tasks.get_token_refresh_service') as mock_get_service:
                    # Mock successful refresh
                    mock_refresh_service = MagicMock()
                    mock_get_service.return_value = mock_refresh_service
                    
                    new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
                    mock_refresh_service.refresh_meta_connection = AsyncMock(
                        return_value=(True, new_expiry, "Refresh successful")
                    )
                    
                    # Run audit
                    audit_all_tokens()
        
        # Check that audit logs were created
        final_audit_count = db_session.query(SocialAudit).count()
        assert final_audit_count > initial_audit_count
        
        # Check for specific refresh audit logs
        refresh_audits = db_session.query(SocialAudit).filter(
            SocialAudit.action == "refresh"
        ).all()
        
        assert len(refresh_audits) > 0
        
        # Verify audit log content
        audit = refresh_audits[0]
        assert audit.platform in ["meta", "x"]
        assert audit.status in ["success", "failure"]
        assert audit.organization_id is not None

    def test_database_transaction_handling(self, db_session, expiring_meta_connection):
        """Test that database transactions are properly handled"""
        # Verify connection exists before audit
        connection = db_session.query(SocialConnection).filter(
            SocialConnection.id == expiring_meta_connection.id
        ).first()
        assert connection is not None
        
        with patch('backend.tasks.token_health_tasks.is_partner_oauth_enabled', return_value=True):
            with patch('backend.tasks.token_health_tasks.get_db', return_value=iter([db_session])):
                with patch('backend.tasks.token_health_tasks.get_token_refresh_service') as mock_get_service:
                    # Mock successful refresh
                    mock_refresh_service = MagicMock()
                    mock_get_service.return_value = mock_refresh_service
                    
                    new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
                    mock_refresh_service.refresh_meta_connection = AsyncMock(
                        return_value=(True, new_expiry, "Refresh successful")
                    )
                    
                    # Run audit
                    result = audit_all_tokens()
        
        # Verify the audit completed successfully
        assert result["refresh_successes"] >= 1
        
        # Verify connection is still accessible after transactions
        connection = db_session.query(SocialConnection).filter(
            SocialConnection.id == expiring_meta_connection.id
        ).first()
        assert connection is not None