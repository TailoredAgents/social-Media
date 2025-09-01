"""
Comprehensive test suite for integration services API endpoints

Tests all social media integration endpoints including Instagram, Facebook, TikTok,
research automation, content generation, and workflow orchestration services.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.main import app
from backend.db.models import User, ContentItem, ResearchData
from backend.auth.dependencies import get_current_active_user
from backend.db.database import get_db


class TestIntegrationServicesAPI:
    """Test suite for integration services API endpoints"""
    
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
        user.is_premium = True
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_content_item(self):
        """Mock content item"""
        content = MagicMock(spec=ContentItem)
        content.id = 1
        content.user_id = 1
        content.platform = "instagram"
        content.content_type = "image"
        content.content = "Test Instagram post"
        content.media_urls = ["https://example.com/image.jpg"]
        content.status = "scheduled"
        content.created_at = datetime.utcnow()
        return content
    
    def test_instagram_post_success(self, client, mock_user, mock_db, mock_content_item):
        """Test successful Instagram post creation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Mock Instagram client response
        mock_response = {
            "id": "instagram_post_123",
            "permalink": "https://instagram.com/p/abc123/",
            "media_type": "IMAGE"
        }
        
        with patch('backend.api.integration_services.instagram_client') as mock_instagram:
            mock_instagram.create_media.return_value = mock_response
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            response = client.post(
                "/api/integrations/instagram/post",
                json={
                    "caption": "Beautiful sunset! #nature #photography",
                    "media_urls": ["https://example.com/sunset.jpg"],
                    "media_type": "IMAGE",
                    "hashtags": ["nature", "photography"],
                    "location_id": "123456"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["instagram_post_id"] == "instagram_post_123"
            assert data["permalink"] == "https://instagram.com/p/abc123/"
        
        app.dependency_overrides.clear()
    
    def test_instagram_post_validation_error(self, client, mock_user, mock_db):
        """Test Instagram post validation errors"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Caption too long
        response = client.post(
            "/api/integrations/instagram/post",
            json={
                "caption": "A" * 2300,  # Exceeds 2200 character limit
                "media_urls": ["https://example.com/image.jpg"],
                "media_type": "IMAGE"
            }
        )
        assert response.status_code == 422
        
        # Invalid media type
        response = client.post(
            "/api/integrations/instagram/post",
            json={
                "caption": "Test post",
                "media_urls": ["https://example.com/image.jpg"],
                "media_type": "INVALID_TYPE"
            }
        )
        assert response.status_code == 422
        
        # No media URLs
        response = client.post(
            "/api/integrations/instagram/post",
            json={
                "caption": "Test post",
                "media_urls": [],
                "media_type": "IMAGE"
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_instagram_post_api_error(self, client, mock_user, mock_db):
        """Test Instagram API error handling"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        with patch('backend.api.integration_services.instagram_client') as mock_instagram:
            mock_instagram.create_media.side_effect = Exception("Invalid access token")
            
            response = client.post(
                "/api/integrations/instagram/post",
                json={
                    "caption": "Test post",
                    "media_urls": ["https://example.com/image.jpg"],
                    "media_type": "IMAGE"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Error posting to Instagram" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_facebook_post_success(self, client, mock_user, mock_db):
        """Test successful Facebook post creation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_response = {
            "id": "facebook_post_456",
            "post_id": "123456789_987654321"
        }
        
        with patch('backend.api.integration_services.facebook_client') as mock_facebook:
            mock_facebook.create_post.return_value = mock_response
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/facebook/post",
                json={
                    "message": "Exciting news to share with everyone!",
                    "media_urls": ["https://example.com/news.jpg"],
                    "link": "https://example.com/article",
                    "targeting": {"countries": ["US", "CA"]}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["facebook_post_id"] == "facebook_post_456"
        
        app.dependency_overrides.clear()
    
    def test_facebook_scheduled_post(self, client, mock_user, mock_db):
        """Test Facebook scheduled post creation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        future_time = datetime.utcnow() + timedelta(hours=2)
        
        with patch('backend.api.integration_services.facebook_client') as mock_facebook:
            mock_facebook.schedule_post.return_value = {"id": "scheduled_post_789"}
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/facebook/post",
                json={
                    "message": "Scheduled post content",
                    "scheduled_publish_time": future_time.isoformat()
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "scheduled" in data["message"].lower()
        
        app.dependency_overrides.clear()
    
    def test_tiktok_video_upload_success(self, client, mock_user, mock_db):
        """Test successful TikTok video upload"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_response = {
            "publish_id": "tiktok_video_123",
            "share_url": "https://tiktok.com/@user/video/123",
            "embed_html": "<iframe>...</iframe>"
        }
        
        with patch('backend.api.integration_services.tiktok_client') as mock_tiktok:
            mock_tiktok.upload_video.return_value = mock_response
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/tiktok/upload",
                json={
                    "video_url": "https://example.com/video.mp4",
                    "description": "Amazing dance video! #dance #trending",
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "auto_add_music": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["publish_id"] == "tiktok_video_123"
            assert data["share_url"] == "https://tiktok.com/@user/video/123"
        
        app.dependency_overrides.clear()
    
    def test_tiktok_video_validation_error(self, client, mock_user, mock_db):
        """Test TikTok video validation errors"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Invalid privacy level
        response = client.post(
            "/api/integrations/tiktok/upload",
            json={
                "video_url": "https://example.com/video.mp4",
                "description": "Test video",
                "privacy_level": "INVALID_PRIVACY"
            }
        )
        assert response.status_code == 422
        
        # Description too long
        response = client.post(
            "/api/integrations/tiktok/upload",
            json={
                "video_url": "https://example.com/video.mp4",
                "description": "A" * 2300,  # Exceeds limit
                "privacy_level": "PUBLIC_TO_EVERYONE"
            }
        )
        assert response.status_code == 422
        
        app.dependency_overrides.clear()
    
    def test_research_automation_success(self, client, mock_user, mock_db):
        """Test successful research automation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_research_results = {
            "query_id": "research_123",
            "results": [
                {
                    "title": "AI Trends 2024",
                    "summary": "Latest developments in AI technology",
                    "source": "TechCrunch",
                    "url": "https://techcrunch.com/ai-trends-2024",
                    "relevance_score": 0.92,
                    "sentiment": "positive"
                },
                {
                    "title": "Machine Learning Breakthroughs",
                    "summary": "Recent ML research findings",
                    "source": "ArXiv",
                    "url": "https://arxiv.org/abs/2024.01234",
                    "relevance_score": 0.88,
                    "sentiment": "neutral"
                }
            ],
            "total_results": 2,
            "processing_time": 3.45
        }
        
        with patch('backend.api.integration_services.research_service') as mock_research:
            mock_research.execute_research_query.return_value = mock_research_results
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/research/query",
                json={
                    "query": "artificial intelligence trends 2024",
                    "sources": ["web", "academic", "news"],
                    "max_results": 10,
                    "include_sentiment": True,
                    "language": "en"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["query_id"] == "research_123"
            assert len(data["results"]) == 2
            assert data["total_results"] == 2
        
        app.dependency_overrides.clear()
    
    def test_content_automation_generation(self, client, mock_user, mock_db):
        """Test automated content generation"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_generated_content = {
            "content_id": "generated_456",
            "platform": "twitter",
            "content": "🚀 Exciting developments in AI are reshaping our future! From healthcare innovations to creative tools, the possibilities are endless. What AI application excites you most? #AI #Innovation #TechTrends",
            "content_type": "text",
            "estimated_engagement": 7.8,
            "hashtags": ["AI", "Innovation", "TechTrends"],
            "optimal_posting_time": "2024-01-16T14:30:00Z",
            "generation_metadata": {
                "model_used": "gpt-5",
                "generation_time": 2.1,
                "confidence_score": 0.94
            }
        }
        
        with patch('backend.api.integration_services.content_automation_service') as mock_content:
            mock_content.generate_content.return_value = mock_generated_content
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/content/generate",
                json={
                    "platform": "twitter",
                    "content_type": "text",
                    "topic": "artificial intelligence trends",
                    "tone": "enthusiastic",
                    "target_audience": "tech professionals",
                    "include_hashtags": True,
                    "max_length": 280
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["content_id"] == "generated_456"
            assert data["platform"] == "twitter"
            assert len(data["content"]) <= 280
            assert data["estimated_engagement"] == 7.8
        
        app.dependency_overrides.clear()
    
    def test_workflow_orchestration_execution(self, client, mock_user, mock_db):
        """Test workflow orchestration execution"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_workflow_result = {
            "workflow_id": "workflow_789",
            "workflow_type": "daily_content_cycle",
            "status": "completed",
            "steps_completed": [
                {"step": "research", "status": "completed", "duration": 45.2},
                {"step": "content_generation", "status": "completed", "duration": 32.1},
                {"step": "content_scheduling", "status": "completed", "duration": 12.8},
                {"step": "performance_analysis", "status": "completed", "duration": 18.5}
            ],
            "total_duration": 108.6,
            "content_generated": 3,
            "posts_scheduled": 3,
            "next_execution": "2024-01-17T06:00:00Z"
        }
        
        with patch('backend.api.integration_services.workflow_orchestrator') as mock_orchestrator:
            mock_orchestrator.execute_workflow.return_value = mock_workflow_result
            
            response = client.post(
                "/api/integrations/workflow/execute",
                json={
                    "workflow_type": "daily_content_cycle",
                    "parameters": {
                        "platforms": ["twitter", ],
                        "content_count": 3,
                        "schedule_immediately": False
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["workflow_id"] == "workflow_789"
            assert data["workflow_status"] == "completed"
            assert data["content_generated"] == 3
            assert len(data["steps_completed"]) == 4
        
        app.dependency_overrides.clear()
    
    def test_integration_analytics_retrieval(self, client, mock_user, mock_db):
        """Test integration analytics retrieval"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        mock_analytics = {
            "period": "last_30_days",
            "platforms": {
                "instagram": {
                    "posts_created": 25,
                    "total_likes": 1250,
                    "total_comments": 89,
                    "total_shares": 45,
                    "avg_engagement_rate": 6.8,
                    "top_performing_post": "post_123"
                },
                "facebook": {
                    "posts_created": 18,
                    "total_reactions": 890,
                    "total_comments": 124,
                    "total_shares": 67,
                    "avg_engagement_rate": 5.2,
                    "top_performing_post": "post_456"
                },
                "tiktok": {
                    "videos_uploaded": 12,
                    "total_views": 15600,
                    "total_likes": 2340,
                    "total_shares": 156,
                    "avg_engagement_rate": 8.9,
                    "top_performing_video": "video_789"
                }
            },
            "overall_metrics": {
                "total_content_created": 55,
                "total_engagement": 20958,
                "avg_engagement_rate": 6.8,
                "growth_rate": 12.3
            }
        }
        
        mock_db.query.return_value.filter.return_value.all.return_value = []  # Mock query results
        
        with patch('backend.api.integration_services.instagram_client') as mock_instagram, \
             patch('backend.api.integration_services.facebook_client') as mock_facebook, \
             patch('backend.api.integration_services.tiktok_client') as mock_tiktok:
            
            mock_instagram.get_analytics.return_value = mock_analytics["platforms"]["instagram"]
            mock_facebook.get_analytics.return_value = mock_analytics["platforms"]["facebook"]
            mock_tiktok.get_analytics.return_value = mock_analytics["platforms"]["tiktok"]
            
            response = client.get("/api/integrations/analytics?period=last_30_days")
            
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "last_30_days"
            assert "platforms" in data
            assert "overall_metrics" in data
            assert data["platforms"]["instagram"]["posts_created"] == 25
        
        app.dependency_overrides.clear()
    
    def test_integration_error_handling(self, client, mock_user, mock_db):
        """Test comprehensive error handling across integrations"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        # Test rate limiting error
        with patch('backend.api.integration_services.instagram_client') as mock_instagram:
            mock_instagram.create_media.side_effect = Exception("Rate limit exceeded")
            
            response = client.post(
                "/api/integrations/instagram/post",
                json={
                    "caption": "Test post",
                    "media_urls": ["https://example.com/image.jpg"],
                    "media_type": "IMAGE"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Rate limit exceeded" in data["detail"]
        
        # Test authentication error
        with patch('backend.api.integration_services.facebook_client') as mock_facebook:
            mock_facebook.create_post.side_effect = Exception("Invalid access token")
            
            response = client.post(
                "/api/integrations/facebook/post",
                json={"message": "Test message"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Invalid access token" in data["detail"]
        
        app.dependency_overrides.clear()
    
    def test_integration_authentication_required(self, client):
        """Test that all integration endpoints require authentication"""
        endpoints = [
            ("/api/integrations/instagram/post", "POST", {"caption": "test", "media_urls": ["url"], "media_type": "IMAGE"}),
            ("/api/integrations/facebook/post", "POST", {"message": "test"}),
            ("/api/integrations/tiktok/upload", "POST", {"video_url": "url", "description": "test"}),
            ("/api/integrations/research/query", "POST", {"query": "test", "sources": ["web"]}),
            ("/api/integrations/content/generate", "POST", {"platform": "twitter", "topic": "test"}),
            ("/api/integrations/workflow/execute", "POST", {"workflow_type": "test"}),
            ("/api/integrations/analytics", "GET", None)
        ]
        
        for endpoint, method, json_data in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code in [401, 403]
    
    def test_integration_bulk_operations(self, client, mock_user, mock_db):
        """Test bulk operations across multiple platforms"""
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        bulk_content = [
            {
                "platform": "instagram",
                "content": "Beautiful landscape #nature",
                "media_urls": ["https://example.com/landscape.jpg"],
                "content_type": "IMAGE"
            },
            {
                "platform": "facebook",
                "content": "Check out this amazing view!",
                "media_urls": ["https://example.com/landscape.jpg"]
            },
            {
                "platform": "twitter",
                "content": "Nature at its finest! 🌄 #landscape #photography"
            }
        ]
        
        with patch('backend.api.integration_services.instagram_client') as mock_instagram, \
             patch('backend.api.integration_services.facebook_client') as mock_facebook, \
             patch('backend.api.integration_services.TwitterClient') as mock_twitter:
            
            mock_instagram.create_media.return_value = {"id": "insta_123"}
            mock_facebook.create_post.return_value = {"id": "fb_456"}
            mock_twitter.return_value.create_tweet.return_value = {"id": "tweet_789"}
            
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            
            response = client.post(
                "/api/integrations/bulk/post",
                json={"content_items": bulk_content}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["total_posted"] == 3
            assert len(data["results"]) == 3
        
        app.dependency_overrides.clear()


class TestIntegrationServicesPerformance:
    """Performance tests for integration services"""
    
    def test_concurrent_platform_posting(self, client, mock_user, mock_db):
        """Test concurrent posting to multiple platforms"""
        # Test concurrent operations performance
        pass
    
    def test_rate_limiting_compliance(self, client, mock_user, mock_db):
        """Test compliance with platform rate limits"""
        # Test rate limiting behavior
        pass
    
    def test_large_content_processing(self, client, mock_user, mock_db):
        """Test processing of large content batches"""
        # Test performance with large datasets
        pass


class TestIntegrationServicesIntegration:
    """Integration tests for services API"""
    
    def test_end_to_end_content_pipeline(self, client, test_db, test_user):
        """Test complete content pipeline from research to posting"""
        # Test: research -> generate -> post -> analyze
        pass
    
    def test_cross_platform_content_adaptation(self, client, test_db, test_user):
        """Test content adaptation across different platforms"""
        pass
    
    def test_error_recovery_and_retry_logic(self, client, test_db, test_user):
        """Test error recovery mechanisms"""
        pass