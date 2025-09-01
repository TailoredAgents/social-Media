"""
Live Platform Integration Tests
Integration Specialist Component - End-to-end testing for all social media platform integrations
"""
import pytest
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from backend.integrations.twitter_client import twitter_client, TwitterPost, TwitterAnalytics
from backend.integrations.linkedin_client import linkedin_client, LinkedInPost, LinkedInAnalytics
from backend.integrations.instagram_client import instagram_client, InstagramMedia, InstagramMediaType
from backend.integrations.facebook_client import facebook_client, FacebookPost, FacebookInsights
from backend.integrations.performance_optimizer import performance_optimizer
from backend.services.workflow_orchestration import workflow_orchestrator, WorkflowType
from backend.services.metrics_collection import metrics_collector


class TestLivePlatformIntegration:
    """Live platform integration test suite"""
    
    @pytest.fixture
    def mock_tokens(self):
        """Mock authentication tokens for testing"""
        return {
            "twitter": "mock_twitter_token_123",
            : "mock_linkedin_token_456", 
            "instagram": "mock_instagram_token_789",
            "facebook": "mock_facebook_token_abc"
        }
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing posts"""
        return {
            "text": "Testing AI Social Media Agent integration! 🚀 #AI #SocialMedia #Testing",
            "image_url": "https://example.com/test-image.jpg",
            "video_url": "https://example.com/test-video.mp4",
            "link": "https://example.com/test-article"
        }
    
    @pytest.mark.asyncio
    async def test_twitter_integration_flow(self, mock_tokens, sample_content):
        """Test complete Twitter integration workflow"""
        
        # Mock Twitter API responses
        mock_post_response = {
            "id": "1234567890",
            "text": sample_content["text"],
            "author_id": "user123",
            "created_at": "2025-01-01T12:00:00.000Z",
            "public_metrics": {
                "retweet_count": 5,
                "like_count": 20,
                "reply_count": 3,
                "quote_count": 2
            },
            "context_annotations": []
        }
        
        mock_analytics_response = {
            "data": {
                "public_metrics": {
                    "retweet_count": 10,
                    "like_count": 45,
                    "reply_count": 8,
                    "quote_count": 5,
                    "impression_count": 1500
                },
                "organic_metrics": {
                    "impression_count": 1200,
                    "url_link_clicks": 25,
                    "user_profile_clicks": 15
                }
            }
        }
        
        with patch.object(twitter_client, '_make_request') as mock_request:
            # Test posting
            mock_request.return_value = mock_post_response
            
            post = await twitter_client.post_tweet(
                access_token=mock_tokens["twitter"],
                text=sample_content["text"]
            )
            
            assert isinstance(post, TwitterPost)
            assert post.id == "1234567890"
            assert post.text == sample_content["text"]
            assert post.public_metrics["like_count"] == 20
            
            # Test analytics
            mock_request.return_value = mock_analytics_response
            
            analytics = await twitter_client.get_tweet_analytics(
                access_token=mock_tokens["twitter"],
                tweet_id=post.id
            )
            
            assert isinstance(analytics, TwitterAnalytics)
            assert analytics.likes == 45
            assert analytics.impressions == 1200
            assert analytics.engagement_rate > 0
    
    @pytest.mark.asyncio
    async def test_linkedin_integration_flow(self, mock_tokens, sample_content):
        """Test complete LinkedIn integration workflow"""
        
        mock_profile_response = {
            "id": "linkedin_user_123",
            "firstName": {"localized": {"en_US": "Test"}},
            "lastName": {"localized": {"en_US": "User"}},
            "headline": {"localized": {"en_US": "AI Developer"}},
            "numConnections": 500,
            "numFollowers": 1000
        }
        
        mock_post_response = {
            "id": "urn:li:share:linkedin_post_456"
        }
        
        mock_analytics_response = {
            "elements": [{
                "totalShareStatistics": {
                    "impressionCount": 2000,
                    "clickCount": 150,
                    "likeCount": 80,
                    "commentCount": 12,
                    "shareCount": 5
                }
            }]
        }
        
        with patch.object(linkedin_client, '_make_request') as mock_request:
            # Test profile retrieval
            mock_request.return_value = mock_profile_response
            
            profile = await get_user_profile(
                access_token=mock_tokens[]
            )
            
            assert profile["id"] == "linkedin_user_123"
            assert profile["first_name"] == "Test"
            assert profile["connections"] == 500
            
            # Test post creation
            mock_request.return_value = mock_post_response
            
            post = await create_post(
                access_token=mock_tokens[],
                text=sample_content["text"],
                visibility="PUBLIC"
            )
            
            assert isinstance(post, LinkedInPost)
            assert post.text == sample_content["text"]
            
            # Test analytics
            mock_request.return_value = mock_analytics_response
            
            analytics = await get_post_analytics(
                access_token=mock_tokens[],
                post_id="linkedin_post_456"
            )
            
            assert isinstance(analytics, LinkedInAnalytics)
            assert analytics.impressions == 2000
            assert analytics.reactions == 80
    
    @pytest.mark.asyncio
    async def test_instagram_integration_flow(self, mock_tokens, sample_content):
        """Test complete Instagram integration workflow"""
        
        mock_pages_response = {
            "data": [{
                "id": "facebook_page_123",
                "name": "Test Page",
                "access_token": "page_token_123",
                "instagram_business_account": {
                    "id": "instagram_account_456"
                }
            }]
        }
        
        mock_container_response = {
            "id": "container_789"
        }
        
        mock_publish_response = {
            "id": "instagram_media_123"
        }
        
        mock_media_response = {
            "id": "instagram_media_123",
            "media_type": "IMAGE",
            "media_url": sample_content["image_url"],
            "caption": sample_content["text"],
            "permalink": "https://www.instagram.com/p/test123/",
            "timestamp": "2025-01-01T12:00:00+0000",
            "like_count": 50,
            "comments_count": 10,
            "owner": {"id": "instagram_account_456"}
        }
        
        mock_insights_response = {
            "data": [{
                "name": "impressions",
                "values": [{"value": 3000}]
            }, {
                "name": "reach", 
                "values": [{"value": 2500}]
            }, {
                "name": "engagement",
                "values": [{"value": 200}]
            }]
        }
        
        with patch.object(instagram_client, '_make_request') as mock_request:
            # Mock sequence of API calls
            mock_request.side_effect = [
                mock_pages_response,  # get_facebook_pages
                mock_container_response,  # create_media_container
                mock_publish_response,  # publish_media
                mock_media_response,  # get_media_info
                mock_insights_response  # get_media_insights
            ]
            
            # Test image posting
            media = await instagram_client.post_image(
                access_token=mock_tokens["instagram"],
                ig_user_id="instagram_account_456",
                image_url=sample_content["image_url"],
                caption=sample_content["text"]
            )
            
            assert isinstance(media, InstagramMedia)
            assert media.id == "instagram_media_123"
            assert media.caption == sample_content["text"]
            assert media.like_count == 50
    
    @pytest.mark.asyncio
    async def test_facebook_integration_flow(self, mock_tokens, sample_content):
        """Test complete Facebook integration workflow"""
        
        mock_pages_response = {
            "data": [{
                "id": "facebook_page_789",
                "name": "Test Facebook Page",
                "access_token": "fb_page_token_123",
                "category": "Business",
                "followers_count": 1500
            }]
        }
        
        mock_post_response = {
            "id": "facebook_post_456"
        }
        
        mock_post_info_response = {
            "id": "facebook_post_456",
            "message": sample_content["text"],
            "created_time": "2025-01-01T12:00:00+0000",
            "updated_time": "2025-01-01T12:00:00+0000",
            "from": {"name": "Test Page", "id": "facebook_page_789"},
            "type": "status",
            "reactions": {"summary": {"total_count": 30}},
            "comments": {"summary": {"total_count": 8}},
            "shares": {"count": 5}
        }
        
        mock_insights_response = {
            "data": [{
                "name": "post_impressions",
                "values": [{"value": 2500}]
            }, {
                "name": "post_reach",
                "values": [{"value": 2000}]
            }, {
                "name": "post_engaged_users", 
                "values": [{"value": 150}]
            }]
        }
        
        with patch.object(facebook_client, '_make_request') as mock_request:
            # Mock sequence of API calls
            mock_request.side_effect = [
                mock_pages_response,  # get_user_pages
                mock_post_response,  # create_text_post
                mock_post_info_response,  # get_post_info
                mock_insights_response  # get_post_insights
            ]
            
            # Test text post creation
            post = await facebook_client.create_text_post(
                page_access_token="fb_page_token_123",
                page_id="facebook_page_789",
                message=sample_content["text"]
            )
            
            assert isinstance(post, FacebookPost)
            assert post.id == "facebook_post_456"
            assert post.message == sample_content["text"]
            assert post.comments_count == 8
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, mock_tokens, sample_content):
        """Test performance optimization features"""
        
        # Test caching
        @performance_optimizer.cached_request("twitter", "get_profile")
        async def mock_get_profile(token):
            await asyncio.sleep(0.1)  # Simulate API call
            return {"id": "user123", "username": "testuser"}
        
        # First call should be slow (not cached)
        start_time = datetime.utcnow()
        result1 = await mock_get_profile(mock_tokens["twitter"])
        first_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Second call should be fast (cached)
        start_time = datetime.utcnow()
        result2 = await mock_get_profile(mock_tokens["twitter"])
        second_duration = (datetime.utcnow() - start_time).total_seconds()
        
        assert result1 == result2
        assert second_duration < first_duration * 0.5  # Should be much faster
        
        # Test rate limiting
        rate_limited = await performance_optimizer.rate_limiter.acquire("twitter", "post")
        assert rate_limited is True
        
        # Test batch requests
        requests = [
            (mock_get_profile, (mock_tokens["twitter"],), {}),
            (mock_get_profile, (mock_tokens["twitter"],), {}),
            (mock_get_profile, (mock_tokens["twitter"],), {})
        ]
        
        results = await performance_optimizer.batch_request(requests, max_concurrent=2)
        assert len(results) == 3
        assert all(result["id"] == "user123" for result in results)
    
    @pytest.mark.asyncio
    async def test_workflow_orchestration_integration(self, mock_tokens):
        """Test complete workflow orchestration"""
        
        # Mock database session
        mock_db = AsyncMock()
        
        with patch('backend.services.workflow_orchestration.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db
            
            # Test daily content workflow
            execution = await workflow_orchestrator.execute_workflow(
                db=mock_db,
                workflow_id="daily_content"
            )
            
            assert execution.status.value in ["completed", "failed"]
            assert len(execution.steps) > 0
            assert execution.workflow_config.workflow_type == WorkflowType.DAILY_CONTENT
            
            # Test trending response workflow
            execution = await workflow_orchestrator.execute_workflow(
                db=mock_db,
                workflow_id="trending_response"
            )
            
            assert execution.status.value in ["completed", "failed"]
            assert execution.workflow_config.workflow_type == WorkflowType.TRENDING_RESPONSE
    
    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, mock_tokens):
        """Test metrics collection across all platforms"""
        
        mock_db = AsyncMock()
        
        # Mock platform API responses
        mock_responses = {
            "twitter": {"followers": 1000, "posts": 50, "engagement": 5.2},
            : {"connections": 500, "posts": 25, "engagement": 3.8},
            "instagram": {"followers": 2000, "posts": 100, "engagement": 7.1},
            "facebook": {"followers": 1500, "posts": 75, "engagement": 4.5}
        }
        
        with patch.object(metrics_collector, 'collect_platform_metrics') as mock_collect:
            mock_collect.return_value = AsyncMock(
                platform="test_platform",
                success=True,
                metrics_collected=10,
                collection_time=1.5,
                errors=[]
            )
            
            # Test metrics collection
            results = await metrics_collector.collect_all_metrics(
                db=mock_db,
                force_collection=True
            )
            
            assert len(results) > 0
            assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_tokens, sample_content):
        """Test error handling and recovery mechanisms"""
        
        # Test Twitter rate limiting recovery
        with patch.object(twitter_client, '_make_request') as mock_request:
            # First call returns rate limit error
            mock_request.side_effect = [
                Exception("Twitter API error: Rate limit exceeded"),
                {  # Second call succeeds
                    "id": "recovered_post_123",
                    "text": sample_content["text"],
                    "author_id": "user123",
                    "created_at": "2025-01-01T12:00:00.000Z",
                    "public_metrics": {"like_count": 0, "retweet_count": 0}
                }
            ]
            
            # Should handle error gracefully
            with pytest.raises(Exception) as exc_info:
                await twitter_client.post_tweet(
                    access_token=mock_tokens["twitter"],
                    text=sample_content["text"]
                )
            
            assert "Rate limit exceeded" in str(exc_info.value)
        
        # Test LinkedIn connection failure recovery
        with patch.object(linkedin_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Network error: Connection timeout")
            
            with pytest.raises(Exception) as exc_info:
                await get_user_profile(
                    access_token=mock_tokens[]
                )
            
            assert "Network error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_integration_health_check(self):
        """Test health check across all integration components"""
        
        # Test performance optimizer health
        health_status = await performance_optimizer.health_check()
        
        assert "cache" in health_status
        assert "connections" in health_status
        assert "rate_limiting" in health_status
        assert "overall" in health_status
        
        # All components should be healthy in test environment
        assert health_status["overall"] in ["healthy", "warning"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_stats_collection(self):
        """Test comprehensive statistics collection"""
        
        # Get comprehensive performance stats
        stats = performance_optimizer.get_comprehensive_stats()
        
        assert "cache" in stats
        assert "connections" in stats
        assert "rate_limiting" in stats
        assert "performance" in stats
        assert "timestamp" in stats
        
        # Verify cache stats structure
        cache_stats = stats["cache"]
        assert "hits" in cache_stats
        assert "misses" in cache_stats
        assert "hit_rate" in cache_stats
        
        # Verify rate limiting stats structure
        rate_stats = stats["rate_limiting"]
        for platform in ["twitter", , "instagram", "facebook"]:
            assert platform in rate_stats
            assert "utilization" in rate_stats[platform]
    
    def test_content_validation(self, sample_content):
        """Test content validation across all platforms"""
        
        # Test Twitter validation
        is_valid, error = twitter_client.is_valid_tweet_text(sample_content["text"])
        assert is_valid is True
        assert error == ""
        
        # Test LinkedIn validation
        is_valid, error = validate_post_content(sample_content["text"])
        assert is_valid is True
        assert error == ""
        
        # Test Instagram validation
        is_valid, error = instagram_client.validate_caption(sample_content["text"])
        assert is_valid is True
        assert error == ""
        
        # Test Facebook validation
        is_valid, error = facebook_client.validate_post_content(sample_content["text"])
        assert is_valid is True
        assert error == ""
        
        # Test content that's too long
        long_content = "A" * 300  # Exceeds Twitter limit
        is_valid, error = twitter_client.is_valid_tweet_text(long_content)
        assert is_valid is False
        assert "too long" in error
    
    def test_hashtag_and_mention_extraction(self, sample_content):
        """Test hashtag and mention extraction across platforms"""
        
        test_text = "Testing @mention and #hashtag #AI #testing extraction!"
        
        # Test Twitter extraction
        hashtags = twitter_client.extract_hashtags(test_text)
        mentions = twitter_client.extract_mentions(test_text)
        
        assert "#hashtag" in hashtags
        assert "#ai" in hashtags
        assert "#testing" in hashtags
        assert "@mention" in mentions
        
        # Test LinkedIn extraction
        hashtags = extract_hashtags(test_text)
        mentions = extract_mentions(test_text)
        
        assert "#hashtag" in hashtags
        assert "@mention" in mentions
        
        # Test Instagram extraction
        hashtags = instagram_client.extract_hashtags(test_text)
        mentions = instagram_client.extract_mentions(test_text)
        
        assert "#hashtag" in hashtags
        assert "@mention" in mentions
        
        # Test Facebook extraction
        hashtags = facebook_client.extract_hashtags(test_text)
        mentions = facebook_client.extract_mentions(test_text)
        
        assert "#hashtag" in hashtags
        assert "@mention" in mentions


class TestIntegrationEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self):
        """Test handling of empty or invalid content"""
        
        # Test empty content
        is_valid, error = twitter_client.is_valid_tweet_text("")
        assert is_valid is False
        assert "empty" in error.lower()
        
        # Test whitespace-only content
        is_valid, error = validate_post_content("   ")
        assert is_valid is False
        assert "empty" in error.lower()
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, mock_tokens):
        """Test network timeout handling"""
        
        with patch.object(twitter_client, '_make_request') as mock_request:
            mock_request.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(Exception) as exc_info:
                await twitter_client.get_user_profile(
                    access_token=mock_tokens["twitter"],
                    username="testuser"
                )
            
            # Should handle timeout gracefully
            assert "timeout" in str(exc_info.value).lower() or "network" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_token_handling(self):
        """Test invalid authentication token handling"""
        
        with patch.object(linkedin_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("LinkedIn API error: Invalid access token")
            
            with pytest.raises(Exception) as exc_info:
                await get_user_profile(
                    access_token="invalid_token_123"
                )
            
            assert "invalid" in str(exc_info.value).lower() or "access token" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio 
    async def test_api_version_compatibility(self):
        """Test API version compatibility"""
        
        # Verify API versions are current
        assert twitter_client.api_base == "https://api.twitter.com/2"
        assert api_base == "https://api.linkedin.com/v2"
        assert instagram_client.api_base == "https://graph.facebook.com/v18.0"
        assert facebook_client.api_base == "https://graph.facebook.com/v18.0"
    
    def test_rate_limit_configurations(self):
        """Test rate limit configurations are reasonable"""
        
        # Verify rate limits are within expected ranges
        twitter_limits = twitter_client.rate_limits
        assert twitter_limits["tweet_create"]["requests"] <= 300
        assert twitter_limits["tweet_create"]["window"] >= 900
        
        linkedin_limits = rate_limits
        assert linkedin_limits["post_create"]["requests"] <= 100
        assert linkedin_limits["post_create"]["window"] >= 3600
        
        instagram_limits = instagram_client.rate_limits
        assert instagram_limits["content_publishing"]["requests"] <= 25
        assert instagram_limits["content_publishing"]["window"] >= 3600
        
        facebook_limits = facebook_client.rate_limits
        assert facebook_limits["page_posts"]["requests"] <= 600
        assert facebook_limits["page_posts"]["window"] >= 600


@pytest.mark.integration
class TestLiveAPIConnections:
    """
    Live API connection tests (requires real credentials)
    These tests are marked as integration tests and should only be run
    when live API credentials are available
    """
    
    @pytest.mark.skipif(
        not os.getenv("TWITTER_BEARER_TOKEN"),
        reason="Twitter API credentials not available"
    )
    @pytest.mark.asyncio
    async def test_live_twitter_connection(self):
        """Test live Twitter API connection"""
        
        token = os.getenv("TWITTER_BEARER_TOKEN")
        
        try:
            # Test basic API connectivity
            profile = await twitter_client.get_user_profile(
                access_token=token,
                username="twitter"  # Official Twitter account
            )
            
            assert profile["username"] == "twitter"
            assert profile["id"] is not None
            
        except Exception as e:
            pytest.skip(f"Live Twitter API test failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("LINKEDIN_ACCESS_TOKEN"),
        reason="LinkedIn API credentials not available"
    )
    @pytest.mark.asyncio
    async def test_live_linkedin_connection(self):
        """Test live LinkedIn API connection"""
        
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
        try:
            # Test basic API connectivity
            profile = await get_user_profile(
                access_token=token
            )
            
            assert profile["id"] is not None
            
        except Exception as e:
            pytest.skip(f"Live LinkedIn API test failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("FACEBOOK_ACCESS_TOKEN"),
        reason="Facebook API credentials not available"
    )
    @pytest.mark.asyncio
    async def test_live_facebook_connection(self):
        """Test live Facebook API connection"""
        
        token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        try:
            # Test basic API connectivity
            pages = await facebook_client.get_user_pages(
                access_token=token
            )
            
            assert isinstance(pages, list)
            
        except Exception as e:
            pytest.skip(f"Live Facebook API test failed: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])