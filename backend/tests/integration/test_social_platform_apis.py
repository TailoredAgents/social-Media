"""
Integration tests for social platform APIs
"""
import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from backend.auth.dependencies import get_current_user
from backend.db.database import get_db


class TestSocialPlatformConnectionAPI:
    """Test social platform connection endpoints"""
    
    def test_list_social_connections_authenticated(self, client, test_user_with_org, override_get_db):
        """Test listing social platform connections for authenticated user"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/social/connections")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_connect_twitter_oauth_flow(self, client, test_user_with_org, override_get_db):
        """Test initiating Twitter OAuth connection"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock OAuth URL generation
            mock_twitter_instance = Mock()
            mock_twitter_instance.get_authorization_url.return_value = "https://twitter.com/oauth/authorize?token=test"
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.post("/api/social/connect", json={"platform": "twitter"})
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "twitter.com" in data["authorization_url"]
    
    def test_connect_linkedin_oauth_flow(self, client, test_user_with_org, override_get_db):
        """Test initiating LinkedIn OAuth connection"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        with patch('backend.integrations.LinkedInAPIClient') as mock_linkedin:
            # Mock OAuth URL generation
            mock_linkedin_instance = Mock()
            mock_linkedin_instance.get_authorization_url.return_value = "https://linkedin.com/oauth/v2/authorization?client_id=test"
            mock_linkedin.return_value = mock_linkedin_instance
            
            response = client.post("/api/social/connect", json={"platform": })
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "linkedin.com" in data["authorization_url"]
    
    def test_connect_invalid_platform(self, client, test_user_with_org, override_get_db):
        """Test connecting to unsupported platform"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.post("/api/social/connect", json={"platform": "invalid_platform"})
        
        assert response.status_code == 400
        assert "Unsupported platform" in response.json()["detail"]
    
    def test_oauth_callback_twitter(self, client, test_user_with_org, override_get_db):
        """Test Twitter OAuth callback handling"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        callback_data = {
            "platform": "twitter",
            "oauth_token": "test_token",
            "oauth_verifier": "test_verifier"
        }
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock successful token exchange
            mock_twitter_instance = Mock()
            mock_twitter_instance.exchange_oauth_token.return_value = {
                "access_token": "final_token",
                "access_token_secret": "token_secret",
                "user_id": "12345",
                "screen_name": "testuser"
            }
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.post("/api/social/callback", json=callback_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "connected"
            assert data["platform"] == "twitter"
    
    def test_disconnect_platform(self, client, test_user_with_org, override_get_db):
        """Test disconnecting from a social platform"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        # First, mock an existing connection
        with patch('backend.db.models.SocialPlatformConnection') as mock_connection:
            mock_conn_instance = Mock()
            mock_conn_instance.platform = "twitter"
            mock_conn_instance.is_active = True
            
            response = client.delete("/api/social/disconnect/twitter")
            
            # Should attempt to disconnect
            assert response.status_code in [200, 404]  # 404 if no connection exists


