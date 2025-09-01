"""
Unit tests for webhook watchdog service
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from backend.tasks.webhook_watchdog import (
    WebhookWatchdog,
    get_webhook_watchdog,
    DLQEntry,
    DLQStatus
)


class TestDLQEntry:
    """Test DLQ entry data structure"""
    
    def test_dlq_entry_creation(self):
        """Test DLQ entry creation and default values"""
        failed_at = datetime.now(timezone.utc)
        
        entry = DLQEntry(
            id="test_123",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_456"},
            error="Processing failed",
            retries_attempted=2,
            failed_at=failed_at
        )
        
        assert entry.id == "test_123"
        assert entry.original_entry == {"id": "page_123"}
        assert entry.error == "Processing failed"
        assert entry.retries_attempted == 2
        assert entry.failed_at == failed_at
        assert entry.last_retry_at is None
        assert entry.status == DLQStatus.PENDING
        assert entry.expiry_date is None
    
    def test_dlq_entry_to_dict(self):
        """Test DLQ entry dictionary conversion"""
        failed_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        entry = DLQEntry(
            id="test_123",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_456"},
            error="Processing failed",
            retries_attempted=2,
            failed_at=failed_at,
            status=DLQStatus.RETRYING
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["id"] == "test_123"
        assert entry_dict["error"] == "Processing failed"
        assert entry_dict["retries_attempted"] == 2
        assert entry_dict["failed_at"] == "2025-01-01T12:00:00+00:00"
        assert entry_dict["status"] == "retrying"
        assert entry_dict["last_retry_at"] is None


class TestWebhookWatchdog:
    """Test webhook watchdog functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        return MagicMock()
    
    @pytest.fixture
    def watchdog(self, mock_settings):
        """Create webhook watchdog with mock settings"""
        return WebhookWatchdog(settings=mock_settings)
    
    def test_init_with_settings(self, mock_settings):
        """Test watchdog initialization with provided settings"""
        watchdog = WebhookWatchdog(settings=mock_settings)
        assert watchdog.settings == mock_settings
        assert watchdog.dlq_retention_days == 30
        assert watchdog.max_watchdog_retries == 3
        assert len(watchdog.watchdog_retry_delays) == 3
    
    @patch('backend.tasks.webhook_watchdog.get_settings')
    def test_init_without_settings(self, mock_get_settings):
        """Test watchdog initialization without provided settings"""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        watchdog = WebhookWatchdog()
        assert watchdog.settings == mock_settings
    
    async def test_scan_dlq_empty(self, watchdog):
        """Test DLQ scan with no entries"""
        with patch.object(watchdog, '_get_dlq_entries', return_value=[]):
            with patch.object(watchdog, '_cleanup_expired_entries', return_value=0):
                result = await watchdog.scan_dlq()
        
        assert result["total_entries"] == 0
        assert result["actions_taken"]["retried"] == 0
        assert result["actions_taken"]["marked_failed"] == 0
        assert result["actions_taken"]["expired"] == 0
        assert "scan_time" in result
        assert "scan_duration_seconds" in result
    
    async def test_scan_dlq_with_entries(self, watchdog):
        """Test DLQ scan with entries"""
        # Create test entries
        entry1 = DLQEntry(
            id="test_1",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Error 1",
            retries_attempted=0,
            failed_at=datetime.now(timezone.utc),
            status=DLQStatus.PENDING
        )
        
        entry2 = DLQEntry(
            id="test_2",
            original_entry={"id": "page_456"},
            event_info={"webhook_id": "hook_2"},
            error="Error 2",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc),
            status=DLQStatus.RETRYING
        )
        
        entries = [entry1, entry2]
        
        with patch.object(watchdog, '_get_dlq_entries', return_value=entries):
            with patch.object(watchdog, '_process_dlq_entry') as mock_process:
                with patch.object(watchdog, '_check_system_alerts', return_value=[]):
                    with patch.object(watchdog, '_cleanup_expired_entries', return_value=1):
                        mock_process.side_effect = [
                            {"action": "retried", "entry_id": "test_1"},
                            {"action": "marked_failed", "entry_id": "test_2"}
                        ]
                        
                        result = await watchdog.scan_dlq()
        
        assert result["total_entries"] == 2
        assert result["entries_by_status"]["pending"] == 1
        assert result["entries_by_status"]["retrying"] == 1
        assert result["actions_taken"]["retried"] == 1
        assert result["actions_taken"]["marked_failed"] == 1
        assert mock_process.call_count == 2
    
    async def test_scan_dlq_exception(self, watchdog):
        """Test DLQ scan with exception"""
        with patch.object(watchdog, '_get_dlq_entries', side_effect=Exception("Scan error")):
            result = await watchdog.scan_dlq()
        
        assert result["status"] == "failed"
        assert "error" in result

    async def test_get_dlq_entries_placeholder(self, watchdog):
        """Test DLQ entries retrieval (placeholder implementation)"""
        entries = await watchdog._get_dlq_entries()
        assert entries == []
    
    async def test_get_dlq_entries_exception(self, watchdog):
        """Test DLQ entries retrieval with exception"""
        with patch.object(watchdog, '_get_dlq_entries', side_effect=Exception("Storage error")):
            entries = await watchdog._get_dlq_entries()
            assert entries == []

    async def test_process_dlq_entry_expired(self, watchdog):
        """Test processing expired DLQ entry"""
        expired_time = datetime.now(timezone.utc) - timedelta(days=1)
        entry = DLQEntry(
            id="test_expired",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Old error",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc),
            expiry_date=expired_time
        )
        
        with patch.object(watchdog, '_update_dlq_entry', return_value=True):
            result = await watchdog._process_dlq_entry(entry)
        
        assert result["action"] == "expired"
        assert result["entry_id"] == "test_expired"
        assert entry.status == DLQStatus.EXPIRED
    
    async def test_process_dlq_entry_already_resolved(self, watchdog):
        """Test processing already resolved DLQ entry"""
        entry = DLQEntry(
            id="test_resolved",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Already resolved",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc),
            status=DLQStatus.RESOLVED
        )
        
        result = await watchdog._process_dlq_entry(entry)
        
        assert result["action"] == "skipped"
        assert result["status"] == "resolved"
    
    async def test_process_dlq_entry_retry_success(self, watchdog):
        """Test processing DLQ entry with successful retry"""
        entry = DLQEntry(
            id="test_retry",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Retryable error",
            retries_attempted=0,
            failed_at=datetime.now(timezone.utc) - timedelta(hours=2),  # Old enough to retry
            status=DLQStatus.PENDING
        )
        
        with patch.object(watchdog, '_should_retry_entry', return_value=True):
            with patch.object(watchdog, '_retry_dlq_entry', return_value={"success": True}):
                with patch.object(watchdog, '_update_dlq_entry', return_value=True):
                    result = await watchdog._process_dlq_entry(entry)
        
        assert result["action"] == "retried"
        assert result["success"] is True
        assert entry.status == DLQStatus.RESOLVED
    
    async def test_process_dlq_entry_retry_failure_max_retries(self, watchdog):
        """Test processing DLQ entry with failed retry and max retries reached"""
        entry = DLQEntry(
            id="test_max_retry",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Persistent error",
            retries_attempted=2,  # Below max but will be incremented
            failed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            status=DLQStatus.RETRYING
        )
        
        with patch.object(watchdog, '_should_retry_entry', return_value=True):
            with patch.object(watchdog, '_retry_dlq_entry', return_value={"success": False}):
                with patch.object(watchdog, '_create_permanent_failure_alert') as mock_alert:
                    with patch.object(watchdog, '_update_dlq_entry', return_value=True):
                        mock_alert.return_value = {"type": "permanent_failure"}
                        
                        result = await watchdog._process_dlq_entry(entry)
        
        assert result["action"] == "marked_failed"
        assert "alert" in result
        assert entry.status == DLQStatus.FAILED_PERMANENT
        assert entry.retries_attempted == 3  # Should be incremented
    
    async def test_process_dlq_entry_old_unresolved(self, watchdog):
        """Test processing old unresolved DLQ entry"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)  # Older than 24h threshold
        entry = DLQEntry(
            id="test_old",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Old error",
            retries_attempted=3,  # Max retries reached
            failed_at=old_time,
            status=DLQStatus.PENDING
        )
        
        with patch.object(watchdog, '_should_retry_entry', return_value=False):  # No more retries
            with patch.object(watchdog, '_create_old_entry_alert') as mock_alert:
                mock_alert.return_value = {"type": "old_unresolved"}
                
                result = await watchdog._process_dlq_entry(entry)
        
        assert result["action"] == "alerted"
        assert "alert" in result

    def test_should_retry_entry_max_retries(self, watchdog):
        """Test retry decision when max retries reached"""
        entry = DLQEntry(
            id="test",
            original_entry={},
            event_info={},
            error="error",
            retries_attempted=3,  # At max
            failed_at=datetime.now(timezone.utc)
        )
        
        should_retry = watchdog._should_retry_entry(entry, datetime.now(timezone.utc))
        assert should_retry is False
    
    def test_should_retry_entry_failed_permanent(self, watchdog):
        """Test retry decision for permanently failed entry"""
        entry = DLQEntry(
            id="test",
            original_entry={},
            event_info={},
            error="error",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc),
            status=DLQStatus.FAILED_PERMANENT
        )
        
        should_retry = watchdog._should_retry_entry(entry, datetime.now(timezone.utc))
        assert should_retry is False
    
    def test_should_retry_entry_delay_not_met(self, watchdog):
        """Test retry decision when delay not met"""
        now = datetime.now(timezone.utc)
        recent_retry = now - timedelta(minutes=30)  # Too recent (delay is 1 hour)
        
        entry = DLQEntry(
            id="test",
            original_entry={},
            event_info={},
            error="error",
            retries_attempted=0,
            failed_at=now - timedelta(hours=2),
            last_retry_at=recent_retry
        )
        
        should_retry = watchdog._should_retry_entry(entry, now)
        assert should_retry is False
    
    def test_should_retry_entry_ready_for_retry(self, watchdog):
        """Test retry decision when entry is ready for retry"""
        now = datetime.now(timezone.utc)
        old_retry = now - timedelta(hours=2)  # Old enough
        
        entry = DLQEntry(
            id="test",
            original_entry={},
            event_info={},
            error="error",
            retries_attempted=1,
            failed_at=now - timedelta(hours=3),
            last_retry_at=old_retry,
            status=DLQStatus.RETRYING
        )
        
        should_retry = watchdog._should_retry_entry(entry, now)
        assert should_retry is True

    @patch('backend.tasks.webhook_watchdog.process_meta_event')
    async def test_retry_dlq_entry_success(self, mock_process_task, watchdog):
        """Test successful DLQ entry retry"""
        mock_task = MagicMock()
        mock_task.id = "retry_task_123"
        mock_process_task.delay.return_value = mock_task
        
        entry = DLQEntry(
            id="test_retry",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Retryable error",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc)
        )
        
        result = await watchdog._retry_dlq_entry(entry)
        
        assert result["success"] is True
        assert result["task_id"] == "retry_task_123"
        assert result["retry_attempt"] == 2  # retries_attempted + 1
        mock_process_task.delay.assert_called_once_with(entry.original_entry, entry.event_info)
    
    @patch('backend.tasks.webhook_watchdog.process_meta_event')
    async def test_retry_dlq_entry_failure(self, mock_process_task, watchdog):
        """Test failed DLQ entry retry"""
        mock_process_task.delay.side_effect = Exception("Celery error")
        
        entry = DLQEntry(
            id="test_retry_fail",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Retryable error",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc)
        )
        
        result = await watchdog._retry_dlq_entry(entry)
        
        assert result["success"] is False
        assert "error" in result

    async def test_check_system_alerts_large_dlq(self, watchdog):
        """Test system alert for large DLQ size"""
        # Create enough entries to trigger large DLQ alert
        entries = []
        for i in range(101):  # Threshold is 100
            entry = DLQEntry(
                id=f"test_{i}",
                original_entry={"id": f"page_{i}"},
                event_info={"webhook_id": f"hook_{i}"},
                error=f"Error {i}",
                retries_attempted=0,
                failed_at=datetime.now(timezone.utc)
            )
            entries.append(entry)
        
        alerts = await watchdog._check_system_alerts(entries)
        
        assert len(alerts) == 1
        assert alerts[0]["type"] == "large_dlq_size"
        assert alerts[0]["severity"] == "warning"
        assert alerts[0]["dlq_size"] == 101
    
    async def test_check_system_alerts_exception(self, watchdog):
        """Test system alerts check with exception"""
        with patch('backend.tasks.webhook_watchdog.len', side_effect=Exception("Alert error")):
            alerts = await watchdog._check_system_alerts([])
            assert alerts == []

    def test_create_permanent_failure_alert(self, watchdog):
        """Test permanent failure alert creation"""
        failed_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        entry = DLQEntry(
            id="test_perm_fail",
            original_entry={"id": "page_123"},
            event_info={"object": "page", "webhook_id": "hook_1"},
            error="Permanent error",
            retries_attempted=3,
            failed_at=failed_time
        )
        
        alert = watchdog._create_permanent_failure_alert(entry)
        
        assert alert["type"] == "permanent_failure"
        assert alert["severity"] == "error"
        assert alert["entry_id"] == "test_perm_fail"
        assert alert["platform"] == "page"
        assert alert["failed_at"] == "2025-01-01T12:00:00+00:00"
        assert alert["error"] == "Permanent error"
    
    def test_create_old_entry_alert(self, watchdog):
        """Test old entry alert creation"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=36)  # 36 hours old
        entry = DLQEntry(
            id="test_old_entry",
            original_entry={"id": "page_123"},
            event_info={"webhook_id": "hook_1"},
            error="Old error",
            retries_attempted=2,
            failed_at=old_time
        )
        
        alert = watchdog._create_old_entry_alert(entry)
        
        assert alert["type"] == "old_unresolved"
        assert alert["severity"] == "warning"
        assert alert["entry_id"] == "test_old_entry"
        assert alert["hours_old"] == 36.0
    
    async def test_update_dlq_entry_success(self, watchdog):
        """Test successful DLQ entry update (placeholder implementation)"""
        entry = DLQEntry(
            id="test_update",
            original_entry={},
            event_info={},
            error="error",
            retries_attempted=1,
            failed_at=datetime.now(timezone.utc),
            status=DLQStatus.RETRYING
        )
        
        result = await watchdog._update_dlq_entry(entry)
        assert result is True
    
    async def test_cleanup_expired_entries(self, watchdog):
        """Test expired entries cleanup (placeholder implementation)"""
        count = await watchdog._cleanup_expired_entries()
        assert count == 0


