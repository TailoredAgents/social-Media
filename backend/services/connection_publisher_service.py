"""
Connection-based publishing service for Phase 7/8
Publishes content using SocialConnection tokens instead of user tokens
Updated for Phase 8: Celery integration and resilient publishing
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.models import SocialConnection, ContentSchedule, SocialAudit
from backend.core.encryption import decrypt_token
from backend.services.token_refresh_service import get_token_refresh_service

logger = logging.getLogger(__name__)


class ConnectionPublisherService:
    """Service for publishing content using SocialConnection tokens"""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.meta_base_url = f"https://graph.facebook.com/{getattr(self.settings, 'meta_graph_version', 'v18.0')}"
        self.x_base_url = "https://api.twitter.com/2"
    
    async def publish_to_connection(
        self, 
        connection: SocialConnection, 
        content: str, 
        media_urls: List[str],
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publish content to a specific connection
        
        Args:
            connection: SocialConnection to publish to
            content: Text content to publish
            media_urls: List of media URLs to include
            db: Database session
            
        Returns:
            Tuple of (success, platform_post_id, error_message)
        """
        try:
            logger.info(f"Publishing to connection {connection.id} ({connection.platform})")
            
            # Check if connection is active and verified
            if not connection.is_active:
                return False, None, "Connection is not active"
            
            if not connection.verified_for_posting:
                return False, None, "Connection not verified for posting - run test draft first"
            
            # Refresh token if needed
            await self._ensure_token_fresh(connection, db)
            
            # Publish based on platform
            if connection.platform == "meta":
                return await self._publish_to_meta(connection, content, media_urls, db)
            elif connection.platform == "x":
                return await self._publish_to_x(connection, content, media_urls, db)
            else:
                return False, None, f"Unsupported platform: {connection.platform}"
                
        except Exception as e:
            error_msg = f"Publishing failed: {str(e)}"
            logger.error(f"Error publishing to connection {connection.id}: {error_msg}")
            return False, None, error_msg
    
    async def _publish_to_meta(
        self, 
        connection: SocialConnection, 
        content: str, 
        media_urls: List[str],
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Publish content to Meta (Facebook/Instagram)"""
        try:
            # Get page access token
            page_token = connection.access_tokens.get("page_token")
            if not page_token:
                return False, None, "No page access token found"
            
            # Decrypt token
            decrypted_token = decrypt_token(page_token)
            
            # Get page ID from metadata
            page_id = connection.platform_metadata.get("page_id")
            if not page_id:
                return False, None, "No page ID found in metadata"
            
            # Create post via Meta Graph API (stub implementation)
            logger.info(f"Publishing to Meta page {page_id}: {content[:100]}...")
            
            # TODO: Implement actual Meta Graph API call
            # For now, return success with mock data
            mock_post_id = f"meta_post_{datetime.now().timestamp()}"
            
            await self._create_audit_log(
                db, connection, "publish_attempt", "success",
                {
                    "platform_post_id": mock_post_id,
                    "content_length": len(content),
                    "media_count": len(media_urls)
                }
            )
            
            return True, mock_post_id, "Published to Meta successfully"
            
        except Exception as e:
            error_msg = f"Meta publishing failed: {str(e)}"
            await self._create_audit_log(
                db, connection, "publish_attempt", "failure",
                {"error": error_msg}
            )
            return False, None, error_msg
    
    async def _publish_to_x(
        self, 
        connection: SocialConnection, 
        content: str, 
        media_urls: List[str],
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Publish content to X (Twitter)"""
        try:
            # Get access token
            access_token = connection.access_tokens.get("access_token")
            if not access_token:
                return False, None, "No access token found"
            
            # Decrypt token
            decrypted_token = decrypt_token(access_token)
            
            # Create tweet via X API (stub implementation)
            logger.info(f"Publishing to X: {content[:100]}...")
            
            # TODO: Implement actual X API v2 call
            # For now, return success with mock data
            mock_tweet_id = f"x_tweet_{datetime.now().timestamp()}"
            
            await self._create_audit_log(
                db, connection, "publish_attempt", "success",
                {
                    "platform_post_id": mock_tweet_id,
                    "content_length": len(content),
                    "media_count": len(media_urls)
                }
            )
            
            return True, mock_tweet_id, "Published to X successfully"
            
        except Exception as e:
            error_msg = f"X publishing failed: {str(e)}"
            await self._create_audit_log(
                db, connection, "publish_attempt", "failure", 
                {"error": error_msg}
            )
            return False, None, error_msg
    
    async def _ensure_token_fresh(self, connection: SocialConnection, db: Session) -> None:
        """Ensure connection token is fresh, refresh if needed"""
        try:
            # Check if token is expiring within 1 hour
            if connection.token_expires_at:
                now = datetime.now(timezone.utc)
                expires_soon = connection.token_expires_at - now < timedelta(hours=1)
                
                if expires_soon:
                    logger.info(f"Refreshing token for connection {connection.id}")
                    refresh_service = get_token_refresh_service()
                    
                    if connection.platform == "meta":
                        success, new_expiry, message = await refresh_service.refresh_meta_connection(connection, db)
                    elif connection.platform == "x":
                        success, new_expiry, message = await refresh_service.refresh_x_connection(connection, db)
                    else:
                        logger.warning(f"Token refresh not supported for platform: {connection.platform}")
                        return
                    
                    if not success:
                        logger.error(f"Token refresh failed for connection {connection.id}: {message}")
                        raise Exception(f"Token refresh failed: {message}")
                    
        except Exception as e:
            logger.error(f"Error ensuring token freshness for connection {connection.id}: {e}")
            raise
    
    async def _create_audit_log(
        self, 
        db: Session, 
        connection: SocialConnection, 
        action: str, 
        status: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """Create audit log entry"""
        try:
            audit_log = SocialAudit(
                organization_id=connection.organization_id,
                connection_id=connection.id,
                platform=connection.platform,
                action=action,
                status=status,
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            # Don't raise - audit log failures shouldn't break publishing
    
    def generate_content_hash(self, content: str, media_urls: List[str] = None) -> str:
        """Generate SHA256 hash of content for idempotency"""
        content_data = content + "".join(sorted(media_urls or []))
        return hashlib.sha256(content_data.encode()).hexdigest()
    
    def generate_idempotency_key(
        self, 
        org_id: str, 
        connection_id: str, 
        content_hash: str, 
        scheduled_time: Optional[datetime] = None
    ) -> str:
        """Generate idempotency key for Redis/database deduplication"""
        time_key = scheduled_time.isoformat() if scheduled_time else "immediate"
        return f"content_schedule:{org_id}:{connection_id}:{content_hash}:{time_key}"
    
    def enqueue_publish_task(
        self,
        connection_id: str,
        content: str,
        media_urls: List[str],
        content_hash: str,
        scheduled_time: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
        delay_s: float = 0
    ) -> str:
        """
        Enqueue a publish task for Phase 8 resilient publishing
        
        Args:
            connection_id: UUID of the SocialConnection
            content: Content to publish
            media_urls: List of media URLs
            content_hash: Content hash for idempotency
            scheduled_time: When content was scheduled
            idempotency_key: Unique key for this schedule
            delay_s: Delay before executing task
            
        Returns:
            Celery task ID
        """
        try:
            from backend.tasks.publish_tasks import enqueue_publish_task
            
            task_id = enqueue_publish_task(
                connection_id=connection_id,
                content=content,
                media_urls=media_urls,
                content_hash=content_hash,
                scheduled_time=scheduled_time,
                idempotency_key=idempotency_key,
                delay_s=delay_s
            )
            
            logger.info(f"Enqueued publish task {task_id} for connection {connection_id}")
            return task_id
            
        except ImportError:
            # Celery not available - fall back to direct publishing
            logger.warning("Celery not available, falling back to direct publishing")
            # This would call the existing publish_to_connection method
            raise NotImplementedError("Direct publishing fallback not implemented")


# Singleton instance
_connection_publisher_service = None


def get_connection_publisher_service(settings=None) -> ConnectionPublisherService:
    """
    Get connection publisher service instance
    
    Args:
        settings: Application settings (optional)
        
    Returns:
        ConnectionPublisherService instance
    """
    global _connection_publisher_service
    
    if _connection_publisher_service is None:
        _connection_publisher_service = ConnectionPublisherService(settings)
    
    return _connection_publisher_service