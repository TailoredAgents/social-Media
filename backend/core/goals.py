from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class GoalType(Enum):
    FOLLOWER_GROWTH = "follower_growth"
    ENGAGEMENT_RATE = "engagement_rate" 
    REACH_INCREASE = "reach_increase"
    CONTENT_VOLUME = "content_volume"
    PLATFORM_EXPANSION = "platform_expansion"
    BRAND_AWARENESS = "brand_awareness"
    CONVERSION_RATE = "conversion_rate"

class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

@dataclass
class Goal:
    goal_id: str
    user_id: str
    title: str
    description: str
    goal_type: GoalType
    target_value: float
    current_value: float
    start_date: datetime
    target_date: datetime
    platform: Optional[str] = None
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = None
    updated_at: datetime = None
    milestones: List[Dict] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.milestones is None:
            self.milestones = []
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage"""
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining to target date"""
        remaining = self.target_date - datetime.utcnow()
        return max(remaining.days, 0)
    
    @property
    def is_on_track(self) -> bool:
        """Determine if goal is on track based on timeline"""
        total_days = (self.target_date - self.start_date).days
        elapsed_days = (datetime.utcnow() - self.start_date).days
        
        if total_days <= 0:
            return True
        
        expected_progress = (elapsed_days / total_days) * 100
        return self.progress_percentage >= expected_progress * 0.8  # 80% tolerance
    
    def to_dict(self) -> Dict:
        """Convert goal to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data['goal_type'] = self.goal_type.value
        data['status'] = self.status.value
        # Convert datetimes to ISO strings
        data['start_date'] = self.start_date.isoformat()
        data['target_date'] = self.target_date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

class GoalTrackingSystem:
    """Goal tracking and progress monitoring system"""
    
    def __init__(self, data_path: str = "data/goals.json"):
        self.data_path = data_path
        self.goals: Dict[str, Goal] = {}
        self._load_goals()
    
    def _load_goals(self):
        """Load goals from disk"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                for goal_data in data.get('goals', []):
                    goal = self._dict_to_goal(goal_data)
                    self.goals[goal.goal_id] = goal
        except FileNotFoundError:
            self.goals = {}
        except Exception as e:
            logger.error(f"Error loading goals: {e}")
            self.goals = {}
    
    def _save_goals(self):
        """Save goals to disk"""
        try:
            import os
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            data = {
                'goals': [goal.to_dict() for goal in self.goals.values()],
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
    
    def _dict_to_goal(self, data: Dict) -> Goal:
        """Convert dictionary to Goal object"""
        return Goal(
            goal_id=data['goal_id'],
            user_id=data['user_id'],
            title=data['title'],
            description=data['description'],
            goal_type=GoalType(data['goal_type']),
            target_value=data['target_value'],
            current_value=data['current_value'],
            start_date=datetime.fromisoformat(data['start_date']),
            target_date=datetime.fromisoformat(data['target_date']),
            platform=data.get('platform'),
            status=GoalStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            milestones=data.get('milestones', [])
        )
    
    def create_goal(self, user_id: str, title: str, description: str, 
                   goal_type: GoalType, target_value: float, target_date: datetime,
                   platform: Optional[str] = None) -> Goal:
        """Create a new goal"""
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            current_value=0.0,
            start_date=datetime.utcnow(),
            target_date=target_date,
            platform=platform
        )
        
        self.goals[goal.goal_id] = goal
        self._save_goals()
        return goal
    
    def update_goal_progress(self, goal_id: str, current_value: float) -> Optional[Goal]:
        """Update goal progress"""
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        old_value = goal.current_value
        goal.current_value = current_value
        goal.updated_at = datetime.utcnow()
        
        # Check for milestone achievements
        if current_value > old_value:
            self._check_milestones(goal, old_value)
        
        # Check if goal is completed
        if goal.progress_percentage >= 100:
            goal.status = GoalStatus.COMPLETED
            self._add_milestone(goal, "Goal completed!", 100.0)
        
        self._save_goals()
        return goal
    
    def _check_milestones(self, goal: Goal, old_value: float):
        """Check and record milestone achievements"""
        milestones = [25, 50, 75, 90]  # Percentage milestones
        
        for milestone in milestones:
            milestone_value = (milestone / 100) * goal.target_value
            
            # Check if we just passed this milestone
            if old_value < milestone_value <= goal.current_value:
                self._add_milestone(goal, f"Reached {milestone}% of goal", milestone)
    
    def _add_milestone(self, goal: Goal, description: str, percentage: float):
        """Add a milestone to goal"""
        milestone = {
            'id': str(uuid.uuid4()),
            'description': description,
            'percentage': percentage,
            'achieved_at': datetime.utcnow().isoformat(),
            'value_at_achievement': goal.current_value
        }
        goal.milestones.append(milestone)
    
    def get_user_goals(self, user_id: str, status: Optional[GoalStatus] = None) -> List[Goal]:
        """Get all goals for a user"""
        user_goals = [goal for goal in self.goals.values() if goal.user_id == user_id]
        
        if status:
            user_goals = [goal for goal in user_goals if goal.status == status]
        
        return sorted(user_goals, key=lambda x: x.created_at, reverse=True)
    
    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """Get specific goal by ID"""
        return self.goals.get(goal_id)
    
    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal"""
        if goal_id in self.goals:
            del self.goals[goal_id]
            self._save_goals()
            return True
        return False
    
    def pause_goal(self, goal_id: str) -> Optional[Goal]:
        """Pause a goal"""
        if goal_id in self.goals:
            goal = self.goals[goal_id]
            goal.status = GoalStatus.PAUSED
            goal.updated_at = datetime.utcnow()
            self._save_goals()
            return goal
        return None
    
    def resume_goal(self, goal_id: str) -> Optional[Goal]:
        """Resume a paused goal"""
        if goal_id in self.goals:
            goal = self.goals[goal_id]
            if goal.status == GoalStatus.PAUSED:
                goal.status = GoalStatus.ACTIVE
                goal.updated_at = datetime.utcnow()
                self._save_goals()
                return goal
        return None
    
    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """Get goal summary for dashboard"""
        user_goals = self.get_user_goals(user_id)
        active_goals = [g for g in user_goals if g.status == GoalStatus.ACTIVE]
        
        if not user_goals:
            return {
                'total_goals': 0,
                'active_goals': 0,
                'completed_goals': 0,
                'on_track_goals': 0,
                'avg_progress': 0,
                'recent_milestones': [],
                'next_deadlines': []
            }
        
        completed_goals = [g for g in user_goals if g.status == GoalStatus.COMPLETED]
        on_track_goals = [g for g in active_goals if g.is_on_track]
        
        # Calculate average progress
        if user_goals:
            avg_progress = sum(g.progress_percentage for g in user_goals) / len(user_goals)
        else:
            avg_progress = 0
        
        # Get recent milestones
        recent_milestones = []
        for goal in user_goals:
            for milestone in goal.milestones[-3:]:  # Last 3 milestones per goal
                recent_milestones.append({
                    'goal_title': goal.title,
                    'milestone': milestone,
                    'achieved_at': milestone['achieved_at']
                })
        
        # Sort by achievement date
        recent_milestones.sort(key=lambda x: x['achieved_at'], reverse=True)
        recent_milestones = recent_milestones[:10]  # Top 10 most recent
        
        # Get upcoming deadlines
        next_deadlines = []
        for goal in active_goals:
            if goal.days_remaining > 0:
                next_deadlines.append({
                    'goal_id': goal.goal_id,
                    'title': goal.title,
                    'target_date': goal.target_date.isoformat(),
                    'days_remaining': goal.days_remaining,
                    'progress': goal.progress_percentage,
                    'is_on_track': goal.is_on_track
                })
        
        # Sort by days remaining
        next_deadlines.sort(key=lambda x: x['days_remaining'])
        next_deadlines = next_deadlines[:5]  # Next 5 deadlines
        
        return {
            'total_goals': len(user_goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'on_track_goals': len(on_track_goals),
            'avg_progress': round(avg_progress, 1),
            'recent_milestones': recent_milestones,
            'next_deadlines': next_deadlines
        }
    
    def suggest_goals(self, user_id: str, current_metrics: Dict[str, float]) -> List[Dict]:
        """Suggest goals based on current metrics"""
        suggestions = []
        
        # Follower growth suggestion
        current_followers = current_metrics.get('followers', 1000)
        growth_target = current_followers * 1.2  # 20% growth
        suggestions.append({
            'title': 'Grow Social Media Following',
            'description': f'Increase followers from {current_followers:,.0f} to {growth_target:,.0f}',
            'goal_type': GoalType.FOLLOWER_GROWTH.value,
            'target_value': growth_target,
            'recommended_timeline': 90  # days
        })
        
        # Engagement rate suggestion
        current_engagement = current_metrics.get('engagement_rate', 3.0)
        engagement_target = current_engagement + 1.5  # +1.5% improvement
        suggestions.append({
            'title': 'Improve Engagement Rate',
            'description': f'Increase engagement from {current_engagement:.1f}% to {engagement_target:.1f}%',
            'goal_type': GoalType.ENGAGEMENT_RATE.value,
            'target_value': engagement_target,
            'recommended_timeline': 60  # days
        })
        
        # Content volume suggestion
        current_posts = current_metrics.get('monthly_posts', 20)
        content_target = current_posts * 1.5  # 50% more content
        suggestions.append({
            'title': 'Increase Content Production',
            'description': f'Publish {content_target:.0f} posts per month (up from {current_posts:.0f})',
            'goal_type': GoalType.CONTENT_VOLUME.value,
            'target_value': content_target,
            'recommended_timeline': 30  # days
        })
        
        return suggestions

# Global goal tracking instance
goal_tracker = GoalTrackingSystem()