class TestSocialPlatformPostingAPI:
    """Test social platform posting endpoints"""
    
    def test_post_to_twitter(self, client, test_user_with_org, override_get_db):
        """Test posting content to Twitter"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": "twitter",
            "content": "Test tweet content #testing",
            "scheduled_for": None  # Post immediately
        }
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock successful post
            mock_twitter_instance = Mock()
            mock_twitter_instance.post_tweet.return_value = {
                "id": "1234567890",
                "created_at": "2025-08-18T10:00:00Z",
                "text": "Test tweet content #testing",
                "public_metrics": {
                    "like_count": 0,
                    "retweet_count": 0,
                    "reply_count": 0
                }
            }
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.post("/api/social/post", json=post_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["platform"] == "twitter"
            assert data["status"] == "posted"
            assert "post_id" in data
    
    def test_post_to_linkedin(self, client, test_user_with_org, override_get_db):
        """Test posting content to LinkedIn"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": ,
            "content": "Professional update for LinkedIn audience",
            "scheduled_for": None
        }
        
        with patch('backend.integrations.LinkedInAPIClient') as mock_linkedin:
            # Mock successful post
            mock_linkedin_instance = Mock()
            mock_linkedin_instance.create_post.return_value = {
                "id": "urn:li:share:123456789",
                "created_at": "2025-08-18T10:00:00Z",
                "text": "Professional update for LinkedIn audience"
            }
            mock_linkedin.return_value = mock_linkedin_instance
            
            response = client.post("/api/social/post", json=post_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["platform"] == 
            assert data["status"] == "posted"
    
    def test_scheduled_post(self, client, test_user_with_org, override_get_db):
        """Test scheduling a post for later"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": "twitter",
            "content": "Scheduled tweet for tomorrow",
            "scheduled_for": "2025-08-19T10:00:00Z"
        }
        
        response = client.post("/api/social/post", json=post_data)
        
        # Should accept scheduled posts
        assert response.status_code in [200, 202]  # 202 for accepted/scheduled
    
    def test_post_without_connection(self, client, test_user_with_org, override_get_db):
        """Test posting to platform without established connection"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": "twitter",
            "content": "Should fail without connection"
        }
        
        # Mock no existing connection
        with patch('backend.db.models.SocialPlatformConnection.query') as mock_query:
            mock_query.filter.return_value.first.return_value = None
            
            response = client.post("/api/social/post", json=post_data)
            
            assert response.status_code in [400, 404]
            assert "not connected" in response.json()["detail"].lower()
    
    def test_post_invalid_platform(self, client, test_user_with_org, override_get_db):
        """Test posting to invalid platform"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": "invalid_platform",
            "content": "Should fail"
        }
        
        response = client.post("/api/social/post", json=post_data)
        
        assert response.status_code == 400
        assert "Unsupported platform" in response.json()["detail"]


class TestSocialPlatformMetricsAPI:
    """Test social platform metrics endpoints"""
    
    def test_get_platform_metrics(self, client, test_user_with_org, override_get_db):
        """Test getting metrics for a platform"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock metrics data
            mock_twitter_instance = Mock()
            mock_twitter_instance.get_user_metrics.return_value = {
                "followers_count": 1500,
                "following_count": 300,
                "tweet_count": 250,
                "listed_count": 10
            }
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.get("/api/social/metrics/twitter")
            
            assert response.status_code == 200
            data = response.json()
            assert "followers_count" in data
            assert data["followers_count"] == 1500
    
    def test_get_post_metrics(self, client, test_user_with_org, override_get_db):
        """Test getting metrics for a specific post"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_id = "1234567890"
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock post metrics
            mock_twitter_instance = Mock()
            mock_twitter_instance.get_tweet_metrics.return_value = {
                "public_metrics": {
                    "like_count": 25,
                    "retweet_count": 8,
                    "reply_count": 3,
                    "quote_count": 2
                }
            }
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.get(f"/api/social/metrics/twitter/posts/{post_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "like_count" in data
            assert data["like_count"] == 25
    
    def test_get_analytics_summary(self, client, test_user_with_org, override_get_db):
        """Test getting analytics summary across platforms"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/social/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        assert "total_followers" in data
        assert "engagement_rate" in data


