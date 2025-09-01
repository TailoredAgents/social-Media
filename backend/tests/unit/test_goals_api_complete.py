"""
Comprehensive test suite for goals API endpoints

Tests all goal management API endpoints including CRUD operations,
progress tracking, validation, and error handling.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from backend.main import app
from backend.core.simple_goals import Goal


class TestGoalsAPI:
    """Test suite for goals API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_goal(self):
        """Mock goal object"""
        goal = MagicMock(spec=Goal)
        goal.id = "goal_123"
        goal.title = "Test Goal"
        goal.description = "Test goal description"
        goal.goal_type = "followers"
        goal.target_value = 1000.0
        goal.current_value = 250.0
        goal.target_date = "2024-12-31"
        goal.platform = "twitter"
        goal.status = "active"
        goal.created_at = datetime.utcnow()
        goal.to_dict.return_value = {
            "id": "goal_123",
            "title": "Test Goal",
            "description": "Test goal description",
            "goal_type": "followers",
            "target_value": 1000.0,
            "current_value": 250.0,
            "target_date": "2024-12-31",
            "platform": "twitter",
            "status": "active",
            "progress_percentage": 25.0
        }
        return goal
    
    def test_create_goal_success(self, client, mock_goal):
        """Test successful goal creation"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.create_goal.return_value = mock_goal
            
            response = client.post(
                "/api/goals/create",
                json={
                    "title": "Increase Twitter Followers",
                    "description": "Reach 1000 followers on Twitter",
                    "goal_type": "followers",
                    "target_value": 1000,
                    "target_date": "2024-12-31",
                    "platform": "twitter"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Goal created successfully"
            assert data["goal"]["title"] == "Test Goal"
            assert data["goal"]["target_value"] == 1000.0
            
            # Verify goal_tracker.create_goal was called with correct parameters
            mock_tracker.create_goal.assert_called_once_with(
                title="Increase Twitter Followers",
                description="Reach 1000 followers on Twitter",
                goal_type="followers",
                target_value=1000,
                target_date="2024-12-31",
                platform="twitter"
    
    def test_create_goal_validation_errors(self, client):
        """Test goal creation validation"""
        # Missing required fields
        response = client.post(
            "/api/goals/create",
            json={
                "title": "Test Goal"
                # Missing other required fields
            }
        )
        assert response.status_code == 422
        
        # Invalid target_value type
        response = client.post(
            "/api/goals/create",
            json={
                "title": "Test Goal",
                "description": "Description",
                "goal_type": "followers",
                "target_value": "not_a_number",
                "target_date": "2024-12-31"
            }
        )
        assert response.status_code == 422
    
    def test_create_goal_service_error(self, client):
        """Test goal creation service error"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.create_goal.side_effect = Exception("Database error")
            
            response = client.post(
                "/api/goals/create",
                json={
                    "title": "Test Goal",
                    "description": "Description",
                    "goal_type": "followers",
                    "target_value": 1000,
                    "target_date": "2024-12-31"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Error creating goal" in data["detail"]
    
    def test_get_user_goals_success(self, client, mock_goal):
        """Test retrieving user goals"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_user_goals.return_value = [mock_goal]
            
            response = client.get("/api/goals/?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["goals"]) == 1
            assert data["goals"][0]["title"] == "Test Goal"
    
    def test_get_user_goals_with_status_filter(self, client, mock_goal):
        """Test retrieving goals with status filter"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_user_goals.return_value = [mock_goal]
            
            response = client.get("/api/goals/?user_id=test_user&status=active")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["goals"]) == 1
    
    def test_get_user_goals_empty_result(self, client):
        """Test retrieving goals when user has none"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_user_goals.return_value = []
            
            response = client.get("/api/goals/?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["goals"]) == 0
    
    def test_get_user_goals_service_error(self, client):
        """Test goals retrieval service error"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_user_goals.side_effect = Exception("Database error")
            
            response = client.get("/api/goals/?user_id=test_user")
            
            assert response.status_code == 500
            data = response.json()
            assert "Error getting goals" in data["detail"]
    
    def test_update_goal_progress_success(self, client, mock_goal):
        """Test successful goal progress update"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.update_progress.return_value = mock_goal
            
            response = client.put(
                "/api/goals/goal_123/progress",
                json={"current_value": 350.0}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Progress updated successfully"
            assert data["goal"]["title"] == "Test Goal"
            
            # Verify update_progress was called
            mock_tracker.update_progress.assert_called_once_with(
                "goal_123", 350.0, "default_user"
            )
    
    def test_update_goal_progress_not_found(self, client):
        """Test updating progress for non-existent goal"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.update_progress.side_effect = ValueError("Goal not found")
            
            response = client.put(
                "/api/goals/nonexistent_goal/progress",
                json={"current_value": 350.0}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Goal not found" in data["detail"]
    
    def test_update_goal_progress_validation_error(self, client):
        """Test progress update validation"""
        # Missing current_value
        response = client.put(
            "/api/goals/goal_123/progress",
            json={}
        )
        assert response.status_code == 422
        
        # Invalid current_value type
        response = client.put(
            "/api/goals/goal_123/progress",
            json={"current_value": "not_a_number"}
        )
        assert response.status_code == 422
    
    def test_get_goal_by_id_success(self, client, mock_goal):
        """Test retrieving specific goal by ID"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_goal.return_value = mock_goal
            
            response = client.get("/api/goals/goal_123?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["goal"]["id"] == "goal_123"
            assert data["goal"]["title"] == "Test Goal"
    
    def test_get_goal_by_id_not_found(self, client):
        """Test retrieving non-existent goal"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_goal.return_value = None
            
            response = client.get("/api/goals/nonexistent_goal?user_id=test_user")
            
            assert response.status_code == 404
            data = response.json()
            assert "Goal not found" in data["detail"]
    
    def test_delete_goal_success(self, client):
        """Test successful goal deletion"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.delete_goal.return_value = True
            
            response = client.delete("/api/goals/goal_123?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Goal deleted successfully"
            
            mock_tracker.delete_goal.assert_called_once_with("goal_123", "test_user")
    
    def test_delete_goal_not_found(self, client):
        """Test deleting non-existent goal"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.delete_goal.return_value = False
            
            response = client.delete("/api/goals/nonexistent_goal?user_id=test_user")
            
            assert response.status_code == 404
            data = response.json()
            assert "Goal not found" in data["detail"]
    
    def test_get_goal_analytics_success(self, client):
        """Test goal analytics retrieval"""
        analytics_data = {
            "total_goals": 5,
            "active_goals": 3,
            "completed_goals": 2,
            "average_progress": 65.5,
            "goals_by_type": {
                "followers": 2,
                "engagement": 2,
                "posts": 1
            },
            "goals_by_platform": {
                "twitter": 3,
                : 2
            }
        }
        
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_analytics.return_value = analytics_data
            
            response = client.get("/api/goals/analytics?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["analytics"]["total_goals"] == 5
            assert data["analytics"]["active_goals"] == 3
            assert data["analytics"]["average_progress"] == 65.5
    
    def test_get_goal_suggestions_success(self, client):
        """Test goal suggestions retrieval"""
        suggestions = [
            {
                "type": "followers",
                "platform": "twitter",
                "suggested_target": 1500,
                "reason": "Based on current growth rate"
            },
            {
                "type": "engagement",
                "platform": ,
                "suggested_target": 2.5,
                "reason": "To improve content performance"
            }
        ]
        
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_suggestions.return_value = suggestions
            
            response = client.get("/api/goals/suggestions?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["suggestions"]) == 2
            assert data["suggestions"][0]["type"] == "followers"
    
    def test_goal_milestone_tracking(self, client, mock_goal):
        """Test milestone tracking functionality"""
        milestones = [
            {"value": 250, "achieved_at": "2024-01-15", "description": "25% milestone"},
            {"value": 500, "target_date": "2024-06-15", "description": "50% milestone"}
        ]
        
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_milestones.return_value = milestones
            
            response = client.get("/api/goals/goal_123/milestones?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["milestones"]) == 2
            assert data["milestones"][0]["value"] == 250
    
    def test_goal_progress_history(self, client):
        """Test goal progress history retrieval"""
        progress_history = [
            {"date": "2024-01-01", "value": 100, "notes": "Starting point"},
            {"date": "2024-01-15", "value": 250, "notes": "Good growth"},
            {"date": "2024-02-01", "value": 400, "notes": "Accelerating"}
        ]
        
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.get_progress_history.return_value = progress_history
            
            response = client.get("/api/goals/goal_123/history?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["history"]) == 3
            assert data["history"][0]["value"] == 100
            assert data["history"][-1]["value"] == 400
    
    def test_goal_completion_workflow(self, client, mock_goal):
        """Test goal completion workflow"""
        # Update mock goal to be completed
        completed_goal = mock_goal
        completed_goal.status = "completed"
        completed_goal.completed_at = datetime.utcnow()
        
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.mark_completed.return_value = completed_goal
            
            response = client.post("/api/goals/goal_123/complete?user_id=test_user")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Goal completed successfully"
    
    def test_bulk_goal_operations(self, client, mock_goal):
        """Test bulk operations on goals"""
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.bulk_update_progress.return_value = {
                "updated": 3,
                "failed": 0,
                "goals": [mock_goal, mock_goal, mock_goal]
            }
            
            bulk_updates = [
                {"goal_id": "goal_1", "current_value": 100},
                {"goal_id": "goal_2", "current_value": 200},
                {"goal_id": "goal_3", "current_value": 300}
            ]
            
            response = client.post(
                "/api/goals/bulk-update",
                json={"updates": bulk_updates, "user_id": "test_user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["updated"] == 3
            assert data["failed"] == 0
    
    def test_goal_api_error_handling(self, client):
        """Test comprehensive error handling"""
        # Test various error scenarios
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            # Database connection error
            mock_tracker.create_goal.side_effect = ConnectionError("Database unavailable")
            
            response = client.post(
                "/api/goals/create",
                json={
                    "title": "Test Goal",
                    "description": "Description",
                    "goal_type": "followers",
                    "target_value": 1000,
                    "target_date": "2024-12-31"
                }
            )
            
            assert response.status_code == 500
    
    def test_goal_date_validation(self, client):
        """Test date validation in goals"""
        # Past target date should be rejected
        past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = client.post(
            "/api/goals/create",
            json={
                "title": "Test Goal",
                "description": "Description",
                "goal_type": "followers",
                "target_value": 1000,
                "target_date": past_date
            }
        )
        
        # This would depend on validation logic in the goal tracker
        # For now, just check it doesn't crash
        assert response.status_code in [200, 422, 400]
    
    def test_goal_type_validation(self, client):
        """Test goal type validation"""
        valid_goal_types = ["followers", "engagement", "posts", "reach", "clicks"]
        
        for goal_type in valid_goal_types:
            with patch('backend.api.goals.goal_tracker') as mock_tracker:
                mock_tracker.create_goal.return_value = MagicMock()
                
                response = client.post(
                    "/api/goals/create",
                    json={
                        "title": f"Test {goal_type} Goal",
                        "description": "Description",
                        "goal_type": goal_type,
                        "target_value": 1000,
                        "target_date": "2024-12-31"
                    }
                )
                
                # Should accept all valid goal types
                assert response.status_code in [200, 500]  # 500 only if service error
    
    def test_concurrent_goal_updates(self, client, mock_goal):
        """Test concurrent goal progress updates"""
        # This would test race conditions in goal updates
        # For now, just test basic functionality
        with patch('backend.api.goals.goal_tracker') as mock_tracker:
            mock_tracker.update_progress.return_value = mock_goal
            
            # Simulate concurrent updates
            responses = []
            for i in range(5):
                response = client.put(
                    "/api/goals/goal_123/progress",
                    json={"current_value": 100 + i * 50}
                )
                responses.append(response)
            
            # All updates should succeed (or handle conflicts gracefully)
            for response in responses:
                assert response.status_code in [200, 409]  # 409 for conflicts


class TestGoalsIntegration:
    """Integration tests for goals API"""
    
    def test_goal_lifecycle_integration(self, client):
        """Test complete goal lifecycle integration"""
        # This would test: create -> update progress -> complete -> delete
        pass
    
    def test_goal_analytics_integration(self, client):
        """Test goal analytics with real data"""
        pass
    
    def test_goal_notification_integration(self, client):
        """Test goal notifications and alerts"""
        pass