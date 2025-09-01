from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from backend.core.workflow import workflow_manager

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

@router.get("/status")
async def get_workflow_status():
    """Get current workflow status"""
    try:
        status = workflow_manager.get_workflow_status()
        return {
            "status": "success",
            "workflow": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")

@router.post("/run-cycle")
async def run_daily_cycle(
    background_tasks: BackgroundTasks,
    user_id: str = "default_user"
):
    """Trigger a daily workflow cycle"""
    try:
        # Run the cycle in the background
        background_tasks.add_task(workflow_manager.run_daily_cycle, user_id)
        
        return {
            "status": "success",
            "message": "Daily workflow cycle started",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting workflow cycle: {str(e)}")

@router.get("/metrics")
async def get_workflow_metrics():
    """Get workflow performance metrics"""
    try:
        status = workflow_manager.get_workflow_status()
        
        return {
            "status": "success",
            "metrics": status['metrics'],
            "cycle_count": status['cycle_count'],
            "last_cycle": status['last_full_cycle'],
            "current_stage": status['current_stage']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow metrics: {str(e)}")

@router.get("/stages")
async def get_workflow_stages():
    """Get detailed information about workflow stages"""
    try:
        status = workflow_manager.get_workflow_status()
        
        return {
            "status": "success",
            "stages": status['stages'],
            "total_stages": len(status['stages'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow stages: {str(e)}")

@router.get("/errors")
async def get_workflow_errors():
    """Get recent workflow errors"""
    try:
        status = workflow_manager.get_workflow_status()
        
        return {
            "status": "success",
            "recent_errors": status['recent_errors'],
            "error_count": len(status['recent_errors'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow errors: {str(e)}")