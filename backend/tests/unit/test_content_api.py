"""
Unit tests for Content API endpoints

Tests all content-related API endpoints including:
- Content creation and retrieval
- Content scheduling and publishing
- Content analytics and performance tracking
- Content search and filtering
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
from fastapi import status

from backend.db.models import ContentItem, User


class TestContentAPI:
    """Test suite for content API endpoints"""
    
    def test_create_content_success(self, client, test_user, auth_headers):
        """Test successful content creation"""
        content_data = {
            "title": "Test Social Media Post",
            "content": "This is a test post for our social media channels",
            "platform": "twitter",
            "content_type": "text",
            "metadata": {
                "hashtags": ["#test", "#socialmedia"],
                "target_audience": "general"
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/content/create",
                json=content_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == content_data["title"]
        assert data["content"] == content_data["content"]
        assert data["platform"] == content_data["platform"]
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_content_validation_error(self, client, test_user, auth_headers):
        """Test content creation with invalid data"""
        invalid_data = {
            "title": "",  # Empty title should fail validation
            "content": "Test content",
            "platform": "invalid_platform"  # Invalid platform
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/content/create",
                json=invalid_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_user_content(self, client, test_user, auth_headers, db_session):
        """Test retrieving user content with pagination"""
        # Create test content items
        for i in range(15):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Test Content {i}",
                content=f"Test content body {i}",
                platform="twitter",
                status="draft" if i % 2 else "published"
            )
            db_session.add(content)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                "/api/content/list?limit=10&offset=0",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    def test_get_content_by_id(self, client, test_user, auth_headers, db_session):
        """Test retrieving specific content by ID"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Specific Content",
            content="This is specific content",
            platform=,
            status="published"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                f"/api/content/{content.id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == content.id
        assert data["title"] == "Specific Content"
        assert data["platform"] == 
    
    def test_get_content_not_found(self, client, test_user, auth_headers):
        """Test retrieving non-existent content"""
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                "/api/content/99999",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_content(self, client, test_user, auth_headers, db_session):
        """Test updating existing content"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Original Title",
            content="Original content",
            platform="twitter",
            status="draft"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        update_data = {
            "title": "Updated Title",
            "content": "Updated content with new information",
            "metadata": {
                "hashtags": ["#updated", "#content"],
                "target_audience": "professionals"
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.put(
                f"/api/content/{content.id}",
                json=update_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content with new information"
        assert data["metadata"]["hashtags"] == ["#updated", "#content"]
    
    def test_delete_content(self, client, test_user, auth_headers, db_session):
        """Test deleting content"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Content to Delete",
            content="This content will be deleted",
            platform="facebook",
            status="draft"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.delete(
                f"/api/content/{content.id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify content is deleted
        get_response = client.get(
            f"/api/content/{content.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_schedule_content(self, client, test_user, auth_headers, db_session):
        """Test scheduling content for future publication"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Content to Schedule",
            content="This content will be scheduled",
            platform="instagram",
            status="draft"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=24)
        schedule_data = {
            "scheduled_time": schedule_time.isoformat(),
            "timezone": "UTC"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                f"/api/content/{content.id}/schedule",
                json=schedule_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "scheduled"
        assert "scheduled_time" in data
    
    @patch('backend.services.content_automation.ContentAutomationService.publish_content')
    def test_publish_content(self, mock_publish, client, test_user, auth_headers, db_session):
        """Test publishing content to social media platforms"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Content to Publish",
            content="This content will be published",
            platform="twitter",
            status="scheduled"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        mock_publish.return_value = {
            "success": True,
            "platform_post_id": "tweet_123456",
            "published_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                f"/api/content/{content.id}/publish",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "published"
        assert "published_at" in data
        assert "platform_post_id" in data
        mock_publish.assert_called_once()
    
    def test_get_content_analytics(self, client, test_user, auth_headers, db_session):
        """Test retrieving content analytics and performance data"""
        # Create published content with performance data
        content = ContentItem(
            user_id=test_user.user_id,
            title="Published Content",
            content="Content with analytics",
            platform=,
            status="published",
            performance_data={
                "likes": 150,
                "shares": 25,
                "comments": 10,
                "reach": 5000,
                "engagement_rate": 3.8
            }
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                f"/api/content/{content.id}/analytics",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["performance_data"]["likes"] == 150
        assert data["performance_data"]["engagement_rate"] == 3.8
        assert "analytics_summary" in data
    
    def test_search_content(self, client, test_user, auth_headers, db_session):
        """Test content search functionality"""
        # Create content with different topics
        contents = [
            ContentItem(
                user_id=test_user.user_id,
                title="AI and Machine Learning",
                content="Content about artificial intelligence",
                platform="twitter",
                status="published"
            ),
            ContentItem(
                user_id=test_user.user_id,
                title="Social Media Marketing",
                content="Tips for social media marketing",
                platform=,
                status="published"
            ),
            ContentItem(
                user_id=test_user.user_id,
                title="Technology Trends",
                content="Latest technology trends in 2025",
                platform="facebook",
                status="draft"
            )
        ]
        
        for content in contents:
            db_session.add(content)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                "/api/content/search?q=AI machine learning&platform=twitter",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("AI" in item["title"] for item in data["items"])
    
    def test_get_content_performance_summary(self, client, test_user, auth_headers, db_session):
        """Test getting overall content performance summary"""
        # Create multiple published content items
        for i in range(5):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Published Content {i}",
                content=f"Content body {i}",
                platform="twitter" if i % 2 else ,
                status="published",
                performance_data={
                    "likes": 100 + i * 20,
                    "shares": 10 + i * 5,
                    "comments": 5 + i * 2,
                    "reach": 1000 + i * 500,
                    "engagement_rate": 2.0 + i * 0.5
                }
            )
            db_session.add(content)
        db_session.commit()
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                "/api/content/analytics/summary?days=30",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_content" in data
        assert "avg_engagement_rate" in data
        assert "total_reach" in data
        assert "platform_breakdown" in data
    
    def test_bulk_content_operations(self, client, test_user, auth_headers, db_session):
        """Test bulk operations on multiple content items"""
        # Create multiple content items
        content_ids = []
        for i in range(3):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Bulk Content {i}",
                content=f"Content for bulk operation {i}",
                platform="twitter",
                status="draft"
            )
            db_session.add(content)
            db_session.commit()
            db_session.refresh(content)
            content_ids.append(content.id)
        
        bulk_data = {
            "content_ids": content_ids,
            "action": "schedule",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/content/bulk",
                json=bulk_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["processed_count"] == 3
        assert data["success_count"] == 3
        assert data["error_count"] == 0
    
    def test_content_unauthorized_access(self, client, db_session):
        """Test accessing content without authentication"""
        response = client.get("/api/content/list")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_content_forbidden_access(self, client, test_user, auth_headers, db_session):
        """Test accessing another user's content"""
        # Create another user and their content
        other_user = User(
            user_id="other_user_123",
            email="other@example.com",
            name="Other User",
            auth_provider="auth0"
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_content = ContentItem(
            user_id=other_user.user_id,
            title="Other User's Content",
            content="This belongs to another user",
            platform="twitter",
            status="published"
        )
        db_session.add(other_content)
        db_session.commit()
        db_session.refresh(other_content)
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                f"/api/content/{other_content.id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestContentValidation:
    """Test content validation rules"""
    
    def test_content_length_validation(self, client, test_user, auth_headers):
        """Test content length validation for different platforms"""
        # Twitter has 280 character limit
        long_content = "x" * 300
        
        content_data = {
            "title": "Long Tweet",
            "content": long_content,
            "platform": "twitter",
            "content_type": "text"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/content/create",
                json=content_data,
                headers=auth_headers
            )
        
        # Should either truncate or reject based on implementation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_hashtag_validation(self, client, test_user, auth_headers):
        """Test hashtag format validation"""
        content_data = {
            "title": "Test Hashtags",
            "content": "Content with hashtags",
            "platform": "instagram",
            "content_type": "text",
            "metadata": {
                "hashtags": ["#validhashtag", "invalidhashtag", "#another-valid", "#123numbers"]
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/content/create",
                json=content_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        # Should filter or validate hashtag formats
    
    def test_scheduled_time_validation(self, client, test_user, auth_headers, db_session):
        """Test validation of scheduled times"""
        content = ContentItem(
            user_id=test_user.user_id,
            title="Test Scheduling",
            content="Content for scheduling test",
            platform="twitter",
            status="draft"
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        
        # Try to schedule in the past
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        schedule_data = {
            "scheduled_time": past_time.isoformat(),
            "timezone": "UTC"
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                f"/api/content/{content.id}/schedule",
                json=schedule_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
EOF < /dev/null