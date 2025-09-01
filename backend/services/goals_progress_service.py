"""
Goals Progress Tracking Service

This service handles automated progress tracking for goals by:
1. Fetching metrics from integrated social platforms
2. Updating goal progress based on current metrics
3. Triggering milestone notifications
4. Detecting at-risk and stagnant goals
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from backend.db.models import Goal, GoalProgress, User, ContentItem, ContentPerformanceSnapshot
from backend.db.database import get_db
from backend.services.notification_service import NotificationService
from backend.integrations.twitter_client import TwitterAPIClient as TwitterClient
# LinkedIn integration removed - using stub
LinkedInClient = None
from backend.integrations.instagram_client import InstagramAPIClient as InstagramClient
from backend.integrations.facebook_client import FacebookAPIClient as FacebookClient

logger = logging.getLogger(__name__)


class GoalsProgressService:
    """Service for automated goal progress tracking and updates"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.social_clients = {
            'twitter': TwitterClient,
            'linkedin': LinkedInClient,
            'instagram': InstagramClient,
            'facebook': FacebookClient
        }
    
    async def update_all_user_goals(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Update progress for all active goals for a user"""
        try:
            # Get all active goals for the user
            active_goals = db.query(Goal).filter(
                and_(
                    Goal.user_id == user_id,
                    Goal.status.in_(['active', 'at_risk'])
                )
            ).all()
            
            if not active_goals:
                return {"message": "No active goals found", "updated_count": 0}
            
            updated_goals = []
            errors = []
            
            for goal in active_goals:
                try:
                    # Update progress based on goal type and platform
                    result = await self._update_goal_progress(db, goal)
                    if result['updated']:
                        updated_goals.append(goal.id)
                except Exception as e:
                    logger.error(f"Error updating goal {goal.id}: {str(e)}")
                    errors.append({"goal_id": goal.id, "error": str(e)})
            
            # Check all goals for notifications
            notifications = await self.notification_service.check_all_goals(db, user_id)
            
            return {
                "updated_count": len(updated_goals),
                "updated_goal_ids": updated_goals,
                "notifications_created": len(notifications),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error updating user goals: {str(e)}")
            raise
    
    async def _update_goal_progress(self, db: Session, goal: Goal) -> Dict[str, Any]:
        """Update progress for a single goal based on its type"""
        try:
            # Get the appropriate metrics based on goal type
            current_metric_value = await self._fetch_current_metric(db, goal)
            
            if current_metric_value is None:
                return {"updated": False, "reason": "Could not fetch metric"}
            
            # Only update if the value has changed
            if goal.current_value == current_metric_value:
                return {"updated": False, "reason": "No change in metric"}
            
            # Store previous value for comparison
            previous_value = goal.current_value
            
            # Update the goal's current value
            goal.current_value = current_metric_value
            goal.updated_at = datetime.utcnow()
            
            # Create progress history entry
            progress_entry = GoalProgress(
                goal_id=goal.id,
                value=current_metric_value,
                notes=f"Automated update from {goal.platform} metrics"
            )
            db.add(progress_entry)
            
            # Check if goal is completed
            if goal.target_value and current_metric_value >= goal.target_value:
                goal.status = 'completed'
                goal.completed_at = datetime.utcnow()
            
            # Check if goal is at risk (less than expected progress)
            elif self._is_goal_at_risk(goal):
                goal.status = 'at_risk'
            
            db.commit()
            
            # Log the update
            logger.info(f"Updated goal {goal.id} progress: {previous_value} -> {current_metric_value}")
            
            return {
                "updated": True,
                "previous_value": previous_value,
                "new_value": current_metric_value,
                "status": goal.status
            }
            
        except Exception as e:
            logger.error(f"Error updating goal progress: {str(e)}")
            db.rollback()
            raise
    
    async def _fetch_current_metric(self, db: Session, goal: Goal) -> Optional[float]:
        """Fetch the current metric value based on goal type and platform"""
        try:
            # For content-based metrics, aggregate from ContentPerformanceSnapshot
            if goal.goal_type in ['engagement_rate', 'reach_increase', 'content_volume']:
                return await self._fetch_content_based_metric(db, goal)
            
            # For platform-specific metrics, use social media APIs
            elif goal.goal_type == 'follower_growth':
                return await self._fetch_follower_count(db, goal)
            
            # For custom goals, check if there's a linked metric
            elif goal.goal_type == 'custom':
                return await self._fetch_custom_metric(db, goal)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching metric for goal {goal.id}: {str(e)}")
            return None
    
    async def _fetch_content_based_metric(self, db: Session, goal: Goal) -> Optional[float]:
        """Fetch metrics based on content performance"""
        try:
            # Get date range for the goal
            start_date = goal.start_date or goal.created_at
            end_date = goal.deadline or datetime.utcnow()
            
            # Query content performance for the goal's platform
            query = db.query(ContentPerformanceSnapshot).join(ContentItem).filter(
                and_(
                    ContentItem.user_id == goal.user_id,
                    ContentItem.platform == goal.platform,
                    ContentPerformanceSnapshot.timestamp >= start_date,
                    ContentPerformanceSnapshot.timestamp <= end_date
                )
            )
            
            if goal.goal_type == 'engagement_rate':
                # Calculate average engagement rate
                snapshots = query.all()
                if not snapshots:
                    return 0.0
                
                total_engagement = sum(s.likes + s.shares + s.comments for s in snapshots)
                total_impressions = sum(s.impressions for s in snapshots)
                
                if total_impressions == 0:
                    return 0.0
                
                return (total_engagement / total_impressions) * 100
            
            elif goal.goal_type == 'reach_increase':
                # Calculate total reach/impressions
                total_reach = query.with_entities(
                    func.sum(ContentPerformanceSnapshot.impressions)
                ).scalar()
                return float(total_reach or 0)
            
            elif goal.goal_type == 'content_volume':
                # Count unique content items
                content_count = query.with_entities(
                    func.count(func.distinct(ContentItem.id))
                ).scalar()
                return float(content_count or 0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching content metric: {str(e)}")
            return None
    
    async def _fetch_follower_count(self, db: Session, goal: Goal) -> Optional[float]:
        """Fetch current follower count from social platform"""
        try:
            # Get user's social account credentials
            user = db.query(User).filter(User.id == goal.user_id).first()
            if not user:
                return None
            
            # Get the appropriate social client
            client_class = self.social_clients.get(goal.platform)
            if not client_class:
                logger.warning(f"No client available for platform: {goal.platform}")
                return None
            
            # Initialize client with user's credentials
            # This assumes social accounts are stored in user preferences
            social_accounts = user.preferences.get('social_accounts', {})
            platform_auth = social_accounts.get(goal.platform, {})
            
            if not platform_auth:
                logger.warning(f"No auth credentials for platform: {goal.platform}")
                return None
            
            client = client_class(
                access_token=platform_auth.get('access_token'),
                access_token_secret=platform_auth.get('access_token_secret')  # For Twitter
            )
            
            # Get follower count
            metrics = await client.get_account_metrics()
            return float(metrics.get('followers_count', 0))
            
        except Exception as e:
            logger.error(f"Error fetching follower count: {str(e)}")
            return None
    
    async def _fetch_custom_metric(self, db: Session, goal: Goal) -> Optional[float]:
        """Fetch custom metric value - can be extended based on requirements"""
        try:
            # For custom goals, check if there's a metric mapping in goal metadata
            if goal.metadata and 'metric_source' in goal.metadata:
                metric_source = goal.metadata['metric_source']
                
                # Handle different metric sources
                if metric_source['type'] == 'content_aggregate':
                    return await self._fetch_content_aggregate_metric(db, goal, metric_source)
                elif metric_source['type'] == 'external_api':
                    # Placeholder for external API integration
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching custom metric: {str(e)}")
            return None
    
    async def _fetch_content_aggregate_metric(self, db: Session, goal: Goal, 
                                            metric_source: Dict) -> Optional[float]:
        """Fetch aggregated content metrics for custom goals"""
        try:
            field = metric_source.get('field')
            aggregation = metric_source.get('aggregation', 'sum')
            
            query = db.query(ContentPerformanceSnapshot).join(ContentItem).filter(
                and_(
                    ContentItem.user_id == goal.user_id,
                    ContentItem.platform == goal.platform
                )
            )
            
            if aggregation == 'sum':
                result = query.with_entities(func.sum(getattr(ContentPerformanceSnapshot, field))).scalar()
            elif aggregation == 'avg':
                result = query.with_entities(func.avg(getattr(ContentPerformanceSnapshot, field))).scalar()
            elif aggregation == 'max':
                result = query.with_entities(func.max(getattr(ContentPerformanceSnapshot, field))).scalar()
            elif aggregation == 'count':
                result = query.count()
            else:
                return None
            
            return float(result or 0)
            
        except Exception as e:
            logger.error(f"Error fetching content aggregate metric: {str(e)}")
            return None
    
    def _is_goal_at_risk(self, goal: Goal) -> bool:
        """Determine if a goal is at risk of not being met"""
        if not goal.deadline or not goal.target_value:
            return False
        
        # Calculate expected progress
        total_days = (goal.deadline - goal.created_at).days
        elapsed_days = (datetime.utcnow() - goal.created_at).days
        
        if total_days <= 0 or elapsed_days <= 0:
            return False
        
        # Expected progress percentage
        expected_progress_pct = (elapsed_days / total_days) * 100
        
        # Actual progress percentage
        progress_range = goal.target_value - (goal.metadata.get('initial_value', 0) if goal.metadata else 0)
        if progress_range <= 0:
            return False
        
        actual_progress = goal.current_value - (goal.metadata.get('initial_value', 0) if goal.metadata else 0)
        actual_progress_pct = (actual_progress / progress_range) * 100
        
        # Goal is at risk if actual progress is 20% behind expected
        return actual_progress_pct < (expected_progress_pct - 20)
    
    async def sync_platform_metrics(self, db: Session, user_id: int, platform: str) -> Dict[str, Any]:
        """Sync all metrics for a specific platform"""
        try:
            # Get all active goals for the platform
            platform_goals = db.query(Goal).filter(
                and_(
                    Goal.user_id == user_id,
                    Goal.platform == platform,
                    Goal.status.in_(['active', 'at_risk'])
                )
            ).all()
            
            if not platform_goals:
                return {"message": f"No active goals for {platform}", "synced_count": 0}
            
            synced_goals = []
            
            for goal in platform_goals:
                result = await self._update_goal_progress(db, goal)
                if result['updated']:
                    synced_goals.append({
                        "goal_id": goal.id,
                        "title": goal.title,
                        "new_value": result['new_value'],
                        "status": result['status']
                    })
            
            return {
                "platform": platform,
                "synced_count": len(synced_goals),
                "synced_goals": synced_goals
            }
            
        except Exception as e:
            logger.error(f"Error syncing platform metrics: {str(e)}")
            raise