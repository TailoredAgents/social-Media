"""
Celery tasks for automated goals progress tracking

These tasks run periodically to:
1. Update goal progress from social media metrics
2. Check for milestone achievements
3. Send notifications for at-risk goals
4. Generate daily/weekly goal reports
"""

# Ensure warnings are suppressed in worker processes
from backend.core.suppress_warnings import suppress_third_party_warnings
suppress_third_party_warnings()

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

from backend.db.database import SessionLocal
from backend.db.models import User, Goal
from backend.services.goals_progress_service import GoalsProgressService
from backend.services.notification_service import NotificationService

logger = get_task_logger(__name__)


@shared_task(name="update_all_goals_progress")
def update_all_goals_progress() -> Dict[str, Any]:
    """
    Celery task to update progress for all active goals across all users.
    This task should run every hour.
    """
    db = SessionLocal()
    service = GoalsProgressService()
    
    try:
        # Get all users with active goals
        users_with_goals = db.query(User).join(Goal).filter(
            Goal.status.in_(['active', 'at_risk'])
        ).distinct().all()
        
        results = {
            "total_users": len(users_with_goals),
            "total_goals_updated": 0,
            "total_notifications": 0,
            "errors": []
        }
        
        # Update goals for each user
        for user in users_with_goals:
            try:
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                update_result = loop.run_until_complete(
                    service.update_all_user_goals(db, user.id)
                )
                
                results["total_goals_updated"] += update_result["updated_count"]
                results["total_notifications"] += update_result["notifications_created"]
                
                logger.info(f"Updated goals for user {user.id}: {update_result['updated_count']} goals")
                
            except Exception as e:
                logger.error(f"Error updating goals for user {user.id}: {str(e)}")
                results["errors"].append({
                    "user_id": user.id,
                    "error": str(e)
                })
            finally:
                if loop:
                    loop.close()
        
        logger.info(f"Goals progress update completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in update_all_goals_progress task: {str(e)}")
        raise
    finally:
        db.close()


@shared_task(name="sync_platform_metrics")
def sync_platform_metrics(user_id: int, platform: str) -> Dict[str, Any]:
    """
    Celery task to sync metrics for a specific user and platform.
    Can be triggered manually or scheduled.
    """
    db = SessionLocal()
    service = GoalsProgressService()
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            service.sync_platform_metrics(db, user_id, platform)
        )
        
        logger.info(f"Synced {platform} metrics for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing platform metrics: {str(e)}")
        raise
    finally:
        if loop:
            loop.close()
        db.close()


