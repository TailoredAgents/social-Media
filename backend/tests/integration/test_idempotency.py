"""
Integration tests for idempotency (Phase 8)
Tests that duplicate schedules with same content_hash don't double-post
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from celery.result import AsyncResult

from backend.tasks.publish_tasks import publish_via_connection
from backend.db.models import SocialConnection, ContentSchedule
from backend.services.publish_runner import PublishPayload


@pytest.fixture
def mock_connection():
    """Create mock social connection"""
    connection = Mock(spec=SocialConnection)
    connection.id = "test-connection-id"
    connection.organization_id = "test-org-id"
    connection.platform = "meta"
    connection.is_active = True
    connection.verified_for_posting = True
    connection.access_tokens = {"page_token": "encrypted_token"}
    connection.platform_metadata = {"page_id": "test_page"}
    connection.token_expires_at = None
    connection.revoked_at = None
    return connection


@pytest.fixture
def payload_dict():
    """Create test payload dictionary"""
    return {
        "content": "Test content for idempotency",
        "media_urls": ["https://example.com/image.jpg"],
        "idempotency_key": "test_idempotency_key_12345"
    }


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    mock_db = Mock()
    
    # Mock database operations
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.close = Mock()
    
    return mock_db


class TestIdempotency:
    """Test idempotency in publish tasks and content scheduling"""
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    @patch('backend.tasks.publish_tasks.get_publish_runner')
    async def test_duplicate_content_hash_prevents_double_post(self, mock_runner, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that duplicate content hash prevents double posting"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock existing successful schedule
        existing_schedule = Mock(spec=ContentSchedule)
        existing_schedule.platform_post_id = "existing_post_123"
        existing_schedule.status = "published"
        
        # First query returns the connection
        # Second query returns existing successful schedule
        mock_db_session.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=mock_connection)),  # Connection query
            Mock(first=Mock(return_value=existing_schedule))  # ContentSchedule query
        ]
        
        content_hash = "test_content_hash_12345"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Call the task function directly
        result = await publish_via_connection.__wrapped__(
            mock_task,
            str(mock_connection.id),
            payload_dict,
            content_hash,
            None
        )
        
        # Verify idempotency - should return existing success without attempting publish
        assert result['success'] is True
        assert result['platform_post_id'] == "existing_post_123"
        assert result['message'] == "Already published (idempotency)"
        
        # Verify publish runner was never called
        mock_runner.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    @patch('backend.tasks.publish_tasks.get_publish_runner')
    async def test_new_content_hash_allows_publish(self, mock_runner, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that new content hash allows publish to proceed"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock no existing schedule
        mock_db_session.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=mock_connection)),  # Connection query
            Mock(first=Mock(return_value=None))  # No existing ContentSchedule
        ]
        
        # Mock successful publish
        mock_publish_runner = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.platform_post_id = "new_post_456"
        mock_result.should_retry = False
        mock_result.metrics = {"test": "metrics"}
        mock_publish_runner.run_publish = AsyncMock(return_value=mock_result)
        mock_runner.return_value = mock_publish_runner
        
        content_hash = "new_content_hash_67890"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Call the task function
        result = await publish_via_connection.__wrapped__(
            mock_task,
            str(mock_connection.id),
            payload_dict,
            content_hash,
            None
        )
        
        # Verify new publish was attempted
        assert result['success'] is True
        assert result['platform_post_id'] == "new_post_456"
        assert result['message'] == "Published successfully"
        
        # Verify publish runner was called
        mock_publish_runner.run_publish.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    async def test_missing_connection_prevents_duplicate_check(self, mock_get_db, payload_dict, mock_db_session):
        """Test that missing connection prevents duplicate check"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock connection not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        content_hash = "test_content_hash"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Call the task function
        result = await publish_via_connection.__wrapped__(
            mock_task,
            "nonexistent_connection_id",
            payload_dict,
            content_hash,
            None
        )
        
        # Verify error response
        assert result['success'] is False
        assert "not found" in result['error_message']
        assert result.get('is_fatal') is True
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    @patch('backend.tasks.publish_tasks.get_publish_runner')
    async def test_idempotency_key_updates_schedule_status(self, mock_runner, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that successful publish updates ContentSchedule status via idempotency key"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock existing schedule in pending state
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.status = "scheduled"
        mock_schedule.platform_post_id = None
        
        # Mock database queries
        mock_db_session.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=mock_connection)),  # Connection query
            Mock(first=Mock(return_value=None)),  # No duplicate check hit
            Mock(first=Mock(return_value=mock_schedule))  # Idempotency key query
        ]
        
        # Mock successful publish
        mock_publish_runner = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.platform_post_id = "updated_post_789"
        mock_result.should_retry = False
        mock_result.metrics = {"test": "metrics"}
        mock_publish_runner.run_publish = AsyncMock(return_value=mock_result)
        mock_runner.return_value = mock_publish_runner
        
        content_hash = "test_content_hash"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Call the task function
        result = await publish_via_connection.__wrapped__(
            mock_task,
            str(mock_connection.id),
            payload_dict,
            content_hash,
            None
        )
        
        # Verify success
        assert result['success'] is True
        assert result['platform_post_id'] == "updated_post_789"
        
        # Verify schedule was updated
        assert mock_schedule.status == "published"
        assert mock_schedule.platform_post_id == "updated_post_789"
        assert mock_schedule.published_at is not None
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    @patch('backend.tasks.publish_tasks.get_publish_runner')
    async def test_retry_updates_schedule_status(self, mock_runner, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that retryable failure updates ContentSchedule status"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock existing schedule
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.status = "scheduled"
        
        mock_db_session.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=mock_connection)),  # Connection query
            Mock(first=Mock(return_value=None)),  # No duplicate
            Mock(first=Mock(return_value=mock_schedule))  # Idempotency key query
        ]
        
        # Mock retryable failure
        mock_publish_runner = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.should_retry = True
        mock_result.retry_after_s = 60
        mock_result.error_message = "Rate limited"
        mock_result.metrics = {"test": "metrics"}
        mock_publish_runner.run_publish = AsyncMock(return_value=mock_result)
        mock_runner.return_value = mock_publish_runner
        
        content_hash = "test_content_hash"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 6
        mock_task.retry = Mock(side_effect=Exception("Retry called"))  # To catch retry
        
        # Expect retry exception
        with pytest.raises(Exception, match="Retry called"):
            await publish_via_connection.__wrapped__(
                mock_task,
                str(mock_connection.id),
                payload_dict,
                content_hash,
                None
            )
        
        # Verify schedule status was updated for retry
        assert mock_schedule.status == "retrying_attempt_1"
        assert mock_schedule.error_message == "Rate limited"
        
        # Verify retry was called
        mock_task.retry.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    @patch('backend.tasks.publish_tasks.get_publish_runner')
    async def test_fatal_error_updates_schedule_status(self, mock_runner, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that fatal error updates ContentSchedule status"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock existing schedule
        mock_schedule = Mock(spec=ContentSchedule)
        mock_schedule.status = "scheduled"
        
        mock_db_session.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=mock_connection)),  # Connection query
            Mock(first=Mock(return_value=None)),  # No duplicate
            Mock(first=Mock(return_value=mock_schedule))  # Idempotency key query
        ]
        
        # Mock fatal failure
        mock_publish_runner = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.should_retry = False
        mock_result.error_message = "Authentication failed"
        mock_result.metrics = {"test": "metrics"}
        mock_publish_runner.run_publish = AsyncMock(return_value=mock_result)
        mock_runner.return_value = mock_publish_runner
        
        content_hash = "test_content_hash"
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        # Call the task function
        result = await publish_via_connection.__wrapped__(
            mock_task,
            str(mock_connection.id),
            payload_dict,
            content_hash,
            None
        )
        
        # Verify fatal error response
        assert result['success'] is False
        assert result['error_message'] == "Authentication failed"
        
        # Verify schedule status was updated
        assert mock_schedule.status == "failed"
        assert mock_schedule.error_message == "Authentication failed"
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.publish_tasks.get_db')
    async def test_empty_content_hash_skips_duplicate_check(self, mock_get_db, mock_connection, payload_dict, mock_db_session):
        """Test that empty/None content hash skips duplicate check"""
        # Setup mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        
        # Mock connection found, but no duplicate check should be made
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Create mock Celery task
        mock_task = Mock()
        mock_task.request.retries = 0
        
        with patch('backend.tasks.publish_tasks.get_publish_runner') as mock_runner:
            # Mock successful publish
            mock_publish_runner = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.platform_post_id = "no_hash_post_123"
            mock_result.should_retry = False
            mock_result.metrics = {"test": "metrics"}
            mock_publish_runner.run_publish = AsyncMock(return_value=mock_result)
            mock_runner.return_value = mock_publish_runner
            
            # Call with None content hash
            result = await publish_via_connection.__wrapped__(
                mock_task,
                str(mock_connection.id),
                payload_dict,
                None,  # No content hash
                None
            )
            
            # Verify success without duplicate check
            assert result['success'] is True
            assert result['platform_post_id'] == "no_hash_post_123"
            
            # Verify only connection query was made (no duplicate check)
            assert mock_db_session.query.call_count == 1