class TestWebhookWatchdogSingleton:
    """Test webhook watchdog singleton functionality"""
    
    @patch('backend.tasks.webhook_watchdog.get_settings')
    def test_get_webhook_watchdog_singleton(self, mock_get_settings):
        """Test that get_webhook_watchdog returns singleton"""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Reset singleton
        import backend.tasks.webhook_watchdog
        backend.tasks.webhook_watchdog._webhook_watchdog = None
        
        watchdog1 = get_webhook_watchdog()
        watchdog2 = get_webhook_watchdog()
        
        assert watchdog1 is watchdog2
        mock_get_settings.assert_called_once()
    
    def test_get_webhook_watchdog_with_settings(self):
        """Test get_webhook_watchdog with provided settings"""
        settings = MagicMock()
        
        # Reset singleton
        import backend.tasks.webhook_watchdog
        backend.tasks.webhook_watchdog._webhook_watchdog = None
        
        watchdog = get_webhook_watchdog(settings=settings)
        assert watchdog.settings == settings


class TestDLQStatus:
    """Test DLQ status enumeration"""
    
    def test_dlq_status_values(self):
        """Test DLQ status enumeration values"""
        assert DLQStatus.PENDING.value == "pending"
        assert DLQStatus.RETRYING.value == "retrying"
        assert DLQStatus.FAILED_PERMANENT.value == "failed_permanent"
        assert DLQStatus.RESOLVED.value == "resolved"
        assert DLQStatus.EXPIRED.value == "expired"