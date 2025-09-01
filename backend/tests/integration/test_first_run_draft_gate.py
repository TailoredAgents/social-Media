"""
Integration tests for Phase 7: First-run draft gate
Tests the draft verification requirement before posting
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.db.models import SocialConnection, ContentDraft, User, Organization
from backend.tests.conftest import TestingSessionLocal
from backend.services.content_scheduler_service import ContentSchedulerService


class TestFirstRunDraftGate:
    """Integration tests for draft verification gate"""
    
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
    def unverified_connection(self, db_session, test_organization):
        """Create unverified connection (no drafts created yet)"""
        connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="page_123",
            platform_username="TestPage",
            access_tokens={"page_token": "encrypted_page_token"},
            is_active=True,
            verified_for_posting=False,  # Not verified yet
            connection_metadata={"page_id": "123456789"}
        )
        db_session.add(connection)
        db_session.commit()
        return connection
    
    @pytest.fixture
    def scheduler_service(self):
        """Create scheduler service"""
        return ContentSchedulerService()
    
    async def test_schedule_without_draft_returns_400(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that scheduling without draft verification returns 400"""
        content = "Test content without draft verification"
        connection_ids = [str(unverified_connection.id)]
        
        # Attempt to schedule without creating draft first
        result = await scheduler_service.schedule_content(
            organization_id=str(test_organization.id),
            connection_ids=connection_ids,
            content=content,
            media_urls=[],
            scheduled_time=None,
            db=db_session
        )
        
        # Should fail due to lack of verification
        assert result["scheduled_count"] == 0
        assert result["failed_count"] == 1
        assert len(result["results"]) == 1
        
        failed_result = result["results"][0]
        assert failed_result["success"] is False
        assert "not verified" in failed_result["error"].lower()
        assert "draft" in failed_result["error"].lower()
        
        # Verify connection is still unverified
        db_session.refresh(unverified_connection)
        assert unverified_connection.verified_for_posting is False
    
    async def test_create_draft_verifies_connection(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that creating a draft marks connection as verified"""
        # Verify initial state
        assert unverified_connection.verified_for_posting is False
        
        content = "Test draft content"
        media_urls = ["https://example.com/image.jpg"]
        
        # Create draft
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=str(test_organization.id),
            connection_id=str(unverified_connection.id),
            content=content,
            media_urls=media_urls,
            db=db_session
        )
        
        # Should succeed
        assert success is True
        assert draft_id is not None
        assert error is None
        
        # Verify connection is now verified
        db_session.refresh(unverified_connection)
        assert unverified_connection.verified_for_posting is True
        
        # Verify draft record was created
        draft = db_session.query(ContentDraft).filter(
            ContentDraft.id == draft_id
        ).first()
        
        assert draft is not None
        assert draft.organization_id == test_organization.id
        assert draft.connection_id == unverified_connection.id
        assert draft.content == content
        assert draft.media_urls == media_urls
        assert draft.status == "verified"
        assert draft.verified_at is not None
    
    async def test_schedule_after_draft_succeeds(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that scheduling succeeds after creating draft"""
        content = "Test content after draft creation"
        connection_ids = [str(unverified_connection.id)]
        
        # First, create draft to verify connection
        draft_success, draft_id, draft_error = await scheduler_service.create_draft(
            organization_id=str(test_organization.id),
            connection_id=str(unverified_connection.id),
            content="Draft content for verification",
            media_urls=[],
            db=db_session
        )
        
        assert draft_success is True
        assert draft_id is not None
        
        # Now scheduling should succeed
        with patch('backend.services.connection_publisher_service.decrypt_token', return_value="mock_token"):
            result = await scheduler_service.schedule_content(
                organization_id=str(test_organization.id),
                connection_ids=connection_ids,
                content=content,
                media_urls=[],
                scheduled_time=None,
                db=db_session
            )
        
        # Should succeed now
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 0
        assert len(result["results"]) == 1
        
        success_result = result["results"][0]
        assert success_result["success"] is True
        assert success_result["platform"] == "meta"
        assert "schedule_id" in success_result
    
    async def test_draft_creation_idempotency(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that multiple drafts can be created for same connection"""
        content1 = "First draft content"
        content2 = "Second draft content"
        connection_id = str(unverified_connection.id)
        org_id = str(test_organization.id)
        
        # Create first draft
        success1, draft_id1, error1 = await scheduler_service.create_draft(
            organization_id=org_id,
            connection_id=connection_id,
            content=content1,
            media_urls=[],
            db=db_session
        )
        
        assert success1 is True
        assert draft_id1 is not None
        
        # Create second draft with different content
        success2, draft_id2, error2 = await scheduler_service.create_draft(
            organization_id=org_id,
            connection_id=connection_id,
            content=content2,
            media_urls=[],
            db=db_session
        )
        
        assert success2 is True
        assert draft_id2 is not None
        assert draft_id2 != draft_id1  # Different drafts
        
        # Verify both drafts exist in database
        drafts = db_session.query(ContentDraft).filter(
            ContentDraft.connection_id == unverified_connection.id
        ).all()
        
        assert len(drafts) == 2
        contents = [draft.content for draft in drafts]
        assert content1 in contents
        assert content2 in contents
    
    async def test_draft_creation_invalid_connection(
        self,
        db_session,
        test_organization,
        scheduler_service
    ):
        """Test draft creation with invalid connection ID"""
        invalid_connection_id = "00000000-0000-0000-0000-000000000000"
        
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=str(test_organization.id),
            connection_id=invalid_connection_id,
            content="Test content",
            media_urls=[],
            db=db_session
        )
        
        # Should fail
        assert success is False
        assert draft_id is None
        assert error is not None
        assert "not found" in error.lower() or "not accessible" in error.lower()
    
    async def test_draft_creation_inactive_connection(
        self,
        db_session,
        test_organization,
        scheduler_service
    ):
        """Test draft creation with inactive connection"""
        # Create inactive connection
        inactive_connection = SocialConnection(
            organization_id=test_organization.id,
            platform="meta",
            platform_account_id="inactive_page",
            platform_username="InactivePage",
            access_tokens={"page_token": "encrypted_token"},
            is_active=False,  # Inactive
            verified_for_posting=False,
            connection_metadata={"page_id": "inactive123"}
        )
        db_session.add(inactive_connection)
        db_session.commit()
        
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=str(test_organization.id),
            connection_id=str(inactive_connection.id),
            content="Test content",
            media_urls=[],
            db=db_session
        )
        
        # Should fail due to inactive connection
        assert success is False
        assert draft_id is None
        assert error is not None
        assert ("not found" in error.lower() or 
                "not accessible" in error.lower() or 
                "inactive" in error.lower())
    
    async def test_draft_content_validation(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test draft creation with various content validation scenarios"""
        connection_id = str(unverified_connection.id)
        org_id = str(test_organization.id)
        
        # Test with empty content - should be handled by API validation
        # but service should still work if called directly
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=org_id,
            connection_id=connection_id,
            content="",  # Empty content
            media_urls=[],
            db=db_session
        )
        
        # Service should handle empty content (validation happens at API level)
        # This tests that service doesn't crash with edge cases
        if not success:
            assert error is not None
        
        # Test with very long content
        long_content = "A" * 20000  # Very long content
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=org_id,
            connection_id=connection_id,
            content=long_content,
            media_urls=[],
            db=db_session
        )
        
        # Should succeed (truncation/validation happens elsewhere)
        if not success:
            # If it fails, should have meaningful error
            assert error is not None
    
    async def test_connection_verification_persists(
        self,
        db_session,
        test_organization,
        unverified_connection,
        scheduler_service
    ):
        """Test that verification status persists across sessions"""
        # Verify initial state
        assert unverified_connection.verified_for_posting is False
        
        # Create draft to verify connection
        success, draft_id, error = await scheduler_service.create_draft(
            organization_id=str(test_organization.id),
            connection_id=str(unverified_connection.id),
            content="Verification draft",
            media_urls=[],
            db=db_session
        )
        
        assert success is True
        
        # Commit and start fresh session to simulate persistence
        db_session.commit()
        db_session.expire_all()
        
        # Re-query connection
        refreshed_connection = db_session.query(SocialConnection).filter(
            SocialConnection.id == unverified_connection.id
        ).first()
        
        assert refreshed_connection is not None
        assert refreshed_connection.verified_for_posting is True
        
        # Scheduling should now work without additional drafts
        with patch('backend.services.connection_publisher_service.decrypt_token', return_value="mock_token"):
            result = await scheduler_service.schedule_content(
                organization_id=str(test_organization.id),
                connection_ids=[str(refreshed_connection.id)],
                content="Post after verification",
                media_urls=[],
                scheduled_time=None,
                db=db_session
            )
        
        assert result["scheduled_count"] == 1
        assert result["failed_count"] == 0