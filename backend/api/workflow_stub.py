"""
Minimal workflow API stub for production deployment
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import logging

router = APIRouter(prefix="/api/workflow", tags=["workflow"])
logger = logging.getLogger(__name__)

@router.get("/status/summary")
async def get_workflow_status_summary():
    """Get workflow status summary - minimal stub"""
    return {
        "workflows": [],
        "active_count": 0,
        "total_count": 0,
        "message": "Workflow service temporarily unavailable - database not configured"
    }

@router.get("/")
async def get_workflows():
    """Get workflows"""
    return {
        "workflows": [],
        "total": 0,
        "message": "Workflow service temporarily unavailable"
    }