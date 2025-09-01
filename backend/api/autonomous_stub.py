"""
Minimal autonomous API stub for production deployment
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import logging

router = APIRouter(prefix="/api/autonomous", tags=["autonomous"])
logger = logging.getLogger(__name__)

@router.get("/research/latest")
async def get_latest_research():
    """Get latest research - minimal stub"""
    return {
        "research": [],
        "total": 0,
        "message": "Autonomous research temporarily unavailable - CrewAI not configured"
    }

@router.get("/status")
async def get_autonomous_status():
    """Get autonomous system status"""
    return {
        "status": "inactive",
        "message": "Autonomous system temporarily unavailable - missing dependencies"
    }