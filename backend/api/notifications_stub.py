"""
Minimal notifications API stub for production deployment
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import logging

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

@router.get("/")
async def get_notifications():
    """Get notifications - minimal stub"""
    return {
        "notifications": [],
        "total": 0,
        "message": "Notifications service temporarily unavailable - database not configured"
    }

@router.get("/unread")
async def get_unread_notifications():
    """Get unread notifications count"""
    return {
        "unread_count": 0,
        "message": "Notifications service temporarily unavailable"
    }

@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    return {
        "success": False,
        "message": "Notifications service temporarily unavailable"
    }