@shared_task(name="check_goal_deadlines")
def check_goal_deadlines() -> Dict[str, Any]:
    """
    Celery task to check for approaching goal deadlines and send reminders.
    This task should run daily.
    """
    db = SessionLocal()
    notification_service = NotificationService()
    
    try:
        # Check for goals with deadlines in the next 7 days
        upcoming_deadline = datetime.utcnow() + timedelta(days=7)
        
        goals_near_deadline = db.query(Goal).filter(
            Goal.status == 'active',
            Goal.deadline <= upcoming_deadline,
            Goal.deadline > datetime.utcnow()
        ).all()
        
        notifications_sent = 0
        
        for goal in goals_near_deadline:
            days_remaining = (goal.deadline - datetime.utcnow()).days
            
            # Create deadline reminder notification
            notification = notification_service.create_notification(
                db=db,
                user_id=goal.user_id,
                notification_type='goal_deadline',
                title=f"Goal deadline approaching: {goal.title}",
                message=f"Your goal '{goal.title}' has {days_remaining} days remaining. "
                       f"Current progress: {goal.current_value}/{goal.target_value}",
                metadata={
                    "goal_id": goal.id,
                    "days_remaining": days_remaining,
                    "progress_percentage": (goal.current_value / goal.target_value * 100) if goal.target_value else 0
                }
            )
            
            if notification:
                notifications_sent += 1
        
        db.commit()
        
        result = {
            "goals_checked": len(goals_near_deadline),
            "notifications_sent": notifications_sent
        }
        
        logger.info(f"Goal deadline check completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error checking goal deadlines: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(name="generate_weekly_goal_report")
def generate_weekly_goal_report(user_id: int) -> Dict[str, Any]:
    """
    Celery task to generate weekly goal progress reports for a user.
    This task should run weekly on Sundays.
    """
    db = SessionLocal()
    notification_service = NotificationService()
    
    try:
        # Get all user's goals
        user_goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        
        if not user_goals:
            return {"message": "No goals found for user"}
        
        # Calculate weekly statistics
        active_goals = [g for g in user_goals if g.status == 'active']
        completed_this_week = [g for g in user_goals if g.status == 'completed' and 
                               g.completed_at and g.completed_at >= datetime.utcnow() - timedelta(days=7)]
        at_risk_goals = [g for g in user_goals if g.status == 'at_risk']
        
        # Calculate average progress for active goals
        total_progress = 0
        goals_with_progress = 0
        
        for goal in active_goals:
            if goal.target_value and goal.current_value is not None:
                progress_pct = (goal.current_value / goal.target_value) * 100
                total_progress += progress_pct
                goals_with_progress += 1
        
        avg_progress = total_progress / goals_with_progress if goals_with_progress > 0 else 0
        
        # Create weekly report notification
        report_message = f"""
Weekly Goal Progress Report:

Active Goals: {len(active_goals)}
Completed This Week: {len(completed_this_week)}
At Risk: {len(at_risk_goals)}
Average Progress: {avg_progress:.1f}%

Keep up the great work! 🎯
"""
        
        notification = notification_service.create_notification(
            db=db,
            user_id=user_id,
            notification_type='goal_report',
            title="Your Weekly Goal Progress Report",
            message=report_message.strip(),
            metadata={
                "report_type": "weekly",
                "active_goals": len(active_goals),
                "completed_this_week": len(completed_this_week),
                "at_risk_goals": len(at_risk_goals),
                "average_progress": avg_progress
            }
        )
        
        db.commit()
        
        result = {
            "user_id": user_id,
            "report_generated": True,
            "stats": {
                "active_goals": len(active_goals),
                "completed_this_week": len(completed_this_week),
                "at_risk_goals": len(at_risk_goals),
                "average_progress": avg_progress
            }
        }
        
        logger.info(f"Weekly goal report generated for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating weekly goal report: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task(name="detect_stagnant_goals")
def detect_stagnant_goals() -> Dict[str, Any]:
    """
    Celery task to detect goals with no progress in the last 7 days.
    This task should run daily.
    """
    db = SessionLocal()
    notification_service = NotificationService()
    
    try:
        # Find goals with no recent progress
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get active goals
        active_goals = db.query(Goal).filter(
            Goal.status == 'active'
        ).all()
        
        stagnant_goals = []
        notifications_sent = 0
        
        for goal in active_goals:
            # Check if goal has any progress in the last 7 days
            recent_progress = db.query(Goal).filter(
                Goal.id == goal.id,
                Goal.updated_at > seven_days_ago
            ).first()
            
            if not recent_progress or goal.updated_at <= seven_days_ago:
                stagnant_goals.append(goal)
                
                # Create stagnant goal notification
                notification = notification_service.create_notification(
                    db=db,
                    user_id=goal.user_id,
                    notification_type='goal_stagnant',
                    title=f"Goal needs attention: {goal.title}",
                    message=f"Your goal '{goal.title}' hasn't shown progress in the last 7 days. "
                           f"Consider updating your strategy or breaking it into smaller milestones.",
                    metadata={
                        "goal_id": goal.id,
                        "days_stagnant": (datetime.utcnow() - goal.updated_at).days,
                        "current_progress": (goal.current_value / goal.target_value * 100) if goal.target_value else 0
                    }
                )
                
                if notification:
                    notifications_sent += 1
        
        db.commit()
        
        result = {
            "goals_checked": len(active_goals),
            "stagnant_goals": len(stagnant_goals),
            "notifications_sent": notifications_sent
        }
        
        logger.info(f"Stagnant goals detection completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error detecting stagnant goals: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()