"""
Comprehensive integration tests for workflow orchestration and automation

Tests complete workflows including research automation, content generation,
multi-platform publishing, performance analysis, and error recovery.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.db.models import User, ContentItem, WorkflowExecution, ResearchData
from backend.services.workflow_orchestration import workflow_orchestrator
from backend.services.research_automation import research_service
from backend.services.content_automation import content_automation_service
from backend.integrations.twitter_client import TwitterAPIClient as TwitterClient
from backend.integrations.linkedin_client import LinkedInClient


class TestWorkflowOrchestrationIntegration:
    """Integration tests for complete workflow orchestration"""
    
    @pytest.fixture
    def client(self):
        """Test client with real app"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.is_active = True
        user.tier = "premium"
        return user
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_research_data(self):
        """Sample research data for testing"""
        return [
            {
                "title": "AI Trends in 2024",
                "summary": "Artificial intelligence continues to evolve with new breakthroughs in machine learning, natural language processing, and computer vision.",
                "url": "https://example.com/ai-trends-2024",
                "source": "TechCrunch",
                "relevance_score": 0.92,
                "sentiment": "positive"
            },
            {
                "title": "The Future of Automation",
                "summary": "Automation technologies are transforming industries from manufacturing to healthcare.",
                "url": "https://example.com/automation-future",
                "source": "MIT Technology Review",
                "relevance_score": 0.87,
                "sentiment": "neutral"
            }
        ]
    
    @pytest.fixture
    def sample_generated_content(self):
        """Sample generated content for testing"""
        return [
            {
                "platform": "twitter",
                "content": "🚀 AI is revolutionizing how we work and live! From healthcare breakthroughs to smart automation, the future is now. What AI application excites you most? #AI #Innovation #TechTrends",
                "content_type": "text",
                "hashtags": ["AI", "Innovation", "TechTrends"],
                "estimated_engagement": 7.8,
                "optimal_posting_time": datetime.utcnow() + timedelta(hours=2)
            },
            {
                "platform": ,
                "content": "The landscape of artificial intelligence is evolving at an unprecedented pace. Recent developments in machine learning and automation are not just changing technology—they're reshaping entire industries.\n\nKey insights from recent research:\n🔹 AI diagnostic accuracy improved by 25%\n🔹 Automation reducing operational costs by 30%\n🔹 ML models achieving human-level performance in specific domains\n\nWhat challenges and opportunities do you see in AI adoption within your industry?\n\n#ArtificialIntelligence #MachineLearning #Innovation #Technology",
                "content_type": "text",
                "estimated_engagement": 6.5,
                "optimal_posting_time": datetime.utcnow() + timedelta(hours=1)
            }
        ]
    
    @pytest.mark.asyncio
    async def test_daily_content_workflow_complete(self, mock_user, mock_db_session, sample_research_data, sample_generated_content):
        """Test complete daily content workflow from research to publishing"""
        
        # Mock workflow orchestrator dependencies
        with patch('backend.services.workflow_orchestration.research_service') as mock_research, \
             patch('backend.services.workflow_orchestration.content_automation_service') as mock_content, \
             patch('backend.services.workflow_orchestration.TwitterClient') as mock_twitter, \
             patch('backend.services.workflow_orchestration.LinkedInClient') as mock_ \
             patch('backend.services.workflow_orchestration.get_db') as mock_get_db:
            
            # Setup mocks
            mock_get_db.return_value = mock_db_session
            mock_research.execute_research_automation.return_value = {
                "research_id": "research_123",
                "results": sample_research_data,
                "total_results": len(sample_research_data)
            }
            
            mock_content.generate_platform_content.return_value = sample_generated_content
            
            # Mock social media clients
            mock_twitter_client = MagicMock()
            mock_twitter_client.create_tweet.return_value = {"id": "tweet_123", "url": "https://twitter.com/status/123"}
            mock_twitter.return_value = mock_twitter_client
            
            mock_linkedin_client = MagicMock()
            mock_create_post.return_value = {"id": "post_456", "url": "https://linkedin.com/posts/456"}
            mock_linkedin.return_value = mock_linkedin_client
            
            # Mock database operations
            mock_db_session.add.return_value = None
            mock_db_session.commit.return_value = None
            mock_db_session.refresh.return_value = None
            
            # Execute workflow
            workflow_params = {
                "user_id": mock_user.id,
                "workflow_type": "daily_content_cycle",
                "research_topics": ["artificial intelligence", "automation"],
                "target_platforms": ["twitter", ],
                "content_count": 2,
                "schedule_immediately": False
            }
            
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="daily_content_cycle",
                parameters=workflow_params,
                user_id=mock_user.id
            )
            
            # Verify workflow execution
            assert result["status"] == "completed"
            assert result["workflow_type"] == "daily_content_cycle"
            assert len(result["steps_completed"]) >= 4  # research, generate, schedule, analyze
            assert result["content_generated"] == 2
            assert result["platforms_targeted"] == ["twitter", ]
            
            # Verify research was executed
            mock_research.execute_research_automation.assert_called_once()
            
            # Verify content generation
            mock_content.generate_platform_content.assert_called_once()
            
            # Verify social media posting
            mock_twitter_client.create_tweet.assert_called_once()
            mock_create_post.assert_called_once()
            
            # Verify database operations
            assert mock_db_session.add.call_count >= 2  # Content items saved
            assert mock_db_session.commit.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_trending_content_workflow(self, mock_user, mock_db_session):
        """Test trending content detection and rapid response workflow"""
        
        mock_trending_data = [
            {
                "topic": "GPT-5 announcement",
                "trend_score": 0.95,
                "engagement_velocity": 450,  # mentions per hour
                "sentiment": "excitement",
                "platforms": ["twitter", , "reddit"],
                "related_keywords": ["OpenAI", "GPT-5", "AI breakthrough"]
            }
        ]
        
        mock_rapid_content = [
            {
                "platform": "twitter",
                "content": "🚨 Breaking: GPT-5 just announced! This could be the AI breakthrough we've been waiting for. The implications for content creation, coding, and creative work are massive. What are your thoughts? #GPT5 #OpenAI #AIBreakthrough",
                "urgency": "high",
                "optimal_posting_time": datetime.utcnow() + timedelta(minutes=15)
            }
        ]
        
        with patch('backend.services.workflow_orchestration.trend_detection_service') as mock_trends, \
             patch('backend.services.workflow_orchestration.content_automation_service') as mock_content, \
             patch('backend.services.workflow_orchestration.TwitterClient') as mock_twitter:
            
            # Setup mocks
            mock_trends.detect_trending_topics.return_value = mock_trending_data
            mock_content.generate_trending_content.return_value = mock_rapid_content
            
            mock_twitter_client = MagicMock()
            mock_twitter_client.create_tweet.return_value = {"id": "trending_tweet_789"}
            mock_twitter.return_value = mock_twitter_client
            
            # Execute trending workflow
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="trending_response",
                parameters={
                    "user_id": mock_user.id,
                    "trend_threshold": 0.8,
                    "response_speed": "rapid",
                    "platforms": ["twitter"]
                },
                user_id=mock_user.id
            )
            
            # Verify rapid response
            assert result["status"] == "completed"
            assert result["response_time"] < 300  # Less than 5 minutes
            assert result["trending_topics_detected"] == 1
            assert result["rapid_content_created"] == 1
            
            # Verify trend detection
            mock_trends.detect_trending_topics.assert_called_once()
            
            # Verify rapid content generation
            mock_content.generate_trending_content.assert_called_once()
            
            # Verify immediate posting
            mock_twitter_client.create_tweet.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_goal_driven_workflow(self, mock_user, mock_db_session):
        """Test goal-driven content workflow based on performance targets"""
        
        mock_goal_data = {
            "goal_id": "goal_123",
            "goal_type": "follower_growth",
            "target_value": 1000,
            "current_value": 750,
            "progress_percentage": 75,
            "time_remaining_days": 30,
            "required_daily_growth": 8.33
        }
        
        mock_optimized_content = [
            {
                "platform": "twitter",
                "content": "💡 Pro tip: The key to AI success isn't just the technology—it's understanding your users' real problems. What AI challenge are you trying to solve? Let's discuss solutions! 👇 #AI #ProblemSolving #TechTips",
                "optimization_score": 9.2,
                "predicted_engagement": 8.5,
                "goal_alignment": 0.92
            }
        ]
        
        with patch('backend.services.workflow_orchestration.goal_tracker') as mock_goals, \
             patch('backend.services.workflow_orchestration.content_automation_service') as mock_content, \
             patch('backend.services.workflow_orchestration.performance_optimizer') as mock_optimizer:
            
            # Setup mocks
            mock_goals.get_active_goals.return_value = [mock_goal_data]
            mock_content.generate_goal_optimized_content.return_value = mock_optimized_content
            mock_optimizer.predict_content_performance.return_value = {"predicted_reach": 1200, "engagement_rate": 8.5}
            
            # Execute goal-driven workflow
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="goal_driven_content",
                parameters={
                    "user_id": mock_user.id,
                    "goal_focus": "follower_growth",
                    "optimization_level": "high",
                    "platforms": ["twitter", ]
                },
                user_id=mock_user.id
            )
            
            # Verify goal-driven optimization
            assert result["status"] == "completed"
            assert result["goal_alignment_score"] >= 0.9
            assert result["optimization_applied"] is True
            assert result["predicted_goal_impact"] > 0
            
            # Verify goal analysis
            mock_goals.get_active_goals.assert_called_once()
            
            # Verify optimized content generation
            mock_content.generate_goal_optimized_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_platform_workflow_coordination(self, mock_user, mock_db_session, sample_generated_content):
        """Test coordinated multi-platform content workflow"""
        
        platforms = ["twitter", , "instagram", "facebook"]
        
        with patch('backend.services.workflow_orchestration.content_automation_service') as mock_content, \
             patch('backend.services.workflow_orchestration.TwitterClient') as mock_twitter, \
             patch('backend.services.workflow_orchestration.LinkedInClient') as mock_ \
             patch('backend.services.workflow_orchestration.instagram_client') as mock_instagram, \
             patch('backend.services.workflow_orchestration.facebook_client') as mock_facebook:
            
            # Setup content for all platforms
            multi_platform_content = [
                {"platform": "twitter", "content": "Twitter optimized content", "id": "twitter_123"},
                {"platform": , "content": "LinkedIn professional content", "id": "linkedin_456"},
                {"platform": "instagram", "content": "Instagram visual content", "id": "instagram_789", "media_urls": ["img.jpg"]},
                {"platform": "facebook", "content": "Facebook engaging content", "id": "facebook_101"}
            ]
            
            mock_content.generate_multi_platform_content.return_value = multi_platform_content
            
            # Mock platform clients
            mock_twitter.return_value.create_tweet.return_value = {"id": "tweet_multi_123"}
            mock_linkedin.return_value.create_post.return_value = {"id": "post_multi_456"}
            mock_instagram.create_media.return_value = {"id": "media_multi_789"}
            mock_facebook.create_post.return_value = {"id": "fb_multi_101"}
            
            # Execute multi-platform workflow
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="multi_platform_campaign",
                parameters={
                    "user_id": mock_user.id,
                    "platforms": platforms,
                    "content_theme": "AI innovation",
                    "coordination_timing": "simultaneous",
                    "cross_platform_promotion": True
                },
                user_id=mock_user.id
            )
            
            # Verify multi-platform coordination
            assert result["status"] == "completed"
            assert len(result["platforms_published"]) == 4
            assert result["coordination_success"] is True
            assert result["cross_platform_links_created"] is True
            
            # Verify all platforms were used
            mock_content.generate_multi_platform_content.assert_called_once()
            mock_twitter.return_value.create_tweet.assert_called_once()
            mock_linkedin.return_value.create_post.assert_called_once()
            mock_instagram.create_media.assert_called_once()
            mock_facebook.create_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, mock_user, mock_db_session):
        """Test workflow error recovery and retry mechanisms"""
        
        with patch('backend.services.workflow_orchestration.research_service') as mock_research, \
             patch('backend.services.workflow_orchestration.content_automation_service') as mock_content, \
             patch('backend.services.workflow_orchestration.TwitterClient') as mock_twitter:
            
            # Setup failure scenarios
            mock_research.execute_research_automation.side_effect = [
                Exception("API rate limit exceeded"),  # First attempt fails
                {"research_id": "research_retry_123", "results": []}  # Second attempt succeeds
            ]
            
            mock_content.generate_platform_content.return_value = [
                {"platform": "twitter", "content": "Recovered content", "id": "recovered_123"}
            ]
            
            mock_twitter_client = MagicMock()
            mock_twitter_client.create_tweet.side_effect = [
                Exception("Twitter API error"),  # First post fails
                {"id": "tweet_recovered_456"}  # Retry succeeds
            ]
            mock_twitter.return_value = mock_twitter_client
            
            # Execute workflow with error recovery
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="daily_content_cycle",
                parameters={
                    "user_id": mock_user.id,
                    "retry_enabled": True,
                    "max_retries": 3,
                    "retry_delay": 1  # 1 second for testing
                },
                user_id=mock_user.id
            )
            
            # Verify error recovery
            assert result["status"] == "completed_with_retries"
            assert result["retry_count"] > 0
            assert result["errors_encountered"] >= 2
            assert result["final_success"] is True
            
            # Verify retries were attempted
            assert mock_research.execute_research_automation.call_count == 2
            assert mock_twitter_client.create_tweet.call_count == 2
    
    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self, mock_user, mock_db_session):
        """Test workflow performance monitoring and optimization"""
        
        with patch('backend.services.workflow_orchestration.performance_monitor') as mock_monitor, \
             patch('backend.services.workflow_orchestration.content_automation_service') as mock_content:
            
            # Setup performance monitoring
            mock_monitor.start_monitoring.return_value = {"monitor_id": "monitor_123"}
            mock_monitor.get_performance_metrics.return_value = {
                "execution_time": 145.6,
                "memory_usage": 256,
                "api_calls_made": 15,
                "success_rate": 0.93,
                "bottlenecks": ["content_generation: 45s", "api_rate_limits: 12s"]
            }
            
            mock_content.generate_platform_content.return_value = [
                {"platform": "twitter", "content": "Performance test content"}
            ]
            
            # Execute workflow with performance monitoring
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="performance_monitored_cycle",
                parameters={
                    "user_id": mock_user.id,
                    "enable_monitoring": True,
                    "performance_optimization": True
                },
                user_id=mock_user.id
            )
            
            # Verify performance monitoring
            assert result["status"] == "completed"
            assert "performance_metrics" in result
            assert result["performance_metrics"]["execution_time"] < 200  # Under 200 seconds
            assert result["performance_metrics"]["success_rate"] > 0.9
            assert "optimization_suggestions" in result
            
            # Verify monitoring was enabled
            mock_monitor.start_monitoring.assert_called_once()
            mock_monitor.get_performance_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_scheduling_and_timing(self, mock_user, mock_db_session):
        """Test workflow scheduling and optimal timing calculations"""
        
        with patch('backend.services.workflow_orchestration.timing_optimizer') as mock_timing, \
             patch('backend.services.workflow_orchestration.scheduler') as mock_scheduler:
            
            # Setup timing optimization
            optimal_times = {
                "twitter": datetime.utcnow() + timedelta(hours=2),
                : datetime.utcnow() + timedelta(hours=1),
                "instagram": datetime.utcnow() + timedelta(hours=3)
            }
            
            mock_timing.calculate_optimal_posting_times.return_value = optimal_times
            mock_scheduler.schedule_content.return_value = {
                "scheduled_items": 3,
                "schedule_success": True,
                "next_execution": min(optimal_times.values())
            }
            
            # Execute workflow with scheduling
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="scheduled_content_cycle",
                parameters={
                    "user_id": mock_user.id,
                    "optimize_timing": True,
                    "schedule_content": True,
                    "platforms": ["twitter", , "instagram"]
                },
                user_id=mock_user.id
            )
            
            # Verify scheduling optimization
            assert result["status"] == "completed"
            assert result["content_scheduled"] is True
            assert result["optimal_timing_applied"] is True
            assert "next_execution_time" in result
            assert len(result["scheduled_platforms"]) == 3
            
            # Verify timing optimization
            mock_timing.calculate_optimal_posting_times.assert_called_once()
            mock_scheduler.schedule_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_analytics_and_feedback(self, mock_user, mock_db_session):
        """Test workflow analytics collection and feedback loop"""
        
        with patch('backend.services.workflow_orchestration.analytics_collector') as mock_analytics, \
             patch('backend.services.workflow_orchestration.feedback_processor') as mock_feedback:
            
            # Setup analytics collection
            workflow_analytics = {
                "workflow_id": "workflow_analytics_123",
                "execution_metrics": {
                    "total_duration": 180.5,
                    "step_durations": {
                        "research": 45.2,
                        "content_generation": 78.1,
                        "publishing": 32.8,
                        "analysis": 24.4
                    },
                    "resource_usage": {"cpu": 65, "memory": 412, "network": 1.2}
                },
                "content_metrics": {
                    "content_generated": 4,
                    "platforms_used": 2,
                    "estimated_reach": 2500,
                    "predicted_engagement": 7.8
                }
            }
            
            mock_analytics.collect_workflow_metrics.return_value = workflow_analytics
            mock_feedback.process_performance_feedback.return_value = {
                "optimization_suggestions": [
                    "Reduce content generation time by using cached templates",
                    "Optimize API call batching for better performance"
                ],
                "quality_score": 8.7,
                "improvement_areas": ["timing", "resource_efficiency"]
            }
            
            # Execute workflow with analytics
            result = await workflow_orchestrator.execute_workflow(
                workflow_type="analytics_enabled_cycle",
                parameters={
                    "user_id": mock_user.id,
                    "collect_analytics": True,
                    "enable_feedback_loop": True
                },
                user_id=mock_user.id
            )
            
            # Verify analytics collection
            assert result["status"] == "completed"
            assert "analytics" in result
            assert "feedback" in result
            assert result["analytics"]["quality_score"] > 8.0
            assert len(result["feedback"]["optimization_suggestions"]) > 0
            
            # Verify analytics and feedback processing
            mock_analytics.collect_workflow_metrics.assert_called_once()
            mock_feedback.process_performance_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, mock_user, mock_db_session):
        """Test concurrent execution of multiple workflows"""
        
        with patch('backend.services.workflow_orchestration.content_automation_service') as mock_content:
            
            mock_content.generate_platform_content.return_value = [
                {"platform": "twitter", "content": f"Concurrent content"}
            ]
            
            # Execute multiple workflows concurrently
            workflows = [
                ("daily_content_cycle", {"user_id": mock_user.id, "theme": "AI"}),
                ("trending_response", {"user_id": mock_user.id, "urgency": "high"}),
                ("goal_driven_content", {"user_id": mock_user.id, "goal_type": "engagement"})
            ]
            
            tasks = []
            for workflow_type, params in workflows:
                task = workflow_orchestrator.execute_workflow(
                    workflow_type=workflow_type,
                    parameters=params,
                    user_id=mock_user.id
                )
                tasks.append(task)
            
            # Wait for all workflows to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify concurrent execution
            successful_workflows = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_workflows) == 3
            
            for result in successful_workflows:
                assert result["status"] in ["completed", "completed_with_retries"]
                assert "workflow_type" in result
                assert result["execution_time"] > 0


class TestWorkflowOrchestrationEdgeCases:
    """Test edge cases and error scenarios in workflow orchestration"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_insufficient_resources(self):
        """Test workflow behavior under resource constraints"""
        # Test workflow execution when system resources are limited
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_with_api_quotas_exceeded(self):
        """Test workflow handling when API quotas are exceeded"""
        # Test graceful degradation when API limits are hit
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_database_connection_loss(self):
        """Test workflow recovery from database connection loss"""
        # Test workflow resilience to database issues
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_partial_platform_failures(self):
        """Test workflow continuation when some platforms fail"""
        # Test workflow adaptation when some social platforms are unavailable
        pass


class TestWorkflowOrchestrationPerformance:
    """Performance tests for workflow orchestration"""
    
    @pytest.mark.asyncio
    async def test_workflow_scalability(self):
        """Test workflow performance with increasing load"""
        # Test workflow performance under various load conditions
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_memory_efficiency(self):
        """Test workflow memory usage and optimization"""
        # Test memory efficiency during long-running workflows
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_execution_time_optimization(self):
        """Test workflow execution time optimization"""
        # Test various optimization strategies for workflow speed
        pass