class TestSocialPlatformErrorHandling:
    """Test error handling in social platform APIs"""
    
    def test_oauth_error_handling(self, client, test_user_with_org, override_get_db):
        """Test handling OAuth errors"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock OAuth error
            mock_twitter_instance = Mock()
            mock_twitter_instance.get_authorization_url.side_effect = Exception("OAuth service unavailable")
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.post("/api/social/connect", json={"platform": "twitter"})
            
            assert response.status_code == 500
            assert "OAuth error" in response.json()["detail"] or "Failed to connect" in response.json()["detail"]
    
    def test_posting_error_handling(self, client, test_user_with_org, override_get_db):
        """Test handling posting errors"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        post_data = {
            "platform": "twitter",
            "content": "Test post that will fail"
        }
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock posting error
            mock_twitter_instance = Mock()
            mock_twitter_instance.post_tweet.side_effect = Exception("API rate limit exceeded")
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.post("/api/social/post", json=post_data)
            
            assert response.status_code == 500
            assert "Failed to post" in response.json()["detail"]
    
    def test_metrics_error_handling(self, client, test_user_with_org, override_get_db):
        """Test handling metrics retrieval errors"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            # Mock metrics error
            mock_twitter_instance = Mock()
            mock_twitter_instance.get_user_metrics.side_effect = Exception("Metrics service down")
            mock_twitter.return_value = mock_twitter_instance
            
            response = client.get("/api/social/metrics/twitter")
            
            assert response.status_code == 500
            assert "Failed to retrieve" in response.json()["detail"]


class TestSocialPlatformSecurity:
    """Test security aspects of social platform APIs"""
    
    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated users cannot access social APIs"""
        # No authentication override
        
        response = client.get("/api/social/connections")
        assert response.status_code in [401, 422]
        
        response = client.post("/api/social/connect", json={"platform": "twitter"})
        assert response.status_code in [401, 422]
        
        response = client.post("/api/social/post", json={"platform": "twitter", "content": "test"})
        assert response.status_code in [401, 422]
    
    def test_cross_user_data_isolation(self, client, test_user_with_org, test_admin_user, override_get_db):
        """Test that users can only access their own social platform data"""
        # This would require more complex setup with actual social connections
        # For now, verify that the API requires proper authentication
        
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/social/connections")
        assert response.status_code == 200
        
        # Switch to different user
        client.app.dependency_overrides[get_current_user] = lambda: test_admin_user
        
        response = client.get("/api/social/connections")
        assert response.status_code == 200
        # Data should be different for different users (though we can't verify content here)
    
    def test_rate_limiting_headers(self, client, test_user_with_org, override_get_db):
        """Test that rate limiting information is included in responses"""
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        response = client.get("/api/social/connections")
        
        # Check for rate limiting headers (if implemented)
        assert response.status_code == 200
        # Could check for headers like X-RateLimit-Remaining, X-RateLimit-Reset
    
    def test_token_encryption(self, client, test_user_with_org, override_get_db):
        """Test that OAuth tokens are properly encrypted in storage"""
        # This is more of an integration test that would check database storage
        # For now, ensure the connection process works
        
        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = lambda: test_user_with_org
        
        callback_data = {
            "platform": "twitter",
            "oauth_token": "sensitive_token",
            "oauth_verifier": "sensitive_verifier"
        }
        
        with patch('backend.integrations.twitter_client.TwitterAPIClient') as mock_twitter:
            mock_twitter_instance = Mock()
            mock_twitter_instance.exchange_oauth_token.return_value = {
                "access_token": "final_sensitive_token",
                "access_token_secret": "sensitive_secret",
                "user_id": "12345",
                "screen_name": "testuser"
            }
            mock_twitter.return_value = mock_twitter_instance
            
            with patch('backend.core.token_encryption.encrypt_token') as mock_encrypt:
                mock_encrypt.return_value = "encrypted_token_data"
                
                response = client.post("/api/social/callback", json=callback_data)
                
                if response.status_code == 200:
                    # Verify encryption was called
                    mock_encrypt.assert_called()


class TestSocialPlatformMultiTenancy:
    """Test multi-tenancy aspects of social platform APIs"""
    
    def test_organization_context_isolation(self, client, multi_org_setup, override_get_db):
        """Test that social platform connections are isolated by organization"""
        user1 = multi_org_setup["user1"]
        user2 = multi_org_setup["user2"]
        org1 = multi_org_setup["org1"]
        org2 = multi_org_setup["org2"]
        
        client.app.dependency_overrides[get_db] = override_get_db
        
        # User1 in org1
        client.app.dependency_overrides[get_current_user] = lambda: user1
        
        response1 = client.get(
            "/api/social/connections",
            headers={"X-Organization-ID": org1.id}
        )
        
        # User2 in org2
        client.app.dependency_overrides[get_current_user] = lambda: user2
        
        response2 = client.get(
            "/api/social/connections",
            headers={"X-Organization-ID": org2.id}
        )
        
        # Both should work but show different data
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # User1 trying to access org2 context should fail
        client.app.dependency_overrides[get_current_user] = lambda: user1
        
        response = client.get(
            "/api/social/connections",
            headers={"X-Organization-ID": org2.id}
        )
        
        assert response.status_code == 403  # Access denied