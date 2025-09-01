"""
Celery tasks for token health management
Handles automated token refresh and health auditing
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from celery import Celery
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import SocialConnection, SocialAudit
from backend.services.token_refresh_service import get_token_refresh_service

logger = logging.getLogger(__name__)

# Initialize Celery app (this should match your main Celery configuration)
settings = get_settings()
celery_app = Celery('token_health_tasks')

# Configure Celery for token health tasks
celery_app.conf.update(
    # Task routing
    task_routes={
        'backend.tasks.token_health_tasks.audit_all_tokens': {'queue': 'token_health'},
        'backend.tasks.token_health_tasks.refresh_connection': {'queue': 'token_health'},
    },
    
    # Task settings
    task_soft_time_limit=600,  # 10 minutes
    task_time_limit=900,       # 15 minutes
    result_expires=86400,      # 24 hours
)


def is_partner_oauth_enabled() -> bool:
    """Check if partner OAuth feature is enabled"""
    settings = get_settings()
    return getattr(settings, 'feature_partner_oauth', False)


@celery_app.task(name='backend.tasks.token_health_tasks.audit_all_tokens')
def audit_all_tokens() -> Dict[str, Any]:
    """
    Audit all tokens and refresh those that are expiring or have unknown expiry
    
    This task runs nightly to maintain connection health by:
    - Finding connections expiring within 72 hours
    - Finding connections with unknown expiry dates
    - Attempting to refresh their tokens
    - Creating audit logs for all refresh attempts
    
    Returns:
        Dictionary with audit results and statistics
    """
    try:
        if not is_partner_oauth_enabled():
            logger.info("Token health audit skipped - feature disabled")
            return {"status": "skipped", "reason": "feature_disabled"}
        
        start_time = datetime.now(timezone.utc)
        logger.info("Starting nightly token health audit")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Find connections that need token refresh
            connections_to_refresh = _find_connections_needing_refresh(db)
            
            audit_results = {
                "audit_time": start_time.isoformat(),
                "connections_checked": len(connections_to_refresh),
                "refresh_attempts": 0,
                "refresh_successes": 0,
                "refresh_failures": 0,
                "platforms": {"meta": 0, "x": 0},
                "errors": []
            }
            
            # Refresh each connection
            refresh_service = get_token_refresh_service()
            
            for connection in connections_to_refresh:
                try:
                    audit_results["refresh_attempts"] += 1
                    audit_results["platforms"][connection.platform] += 1
                    
                    logger.info(f"Refreshing connection {connection.id} ({connection.platform})")
                    
                    # Refresh based on platform
                    if connection.platform == "meta":
                        success, new_expiry, message = asyncio.run(refresh_service.refresh_meta_connection(connection, db))
                    elif connection.platform == "x":
                        success, new_expiry, message = asyncio.run(refresh_service.refresh_x_connection(connection, db))
                    else:
                        logger.warning(f"Unknown platform for refresh: {connection.platform}")
                        continue
                    
                    if success:
                        audit_results["refresh_successes"] += 1
                        logger.info(f"Successfully refreshed connection {connection.id}: {message}")
                    else:
                        audit_results["refresh_failures"] += 1
                        logger.warning(f"Failed to refresh connection {connection.id}: {message}")
                        audit_results["errors"].append({
                            "connection_id": str(connection.id),
                            "platform": connection.platform,
                            "error": message
                        })
                
                except Exception as e:
                    audit_results["refresh_failures"] += 1
                    error_msg = f"Exception refreshing connection {connection.id}: {str(e)}"
                    logger.error(error_msg)
                    audit_results["errors"].append({
                        "connection_id": str(connection.id),
                        "platform": connection.platform if connection else "unknown",
                        "error": str(e)
                    })
            
            # Calculate audit duration
            end_time = datetime.now(timezone.utc)
            audit_duration = (end_time - start_time).total_seconds()
            audit_results["audit_duration_seconds"] = audit_duration
            
            logger.info(f"Token health audit completed: {audit_results}")
            return audit_results
            
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"Token health audit failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "audit_time": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(name='backend.tasks.token_health_tasks.refresh_connection')
def refresh_connection(connection_id: str) -> Dict[str, Any]:
    """
    Refresh a single connection's tokens (for manual refresh endpoint)
    
    Args:
        connection_id: UUID string of the connection to refresh
        
    Returns:
        Dictionary with refresh result
    """
    try:
        if not is_partner_oauth_enabled():
            return {"status": "skipped", "reason": "feature_disabled"}
        
        logger.info(f"Manual refresh requested for connection {connection_id}")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Find the connection
            connection = db.query(SocialConnection).filter(
                SocialConnection.id == connection_id,
                SocialConnection.is_active == True
            ).first()
            
            if not connection:
                return {
                    "status": "failed",
                    "error": "Connection not found or inactive",
                    "connection_id": connection_id
                }
            
            # Refresh based on platform
            refresh_service = get_token_refresh_service()
            
            if connection.platform == "meta":
                success, new_expiry, message = asyncio.run(refresh_service.refresh_meta_connection(connection, db))
            elif connection.platform == "x":
                success, new_expiry, message = asyncio.run(refresh_service.refresh_x_connection(connection, db))
            else:
                return {
                    "status": "failed",
                    "error": f"Unsupported platform: {connection.platform}",
                    "connection_id": connection_id
                }
            
            result = {
                "status": "success" if success else "failed",
                "connection_id": connection_id,
                "platform": connection.platform,
                "message": message,
                "new_expiry": new_expiry.isoformat() if new_expiry else None,
                "refresh_time": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Manual refresh completed for connection {connection_id}: {result}")
            return result
            
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"Manual refresh failed for connection {connection_id}: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "connection_id": connection_id,
            "refresh_time": datetime.now(timezone.utc).isoformat()
        }


def _find_connections_needing_refresh(db: Session) -> List[SocialConnection]:
    """
    Find connections that need token refresh
    
    Criteria:
    - Active connections only
    - Partner OAuth platforms (meta, x) only
    - Token expires within 72 hours OR unknown expiry date
    
    Args:
        db: Database session
        
    Returns:
        List of SocialConnection instances needing refresh
    """
    try:
        # Calculate threshold for expiring tokens (72 hours from now)
        expiry_threshold = datetime.now(timezone.utc) + timedelta(hours=72)
        
        # Query for connections needing refresh
        connections = db.query(SocialConnection).filter(
            SocialConnection.is_active == True,
            SocialConnection.platform.in_(["meta", "x"]),
            # Either expiring soon or unknown expiry
            (
                (SocialConnection.token_expires_at.is_(None)) |
                (SocialConnection.token_expires_at <= expiry_threshold)
            )
        ).all()
        
        logger.info(f"Found {len(connections)} connections needing token refresh")
        
        # Log breakdown by platform and reason
        platform_counts = {"meta": 0, "x": 0}
        expiry_reasons = {"unknown_expiry": 0, "expiring_soon": 0}
        
        for conn in connections:
            platform_counts[conn.platform] += 1
            if conn.token_expires_at is None:
                expiry_reasons["unknown_expiry"] += 1
            else:
                expiry_reasons["expiring_soon"] += 1
        
        logger.info(f"Connections by platform: {platform_counts}")
        logger.info(f"Connections by reason: {expiry_reasons}")
        
        return connections
    
    except Exception as e:
        logger.error(f"Error finding connections needing refresh: {e}")
        return []


@celery_app.task(name='backend.tasks.token_health_tasks.cleanup_old_audits')
def cleanup_old_audits(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old audit logs to prevent database bloat
    
    Args:
        days_to_keep: Number of days of audit logs to keep (default 90)
        
    Returns:
        Dictionary with cleanup results
    """
    try:
        if not is_partner_oauth_enabled():
            return {"status": "skipped", "reason": "feature_disabled"}
        
        logger.info(f"Starting audit cleanup - keeping last {days_to_keep} days")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            # Count records to be deleted
            old_audits_count = db.query(SocialAudit).filter(
                SocialAudit.created_at < cutoff_date,
                SocialAudit.action.in_(["refresh", "poll_mentions"])
            ).count()
            
            if old_audits_count == 0:
                logger.info("No old audit records found to cleanup")
                return {
                    "status": "completed",
                    "records_deleted": 0,
                    "cutoff_date": cutoff_date.isoformat()
                }
            
            # Delete old audit records
            deleted_count = db.query(SocialAudit).filter(
                SocialAudit.created_at < cutoff_date,
                SocialAudit.action.in_(["refresh", "poll_mentions"])
            ).delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old audit records")
            return {
                "status": "completed",
                "records_deleted": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        finally:
            db.close()
    
    except Exception as e:
        error_msg = f"Audit cleanup failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }