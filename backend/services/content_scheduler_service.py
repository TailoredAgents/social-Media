"""
Content scheduling service for Phase 7
Handles scheduling content with connection IDs and draft verification
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.core.config import get_settings
from backend.db.models import (
    SocialConnection, ContentSchedule, ContentDraft, 
    SocialAudit, Organization
)
from backend.services.connection_publisher_service import get_connection_publisher_service

logger = logging.getLogger(__name__)


class ContentSchedulerService:
    """Service for scheduling content with connection-based publishing"""
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.publisher_service = get_connection_publisher_service(settings)
    
    async def create_draft(
        self,
        organization_id: str,
        connection_id: str,
        content: str,
        media_urls: List[str],
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a test draft for connection verification
        
        Args:
            organization_id: Organization ID
            connection_id: Connection ID to create draft for
            content: Content text
            media_urls: List of media URLs
            db: Database session
            
        Returns:
            Tuple of (success, draft_id, error_message)
        """
        try:
            # Validate connection
            connection = db.query(SocialConnection).filter(
                and_(
                    SocialConnection.id == connection_id,
                    SocialConnection.organization_id == organization_id,
                    SocialConnection.is_active == True,
                    SocialConnection.revoked_at.is_(None)
                )
            ).first()
            
            if not connection:
                return False, None, "Connection not found or not accessible"
            
            # Generate content hash
            content_hash = self.publisher_service.generate_content_hash(content, media_urls)
            
            # Create draft record
            draft = ContentDraft(
                organization_id=organization_id,
                connection_id=connection_id,
                content=content,
                content_hash=content_hash,
                media_urls=media_urls,
                status="created"
            )
            
            db.add(draft)
            db.commit()
            
            # Mark connection as verified after first successful draft
            if not connection.verified_for_posting:
                connection.verified_for_posting = True
                db.commit()
                logger.info(f"Connection {connection_id} verified for posting")
            
            # Create audit log
            await self._create_audit_log(
                db, connection, "draft_create", "success",
                {
                    "draft_id": str(draft.id),
                    "content_hash": content_hash,
                    "content_length": len(content),
                    "media_count": len(media_urls)
                }
            )
            
            draft.status = "verified"
            draft.verified_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Draft created successfully: {draft.id}")
            return True, str(draft.id), None
            
        except Exception as e:
            db.rollback()
            error_msg = f"Draft creation failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def schedule_content(
        self,
        organization_id: str,
        connection_ids: List[str],
        content: str,
        media_urls: List[str],
        scheduled_time: Optional[datetime],
        db: Session
    ) -> Dict[str, Any]:
        """
        Schedule content for publishing to multiple connections
        
        Args:
            organization_id: Organization ID
            connection_ids: List of connection IDs to publish to
            content: Content text
            media_urls: List of media URLs
            scheduled_time: When to publish (None for immediate)
            db: Database session
            
        Returns:
            Dictionary with scheduling results
        """
        results = {
            "scheduled_count": 0,
            "failed_count": 0,
            "results": [],
            "errors": []
        }
        
        try:
            # Validate all connections first
            connections = db.query(SocialConnection).filter(
                and_(
                    SocialConnection.id.in_(connection_ids),
                    SocialConnection.organization_id == organization_id,
                    SocialConnection.is_active == True,
                    SocialConnection.revoked_at.is_(None)
                )
            ).all()
            
            if len(connections) != len(connection_ids):
                found_ids = [str(conn.id) for conn in connections]
                missing_ids = [cid for cid in connection_ids if cid not in found_ids]
                results["errors"].append(f"Connections not found: {missing_ids}")
            
            # Generate content hash for idempotency
            content_hash = self.publisher_service.generate_content_hash(content, media_urls)
            
            # Process each connection
            for connection in connections:
                try:
                    # Check draft verification
                    if not connection.verified_for_posting:
                        results["failed_count"] += 1
                        results["results"].append({
                            "connection_id": str(connection.id),
                            "platform": connection.platform,
                            "success": False,
                            "error": "Connection not verified - run test draft first"
                        })
                        continue
                    
                    # Generate idempotency key
                    idempotency_key = self.publisher_service.generate_idempotency_key(
                        organization_id, str(connection.id), content_hash, scheduled_time
                    )
                    
                    # Check for duplicates
                    existing = db.query(ContentSchedule).filter(
                        ContentSchedule.idempotency_key == idempotency_key
                    ).first()
                    
                    if existing:
                        results["results"].append({
                            "connection_id": str(connection.id),
                            "platform": connection.platform,
                            "success": False,
                            "error": "Duplicate content (already scheduled)",
                            "existing_id": str(existing.id)
                        })
                        continue
                    
                    # Create schedule record
                    schedule = ContentSchedule(
                        organization_id=organization_id,
                        connection_id=connection.id,
                        content=content,
                        content_hash=content_hash,
                        media_urls=media_urls,
                        scheduled_for=scheduled_time,
                        idempotency_key=idempotency_key,
                        status="scheduled" if scheduled_time else "publishing"
                    )
                    
                    db.add(schedule)
                    db.commit()
                    
                    # If immediate publish, do it now
                    if not scheduled_time:
                        success, post_id, error = await self.publisher_service.publish_to_connection(
                            connection, content, media_urls, db
                        )
                        
                        if success:
                            schedule.status = "published"
                            schedule.published_at = datetime.now(timezone.utc)
                            schedule.platform_post_id = post_id
                            results["scheduled_count"] += 1
                        else:
                            schedule.status = "failed"
                            schedule.error_message = error
                            results["failed_count"] += 1
                        
                        db.commit()
                        
                        results["results"].append({
                            "connection_id": str(connection.id),
                            "platform": connection.platform,
                            "success": success,
                            "schedule_id": str(schedule.id),
                            "platform_post_id": post_id,
                            "error": error
                        })
                    else:
                        # Scheduled for later
                        results["scheduled_count"] += 1
                        results["results"].append({
                            "connection_id": str(connection.id),
                            "platform": connection.platform,
                            "success": True,
                            "schedule_id": str(schedule.id),
                            "scheduled_for": scheduled_time.isoformat()
                        })
                    
                    # Create audit log
                    await self._create_audit_log(
                        db, connection, 
                        "schedule_content" if scheduled_time else "publish_content",
                        "success" if schedule.status in ["scheduled", "published"] else "failure",
                        {
                            "schedule_id": str(schedule.id),
                            "content_hash": content_hash,
                            "scheduled_for": scheduled_time.isoformat() if scheduled_time else None
                        }
                    )
                    
                except Exception as e:
                    db.rollback()
                    error_msg = f"Error processing connection {connection.id}: {str(e)}"
                    logger.error(error_msg)
                    results["failed_count"] += 1
                    results["errors"].append(error_msg)
                    results["results"].append({
                        "connection_id": str(connection.id),
                        "platform": connection.platform,
                        "success": False,
                        "error": error_msg
                    })
            
            return results
            
        except Exception as e:
            db.rollback()
            error_msg = f"Content scheduling failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
    
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
            # Don't raise - audit log failures shouldn't break scheduling


# Singleton instance
_content_scheduler_service = None


def get_content_scheduler_service(settings=None) -> ContentSchedulerService:
    """
    Get content scheduler service instance
    
    Args:
        settings: Application settings (optional)
        
    Returns:
        ContentSchedulerService instance
    """
    global _content_scheduler_service
    
    if _content_scheduler_service is None:
        _content_scheduler_service = ContentSchedulerService(settings)
    
    return _content_scheduler_service