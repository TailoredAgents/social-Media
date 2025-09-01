"""
Resilient publish runner for Phase 8
Handles rate limiting, circuit breaking, retries, and metrics logging
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from backend.db.models import SocialConnection, SocialAudit
from backend.services.rate_limit import (
    get_token_bucket, get_circuit_breaker, 
    RetryableError, FatalError, exponential_backoff_with_jitter
)
from backend.services.publisher_adapters.meta_adapter import MetaAdapter
from backend.services.publisher_adapters.x_adapter import XAdapter

logger = logging.getLogger(__name__)


@dataclass
class PublishPayload:
    """Payload for publishing content"""
    content: str
    media_urls: list
    content_hash: str
    scheduled_time: Optional[datetime] = None
    idempotency_key: Optional[str] = None


@dataclass 
class PublishResult:
    """Result of publish attempt"""
    success: bool
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    should_retry: bool = False
    retry_after_s: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class PublishRunner:
    """Resilient publishing pipeline with rate limiting and circuit breaking"""
    
    def __init__(self):
        self.token_bucket = get_token_bucket()
        self.circuit_breaker = get_circuit_breaker()
        self.meta_adapter = MetaAdapter()
        self.x_adapter = XAdapter()
    
    async def run_publish(
        self,
        connection: SocialConnection,
        payload: PublishPayload,
        db: Session,
        attempt: int = 0
    ) -> PublishResult:
        """
        Execute resilient publish with rate limiting and circuit breaking
        
        Args:
            connection: SocialConnection to publish to
            payload: Content payload
            db: Database session
            attempt: Current retry attempt (0-based)
            
        Returns:
            PublishResult with success status and metadata
        """
        org_id = str(connection.organization_id)
        platform = connection.platform
        
        start_time = time.time()
        metrics = {
            'org_id': org_id,
            'platform': platform,
            'connection_id': str(connection.id),
            'attempt': attempt,
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Step 1: Check circuit breaker
            if not self.circuit_breaker.allow(org_id, platform):
                cb_state = self.circuit_breaker.get_state(org_id, platform)
                retry_after = cb_state.get('remaining_cooldown_s', 120)
                
                metrics.update({
                    'result': 'circuit_open',
                    'retry_after_s': retry_after,
                    'circuit_state': cb_state
                })
                
                await self._log_publish_attempt(
                    db, connection, payload, 'circuit_open', metrics
                )
                
                return PublishResult(
                    success=False,
                    error_message=f"Circuit breaker open for {platform}",
                    should_retry=True,
                    retry_after_s=retry_after,
                    metrics=metrics
                )
            
            # Step 2: Check rate limiting
            if not self.token_bucket.acquire(org_id, platform, tokens=1):
                remaining = self.token_bucket.get_remaining(org_id, platform)
                reset_time = self.token_bucket.get_reset_time(org_id, platform)
                retry_after = max(1, reset_time - time.time())
                
                metrics.update({
                    'result': 'rate_limited',
                    'tokens_remaining': remaining,
                    'retry_after_s': retry_after
                })
                
                await self._log_publish_attempt(
                    db, connection, payload, 'rate_limited', metrics
                )
                
                logger.warning(
                    f"Rate limited org {org_id} platform {platform}: "
                    f"{remaining} tokens remaining, retry in {retry_after:.1f}s"
                )
                
                return PublishResult(
                    success=False,
                    error_message=f"Rate limited - {remaining} requests remaining",
                    should_retry=True,
                    retry_after_s=retry_after,
                    metrics=metrics
                )
            
            # Step 3: Attempt actual publishing
            try:
                logger.info(f"Publishing to {platform} for org {org_id}, attempt {attempt + 1}")
                
                if platform == "meta":
                    success, post_id, error = await self.meta_adapter.publish(
                        connection, payload.content, payload.media_urls
                    )
                elif platform == "x":
                    success, post_id, error = await self.x_adapter.publish(
                        connection, payload.content, payload.media_urls
                    )
                else:
                    raise FatalError(f"Unsupported platform: {platform}")
                
                duration = time.time() - start_time
                
                if success:
                    # Record success
                    self.circuit_breaker.record_success(org_id, platform)
                    
                    metrics.update({
                        'result': 'success',
                        'platform_post_id': post_id,
                        'duration_s': duration
                    })
                    
                    await self._log_publish_attempt(
                        db, connection, payload, 'success', metrics, post_id
                    )
                    
                    logger.info(
                        f"Successfully published to {platform} for org {org_id}: {post_id}"
                    )
                    
                    return PublishResult(
                        success=True,
                        platform_post_id=post_id,
                        metrics=metrics
                    )
                else:
                    # Handle failure
                    return await self._handle_publish_failure(
                        connection, payload, error, attempt, metrics, duration, db
                    )
                    
            except RetryableError as e:
                duration = time.time() - start_time
                return await self._handle_publish_failure(
                    connection, payload, str(e), attempt, metrics, duration, db, is_retryable=True
                )
                
            except FatalError as e:
                duration = time.time() - start_time
                return await self._handle_publish_failure(
                    connection, payload, str(e), attempt, metrics, duration, db, is_retryable=False
                )
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Unexpected error in publish runner: {e}")
            
            return await self._handle_publish_failure(
                connection, payload, f"Unexpected error: {str(e)}", 
                attempt, metrics, duration, db, is_retryable=True
            )
    
    async def _handle_publish_failure(
        self,
        connection: SocialConnection,
        payload: PublishPayload,
        error_msg: str,
        attempt: int,
        metrics: Dict[str, Any],
        duration: float,
        db: Session,
        is_retryable: bool = True
    ) -> PublishResult:
        """Handle publish failure with appropriate retry logic"""
        
        org_id = str(connection.organization_id)
        platform = connection.platform
        
        # Record failure in circuit breaker
        self.circuit_breaker.record_failure(org_id, platform)
        
        metrics.update({
            'result': 'failure',
            'error_message': error_msg,
            'duration_s': duration,
            'is_retryable': is_retryable
        })
        
        if is_retryable:
            # Calculate backoff delay
            retry_after = exponential_backoff_with_jitter(attempt)
            metrics['retry_after_s'] = retry_after
            
            await self._log_publish_attempt(
                db, connection, payload, 'failure_retryable', metrics
            )
            
            logger.warning(
                f"Retryable failure for org {org_id} platform {platform}, attempt {attempt + 1}: "
                f"{error_msg}. Retry in {retry_after:.1f}s"
            )
            
            return PublishResult(
                success=False,
                error_message=error_msg,
                should_retry=True,
                retry_after_s=retry_after,
                metrics=metrics
            )
        else:
            await self._log_publish_attempt(
                db, connection, payload, 'failure_fatal', metrics
            )
            
            logger.error(
                f"Fatal failure for org {org_id} platform {platform}: {error_msg}"
            )
            
            return PublishResult(
                success=False,
                error_message=error_msg,
                should_retry=False,
                metrics=metrics
            )
    
    async def _log_publish_attempt(
        self,
        db: Session,
        connection: SocialConnection,
        payload: PublishPayload,
        status: str,
        metrics: Dict[str, Any],
        platform_post_id: Optional[str] = None
    ) -> None:
        """Log publish attempt to audit trail"""
        try:
            # Clean metrics for storage (remove sensitive data)
            audit_metrics = {
                k: v for k, v in metrics.items()
                if k not in ['access_token', 'refresh_token', 'api_key']
            }
            
            # Add content metadata without sensitive content
            audit_metrics.update({
                'content_length': len(payload.content),
                'media_count': len(payload.media_urls),
                'content_hash': payload.content_hash,
                'platform_post_id': platform_post_id
            })
            
            audit_log = SocialAudit(
                organization_id=connection.organization_id,
                connection_id=connection.id,
                platform=connection.platform,
                action='publish_attempt',
                status=status,
                metadata=audit_metrics,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(audit_log)
            db.commit()
            
            # Also log metrics for monitoring
            logger.info(
                f"Publish metrics - org:{metrics['org_id']} "
                f"platform:{metrics['platform']} "
                f"result:{metrics['result']} "
                f"attempt:{metrics['attempt']} "
                f"duration:{metrics.get('duration_s', 0):.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error logging publish attempt: {e}")
            # Don't raise - audit logging shouldn't break the main flow
    
    def get_rate_limit_status(self, org_id: str, platform: str) -> Dict[str, Any]:
        """
        Get current rate limiting status for organization and platform
        
        Args:
            org_id: Organization ID
            platform: Platform name
            
        Returns:
            Dictionary with rate limiting status
        """
        try:
            remaining = self.token_bucket.get_remaining(org_id, platform)
            reset_time = self.token_bucket.get_reset_time(org_id, platform)
            cb_state = self.circuit_breaker.get_state(org_id, platform)
            
            return {
                'rate_limit': {
                    'remaining': remaining,
                    'limit': self.token_bucket.capacity,
                    'reset_time': reset_time,
                    'window_s': self.token_bucket.window_s
                },
                'circuit_breaker': cb_state
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {
                'rate_limit': {
                    'remaining': self.token_bucket.capacity,
                    'limit': self.token_bucket.capacity,
                    'reset_time': time.time(),
                    'window_s': self.token_bucket.window_s
                },
                'circuit_breaker': {
                    'state': 'closed',
                    'failures': 0
                }
            }


# Singleton instance
_publish_runner = None


def get_publish_runner() -> PublishRunner:
    """
    Get publish runner singleton instance
    
    Returns:
        PublishRunner instance
    """
    global _publish_runner
    
    if _publish_runner is None:
        _publish_runner = PublishRunner()
    
    return _publish_runner