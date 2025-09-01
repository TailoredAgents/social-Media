"""
Integration tests for Phase 7: Partial failures
Tests scenarios where some connections succeed and others fail
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.db.models import SocialConnection, ContentSchedule, SocialAudit, User, Organization
from backend.tests.conftest import TestingSessionLocal
from backend.services.content_scheduler_service import ContentSchedulerService


class TestPartialFailures:
    """Integration tests for partial failure scenarios"""
    
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
        org = Organization(name="Test Org")
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
    def working_meta_connection(self, db_session, test_organization):
        """Create working Meta connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="working_page",
            platform_username="WorkingPage",
            access_tokens={"page_token": "encrypted_working_token"},
            is_active=True,
            verified_for_posting=True,
            connection_metadata={"page_id": "working123"}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def working_x_connection(self, db_session, test_organization):
        """Create working X connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="x",
            platform_account_id="working_user",
            platform_username="WorkingUser",
            access_tokens={"access_token": "encrypted_working_token"},
            is_active=True,
            verified_for_posting=True,
            connection_metadata={}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def broken_meta_connection(self, db_session, test_organization):
        """Create Meta connection that will fail (missing page_id)"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="broken_page",
            platform_username="BrokenPage",
            access_tokens={"page_token": "encrypted_broken_token"},
            is_active=True,
            verified_for_posting=True,
            connection_metadata={}  # Missing page_id - will cause failure
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def unverified_connection(self, db_session, test_organization):
        """Create unverified connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="unverified_page",
            platform_username="UnverifiedPage",
            access_tokens={"page_token": "encrypted_token"},
            is_active=True,
            verified_for_posting=False,  # Not verified
            connection_metadata={"page_id": "unverified123"}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def inactive_connection(self, db_session, test_organization):
        """Create inactive connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="x",
            platform_account_id="inactive_user",
            platform_username="InactiveUser",
            access_tokens={"access_token": "encrypted_token"},
            is_active=False,  # Inactive
            verified_for_posting=True,
            connection_metadata={}
        )
        db_session.add(inactive_connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def scheduler_service(self):
        """Create scheduler service"""
        return ContentSchedulerService()
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_mixed_success_failure_immediate_publish(
        self,
        mock_decrypt,
        db_session,
        test_organization,
        working_meta_connection,
        broken_meta_connection,
        unverified_connection,
        scheduler_service
    ):
        """Test immediate publishing with mixed success/failure"""
        mock_decrypt.return_value = "decrypted_token"
        
        content = "Test content for mixed results"
        connection_ids = [
            str(working_meta_connection.id),
            str(broken_meta_connection.id), 
            str(unverified_connection.id)
        ]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,  # Immediate
            db=db_session
        )
        
        # Should have 1 success, 2 failures
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 2
        assert len(result["results"]) == 3
        
        # Verify individual results
        success_results = [r for r in result["results"] if r["success"]]
        failure_results = [r for r in result["results"] if not r["success"]]
        
        assert len(success_results) == 1
        assert len(failure_results) == 2
        
        # Check success result
        success_result = success_results[0]
        assert success_result["connection_id"] == str(working_meta_connection.id)
        assert success_result["platform"] == "meta"
        assert "schedule_id" in success_result
        assert "platform_post_id" in success_result
        
        # Check failure results
        failure_connection_ids = [r["connection_id"] for r in failure_results]
        assert str(broken_meta_connection.id) in failure_connection_ids
        assert str(unverified_connection.id) in failure_connection_ids
        
        # Verify error messages
        unverified_result = next(r for r in failure_results if r["connection_id"] == str(unverified_connection.id))
        assert "not verified" in unverified_result["error"].lower()
        
        broken_result = next(r for r in failure_results if r["connection_id"] == str(broken_meta_connection.id))
        # This would fail during publishing due to missing page_id, but since we're using stubs,
        # it might succeed in the current implementation
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_all_connections_fail(
        self,
        mock_decrypt,
        db_session,
        test_organization,
        unverified_connection,
        inactive_connection,
        scheduler_service
    ):
        """Test scenario where all connections fail"""
        mock_decrypt.return_value = "decrypted_token"
        
        content = "Test content for all failures"
        connection_ids = [str(unverified_connection.id), str(inactive_connection.id)]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # All should fail
        assert result["scheduled_count"] == 0
        assert result["failed_count"] == 2
        assert len(result["results"]) == 2
        
        # All results should be failures
        for result_item in result["results"]:
            assert result_item["success"] is False
            assert "error" in result_item
        
        # Check specific error messages
        unverified_result = next(r for r in result["results"] if r["connection_id"] == str(unverified_connection.id))
        assert "not verified" in unverified_result["error"].lower()
        
        # Inactive connection should fail at the connection validation level
        # (not found in active connections query)
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_partial_failure_audit_logs(
        self,
        mock_decrypt,
        db_session,
        test_organization,
        working_meta_connection,
        unverified_connection,
        scheduler_service
    ):
        """Test that audit logs are created for both successes and failures"""
        mock_decrypt.return_value = "decrypted_token"
        
        # Get initial audit count
        initial_audit_count = db_session.query(SocialAudit).count()
        
        content = "Test content for audit logging"
        connection_ids = [str(working_meta_connection.id), str(unverified_connection.id)]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Should have 1 success, 1 failure
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 1
        
        # Check audit logs were created
        final_audit_count = db_session.query(SocialAudit).count()
        assert final_audit_count > initial_audit_count
        
        # Verify specific audit logs
        audit_logs = db_session.query(SocialAudit).filter(
            SocialAudit.organization_id == test_organization.id
        ).order_by(SocialAudit.timestamp.desc()).all()
        
        # Should have audit logs for both connections
        connection_ids_in_audits = [str(audit.connection_id) for audit in audit_logs[:2]]
        assert str(working_meta_connection.id) in connection_ids_in_audits
        
        # Check audit log statuses
        success_audit = next((audit for audit in audit_logs if str(audit.connection_id) == str(working_meta_connection.id)), None)
        assert success_audit is not None
        assert success_audit.status == "success"
        assert success_audit.action in ["publish_content", "schedule_content"]
    
    async def test_partial_failure_database_consistency(
        self,
        db_session,
        test_organization,
        working_meta_connection,
        unverified_connection,
        scheduler_service
    ):
        """Test database consistency during partial failures"""
        with patch('backend.services.connection_publisher_service.decrypt_token', return_value="token"):
            content = "Test content for database consistency"
            connection_ids = [str(working_meta_connection.id), str(unverified_connection.id)]
            
            # Schedule content
            result = await scheduler_service.schedule_content(
                organization_id=str(test_organization.id),
                connection_ids=connection_ids,
                content=content,
                media_urls=[],
                scheduled_time=None,
                db=db_session
            )
        
        # Verify database state
        schedules = db_session.query(ContentSchedule).filter(
            ContentSchedule.organization_id == test_organization.id
        ).all()
        
        # Only successful schedules should be in database
        assert len(schedules) == result["scheduled_count"]
        
        # Verify the successful schedule
        if result["scheduled_count"] > 0:
            successful_schedule = schedules[0]
            assert successful_schedule.connection_id == working_meta_connection.id
            assert successful_schedule.status == "published"
            assert successful_schedule.content == content
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_mixed_platforms_partial_failure(
        self,
        mock_decrypt,
        db_session,
        test_organization,
        working_meta_connection,
        working_x_connection,
        unverified_connection,
        scheduler_service
    ):
        """Test partial failures across different platforms"""
        mock_decrypt.return_value = "decrypted_token"
        
        content = "Test content for mixed platforms"
        connection_ids = [
            str(working_meta_connection.id),
            str(working_x_connection.id),
            str(unverified_connection.id)
        ]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Should have 2 successes (Meta + X), 1 failure
        assert result["scheduled_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["results"]) == 3
        
        # Verify platform distribution in results
        success_results = [r for r in result["results"] if r["success"]]
        failure_results = [r for r in result["results"] if not r["success"]]
        
        assert len(success_results) == 2
        assert len(failure_results) == 1
        
        # Check that both platforms succeeded
        success_platforms = [r["platform"] for r in success_results]
        assert "meta" in success_platforms
        assert "x" in success_platforms
        
        # Check that unverified connection failed
        failure_result = failure_results[0]
        assert failure_result["connection_id"] == str(unverified_connection.id)
        assert "not verified" in failure_result["error"].lower()
    
    async def test_nonexistent_connections_handled(
        self,
        db_session,
        test_organization,
        working_meta_connection,
        scheduler_service
    ):
        """Test handling of non-existent connection IDs in the mix"""
        content = "Test content with invalid connection"
        connection_ids = [
            str(working_meta_connection.id),
            "00000000-0000-0000-0000-000000000000"  # Non-existent
        ]
        
        with patch('backend.services.connection_publisher_service.decrypt_token', return_value="token"):
            result = await scheduler_service.schedule_content(
                organization_id=str(test_organization.id),
                connection_ids=connection_ids,
                content=content,
                media_urls=[],
                scheduled_time=None,
                db=db_session
            )
        
        # Should succeed for valid connection, error for invalid
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 0
        assert len(result["results"]) == 1  # Only valid connection processed
        assert len(result["errors"]) > 0  # Error about missing connection
        
        # Check error message
        assert "not found" in result["errors"][0].lower()
        
        # Check successful result
        success_result = result["results"][0]
        assert success_result["connection_id"] == str(working_meta_connection.id)
        assert success_result["success"] is True
    
    async def test_error_isolation(
        self,
        db_session,
        test_organization,
        working_meta_connection,
        working_x_connection,
        scheduler_service
    ):
        """Test that errors in one connection don't affect others"""
        content = "Test content for error isolation"
        
        # Mock one connection to fail, other to succeed
        with patch('backend.services.connection_publisher_service.decrypt_token') as mock_decrypt:
            with patch.object(scheduler_service.publisher_service, 'publish_to_connection') as mock_publish:
                # Set up side effects - first call fails, second succeeds
                mock_publish.side_effect = [
                    (False, None, "First connection error"),  # Meta fails
                    (True, "x_post_123", "Success")  # X succeeds
                ]
                
                connection_ids = [str(working_meta_connection.id), str(working_x_connection.id)]
                
                result = await scheduler_service.schedule_content(
                    organization_id=str(test_organization.id),
                    connection_ids=connection_ids,
                    content=content,
                    media_urls=[],
                    scheduled_time=None,
                    db=db_session
                )
        
        # Should have 1 success, 1 failure
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["results"]) == 2
        
        # Verify results
        results_by_platform = {r["platform"]: r for r in result["results"]}
        
        assert results_by_platform["meta"]["success"] is False
        assert results_by_platform["x"]["success"] is True
        assert "First connection error" in results_by_platform["meta"]["error"]