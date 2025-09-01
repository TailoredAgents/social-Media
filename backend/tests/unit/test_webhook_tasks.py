"""
Unit tests for webhook Celery tasks
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from celery.exceptions import Retry

from backend.tasks.webhook_tasks import (
    process_meta_event,
    _process_normalized_entry,
    _process_page_change,
    _process_messaging_event,
    _process_feed_event,
    _process_mention_event,
    _process_messaging_change,
    _is_retryable_error,
    _send_to_dlq,
    watchdog_scan,
    DLQ_MAX_RETRIES,
    DLQ_RETRY_DELAYS
)


class TestProcessMetaEvent:
    """Test process_meta_event Celery task"""
    
    @pytest.fixture
    def mock_celery_task(self):
        """Create mock Celery task instance"""
        task = MagicMock()
        task.request.id = "test_task_123"
        task.request.retries = 0
        return task
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    @patch('backend.tasks.webhook_tasks._process_normalized_entry')
    async def test_process_meta_event_success(self, mock_process_entry, mock_get_service, mock_celery_task):
        """Test successful Meta event processing"""
        # Mock webhook service
        mock_service = MagicMock()
        mock_service.normalize_webhook_entry.return_value = {"normalized": True}
        mock_get_service.return_value = mock_service
        
        # Mock processing result
        mock_process_entry.return_value = {"events_processed": 2}
        
        entry = {"id": "page_123", "changes": []}
        event_info = {"entry_id": "page_123", "webhook_id": "test"}
        
        # Mock the task function directly
        with patch('backend.tasks.webhook_tasks.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 1, tzinfo=timezone.utc)
            
            result = await process_meta_event.__wrapped__(mock_celery_task, entry, event_info)
        
        assert result["status"] == "success"
        assert result["task_id"] == "test_task_123"
        assert result["events_processed"] == 2
        mock_service.normalize_webhook_entry.assert_called_once_with(entry)
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    @patch('backend.tasks.webhook_tasks._send_to_dlq')
    async def test_process_meta_event_non_retryable_error(self, mock_send_dlq, mock_get_service, mock_celery_task):
        """Test Meta event processing with non-retryable error"""
        # Mock service to raise non-retryable error
        mock_service = MagicMock()
        mock_service.normalize_webhook_entry.side_effect = ValueError("Invalid data")
        mock_get_service.return_value = mock_service
        
        mock_send_dlq.return_value = True
        mock_celery_task.request.retries = DLQ_MAX_RETRIES  # Max retries reached
        
        entry = {"id": "page_123"}
        event_info = {"entry_id": "page_123"}
        
        result = await process_meta_event.__wrapped__(mock_celery_task, entry, event_info)
        
        assert result["status"] == "failed"
        assert result["sent_to_dlq"] is True
        mock_send_dlq.assert_called_once()
    
    @patch('backend.tasks.webhook_tasks.get_meta_webhook_service')
    @patch('backend.tasks.webhook_tasks._is_retryable_error')
    async def test_process_meta_event_retryable_error(self, mock_is_retryable, mock_get_service, mock_celery_task):
        """Test Meta event processing with retryable error"""
        # Mock service to raise retryable error
        mock_service = MagicMock()
        connection_error = ConnectionError("Network error")
        mock_service.normalize_webhook_entry.side_effect = connection_error
        mock_get_service.return_value = mock_service
        
        mock_is_retryable.return_value = True
        mock_celery_task.request.retries = 1  # Below max retries
        mock_celery_task.retry.side_effect = Retry("Retrying")
        
        entry = {"id": "page_123"}
        event_info = {"entry_id": "page_123"}
        
        with pytest.raises(Retry):
            await process_meta_event.__wrapped__(mock_celery_task, entry, event_info)
        
        mock_celery_task.retry.assert_called_once()
        # Verify retry delay calculation
        retry_delay = DLQ_RETRY_DELAYS[min(1, len(DLQ_RETRY_DELAYS) - 1)]
        mock_celery_task.retry.assert_called_with(countdown=retry_delay, exc=connection_error)


class TestNormalizedEntryProcessing:
    """Test normalized entry processing functions"""
    
    @patch('backend.tasks.webhook_tasks._process_page_change')
    @patch('backend.tasks.webhook_tasks._process_messaging_event')
    async def test_process_normalized_entry_success(self, mock_messaging, mock_page_change):
        """Test successful normalized entry processing"""
        mock_page_change.return_value = {"processed": True}
        mock_messaging.return_value = {"processed": True}
        
        entry = {
            "changes": [{"field": "feed", "value": {}}],
            "messaging": [{"sender": {"id": "user_123"}}]
        }
        event_info = {"entry_id": "page_123"}
        
        result = await _process_normalized_entry(entry, event_info)
        
        assert result["events_processed"] == 2
        assert len(result["results"]) == 2
        mock_page_change.assert_called_once()
        mock_messaging.assert_called_once()
    
    async def test_process_normalized_entry_with_errors(self):
        """Test normalized entry processing with errors"""
        entry = {"invalid": "structure"}
        event_info = {"entry_id": "page_123"}
        
        # This should handle the error gracefully
        result = await _process_normalized_entry(entry, event_info)
        
        assert result["events_processed"] == 0
        assert len(result["results"]) == 0
    
    @patch('backend.tasks.webhook_tasks._process_feed_event')
    async def test_process_page_change_feed(self, mock_feed_event):
        """Test page change processing for feed events"""
        mock_feed_event.return_value = {"processed": True, "event_type": "feed"}
        
        change = {"field": "feed", "value": {"verb": "add", "item": "post"}}
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_page_change(change, entry, event_info)
        
        assert result["processed"] is True
        mock_feed_event.assert_called_once_with(
            {"verb": "add", "item": "post"}, entry, event_info
        )
    
    @patch('backend.tasks.webhook_tasks._process_mention_event')
    async def test_process_page_change_mentions(self, mock_mention_event):
        """Test page change processing for mention events"""
        mock_mention_event.return_value = {"processed": True, "event_type": "mention"}
        
        change = {"field": "mentions", "value": {"mention_data": "test"}}
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_page_change(change, entry, event_info)
        
        assert result["processed"] is True
        mock_mention_event.assert_called_once()
    
    async def test_process_page_change_unhandled_field(self):
        """Test page change processing for unhandled field"""
        change = {"field": "unknown_field", "value": {}}
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_page_change(change, entry, event_info)
        
        assert result["processed"] is False
        assert result["reason"] == "unhandled_field"
        assert result["field"] == "unknown_field"
    
    async def test_process_page_change_error_handling(self):
        """Test page change processing error handling"""
        change = None  # This will cause an error
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_page_change(change, entry, event_info)
        
        assert result["processed"] is False
        assert "error" in result

    async def test_process_messaging_event_success(self):
        """Test successful messaging event processing"""
        message = {
            "sender": {"id": "user_456"},
            "recipient": {"id": "page_123"},
            "message": {"text": "Hello world"}
        }
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_messaging_event(message, entry, event_info)
        
        assert result["processed"] is True
        assert result["event_type"] == "messaging"
        assert result["sender_id"] == "user_456"
        assert result["recipient_id"] == "page_123"
        assert result["has_text"] is True
    
    async def test_process_messaging_event_no_text(self):
        """Test messaging event processing without text"""
        message = {
            "sender": {"id": "user_456"},
            "recipient": {"id": "page_123"},
            "message": {}  # No text
        }
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_messaging_event(message, entry, event_info)
        
        assert result["processed"] is True
        assert result["has_text"] is False

    async def test_process_feed_event_success(self):
        """Test successful feed event processing"""
        value = {
            "verb": "add",
            "item": "post", 
            "post_id": "post_123"
        }
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_feed_event(value, entry, event_info)
        
        assert result["processed"] is True
        assert result["event_type"] == "feed"
        assert result["verb"] == "add"
        assert result["item"] == "post"
        assert result["post_id"] == "post_123"
    
    async def test_process_mention_event_success(self):
        """Test successful mention event processing"""
        value = {"mention_data": "test_mention"}
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_mention_event(value, entry, event_info)
        
        assert result["processed"] is True
        assert result["event_type"] == "mention"
        assert result["mention_data"] == value
    
    async def test_process_messaging_change_success(self):
        """Test successful messaging change processing"""
        value = {"change_data": "test_change"}
        entry = {"entry_id": "page_123"}
        event_info = {"webhook_id": "test"}
        
        result = await _process_messaging_change(value, entry, event_info)
        
        assert result["processed"] is True
        assert result["event_type"] == "messaging_change"
        assert result["change_data"] == value


class TestErrorHandling:
    """Test error handling utilities"""
    
    def test_is_retryable_error_connection_error(self):
        """Test retryable error detection for connection errors"""
        error = ConnectionError("Network connection failed")
        assert _is_retryable_error(error) is True
    
    def test_is_retryable_error_timeout(self):
        """Test retryable error detection for timeout errors"""
        error = TimeoutError("Request timed out")
        assert _is_retryable_error(error) is True
    
    def test_is_retryable_error_http_status(self):
        """Test retryable error detection for HTTP status errors"""
        error = Exception("Service returned 503 status")
        assert _is_retryable_error(error) is True
        
        error = Exception("Rate limit exceeded")
        assert _is_retryable_error(error) is True
    
    def test_is_retryable_error_non_retryable(self):
        """Test non-retryable error detection"""
        error = ValueError("Invalid input data")
        assert _is_retryable_error(error) is False
        
        error = Exception("Permanent failure")
        assert _is_retryable_error(error) is False

    async def test_send_to_dlq_success(self):
        """Test successful DLQ entry creation"""
        entry = {"id": "page_123", "changes": []}
        event_info = {"entry_id": "page_123", "webhook_id": "test"}
        error = "Processing failed"
        retries = 3
        
        result = await _send_to_dlq(entry, event_info, error, retries)
        
        assert result is True
    
    async def test_send_to_dlq_exception(self):
        """Test DLQ entry creation with exception"""
        with patch('backend.tasks.webhook_tasks.json.dumps', side_effect=Exception("JSON error")):
            result = await _send_to_dlq({}, {}, "error", 0)
            assert result is False


class TestWatchdogScan:
    """Test webhook watchdog scan task"""
    
    def test_watchdog_scan_success(self):
        """Test successful watchdog scan"""
        result = watchdog_scan()
        
        assert result["status"] == "completed"
        assert result["dlq_entries_found"] == 0
        assert result["entries_reprocessed"] == 0
        assert result["alerts_sent"] == 0
        assert "scan_time" in result
    
    @patch('backend.tasks.webhook_tasks.datetime')
    def test_watchdog_scan_with_exception(self, mock_datetime):
        """Test watchdog scan with exception"""
        mock_datetime.now.side_effect = Exception("Scan error")
        
        result = watchdog_scan()
        
        assert result["status"] == "failed"
        assert "error" in result
        assert "scan_time" in result


class TestCeleryConfiguration:
    """Test Celery task configuration"""
    
    def test_task_routing_configuration(self):
        """Test that task routing is properly configured"""
        from backend.tasks.webhook_tasks import celery_app
        
        routes = celery_app.conf.task_routes
        assert 'backend.tasks.webhook_tasks.process_meta_event' in routes
        assert 'backend.tasks.webhook_tasks.watchdog_scan' in routes
        
        # Check queue assignments
        assert routes['backend.tasks.webhook_tasks.process_meta_event']['queue'] == 'webhook_processing'
        assert routes['backend.tasks.webhook_tasks.watchdog_scan']['queue'] == 'webhook_watchdog'
    
    def test_retry_configuration(self):
        """Test Celery retry configuration"""
        from backend.tasks.webhook_tasks import celery_app, DLQ_MAX_RETRIES, DLQ_RETRY_DELAYS
        
        assert celery_app.conf.task_default_retry_delay == 60
        assert celery_app.conf.task_max_retries == 5
        assert DLQ_MAX_RETRIES == 5
        assert len(DLQ_RETRY_DELAYS) == 5
        assert DLQ_RETRY_DELAYS == [60, 300, 900, 3600, 14400]  # Exponential backoff
    
    def test_time_limit_configuration(self):
        """Test Celery time limit configuration"""
        from backend.tasks.webhook_tasks import celery_app
        
        assert celery_app.conf.task_soft_time_limit == 300  # 5 minutes
        assert celery_app.conf.task_time_limit == 600       # 10 minutes