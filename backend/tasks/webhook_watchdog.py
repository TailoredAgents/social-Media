"""
Webhook Watchdog Service
Monitors failed webhook processing tasks and provides alerting/retry mechanisms
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class DLQStatus(Enum):
    """Dead Letter Queue entry status"""
    PENDING = "pending"
    RETRYING = "retrying"  
    FAILED_PERMANENT = "failed_permanent"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class DLQEntry:
    """Dead Letter Queue entry"""
    id: str
    original_entry: Dict[str, Any]
    event_info: Dict[str, Any]
    error: str
    retries_attempted: int
    failed_at: datetime
    last_retry_at: Optional[datetime] = None
    status: DLQStatus = DLQStatus.PENDING
    expiry_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "original_entry": self.original_entry,
            "event_info": self.event_info,
            "error": self.error,
            "retries_attempted": self.retries_attempted,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "last_retry_at": self.last_retry_at.isoformat() if self.last_retry_at else None,
            "status": self.status.value,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None
        }


class WebhookWatchdog:
    """
    Webhook watchdog service for monitoring and managing failed webhook processing
    """
    
    def __init__(self, settings=None):
        """
        Initialize webhook watchdog
        
        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()
        
        # Watchdog configuration
        self.dlq_retention_days = 30  # Keep DLQ entries for 30 days
        self.max_watchdog_retries = 3  # Additional retries by watchdog
        self.watchdog_retry_delays = [3600, 7200, 14400]  # 1h, 2h, 4h
        self.alert_thresholds = {
            "high_failure_rate": 0.1,  # Alert if >10% of events fail
            "large_dlq_size": 100,     # Alert if DLQ has >100 entries
            "old_unresolved": 24       # Alert if entries unresolved for >24h
        }
        
    async def scan_dlq(self) -> Dict[str, Any]:
        """
        Scan Dead Letter Queue and process entries
        
        Returns:
            Scan results with statistics and actions taken
        """
        try:
            scan_start = datetime.now(timezone.utc)
            logger.info("Starting webhook DLQ scan")
            
            # Get all DLQ entries
            entries = await self._get_dlq_entries()
            
            scan_results = {
                "scan_time": scan_start.isoformat(),
                "total_entries": len(entries),
                "entries_by_status": {},
                "actions_taken": {
                    "retried": 0,
                    "marked_failed": 0,
                    "expired": 0,
                    "alerts_sent": 0
                },
                "alerts": []
            }
            
            # Group entries by status
            for entry in entries:
                status = entry.status.value
                scan_results["entries_by_status"][status] = scan_results["entries_by_status"].get(status, 0) + 1
            
            # Process each entry
            for entry in entries:
                action_result = await self._process_dlq_entry(entry)
                
                # Update action counters
                action = action_result.get("action")
                if action in scan_results["actions_taken"]:
                    scan_results["actions_taken"][action] += 1
                
                # Collect any alerts
                if action_result.get("alert"):
                    scan_results["alerts"].append(action_result["alert"])
            
            # Check for system-wide alerts
            system_alerts = await self._check_system_alerts(entries)
            scan_results["alerts"].extend(system_alerts)
            scan_results["actions_taken"]["alerts_sent"] = len(scan_results["alerts"])
            
            # Clean up expired entries
            expired_count = await self._cleanup_expired_entries()
            scan_results["actions_taken"]["expired"] = expired_count
            
            scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
            scan_results["scan_duration_seconds"] = scan_duration
            
            logger.info(f"Webhook DLQ scan completed: {scan_results}")
            
            return scan_results
            
        except Exception as e:
            logger.error(f"Webhook DLQ scan failed: {e}")
            return {
                "scan_time": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e)
            }
    
    async def _get_dlq_entries(self) -> List[DLQEntry]:
        """
        Get all DLQ entries from storage
        
        Returns:
            List of DLQ entries
        """
        try:
            # TODO: Implement actual DLQ storage retrieval
            # This could be from Redis, database, or file system
            # For now, return empty list as placeholder
            
            entries = []
            
            # Example of how entries might be loaded:
            # entries = await self._load_from_redis()
            # or
            # entries = await self._load_from_database()
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to load DLQ entries: {e}")
            return []
    
    async def _process_dlq_entry(self, entry: DLQEntry) -> Dict[str, Any]:
        """
        Process a single DLQ entry
        
        Args:
            entry: DLQ entry to process
            
        Returns:
            Processing result with action taken
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Check if entry has expired
            if entry.expiry_date and now > entry.expiry_date:
                entry.status = DLQStatus.EXPIRED
                await self._update_dlq_entry(entry)
                return {"action": "expired", "entry_id": entry.id}
            
            # Check if entry is already resolved or permanently failed
            if entry.status in [DLQStatus.RESOLVED, DLQStatus.FAILED_PERMANENT, DLQStatus.EXPIRED]:
                return {"action": "skipped", "entry_id": entry.id, "status": entry.status.value}
            
            # Determine if we should retry this entry
            should_retry = await self._should_retry_entry(entry, now)
            
            if should_retry:
                retry_result = await self._retry_dlq_entry(entry)
                
                if retry_result["success"]:
                    entry.status = DLQStatus.RESOLVED
                    entry.last_retry_at = now
                    await self._update_dlq_entry(entry)
                    return {"action": "retried", "entry_id": entry.id, "success": True}
                else:
                    entry.retries_attempted += 1
                    entry.last_retry_at = now
                    
                    # Check if we've exhausted watchdog retries
                    if entry.retries_attempted >= self.max_watchdog_retries:
                        entry.status = DLQStatus.FAILED_PERMANENT
                        alert = await self._create_permanent_failure_alert(entry)
                        await self._update_dlq_entry(entry)
                        return {
                            "action": "marked_failed", 
                            "entry_id": entry.id,
                            "alert": alert
                        }
                    else:
                        entry.status = DLQStatus.RETRYING
                        await self._update_dlq_entry(entry)
                        return {"action": "retried", "entry_id": entry.id, "success": False}
            
            # Check if entry needs alerting (old unresolved entries)
            hours_since_failed = (now - entry.failed_at).total_seconds() / 3600
            if hours_since_failed > self.alert_thresholds["old_unresolved"]:
                alert = await self._create_old_entry_alert(entry)
                return {"action": "alerted", "entry_id": entry.id, "alert": alert}
            
            return {"action": "no_action", "entry_id": entry.id}
            
        except Exception as e:
            logger.error(f"Error processing DLQ entry {entry.id}: {e}")
            return {"action": "error", "entry_id": entry.id, "error": str(e)}
    
    async def _should_retry_entry(self, entry: DLQEntry, now: datetime) -> bool:
        """
        Determine if a DLQ entry should be retried
        
        Args:
            entry: DLQ entry
            now: Current timestamp
            
        Returns:
            True if entry should be retried, False otherwise
        """
        # Don't retry if already at max retries
        if entry.retries_attempted >= self.max_watchdog_retries:
            return False
        
        # Don't retry if status indicates shouldn't retry
        if entry.status in [DLQStatus.FAILED_PERMANENT, DLQStatus.EXPIRED]:
            return False
        
        # Check retry delay
        if entry.last_retry_at:
            required_delay = self.watchdog_retry_delays[
                min(entry.retries_attempted, len(self.watchdog_retry_delays) - 1)
            ]
            time_since_retry = (now - entry.last_retry_at).total_seconds()
            
            if time_since_retry < required_delay:
                return False
        
        return True
    
    async def _retry_dlq_entry(self, entry: DLQEntry) -> Dict[str, Any]:
        """
        Attempt to retry processing a DLQ entry
        
        Args:
            entry: DLQ entry to retry
            
        Returns:
            Retry result
        """
        try:
            # Import here to avoid circular imports
            from backend.tasks.webhook_tasks import process_meta_event
            
            # Resubmit to Celery for processing
            task = process_meta_event.delay(entry.original_entry, entry.event_info)
            
            logger.info(f"Resubmitted DLQ entry {entry.id} as task {task.id}")
            
            return {
                "success": True,
                "task_id": task.id,
                "retry_attempt": entry.retries_attempted + 1
            }
            
        except Exception as e:
            logger.error(f"Failed to retry DLQ entry {entry.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "retry_attempt": entry.retries_attempted + 1
            }
    
    async def _check_system_alerts(self, entries: List[DLQEntry]) -> List[Dict[str, Any]]:
        """
        Check for system-wide alert conditions
        
        Args:
            entries: All DLQ entries
            
        Returns:
            List of system alerts
        """
        alerts = []
        
        try:
            # Alert on large DLQ size
            if len(entries) > self.alert_thresholds["large_dlq_size"]:
                alerts.append({
                    "type": "large_dlq_size",
                    "message": f"DLQ has {len(entries)} entries (threshold: {self.alert_thresholds['large_dlq_size']})",
                    "severity": "warning",
                    "dlq_size": len(entries)
                })
            
            # Alert on high failure rate (requires metrics from last 24h)
            # TODO: Implement failure rate calculation
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking system alerts: {e}")
            return []
    
    async def _create_permanent_failure_alert(self, entry: DLQEntry) -> Dict[str, Any]:
        """
        Create alert for permanently failed entry
        
        Args:
            entry: DLQ entry that failed permanently
            
        Returns:
            Alert data
        """
        return {
            "type": "permanent_failure",
            "message": f"Webhook entry {entry.id} failed permanently after {entry.retries_attempted} retries",
            "severity": "error",
            "entry_id": entry.id,
            "platform": entry.event_info.get("object", "unknown"),
            "failed_at": entry.failed_at.isoformat(),
            "error": entry.error
        }
    
    async def _create_old_entry_alert(self, entry: DLQEntry) -> Dict[str, Any]:
        """
        Create alert for old unresolved entry
        
        Args:
            entry: DLQ entry that's been unresolved for too long
            
        Returns:
            Alert data
        """
        hours_old = (datetime.now(timezone.utc) - entry.failed_at).total_seconds() / 3600
        
        return {
            "type": "old_unresolved",
            "message": f"Webhook entry {entry.id} unresolved for {hours_old:.1f} hours",
            "severity": "warning",
            "entry_id": entry.id,
            "hours_old": hours_old,
            "failed_at": entry.failed_at.isoformat()
        }
    
    async def _update_dlq_entry(self, entry: DLQEntry) -> bool:
        """
        Update DLQ entry in storage
        
        Args:
            entry: DLQ entry to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO: Implement actual DLQ storage update
            # This could be Redis, database, etc.
            
            logger.debug(f"Updated DLQ entry {entry.id}: status={entry.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update DLQ entry {entry.id}: {e}")
            return False
    
    async def _cleanup_expired_entries(self) -> int:
        """
        Remove expired DLQ entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            # TODO: Implement actual cleanup from storage
            
            cleanup_count = 0
            logger.info(f"Cleaned up {cleanup_count} expired DLQ entries")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired DLQ entries: {e}")
            return 0


# Singleton instance
_webhook_watchdog = None


def get_webhook_watchdog(settings=None) -> WebhookWatchdog:
    """
    Get webhook watchdog instance
    
    Args:
        settings: Application settings
        
    Returns:
        WebhookWatchdog instance
    """
    global _webhook_watchdog
    
    if _webhook_watchdog is None:
        _webhook_watchdog = WebhookWatchdog(settings)
    
    return _webhook_watchdog