"""
Unit tests for Goals API endpoints

Tests all goal-related API endpoints including:
- Goal creation and management
- Progress tracking and updates
- Goal analytics and reporting
- Milestone management
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
from fastapi import status

from backend.db.models import Goal, GoalProgress, User


class TestGoalsAPI:
    """Test suite for goals API endpoints"""
    
    def test_create_goal_success(self, client, test_user, auth_headers):
        """Test successful goal creation"""
        goal_data = {
            "title": "Increase LinkedIn Followers",
            "description": "Grow LinkedIn following to build professional network",
            "target_metric": "followers",
            "target_value": 5000,
            "target_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            "category": "growth",
            "priority": "high"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/goals/create",
                json=goal_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == goal_data["title"]
        assert data["target_metric"] == goal_data["target_metric"]
        assert data["target_value"] == goal_data["target_value"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_goal_validation_error(self, client, test_user, auth_headers):
        """Test goal creation with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "target_metric": "invalid_metric",  # Invalid metric
            "target_value": -100,  # Negative value
            "target_date": "invalid_date_format"  # Invalid date
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/goals/create",
                json=invalid_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_user_goals(self, client, test_user, auth_headers, db_session):
        """Test retrieving user goals with filtering"""
        # Create test goals with different statuses
        goals_data = [
            {"title": "Active Goal 1", "status": "active", "priority": "high"},
            {"title": "Active Goal 2", "status": "active", "priority": "medium"},
            {"title": "Completed Goal", "status": "completed", "priority": "high"},
            {"title": "Paused Goal", "status": "paused", "priority": "low"}
        ]
        
        for goal_data in goals_data:
            goal = Goal(
                user_id=test_user.user_id,
                title=goal_data["title"],
                description="Test goal description",
                target_metric="followers",
                target_value=1000,
                current_value=500,
                target_date=datetime.now(timezone.utc) + timedelta(days=30),
                category="growth",
                priority=goal_data["priority"],
                status=goal_data["status"]
            )
            db_session.add(goal)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            # Test getting all goals
            response = client.get("/api/goals/list", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 4
            
            # Test filtering by status  
            response = client.get("/api/goals/list?status=active", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 2
            
            # Test filtering by priority
            response = client.get("/api/goals/list?priority=high", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 2
    
    def test_get_goal_by_id(self, client, test_user, auth_headers, db_session):
        """Test retrieving specific goal by ID"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Specific Goal",
            description="This is a specific goal for testing",
            target_metric="engagement_rate",
            target_value=5.0,
            current_value=3.2,
            target_date=datetime.now(timezone.utc) + timedelta(days=60),
            category="engagement",
            priority="medium",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(f"/api/goals/{goal.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == goal.id
        assert data["title"] == "Specific Goal"
        assert data["target_metric"] == "engagement_rate"
        assert data["current_value"] == 3.2
    
    def test_update_goal(self, client, test_user, auth_headers, db_session):
        """Test updating an existing goal"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Original Goal",
            description="Original description",
            target_metric="followers",
            target_value=1000,
            current_value=400,
            target_date=datetime.now(timezone.utc) + timedelta(days=30),
            category="growth",
            priority="medium",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        update_data = {
            "title": "Updated Goal Title",
            "description": "Updated goal description with more details",
            "target_value": 1500,
            "priority": "high",
            "metadata": {
                "kpis": ["follower_growth_rate", "engagement_increase"],
                "platforms": [, "twitter"]
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.put(
                f"/api/goals/{goal.id}",
                json=update_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Goal Title"
        assert data["target_value"] == 1500
        assert data["priority"] == "high"
    
    def test_update_goal_progress(self, client, test_user, auth_headers, db_session):
        """Test updating goal progress"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Progress Goal",
            description="Goal for testing progress updates",
            target_metric="followers",
            target_value=2000,
            current_value=800,
            target_date=datetime.now(timezone.utc) + timedelta(days=45),
            category="growth",
            priority="high",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        progress_data = {
            "progress_value": 1200,
            "notes": "Good progress this week due to increased posting frequency",
            "metadata": {
                "source": "manual_update",
                "platform_breakdown": {
                    "twitter": 300,
                    : 200,
                    "instagram": 100
                }
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                f"/api/goals/{goal.id}/progress",
                json=progress_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["progress_value"] == 1200
        assert data["progress_percentage"] == 60.0  # 1200/2000 * 100
        assert "recorded_at" in data
    
    def test_get_goal_progress_history(self, client, test_user, auth_headers, db_session):
        """Test retrieving goal progress history"""
        goal = Goal(
            user_id=test_user.user_id,
            title="History Goal",
            description="Goal for testing progress history",
            target_metric="reach",
            target_value=50000,
            current_value=20000,
            target_date=datetime.now(timezone.utc) + timedelta(days=60),
            category="brand_awareness",
            priority="medium",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # Create progress history
        progress_entries = [
            {"value": 10000, "days_ago": 30},
            {"value": 15000, "days_ago": 20},
            {"value": 18000, "days_ago": 10},
            {"value": 20000, "days_ago": 0}
        ]
        
        for entry in progress_entries:
            progress = GoalProgress(
                goal_id=goal.id,
                progress_value=entry["value"],
                progress_percentage=(entry["value"] / 50000) * 100,
                recorded_at=datetime.now(timezone.utc) - timedelta(days=entry["days_ago"])
            )
            db_session.add(progress)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                f"/api/goals/{goal.id}/progress/history?days=60",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["progress_history"]) == 4
        assert data["goal_id"] == goal.id
        assert "trend_analysis" in data
    
    def test_goal_milestone_management(self, client, test_user, auth_headers, db_session):
        """Test managing goal milestones"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Milestone Goal",
            description="Goal with milestones",
            target_metric="followers",
            target_value=10000,
            current_value=2000,
            target_date=datetime.now(timezone.utc) + timedelta(days=120),
            category="growth",
            priority="high",
            status="active",
            metadata={
                "milestones": [
                    {
                        "title": "25% Progress",
                        "target_value": 2500,
                        "target_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                        "completed": False
                    },
                    {
                        "title": "50% Progress", 
                        "target_value": 5000,
                        "target_date": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
                        "completed": False
                    }
                ]
            }
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # Add a new milestone
        milestone_data = {
            "title": "75% Progress",
            "target_value": 7500,
            "target_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            "description": "Three-quarters completion milestone"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                f"/api/goals/{goal.id}/milestones",
                json=milestone_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["milestones"]) == 3
        assert any(m["title"] == "75% Progress" for m in data["milestones"])
    
    def test_goal_analytics_summary(self, client, test_user, auth_headers, db_session):
        """Test getting goal analytics summary"""
        # Create multiple goals with different statuses and progress
        goals_data = [
            {"status": "active", "current": 800, "target": 1000, "category": "growth"},
            {"status": "active", "current": 60, "target": 100, "category": "engagement"},
            {"status": "completed", "current": 500, "target": 500, "category": "conversion"},
            {"status": "paused", "current": 200, "target": 1000, "category": "growth"}
        ]
        
        for i, data in enumerate(goals_data):
            goal = Goal(
                user_id=test_user.user_id,
                title=f"Analytics Goal {i+1}",
                description=f"Goal for analytics testing {i+1}",
                target_metric="followers",
                target_value=data["target"],
                current_value=data["current"],
                target_date=datetime.now(timezone.utc) + timedelta(days=30),
                category=data["category"],
                priority="medium",
                status=data["status"]
            )
            db_session.add(goal)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get("/api/goals/analytics/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_goals"] == 4
        assert data["active_goals"] == 2
        assert data["completed_goals"] == 1
        assert data["paused_goals"] == 1
        assert "average_progress" in data
        assert "category_breakdown" in data
    
    def test_goal_recommendations(self, client, test_user, auth_headers, db_session):
        """Test getting AI-powered goal recommendations"""
        # Create user content and goals for context
        goal = Goal(
            user_id=test_user.user_id,
            title="Current Goal",
            description="Existing goal for recommendations",
            target_metric="engagement_rate",
            target_value=5.0,
            current_value=3.0,
            target_date=datetime.now(timezone.utc) + timedelta(days=30),
            category="engagement",
            priority="high",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        
        with patch('backend.services.goals_progress_service.GoalsProgressService.get_ai_recommendations') as mock_recommendations:
            mock_recommendations.return_value = {
                "recommended_goals": [
                    {
                        "title": "Increase Video Content",
                        "description": "Focus on video content to boost engagement rates",
                        "target_metric": "video_engagement_rate",
                        "suggested_target": 7.5,
                        "reasoning": "Video content typically gets 3x more engagement",
                        "priority": "high"
                    }
                ],
                "optimization_tips": [
                    "Post during peak hours (9-11 AM, 2-4 PM)",
                    "Use more interactive content formats",
                    "Engage with comments within first hour of posting"
                ]
            }
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.get("/api/goals/recommendations", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommended_goals" in data
        assert "optimization_tips" in data
        assert len(data["recommended_goals"]) > 0
    
    def test_goal_performance_prediction(self, client, test_user, auth_headers, db_session):
        """Test goal performance prediction based on current trends"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Prediction Goal",
            description="Goal for testing performance prediction",
            target_metric="followers",
            target_value=5000,
            current_value=2000,
            target_date=datetime.now(timezone.utc) + timedelta(days=60),
            category="growth",
            priority="high",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # Add progress history for prediction
        progress_entries = [
            {"value": 1500, "days_ago": 30},
            {"value": 1750, "days_ago": 20},
            {"value": 1900, "days_ago": 10},
            {"value": 2000, "days_ago": 0}
        ]
        
        for entry in progress_entries:
            progress = GoalProgress(
                goal_id=goal.id,
                progress_value=entry["value"],
                progress_percentage=(entry["value"] / 5000) * 100,
                recorded_at=datetime.now(timezone.utc) - timedelta(days=entry["days_ago"])
            )
            db_session.add(progress)
        db_session.commit()
        
        with patch('backend.services.goals_progress_service.GoalsProgressService.predict_goal_completion') as mock_prediction:
            mock_prediction.return_value = {
                "predicted_completion_date": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
                "probability_of_success": 0.85,
                "predicted_final_value": 5200,
                "growth_rate": 16.67,  # followers per day
                "confidence_interval": {"low": 4800, "high": 5600},
                "recommendations": [
                    "Current growth rate is excellent, maintain consistency",
                    "Consider increasing posting frequency in final 30 days"
                ]
            }
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.get(f"/api/goals/{goal.id}/prediction", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "predicted_completion_date" in data
        assert "probability_of_success" in data
        assert data["probability_of_success"] == 0.85
        assert "growth_rate" in data
    
    def test_delete_goal(self, client, test_user, auth_headers, db_session):
        """Test deleting a goal"""
        goal = Goal(
            user_id=test_user.user_id,
            title="Goal to Delete",
            description="This goal will be deleted",
            target_metric="followers",
            target_value=1000,
            current_value=300,
            target_date=datetime.now(timezone.utc) + timedelta(days=30),
            category="growth",
            priority="low",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.delete(f"/api/goals/{goal.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify goal is deleted
        get_response = client.get(f"/api/goals/{goal.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_goal_unauthorized_access(self, client):
        """Test accessing goals without authentication"""
        response = client.get("/api/goals/list")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_goal_forbidden_access(self, client, test_user, auth_headers, db_session):
        """Test accessing another user's goals"""
        # Create another user and their goal
        other_user = User(
            user_id="other_user_456",
            email="other@example.com",
            name="Other User",
            auth_provider="auth0"
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_goal = Goal(
            user_id=other_user.user_id,
            title="Other User's Goal",
            description="This belongs to another user",
            target_metric="followers",
            target_value=1000,
            current_value=500,
            target_date=datetime.now(timezone.utc) + timedelta(days=30),
            category="growth",
            priority="medium",
            status="active"
        )
        db_session.add(other_goal)
        db_session.commit()
        db_session.refresh(other_goal)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(f"/api/goals/{other_goal.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGoalValidation:
    """Test goal validation rules"""
    
    def test_target_date_validation(self, client, test_user, auth_headers):
        """Test target date validation (must be in future)"""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        goal_data = {
            "title": "Invalid Date Goal",
            "description": "Goal with past target date",
            "target_metric": "followers",
            "target_value": 1000,
            "target_date": past_date.isoformat(),
            "category": "growth",
            "priority": "medium"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/goals/create",
                json=goal_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_target_value_validation(self, client, test_user, auth_headers):
        """Test target value validation (must be positive)"""
        goal_data = {
            "title": "Invalid Value Goal",
            "description": "Goal with negative target value",
            "target_metric": "followers",
            "target_value": -500,  # Invalid negative value
            "target_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "category": "growth",
            "priority": "medium"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/goals/create",
                json=goal_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_goal_metric_validation(self, client, test_user, auth_headers):
        """Test validation of supported goal metrics"""
        valid_metrics = [
            "followers", "engagement_rate", "reach", "website_clicks",
            "leads_generated", "sales", "brand_mentions", "content_shares"
        ]
        
        for metric in valid_metrics:
            goal_data = {
                "title": f"Test {metric} Goal",
                "description": f"Goal for testing {metric} metric",
                "target_metric": metric,
                "target_value": 1000,
                "target_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "category": "growth",
                "priority": "medium"
            }
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    "/api/goals/create",
                    json=goal_data,
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_201_CREATED
EOF < /dev/null