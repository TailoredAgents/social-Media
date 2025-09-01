from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# Simple workflow status for demo
workflow_status = {
    'current_stage': 'content_generation',
    'last_full_cycle': '2025-07-22T06:00:00Z',
    'cycle_count': 142,
    'metrics': {
        'avg_cycle_time': 85.5,
        'success_rate': 96.2,
        'content_generated_today': 12,
        'research_items_today': 8
    },
    'stages': {
        'research': {
            'name': 'Daily Research',
            'status': 'completed',
            'scheduled_time': '06:00',
            'duration_minutes': 30,
            'last_run': '2025-07-22T06:00:00Z'
        },
        'trend_analysis': {
            'name': 'Trend Analysis', 
            'status': 'completed',
            'scheduled_time': '06:30',
            'duration_minutes': 20,
            'last_run': '2025-07-22T06:30:00Z'
        },
        'content_generation': {
            'name': 'Content Generation',
            'status': 'running',
            'scheduled_time': '09:15',
            'duration_minutes': 45,
            'last_run': None
        },
        'automated_posting': {
            'name': 'Automated Posting',
            'status': 'pending',
            'scheduled_time': '15:00',
            'duration_minutes': 30,
            'last_run': None
        }
    },
    'recent_errors': []
}

@router.get("/status")
async def get_workflow_status():
    """Get current workflow status"""
    try:
        return {
            "status": "success",
            "workflow": workflow_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")

@router.get("/metrics")
async def get_workflow_metrics():
    """Get workflow performance metrics"""
    try:
        return {
            "status": "success",
            "metrics": workflow_status['metrics'],
            "cycle_count": workflow_status['cycle_count'],
            "last_cycle": workflow_status['last_full_cycle'],
            "current_stage": workflow_status['current_stage']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow metrics: {str(e)}")

@router.get("/stages")
async def get_workflow_stages():
    """Get detailed information about workflow stages"""
    try:
        return {
            "status": "success",
            "stages": workflow_status['stages'],
            "total_stages": len(workflow_status['stages'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow stages: {str(e)}")

@router.post("/run-cycle")
async def trigger_workflow_cycle():
    """Trigger a workflow cycle (simulated)"""
    try:
        # Update cycle count
        workflow_status['cycle_count'] += 1
        workflow_status['last_full_cycle'] = datetime.utcnow().isoformat()
        workflow_status['current_stage'] = 'research'
        
        return {
            "status": "success",
            "message": "Workflow cycle triggered",
            "cycle_number": workflow_status['cycle_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering workflow: {str(e)}")