from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.core.simple_goals import goal_tracker

router = APIRouter(prefix="/api/goals", tags=["goals"])

class CreateGoalRequest(BaseModel):
    title: str
    description: str
    goal_type: str
    target_value: float
    target_date: str  # ISO format string
    platform: Optional[str] = None

class UpdateProgressRequest(BaseModel):
    current_value: float

@router.post("/create")
async def create_goal(request: CreateGoalRequest, user_id: str = "default_user"):
    """Create a new goal"""
    try:
        goal = goal_tracker.create_goal(
            title=request.title,
            description=request.description,
            goal_type=request.goal_type,
            target_value=request.target_value,
            target_date=request.target_date,
            platform=request.platform
        )
        
        return {
            "status": "success",
            "message": "Goal created successfully",
            "goal": goal.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")

@router.get("/")
async def get_user_goals(
    user_id: str = "default_user",
    status: Optional[str] = None
):
    """Get all goals for a user"""
    try:
        goals = goal_tracker.get_user_goals(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "goals": [goal.to_dict() for goal in goals],
            "count": len(goals)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving goals: {str(e)}")

@router.get("/{goal_id}")
async def get_goal(goal_id: str):
    """Get specific goal by ID"""
    try:
        goal = goal_tracker.get_goal_by_id(goal_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {
            "status": "success",
            "goal": goal.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving goal: {str(e)}")

@router.put("/{goal_id}/progress")
async def update_goal_progress(goal_id: str, request: UpdateProgressRequest):
    """Update goal progress"""
    try:
        goal = goal_tracker.update_goal_progress(goal_id, request.current_value)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {
            "status": "success",
            "message": "Goal progress updated successfully",
            "goal": goal.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating goal progress: {str(e)}")

@router.put("/{goal_id}/pause")
async def pause_goal(goal_id: str):
    """Pause a goal"""
    try:
        goal = goal_tracker.pause_goal(goal_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {
            "status": "success",
            "message": "Goal paused successfully",
            "goal": goal.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing goal: {str(e)}")

@router.put("/{goal_id}/resume")
async def resume_goal(goal_id: str):
    """Resume a paused goal"""
    try:
        goal = goal_tracker.resume_goal(goal_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found or not paused")
        
        return {
            "status": "success",
            "message": "Goal resumed successfully",
            "goal": goal.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming goal: {str(e)}")

@router.delete("/{goal_id}")
async def delete_goal(goal_id: str):
    """Delete a goal"""
    try:
        success = goal_tracker.delete_goal(goal_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return {
            "status": "success",
            "message": "Goal deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting goal: {str(e)}")

@router.get("/dashboard/summary")
async def get_dashboard_summary(user_id: str = "default_user"):
    """Get goal summary for dashboard"""
    try:
        summary = goal_tracker.get_dashboard_summary(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard summary: {str(e)}")

@router.post("/suggestions")
async def get_goal_suggestions(user_id: str = "default_user"):
    """Get goal suggestions based on current metrics"""
    try:
        # Mock current metrics - in production, this would come from analytics
        current_metrics = {
            "followers": 2500,
            "engagement_rate": 4.2,
            "monthly_posts": 25,
            "reach": 15000
        }
        
        suggestions = goal_tracker.suggest_goals(user_id, current_metrics)
        
        return {
            "status": "success",
            "user_id": user_id,
            "current_metrics": current_metrics,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating goal suggestions: {str(e)}")

@router.get("/types/list")
async def list_goal_types():
    """List available goal types"""
    try:
        goal_types = [
            {"value": "follower_growth", "label": "Follower Growth", "description": "Increase your social media following"},
            {"value": "engagement_rate", "label": "Engagement Rate", "description": "Improve interaction rates on your posts"},
            {"value": "reach_increase", "label": "Reach Increase", "description": "Expand your content's reach and visibility"},
            {"value": "content_volume", "label": "Content Volume", "description": "Increase content production consistency"},
        ]
        
        return {
            "status": "success",
            "goal_types": goal_types
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing goal types: {str(e)}")