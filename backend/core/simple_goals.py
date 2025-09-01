import json
import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SimpleGoal:
    goal_id: str
    title: str
    description: str
    goal_type: str
    target_value: float
    current_value: float
    start_date: str
    target_date: str
    platform: Optional[str] = None
    status: str = "active"
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()
    
    @property
    def progress_percentage(self) -> float:
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SimpleGoalTracker:
    """Simplified goal tracking system"""
    
    def __init__(self, data_path: str = "data/goals.json"):
        self.data_path = data_path
        self.goals: Dict[str, SimpleGoal] = {}
        self._load_goals()
    
    def _load_goals(self):
        """Load goals from disk"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    for goal_data in data.get('goals', []):
                        goal = SimpleGoal(**goal_data)
                        self.goals[goal.goal_id] = goal
        except Exception as e:
            logger.error(f"Error loading goals: {e}")
            self.goals = {}
    
    def _save_goals(self):
        """Save goals to disk"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            data = {
                'goals': [goal.to_dict() for goal in self.goals.values()],
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
    
    def create_goal(self, title: str, description: str, goal_type: str, 
                   target_value: float, target_date: str, platform: Optional[str] = None) -> SimpleGoal:
        """Create a new goal"""
        goal = SimpleGoal(
            goal_id=str(uuid.uuid4()),
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            current_value=0.0,
            start_date=datetime.utcnow().isoformat(),
            target_date=target_date,
            platform=platform
        )
        
        self.goals[goal.goal_id] = goal
        self._save_goals()
        return goal
    
    def update_goal_progress(self, goal_id: str, current_value: float) -> Optional[SimpleGoal]:
        """Update goal progress"""
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        goal.current_value = current_value
        goal.updated_at = datetime.utcnow().isoformat()
        
        if goal.progress_percentage >= 100:
            goal.status = "completed"
        
        self._save_goals()
        return goal
    
    def get_user_goals(self, user_id: str = "default_user") -> List[SimpleGoal]:
        """Get all goals for a user"""
        return list(self.goals.values())
    
    def get_goal_by_id(self, goal_id: str) -> Optional[SimpleGoal]:
        """Get specific goal by ID"""
        return self.goals.get(goal_id)
    
    def get_dashboard_summary(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Get goal summary for dashboard"""
        user_goals = self.get_user_goals(user_id)
        active_goals = [g for g in user_goals if g.status == 'active']
        completed_goals = [g for g in user_goals if g.status == 'completed']
        
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
        
        avg_progress = sum(g.progress_percentage for g in user_goals) / len(user_goals)
        
        return {
            'total_goals': len(user_goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'on_track_goals': len([g for g in active_goals if g.progress_percentage > 50]),
            'avg_progress': round(avg_progress, 1),
            'recent_milestones': [],
            'next_deadlines': [
                {
                    'goal_id': g.goal_id,
                    'title': g.title,
                    'target_date': g.target_date,
                    'progress': g.progress_percentage,
                    'is_on_track': g.progress_percentage > 50
                }
                for g in active_goals[:5]
            ]
        }

# Global goal tracker
goal_tracker = SimpleGoalTracker()