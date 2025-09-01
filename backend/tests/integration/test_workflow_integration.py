"""
Integration tests for workflow orchestration

Tests end-to-end workflow execution including:
- Daily research and content generation workflows
- Goal-driven content creation workflows  
- Social media posting workflows
- Multi-platform automation workflows
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock, AsyncMock
from fastapi import status

from backend.db.models import ContentItem, Goal, User, Memory
from backend.services.workflow_orchestration import WorkflowOrchestrationService


class TestWorkflowIntegration:
    """Test complete workflow integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_daily_research_workflow_complete(self, client, test_user, auth_headers, db_session, mock_openai, mock_faiss):
        """Test complete daily research workflow execution"""
        # Mock external services
        with patch('backend.services.research_automation.ResearchAutomationService') as mock_research:
            mock_research_instance = Mock()
            mock_research_instance.execute_daily_research.return_value = {
                "research_items": [
                    {
                        "title": "AI Marketing Trends 2025",
                        "content": "Latest trends in AI-powered marketing automation",
                        "source_url": "https://example.com/ai-trends",
                        "relevance_score": 0.95,
                        "keywords": ["AI", "marketing", "automation"]
                    },
                    {
                        "title": "Social Media Algorithm Updates",
                        "content": "Recent changes to major social platform algorithms",
                        "source_url": "https://example.com/algorithm-updates", 
                        "relevance_score": 0.88,
                        "keywords": ["social media", "algorithms", "updates"]
                    }
                ],
                "trend_analysis": {
                    "top_topics": ["AI marketing", "algorithm changes", "video content"],
                    "emerging_hashtags": ["#AIMarketing2025", "#AlgorithmUpdate", "#VideoFirst"],
                    "recommended_posting_times": ["9:00 AM", "2:00 PM", "7:00 PM"]
                }
            }
            mock_research.return_value = mock_research_instance
            
            # Trigger daily research workflow
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    "/api/workflow/daily-research/execute",
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["research_items_found"] == 2
            assert "trend_analysis" in data
            
            # Verify research items were stored in memory
            memories = db_session.query(Memory).filter(Memory.user_id == test_user.user_id).all()
            assert len(memories) >= 2
            assert any("AI Marketing Trends" in memory.content_text for memory in memories)
    
    @pytest.mark.asyncio
    async def test_content_generation_workflow_complete(self, client, test_user, auth_headers, db_session, mock_openai):
        """Test complete AI content generation workflow"""
        # Create user goal for context
        goal = Goal(
            user_id=test_user.user_id,
            title="Increase LinkedIn Engagement", 
            description="Improve LinkedIn engagement rate to 5%",
            target_metric="engagement_rate",
            target_value=5.0,
            current_value=3.2,
            target_date=datetime.now(timezone.utc) + timedelta(days=60),
            category="engagement",
            priority="high",
            status="active"
        )
        db_session.add(goal)
        db_session.commit()
        
        # Mock CrewAI content generation
        with patch('backend.services.content_automation.ContentAutomationService') as mock_content:
            mock_content_instance = Mock()
            mock_content_instance.generate_goal_driven_content.return_value = {
                "generated_content": [
                    {
                        "title": "5 LinkedIn Engagement Strategies That Actually Work",
                        "content": "Discover proven strategies to boost your LinkedIn engagement rate and build meaningful professional connections...",
                        "platform": ,
                        "content_type": "text",
                        "metadata": {
                            "hashtags": ["#LinkedInTips", "#ProfessionalNetworking", "#EngagementStrategy"],
                            "target_audience": "professionals",
                            "engagement_prediction": 6.2,
                            "optimal_posting_time": "10:00 AM"
                        }
                    },
                    {
                        "title": "Behind the Scenes: How We Increased Engagement by 95%",
                        "content": "A transparent look at the strategies and tactics that led to our 95% engagement increase on LinkedIn...",
                        "platform": , 
                        "content_type": "text",
                        "metadata": {
                            "hashtags": ["#CaseStudy", "#LinkedInGrowth", "#MarketingResults"],
                            "target_audience": "marketers",
                            "engagement_prediction": 7.8,
                            "optimal_posting_time": "2:00 PM"
                        }
                    }
                ],
                "generation_insights": {
                    "goal_alignment_score": 0.92,
                    "brand_voice_consistency": 0.89,
                    "content_diversity": 0.85
                }
            }
            mock_content.return_value = mock_content_instance
            
            # Trigger content generation workflow
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    f"/api/workflow/content-generation/goal/{goal.id}/execute",
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["content_generated_count"] == 2
            assert data["goal_alignment_score"] == 0.92
            
            # Verify content was created in database
            content_items = db_session.query(ContentItem).filter(ContentItem.user_id == test_user.user_id).all()
            assert len(content_items) == 2
            assert all(item.platform ==  for item in content_items)
            assert any("Engagement Strategies" in item.title for item in content_items)
    
    @pytest.mark.asyncio
    async def test_multi_platform_posting_workflow(self, client, test_user, auth_headers, db_session, mock_social_apis):
        """Test multi-platform content posting workflow"""
        # Create scheduled content for multiple platforms
        platforms = ["twitter", , "facebook", "instagram"]
        content_items = []
        
        for platform in platforms:
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Multi-platform Content for {platform.title()}",
                content=f"Optimized content for {platform} platform with platform-specific formatting and hashtags",
                platform=platform,
                status="scheduled",
                scheduled_time=datetime.now(timezone.utc) + timedelta(minutes=5),
                metadata={
                    "hashtags": [f"#{platform}Marketing", "#SocialMedia", "#ContentStrategy"],
                    "platform_optimized": True,
                    "auto_post": True
                }
            )
            db_session.add(content)
            content_items.append(content)
        
        db_session.commit()
        
        # Mock social media API responses
        mock_social_apis['twitter'].create_tweet.return_value = {
            "data": {"id": "1234567890", "text": "Posted content"},
            "success": True
        }
        mock_social_apis['linkedin'].create_post.return_value = {
            "id": "urn:li:share:123456",
            "success": True
        }
        
        with patch('backend.integrations.facebook_client.FacebookClient') as mock_fb:
            mock_fb.return_value.create_post.return_value = {
                "id": "facebook_post_123",
                "success": True
            }
            
            with patch('backend.integrations.instagram_client.InstagramClient') as mock_ig:
                mock_ig.return_value.create_post.return_value = {
                    "id": "instagram_post_123", 
                    "success": True
                }
                
                # Execute multi-platform posting workflow
                with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                    response = client.post(
                        "/api/workflow/multi-platform-posting/execute",
                        json={
                            "content_ids": [item.id for item in content_items],
                            "execute_immediately": True
                        },
                        headers=auth_headers
                    )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "completed"
                assert data["platforms_posted"] == 4
                assert data["success_count"] == 4
                assert data["error_count"] == 0
                
                # Verify content status updated to published
                for content in content_items:
                    db_session.refresh(content)
                    assert content.status == "published"
                    assert content.published_at is not None
    
    @pytest.mark.asyncio
    async def test_goal_driven_workflow_end_to_end(self, client, test_user, auth_headers, db_session, mock_openai, mock_social_apis):
        """Test complete goal-driven workflow from research to posting"""
        # Create a specific goal
        goal = Goal(
            user_id=test_user.user_id,
            title="Grow Twitter Following to 10K",
            description="Increase Twitter followers through consistent, engaging content",
            target_metric="followers",
            target_value=10000,
            current_value=7500,
            target_date=datetime.now(timezone.utc) + timedelta(days=45),
            category="growth",
            priority="high",
            status="active",
            metadata={
                "target_platforms": ["twitter"],
                "content_themes": ["tech tips", "industry insights", "behind-the-scenes"],
                "posting_frequency": "twice_daily"
            }
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # Mock all workflow components
        with patch('backend.services.research_automation.ResearchAutomationService') as mock_research, \
             patch('backend.services.content_automation.ContentAutomationService') as mock_content, \
             patch('backend.services.goals_progress_service.GoalsProgressService') as mock_goals:
            
            # Setup research mock
            mock_research.return_value.execute_goal_focused_research.return_value = {
                "research_items": [
                    {
                        "title": "Twitter Growth Hacks for 2025",
                        "content": "Proven strategies for organic Twitter growth",
                        "relevance_score": 0.98
                    }
                ],
                "trending_topics": ["#TwitterGrowth", "#SocialMediaTips", "#ContentCreator"],
                "optimal_times": ["9:00 AM", "6:00 PM"]
            }
            
            # Setup content generation mock
            mock_content.return_value.generate_goal_driven_content.return_value = {
                "generated_content": [
                    {
                        "title": "Twitter Growth Tip #1",
                        "content": "🧵 Thread: 5 Twitter growth strategies that actually work in 2025 👇\n\n1. Consistency beats perfection every time...",
                        "platform": "twitter",
                        "content_type": "thread",
                        "metadata": {
                            "hashtags": ["#TwitterTips", "#GrowthHacking", "#SocialMedia"],
                            "engagement_prediction": 8.5,
                            "thread_count": 7
                        }
                    },
                    {
                        "title": "Behind the Scenes: Our Twitter Strategy",
                        "content": "Here's exactly how we grew from 5K to 25K followers in 6 months 📈\n\nThe strategy that changed everything 👇",
                        "platform": "twitter",
                        "content_type": "text",
                        "metadata": {
                            "hashtags": ["#TwitterGrowth", "#CaseStudy", "#MarketingTips"],
                            "engagement_prediction": 9.2
                        }
                    }
                ],
                "goal_alignment_score": 0.95
            }
            
            # Setup posting mock
            mock_social_apis['twitter'].create_tweet.return_value = {
                "data": {"id": "tweet_123", "text": "Posted successfully"},
                "success": True
            }
            
            # Setup goal progress tracking mock
            mock_goals.return_value.update_goal_progress.return_value = {
                "current_value": 7650,  # 150 new followers
                "progress_percentage": 76.5,
                "on_track": True
            }
            
            # Execute complete goal-driven workflow
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    f"/api/workflow/goal-driven/{goal.id}/execute",
                    json={
                        "include_research": True,
                        "generate_content": True,
                        "auto_post": True,
                        "update_progress": True
                    },
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["workflow_steps"]["research"]["completed"] == True
            assert data["workflow_steps"]["content_generation"]["completed"] == True
            assert data["workflow_steps"]["posting"]["completed"] == True
            assert data["workflow_steps"]["progress_tracking"]["completed"] == True
            assert data["goal_progress"]["current_value"] == 7650
            
            # Verify database updates
            content_count = db_session.query(ContentItem).filter(
                ContentItem.user_id == test_user.user_id,
                ContentItem.platform == "twitter"
            ).count()
            assert content_count == 2
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling_and_recovery(self, client, test_user, auth_headers, db_session):
        """Test workflow error handling and recovery mechanisms"""
        # Create content that will cause posting errors
        problematic_content = ContentItem(
            user_id=test_user.user_id,
            title="Problematic Content",
            content="Content that will fail to post",
            platform="twitter",
            status="scheduled",
            scheduled_time=datetime.now(timezone.utc) + timedelta(minutes=1)
        )
        db_session.add(problematic_content)
        db_session.commit()
        db_session.refresh(problematic_content)
        
        # Mock social media API to return errors
        with patch('backend.integrations.twitter_client.TwitterClient') as mock_twitter:
            mock_twitter.return_value.create_tweet.side_effect = Exception("API rate limit exceeded")
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    "/api/workflow/posting/execute",
                    json={
                        "content_ids": [problematic_content.id],
                        "retry_on_failure": True,
                        "max_retries": 3
                    },
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed_with_errors"
            assert data["error_count"] == 1
            assert data["retry_attempts"] == 3
            assert "API rate limit exceeded" in data["errors"][0]["error_message"]
            
            # Verify content status updated to failed
            db_session.refresh(problematic_content)
            assert problematic_content.status == "failed"
            assert problematic_content.metadata["error_info"]["last_error"] == "API rate limit exceeded"
    
    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self, client, test_user, auth_headers, db_session, performance_timer):
        """Test workflow performance monitoring and optimization"""
        # Create multiple content items for batch processing
        content_items = []
        for i in range(20):
            content = ContentItem(
                user_id=test_user.user_id,
                title=f"Batch Content {i}",
                content=f"Content item {i} for batch processing test",
                platform="twitter",
                status="scheduled",
                scheduled_time=datetime.now(timezone.utc) + timedelta(minutes=i)
            )
            db_session.add(content)
            content_items.append(content)
        
        db_session.commit()
        
        # Mock fast API responses
        with patch('backend.integrations.twitter_client.TwitterClient') as mock_twitter:
            mock_twitter.return_value.create_tweet.return_value = {
                "data": {"id": "tweet_123"},
                "success": True
            }
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                performance_timer.start()
                
                response = client.post(
                    "/api/workflow/batch-posting/execute",
                    json={
                        "content_ids": [item.id for item in content_items],
                        "batch_size": 5,
                        "parallel_processing": True
                    },
                    headers=auth_headers
                )
                
                execution_time = performance_timer.stop()
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["processed_count"] == 20
        assert data["execution_time_seconds"] < 30  # Should complete in under 30 seconds
        assert execution_time < 5.0  # API call should be fast
        
        # Verify performance metrics
        assert "performance_metrics" in data
        assert data["performance_metrics"]["avg_processing_time_per_item"] < 1.5
        assert data["performance_metrics"]["throughput_items_per_second"] > 5
    
    @pytest.mark.asyncio
    async def test_workflow_scheduling_and_automation(self, client, test_user, auth_headers, db_session):
        """Test workflow scheduling and automated execution"""
        # Create a scheduled workflow
        workflow_config = {
            "name": "Daily Content Automation",
            "schedule": "0 9 * * *",  # Daily at 9 AM
            "workflow_type": "daily_content_generation",
            "parameters": {
                "platforms": ["twitter", ],
                "content_count": 3,
                "include_research": True,
                "auto_post": False  # Generate but don't auto-post
            },
            "active": True
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            # Create scheduled workflow
            response = client.post(
                "/api/workflow/schedule",
                json=workflow_config,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Daily Content Automation"
        assert data["schedule"] == "0 9 * * *"
        assert data["active"] == True
        workflow_id = data["id"]
        
        # Test manual trigger of scheduled workflow
        with patch('backend.services.workflow_orchestration.WorkflowOrchestrationService') as mock_workflow:
            mock_workflow.return_value.execute_scheduled_workflow.return_value = {
                "status": "completed",
                "content_generated": 3,
                "platforms": ["twitter", ],
                "execution_time": 45.2
            }
            
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    f"/api/workflow/schedule/{workflow_id}/trigger",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["content_generated"] == 3
        
        # Test workflow execution history
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.get(
                f"/api/workflow/schedule/{workflow_id}/history",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["executions"]) >= 1
        assert data["executions"][0]["status"] == "completed"


class TestWorkflowValidation:
    """Test workflow validation and constraint checking"""
    
    def test_workflow_parameter_validation(self, client, test_user, auth_headers):
        """Test validation of workflow parameters"""
        invalid_workflows = [
            {
                "workflow_type": "invalid_type",
                "parameters": {}
            },
            {
                "workflow_type": "content_generation",
                "parameters": {
                    "platforms": ["invalid_platform"],
                    "content_count": -1  # Invalid negative count
                }
            },
            {
                "workflow_type": "posting",
                "parameters": {
                    "content_ids": [],  # Empty content IDs
                    "schedule_time": "invalid_datetime"
                }
            }
        ]
        
        for invalid_workflow in invalid_workflows:
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    "/api/workflow/execute",
                    json=invalid_workflow,
                    headers=auth_headers
                )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_workflow_resource_limits(self, client, test_user, auth_headers, db_session):
        """Test workflow resource limits and quotas"""
        # Try to create workflow that exceeds limits
        large_workflow = {
            "workflow_type": "content_generation",
            "parameters": {
                "platforms": ["twitter", , "facebook", "instagram"],
                "content_count": 100,  # Exceeds daily limit
                "batch_size": 50
            }
        }
        
        with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
            response = client.post(
                "/api/workflow/execute",
                json=large_workflow,
                headers=auth_headers
            )
        
        # Should either limit the request or return an error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should limit content count
            assert data["content_generated_count"] <= 50  # System limit
    
    def test_concurrent_workflow_execution_limits(self, client, test_user, auth_headers):
        """Test limits on concurrent workflow execution"""
        import asyncio
        
        workflow_config = {
            "workflow_type": "content_generation",
            "parameters": {
                "platforms": ["twitter"],
                "content_count": 5
            }
        }
        
        # Try to execute multiple workflows concurrently
        async def execute_workflow():
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                return client.post(
                    "/api/workflow/execute",
                    json=workflow_config,
                    headers=auth_headers
                )
        
        # This would normally be tested with actual async calls
        # For now, test sequential execution with rate limiting
        responses = []
        for _ in range(5):
            with patch('backend.auth.dependencies.get_current_user', return_value=test_user):
                response = client.post(
                    "/api/workflow/execute",
                    json=workflow_config,
                    headers=auth_headers
                )
                responses.append(response)
        
        # Should have rate limiting after a certain number of concurrent workflows
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        rate_limited_count = sum(1 for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS)
        
        assert success_count + rate_limited_count == 5
        assert success_count >= 1  # At least one should succeed
EOF < /dev/null