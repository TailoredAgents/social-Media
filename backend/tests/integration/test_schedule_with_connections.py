"""
Integration tests for Phase 7: Schedule with connection IDs
Tests the new connection-based content scheduling flow
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.db.models import SocialConnection, ContentSchedule, SocialAudit, User, Organization
from backend.tests.conftest import TestingSessionLocal
from backend.services.content_scheduler_service import ContentSchedulerService


class TestScheduleWithConnections:
    """Integration tests for connection-based content scheduling"""
    
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
    def verified_meta_connection(self, db_session, test_organization):
        """Create verified Meta connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="page_123",
            platform_username="TestPage",
            access_tokens={"page_token": "encrypted_page_token"},
            is_active=True,
            verified_for_posting=True,  # Already verified
            connection_metadata={"page_id": "123456789"}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def verified_x_connection(self, db_session, test_organization):
        """Create verified X connection"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="x",
            platform_account_id="user_456",
            platform_username="TestUser",
            access_tokens={"access_token": "encrypted_access_token"},
            is_active=True,
            verified_for_posting=True,  # Already verified
            connection_metadata={}
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
            platform_account_id="page_999",
            platform_username="UnverifiedPage",
            access_tokens={"page_token": "encrypted_token"},
            is_active=True,
            verified_for_posting=False,  # Not verified
            connection_metadata={"page_id": "999999999"}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def scheduler_service(self):
        """Create scheduler service"""
        return ContentSchedulerService()
    
    @patch('backend.services.connection_publisher_service.decrypt_token')
    async def test_schedule_immediate_publish_success(
        self, 
        mock_decrypt,
        db_session, 
        test_organization,
        verified_meta_connection, 
        verified_x_connection,
        scheduler_service
    ):
        """Test immediate publishing to multiple connections"""
        mock_decrypt.return_value = "decrypted_token"
        
        content = "Test content for immediate publishing"
        media_urls = ["https://example.com/image1.jpg"]
        connection_ids = [str(verified_meta_connection.id), str(verified_x_connection.id)]
        
        # Schedule for immediate publishing
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=media_urls,
            scheduled_time=None,  # Immediate
            db=db_session
        )
        
        # Verify results
        assert result["scheduled_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["results"]) == 2
        assert len(result["errors"]) == 0
        
        # Check that both connections were processed
        platforms = [r["platform"] for r in result["results"]]
        assert "meta" in platforms
        assert "x" in platforms
        
        # Verify all succeeded
        for r in result["results"]:
            assert r["success"] is True
            assert "schedule_id" in r
            assert "platform_post_id" in r
        
        # Verify database records
        schedules = db_session.query(ContentSchedule).filter(
            ContentSchedule.organization_id == test_organization.id
        ).all()
        
        assert len(schedules) == 2
        for schedule in schedules:
            assert schedule.status == "published"
            assert schedule.published_at is not None
            assert schedule.platform_post_id is not None
            assert schedule.content == content
    
    async def test_schedule_for_later_success(
        self,
        db_session,
        test_organization,
        verified_meta_connection,
        scheduler_service
    ):
        """Test scheduling content for future publishing"""
        content = "Test content for future publishing"
        media_urls = []
        connection_ids = [str(verified_meta_connection.id)]
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=2)
        
        # Schedule for future
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=media_urls,
            scheduled_time=scheduled_time,
            db=db_session
        )
        
        # Verify results
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 0
        assert len(result["results"]) == 1
        
        schedule_result = result["results"][0]
        assert schedule_result["success"] is True
        assert schedule_result["platform"] == "meta"
        assert "schedule_id" in schedule_result
        assert "scheduled_for" in schedule_result
        
        # Verify database record
        schedule = db_session.query(ContentSchedule).filter(
            ContentSchedule.id == schedule_result["schedule_id"]
        ).first()
        
        assert schedule is not None
        assert schedule.status == "scheduled"
        assert schedule.scheduled_for == scheduled_time
        assert schedule.published_at is None  # Not published yet
        assert schedule.platform_post_id is None  # Not published yet
    
    async def test_schedule_unverified_connection_fails(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that unverified connections fail scheduling"""
        content = "Test content for unverified connection"
        connection_ids = [str(unverified_connection.id)]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Verify failure
        assert result["scheduled_count"] == 0
        assert result["failed_count"] == 1
        assert len(result["results"]) == 1
        
        failed_result = result["results"][0]
        assert failed_result["success"] is False
        assert "not verified" in failed_result["error"].lower()
        assert "draft" in failed_result["error"].lower()
    
    async def test_schedule_duplicate_content_prevention(
        self,
        db_session,
        test_organization,
        verified_meta_connection,
        scheduler_service
    ):
        """Test that duplicate content is prevented with idempotency"""
        content = "Duplicate content test"
        connection_ids = [str(verified_meta_connection.id)]
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Schedule first time
        result1 = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=scheduled_time,
            db=db_session
        )
        
        assert result1["scheduled_count"] == 1
        assert result1["failed_count"] == 0
        
        # Try to schedule same content again
        result2 = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=scheduled_time,
            db=db_session
        )
        
        # Second attempt should fail due to duplicate
        assert result2["scheduled_count"] == 0
        assert result2["failed_count"] == 0  # Not counted as failure
        assert len(result2["results"]) == 1
        
        duplicate_result = result2["results"][0]
        assert duplicate_result["success"] is False
        assert "duplicate" in duplicate_result["error"].lower()
        assert "existing_id" in duplicate_result
    
    async def test_schedule_partial_failures(
        self,
        db_session,
        test_organization,
        verified_meta_connection,
        unverified_connection,
        scheduler_service
    ):
        """Test mixed success/failure scenario"""
        content = "Mixed results test"
        connection_ids = [str(verified_meta_connection.id), str(unverified_connection.id)]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Should have one success, one failure
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["results"]) == 2
        
        # Verify results
        success_results = [r for r in result["results"] if r["success"]]
        failure_results = [r for r in result["results"] if not r["success"]]
        
        assert len(success_results) == 1
        assert len(failure_results) == 1
        
        assert success_results[0]["platform"] == "meta"
        assert failure_results[0]["platform"] == "meta"  # unverified connection
        assert "not verified" in failure_results[0]["error"].lower()
    
    async def test_audit_logs_created(
        self,
        db_session,
        test_organization,
        verified_meta_connection,
        scheduler_service
    ):
        """Test that audit logs are created for scheduling operations"""
        # Get initial audit count
        initial_count = db_session.query(SocialAudit).count()
        
        content = "Test content for audit logging"
        connection_ids = [str(verified_meta_connection.id)]
        
        await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Check that audit logs were created
        final_count = db_session.query(SocialAudit).count()
        assert final_count > initial_count
        
        # Verify audit log content
        audit_logs = db_session.query(SocialAudit).filter(
            SocialAudit.connection_id == verified_meta_connection.id
        ).order_by(SocialAudit.timestamp.desc()).all()
        
        assert len(audit_logs) > 0
        
        recent_audit = audit_logs[0]
        assert recent_audit.organization_id == test_organization.id
        assert recent_audit.platform == "meta"
        assert recent_audit.action in ["publish_content", "schedule_content"]
        assert recent_audit.status == "success"
        assert recent_audit.metadata is not None
    
    async def test_invalid_connection_ids(
        self,
        db_session,
        test_organization,
        scheduler_service
    ):
        """Test handling of invalid/non-existent connection IDs"""
        content = "Test content for invalid connections"
        invalid_connection_ids = ["00000000-0000-0000-0000-000000000000"]
        
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=invalid_connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Should have error about missing connections
        assert result["scheduled_count"] == 0
        assert result["failed_count"] == 0
        assert len(result["errors"]) > 0
        assert "not found" in result["errors"][0].lower()
        
        # Should have no results for non-existent connections
        assert len(result["results"]) == 0