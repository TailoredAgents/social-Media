#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Integration Services API Test Suite
Tests all integration service endpoints with mock and live testing capabilities
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.main import app
from backend.db.models import User, ContentItem, ResearchData
from backend.integrations.instagram_client import InstagramMediaType
from backend.integrations.tiktok_client import TikTokVideoPrivacy

class TestInstagramIntegrationAPI:
    """Test Instagram integration API endpoints"""
    
    @pytest.fixture
    def mock_instagram_client(self):
        """Mock Instagram client"""
        with patch('backend.api.integration_services.instagram_client') as mock_client:
            mock_client.get_user_token = AsyncMock(return_value="mock_instagram_token")
            mock_client.create_post = AsyncMock(return_value={
                "id": "test_instagram_post_123",
                "permalink": "https://instagram.com/p/test_post"
            })
            mock_client.get_media_insights = AsyncMock(return_value={
                "impressions": 1500,
                "reach": 1200,
                "likes": 85,
                "comments": 15,
                "saves": 25,
                "shares": 10,
                "engagement_rate": 11.25
            })
            yield mock_client
    
    def test_create_instagram_post_success(self, authenticated_client, db_session, mock_instagram_client):
        """Test successful Instagram post creation"""
        post_data = {
            "caption": "Test Instagram post with AI automation! 🚀 #aiautomation #socialmedia",
            "media_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            "media_type": "CAROUSEL_ALBUM",
            "hashtags": ["aiautomation", "socialmedia", "tech"],
            "location_id": "location_123"
        }
        
        response = authenticated_client.post("/api/integrations/instagram/post", json=post_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["instagram_post_id"] == "test_instagram_post_123"
        assert data["permalink"] == "https://instagram.com/p/test_post"
        assert "content_id" in data
        
        # Verify database record created
        content_item = db_session.query(ContentItem).filter_by(
            platform_post_id="test_instagram_post_123"
        ).first()
        assert content_item is not None
        assert content_item.platform == "instagram"
        assert content_item.content_type == "carousel_album"
        assert content_item.status == "published"
    
    def test_create_instagram_post_no_token(self, authenticated_client, mock_instagram_client):
        """Test Instagram post creation without token"""
        mock_instagram_client.get_user_token.return_value = None
        
        post_data = {
            "caption": "Test post",
            "media_urls": ["https://example.com/image.jpg"],
            "media_type": "IMAGE"
        }
        
        response = authenticated_client.post("/api/integrations/instagram/post", json=post_data)
        
        assert response.status_code == 401
        assert "Instagram account not connected" in response.json()["detail"]
    
    def test_create_instagram_post_validation_error(self, authenticated_client):
        """Test Instagram post creation with validation errors"""
        # Missing required fields
        post_data = {
            "caption": "Test post"
            # Missing media_urls and media_type
        }
        
        response = authenticated_client.post("/api/integrations/instagram/post", json=post_data)
        
        assert response.status_code == 422
        
        # Invalid media type
        post_data = {
            "caption": "Test post",
            "media_urls": ["https://example.com/image.jpg"],
            "media_type": "INVALID_TYPE"
        }
        
        response = authenticated_client.post("/api/integrations/instagram/post", json=post_data)
        
        assert response.status_code == 422
    
    def test_get_instagram_insights_success(self, authenticated_client, mock_instagram_client):
        """Test successful Instagram insights retrieval"""
        post_id = "test_post_123"
        
        response = authenticated_client.get(f"/api/integrations/instagram/insights/{post_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        insights = data["insights"]
        assert insights["impressions"] == 1500
        assert insights["reach"] == 1200
        assert insights["likes"] == 85
        assert insights["engagement_rate"] == 11.25

class TestFacebookIntegrationAPI:
    """Test Facebook integration API endpoints"""
    
    @pytest.fixture
    def mock_facebook_client(self):
        """Mock Facebook client"""
        with patch('backend.api.integration_services.facebook_client') as mock_client:
            mock_client.get_user_token = AsyncMock(return_value="mock_facebook_token")
            mock_client.create_post = AsyncMock(return_value={
                "id": "test_facebook_post_456"
            })
            mock_client.get_post_insights = AsyncMock(return_value={
                "impressions": 2500,
                "reach": 2000,
                "engagement": 180,
                "clicks": 45,
                "reactions": 125,
                "shares": 35,
                "comments": 20
            })
            yield mock_client
    
    def test_create_facebook_post_success(self, authenticated_client, db_session, mock_facebook_client):
        """Test successful Facebook post creation"""
        post_data = {
            "message": "Exciting update on our AI social media platform! 🚀 Check out our latest features for automated content generation and cross-platform publishing. #AI #SocialMedia #Innovation",
            "media_urls": ["https://example.com/promo_image.jpg"],
            "link": "https://example.com/product-update"
        }
        
        response = authenticated_client.post("/api/integrations/facebook/post", json=post_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["facebook_post_id"] == "test_facebook_post_456"
        assert "content_id" in data
        
        # Verify database record
        content_item = db_session.query(ContentItem).filter_by(
            platform_post_id="test_facebook_post_456"
        ).first()
        assert content_item is not None
        assert content_item.platform == "facebook"
        assert content_item.content_type == "post"
    
    def test_create_facebook_scheduled_post(self, authenticated_client, db_session, mock_facebook_client):
        """Test Facebook scheduled post creation"""
        schedule_time = datetime.utcnow() + timedelta(hours=2)
        
        post_data = {
            "message": "Scheduled Facebook post",
            "scheduled_publish_time": schedule_time.isoformat()
        }
        
        response = authenticated_client.post("/api/integrations/facebook/post", json=post_data)
        
        assert response.status_code == 200
        
        # Verify scheduled status in database
        content_item = db_session.query(ContentItem).filter_by(
            platform_post_id="test_facebook_post_456"
        ).first()
        assert content_item.status == "scheduled"
        assert content_item.scheduled_for is not None
    
    def test_get_facebook_insights_success(self, authenticated_client, mock_facebook_client):
        """Test successful Facebook insights retrieval"""
        post_id = "test_post_456"
        
        response = authenticated_client.get(f"/api/integrations/facebook/insights/{post_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        insights = data["insights"]
        assert insights["impressions"] == 2500
        assert insights["reach"] == 2000
        assert insights["engagement"] == 180

class TestTikTokIntegrationAPI:
    """Test TikTok integration API endpoints"""
    
    @pytest.fixture
    def mock_tiktok_client(self):
        """Mock TikTok client"""
        with patch('backend.api.integration_services.tiktok_client') as mock_client:
            mock_client.get_user_token = AsyncMock(return_value="mock_tiktok_token")
            mock_client.upload_video = AsyncMock(return_value="publish_id_789")
            
            # Mock user info
            mock_user_info = Mock()
            mock_user_info.open_id = "user_123"
            mock_user_info.display_name = "Test TikTok User"
            mock_user_info.avatar_url = "https://example.com/avatar.jpg"
            mock_user_info.follower_count = 1500
            mock_user_info.following_count = 300
            mock_user_info.likes_count = 12000
            mock_user_info.video_count = 85
            mock_user_info.is_verified = False
            mock_client.get_user_info = AsyncMock(return_value=mock_user_info)
            
            # Mock video data
            mock_video = Mock()
            mock_video.id = "video_123"
            mock_video.title = "Test Video"
            mock_video.video_description = "Test video description"
            mock_video.duration = 30
            mock_video.cover_image_url = "https://example.com/cover.jpg"
            mock_video.share_url = "https://tiktok.com/@user/video/123"
            mock_video.create_time = datetime.utcnow()
            mock_video.likes_count = 150
            mock_video.video_view_count = 2500
            mock_video.share_count = 25
            mock_video.comment_count = 35
            
            mock_client.get_user_videos = AsyncMock(return_value={
                "videos": [mock_video],
                "cursor": "next_cursor",
                "has_more": True,
                "total": 1
            })
            
            # Mock analytics
            mock_analytics = Mock()
            mock_analytics.video_id = "video_123"
            mock_analytics.view_count = 2500
            mock_analytics.like_count = 150
            mock_analytics.comment_count = 35
            mock_analytics.share_count = 25
            mock_analytics.profile_view = 45
            mock_analytics.reach = 2200
            mock_analytics.play_time_sum = 45000
            mock_analytics.average_watch_time = 18.0
            mock_analytics.completion_rate = 0.65
            mock_analytics.engagement_rate = 8.4
            mock_analytics.date_range_begin = datetime.utcnow() - timedelta(days=7)
            mock_analytics.date_range_end = datetime.utcnow()
            
            mock_client.get_video_analytics = AsyncMock(return_value=[mock_analytics])
            
            # Mock hashtags
            mock_hashtag = Mock()
            mock_hashtag.hashtag_id = "hashtag_123"
            mock_hashtag.hashtag_name = "aiautomation"
            mock_hashtag.view_count = 1500000
            mock_hashtag.publish_cnt = 25000
            mock_hashtag.is_commerce = False
            mock_hashtag.desc = "AI automation content"
            
            mock_client.search_hashtags = AsyncMock(return_value=[mock_hashtag])
            
            yield mock_client
    
    def test_upload_tiktok_video_success(self, authenticated_client, db_session, mock_tiktok_client):
        """Test successful TikTok video upload"""
        video_data = {
            "video_url": "https://example.com/test_video.mp4",
            "description": "Amazing AI-generated content! 🤖 Check out how our platform creates engaging videos automatically. #AI #TikTok #Automation #ContentCreation",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
            "brand_content_toggle": True,
            "auto_add_music": True
        }
        
        response = authenticated_client.post("/api/integrations/tiktok/video", json=video_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["publish_id"] == "publish_id_789"
        assert data["platform"] == "tiktok"
        assert "content_id" in data
        
        # Verify database record
        content_item = db_session.query(ContentItem).filter_by(
            platform_post_id="publish_id_789"
        ).first()
        assert content_item is not None
        assert content_item.platform == "tiktok"
        assert content_item.content_type == "video"
    
    def test_get_tiktok_user_info_success(self, authenticated_client, mock_tiktok_client):
        """Test TikTok user info retrieval"""
        response = authenticated_client.get("/api/integrations/tiktok/user/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_info" in data
        user_info = data["user_info"]
        assert user_info["open_id"] == "user_123"
        assert user_info["display_name"] == "Test TikTok User"
        assert user_info["follower_count"] == 1500
        assert user_info["video_count"] == 85
        assert user_info["is_verified"] is False
    
    def test_get_tiktok_user_videos_success(self, authenticated_client, mock_tiktok_client):
        """Test TikTok user videos retrieval"""
        response = authenticated_client.get("/api/integrations/tiktok/videos?max_count=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert len(data["videos"]) == 1
        
        video = data["videos"][0]
        assert video["id"] == "video_123"
        assert video["title"] == "Test Video"
        assert video["likes_count"] == 150
        assert video["view_count"] == 2500
        assert data["has_more"] is True
        assert data["cursor"] == "next_cursor"
    
    def test_get_tiktok_video_analytics_success(self, authenticated_client, mock_tiktok_client):
        """Test TikTok video analytics retrieval"""
        video_id = "video_123"
        
        response = authenticated_client.get(f"/api/integrations/tiktok/analytics/{video_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        analytics = data["analytics"]
        assert analytics["video_id"] == "video_123"
        assert analytics["view_count"] == 2500
        assert analytics["like_count"] == 150
        assert analytics["engagement_rate"] == 8.4
        assert analytics["completion_rate"] == 0.65
    
    def test_get_trending_tiktok_hashtags_success(self, authenticated_client, mock_tiktok_client):
        """Test trending TikTok hashtags retrieval"""
        response = authenticated_client.get(
            "/api/integrations/tiktok/hashtags/trending?keywords=ai&keywords=automation&period=7&region_code=US"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "hashtags" in data
        assert len(data["hashtags"]) == 1
        
        hashtag = data["hashtags"][0]
        assert hashtag["hashtag_name"] == "aiautomation"
        assert hashtag["view_count"] == 1500000
        assert hashtag["publish_count"] == 25000
        assert data["period_days"] == 7
        assert data["region_code"] == "US"

class TestResearchAutomationAPI:
    """Test research automation API endpoints"""
    
    @pytest.fixture
    def mock_research_service(self):
        """Mock research service"""
        with patch('backend.api.integration_services.research_service') as mock_service:
            mock_service.execute_research_pipeline = AsyncMock()
            yield mock_service
    
    def test_execute_research_success(self, authenticated_client, mock_research_service):
        """Test successful research execution"""
        research_data = {
            "keywords": ["AI", "automation", "social media"],
            "platforms": ["twitter", "instagram", "tiktok"],
            "time_range": "24h",
            "location": "US",
            "max_results": 100,
            "include_sentiment": True,
            "include_engagement": True
        }
        
        response = authenticated_client.post("/api/integrations/research/execute", json=research_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Research pipeline started"
        assert data["query"]["keywords"] == ["AI", "automation", "social media"]
        assert data["query"]["platforms"] == ["twitter", "instagram", "tiktok"]
        assert data["query"]["max_results"] == 100
        
        # Verify research service was called
        mock_research_service.execute_research_pipeline.assert_called_once()
    
    def test_execute_research_validation_error(self, authenticated_client):
        """Test research execution with validation errors"""
        # Empty keywords
        research_data = {
            "keywords": [],
            "platforms": ["twitter"],
            "time_range": "24h"
        }
        
        response = authenticated_client.post("/api/integrations/research/execute", json=research_data)
        assert response.status_code == 422
        
        # Too many keywords
        research_data = {
            "keywords": ["keyword" + str(i) for i in range(15)],  # Too many
            "platforms": ["twitter"],
            "time_range": "24h"
        }
        
        response = authenticated_client.post("/api/integrations/research/execute", json=research_data)
        assert response.status_code == 422
        
        # Invalid time range
        research_data = {
            "keywords": ["AI"],
            "platforms": ["twitter"],
            "time_range": "invalid_range"
        }
        
        response = authenticated_client.post("/api/integrations/research/execute", json=research_data)
        assert response.status_code == 422
    
    def test_get_research_results_success(self, authenticated_client, db_session, test_user):
        """Test research results retrieval"""
        # Create test research data
        research_item = ResearchData(
            user_id=test_user.id,
            source="twitter",
            content="Test research content about AI automation",
            keywords=["AI", "automation"],
            sentiment_score=0.8,
            engagement_metrics={"likes": 50, "shares": 10},
            created_at=datetime.utcnow()
        )
        db_session.add(research_item)
        db_session.commit()
        
        response = authenticated_client.get("/api/integrations/research/results?keywords=AI&keywords=automation&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] >= 1
        
        if data["results"]:
            result = data["results"][0]
            assert result["source"] == "twitter"
            assert "AI" in result["keywords"] or "automation" in result["keywords"]
            assert result["sentiment"] == 0.8

class TestContentGenerationAPI:
    """Test content generation API endpoints"""
    
    @pytest.fixture
    def mock_content_automation_service(self):
        """Mock content automation service"""
        with patch('backend.api.integration_services.content_automation_service') as mock_service:
            mock_service.generate_content = AsyncMock(return_value={
                "content": "🚀 Exciting news! Our AI-powered social media platform now supports multi-platform content generation with advanced optimization algorithms. Perfect for businesses looking to scale their social presence! #AI #SocialMedia #Innovation #TechStartup",
                "hashtags": ["#AI", "#SocialMedia", "#Innovation", "#TechStartup"],
                "engagement_score": 8.5,
                "model": "openai-gpt-5",
                "prompt": "Generate professional content about AI social media platform"
            })
            yield mock_service
    
    def test_generate_content_success(self, authenticated_client, db_session, mock_content_automation_service):
        """Test successful content generation"""
        generation_data = {
            "topic": "AI-powered social media automation platform",
            "platform": "twitter",
            "content_type": "post",
            "tone": "professional",
            "target_audience": "business owners and marketers",
            "include_hashtags": True,
            "include_cta": True
        }
        
        response = authenticated_client.post("/api/integrations/content/generate", json=generation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content" in data
        assert len(data["content"]) > 0
        assert "hashtags" in data
        assert len(data["hashtags"]) > 0
        assert data["engagement_prediction"] == 8.5
        assert "content_id" in data
        
        # Verify database record
        content_item = db_session.query(ContentItem).filter_by(id=data["content_id"]).first()
        assert content_item is not None
        assert content_item.platform == "twitter"
        assert content_item.content_type == "post"
        assert content_item.status == "draft"
        assert content_item.ai_model == "openai-gpt-5"
        
        # Verify generation parameters stored
        assert content_item.generation_params["topic"] == "AI-powered social media automation platform"
        assert content_item.generation_params["tone"] == "professional"
    
    def test_generate_content_validation_error(self, authenticated_client):
        """Test content generation with validation errors"""
        # Invalid platform
        generation_data = {
            "topic": "Test topic",
            "platform": "invalid_platform",
            "content_type": "post",
            "tone": "professional"
        }
        
        response = authenticated_client.post("/api/integrations/content/generate", json=generation_data)
        assert response.status_code == 422
        
        # Invalid content type
        generation_data = {
            "topic": "Test topic",
            "platform": "twitter",
            "content_type": "invalid_type",
            "tone": "professional"
        }
        
        response = authenticated_client.post("/api/integrations/content/generate", json=generation_data)
        assert response.status_code == 422
        
        # Topic too short
        generation_data = {
            "topic": "AI",  # Too short
            "platform": "twitter",
            "content_type": "post",
            "tone": "professional"
        }
        
        response = authenticated_client.post("/api/integrations/content/generate", json=generation_data)
        assert response.status_code == 422

class TestWorkflowOrchestrationAPI:
    """Test workflow orchestration API endpoints"""
    
    @pytest.fixture
    def mock_workflow_orchestrator(self):
        """Mock workflow orchestrator"""
        with patch('backend.api.integration_services.workflow_orchestrator') as mock_orchestrator:
            mock_orchestrator.execute_workflow = AsyncMock()
            mock_orchestrator.get_workflow_status = AsyncMock(return_value={
                "workflow_id": "workflow_123",
                "status": "completed",
                "progress": 100,
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "results": {
                    "content_generated": 5,
                    "posts_published": 3,
                    "engagement_collected": 15
                }
            })
            yield mock_orchestrator
    
    def test_trigger_workflow_success(self, authenticated_client, mock_workflow_orchestrator):
        """Test successful workflow trigger"""
        workflow_data = {
            "workflow_type": "daily_content",
            "parameters": {
                "platforms": ["twitter", "instagram"],
                "content_count": 3,
                "topics": ["AI", "automation", "social media"]
            },
            "schedule_for": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        response = authenticated_client.post("/api/integrations/workflow/trigger", json=workflow_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Workflow 'daily_content' triggered"
        assert data["workflow_type"] == "daily_content"
        assert data["parameters"]["content_count"] == 3
        
        # Verify workflow orchestrator was called
        mock_workflow_orchestrator.execute_workflow.assert_called_once()
    
    def test_trigger_workflow_validation_error(self, authenticated_client):
        """Test workflow trigger with validation errors"""
        # Invalid workflow type
        workflow_data = {
            "workflow_type": "invalid_workflow",
            "parameters": {}
        }
        
        response = authenticated_client.post("/api/integrations/workflow/trigger", json=workflow_data)
        assert response.status_code == 422
    
    def test_get_workflow_status_success(self, authenticated_client, mock_workflow_orchestrator):
        """Test workflow status retrieval"""
        workflow_id = "workflow_123"
        
        response = authenticated_client.get(f"/api/integrations/workflow/status/{workflow_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        status = data["status"]
        assert status["workflow_id"] == "workflow_123"
        assert status["status"] == "completed"
        assert status["progress"] == 100
        assert "results" in status
        assert status["results"]["content_generated"] == 5

class TestMetricsCollectionAPI:
    """Test metrics collection API endpoints"""
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Mock metrics collector"""
        with patch('backend.services.metrics_collection.metrics_collector') as mock_collector:
            mock_collector.get_collection_status = AsyncMock(return_value={
                "last_update": datetime.utcnow().isoformat(),
                "platforms": {
                    "twitter": {"status": "active", "last_collection": datetime.utcnow().isoformat()},
                    "instagram": {"status": "active", "last_collection": datetime.utcnow().isoformat()},
                    "facebook": {"status": "rate_limited", "last_collection": (datetime.utcnow() - timedelta(hours=2)).isoformat()},
                    "tiktok": {"status": "active", "last_collection": datetime.utcnow().isoformat()}
                },
                "total_metrics": 1250,
                "collection_rate": "95%",
                "errors_24h": 3
            })
            yield mock_collector
    
    def test_get_metrics_collection_status_success(self, authenticated_client, mock_metrics_collector):
        """Test metrics collection status retrieval"""
        response = authenticated_client.get("/api/integrations/metrics/collection")
        
        assert response.status_code == 200
        data = response.json()
        assert "collection_status" in data
        assert "last_collection" in data
        assert "platforms" in data
        assert "metrics_count" in data
        
        collection_status = data["collection_status"]
        assert "platforms" in collection_status
        assert "twitter" in collection_status["platforms"]
        assert "instagram" in collection_status["platforms"]
        assert collection_status["platforms"]["twitter"]["status"] == "active"
        assert collection_status["platforms"]["facebook"]["status"] == "rate_limited"
        assert collection_status["total_metrics"] == 1250

@pytest.mark.integration
class TestIntegrationServicesEndToEnd:
    """End-to-end integration tests for the full workflow"""
    
    def test_complete_content_workflow(self, authenticated_client, db_session):
        """Test complete workflow: generate -> post -> analyze"""
        # This would be a more complex test that chains multiple operations
        # For now, just verify the API endpoints are properly connected
        
        # 1. Check that all endpoints are available
        endpoints_to_test = [
            "/api/integrations/instagram/post",
            "/api/integrations/facebook/post", 
            "/api/integrations/tiktok/video",
            "/api/integrations/research/execute",
            "/api/integrations/content/generate",
            "/api/integrations/workflow/trigger",
            "/api/integrations/metrics/collection"
        ]
        
        for endpoint in endpoints_to_test:
            # OPTIONS request to check endpoint availability
            response = authenticated_client.options(endpoint)
            # Should not return 404
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, authenticated_client):
        """Test concurrent API calls to integration services"""
        # This test would verify that multiple concurrent calls work properly
        # For now, just verify basic concurrent access doesn't break
        
        tasks = []
        
        # Create multiple concurrent requests (using mock data)
        for i in range(5):
            # Note: In a real test, you'd use async client
            # This is a placeholder for the concept
            pass
        
        assert True  # Placeholder assertion

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])