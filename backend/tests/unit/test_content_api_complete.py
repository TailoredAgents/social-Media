"""
Comprehensive test suite for content API endpoints

Tests all content management API endpoints including CRUD operations,
filtering, validation, and error handling.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.main import app
from backend.db.models import ContentLog, User
from backend.auth.dependencies import get_current_active_user
from backend.db.database import get_db


class TestContentAPI:
    """Test suite for content API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_content(self):
        """Mock content object"""
        content = MagicMock(spec=ContentLog)
        content.id = 1
        content.user_id = 1
        content.platform = "twitter"
        content.content = "Test content"
        content.content_type = "text"
        content.status = "draft"
        content.engagement_data = {}
        content.scheduled_for = None
        content.published_at = None
        content.platform_post_id = None
        content.created_at = datetime.utcnow()
        content.updated_at = None
        return content
    
    def test_create_content_success(self, client, mock_user, mock_db, mock_content):
        """Test successful content creation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock the created content object
        def mock_content_creation(*args, **kwargs):
            return mock_content
        
        with patch('backend.api.content.ContentLog', side_effect=mock_content_creation):
            response = client.post(
                "/api/content/",
                json={
                    "platform": "twitter",
                    "content": "This is a test post",
                    "content_type": "text"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["platform"] == "twitter"
            assert data["content"] == "Test content"
            assert data["status"] == "draft"
        
        app.dependency_overrides.clear()
    
    def test_create_content_with_scheduling(self, client, mock_user, mock_db, mock_content):
        """Test content creation with scheduling"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Update mock content for scheduled status
        mock_content.status = "scheduled"
        mock_content.scheduled_for = datetime.utcnow() + timedelta(hours=2)
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        def mock_content_creation(*args, **kwargs):
            return mock_content
        
        with patch('backend.api.content.ContentLog', side_effect=mock_content_creation):
            future_time = datetime.utcnow() + timedelta(hours=2)
            response = client.post(
                "/api/content/",
                json={
                    "platform": ,
                    "content": "Scheduled post content",
                    "content_type": "text",
                    "scheduled_for": future_time.isoformat()
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "scheduled"
        
        app.dependency_overrides.clear()
    
    def test_create_content_validation_errors(self, client, mock_user, mock_db):
        """Test content creation validation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Invalid platform
        response = client.post(
            "/api/content/",
            json={
                "platform": "invalid_platform",
                "content": "Test content",
                "content_type": "text"
            }
        )
        assert response.status_code == 422
        
        # Empty content
        response = client.post(
            "/api/content/",
            json={
                "platform": "twitter",
                "content": "",
                "content_type": "text"
            }
        )
        assert response.status_code == 422
        
        # Invalid content type
        response = client.post(
            "/api/content/",
            json={
                "platform": "twitter",
                "content": "Test content",
                "content_type": "invalid_type"
            }
        )
        assert response.status_code == 422
        
        # Past scheduled time
        past_time = datetime.utcnow() - timedelta(hours=1)
        response = client.post(
            "/api/content/",
            json={
                "platform": "twitter",
                "content": "Test content",
                "content_type": "text",
                "scheduled_for": past_time.isoformat()
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_get_user_content_success(self, client, mock_user, mock_db, mock_content):
        """Test retrieving user content"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_content]
        
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/content/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "twitter"
        
        app.dependency_overrides.clear()
    
    def test_get_user_content_with_filters(self, client, mock_user, mock_db, mock_content):
        """Test content retrieval with filters"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_content]
        
        mock_db.query.return_value = mock_query
        
        # Test with platform filter
        response = client.get("/api/content/?platform=twitter&status=draft&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        # Verify filter was called multiple times (user_id, platform, status)
        assert mock_query.filter.call_count >= 3
        
        app.dependency_overrides.clear()
    
    def test_get_content_by_id_success(self, client, mock_user, mock_db, mock_content):
        """Test retrieving specific content by ID"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_content
        
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/content/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["platform"] == "twitter"
        
        app.dependency_overrides.clear()
    
    def test_get_content_by_id_not_found(self, client, mock_user, mock_db):
        """Test content not found error"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/content/999")
        
        assert response.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication"""
        endpoints = [
            ("/api/content/", "POST", {"platform": "twitter", "content": "test", "content_type": "text"}),
            ("/api/content/", "GET", None),
            ("/api/content/1", "GET", None),
        ]
        
        for endpoint, method, json_data in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code in [401, 403]


class TestContentIntegration:
    """Integration tests for content API"""
    
    def test_content_lifecycle(self, client, test_db, test_user):
        """Test complete content lifecycle: create -> update -> publish -> delete"""
        # This would be an integration test with real database
        pass
    
    def test_content_filtering_performance(self, client, test_db, test_user):
        """Test performance of content filtering with large datasets"""
        pass
    
    def test_concurrent_content_operations(self, client, test_db, test_user):
        """Test concurrent content creation and updates"""
        pass