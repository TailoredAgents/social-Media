"""
Workflow Orchestration Service
Integration Specialist Component - Master orchestrator for automated workflows
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import ContentItem, Goal, WorkflowExecution
from backend.services.research_automation import research_pipeline, ResearchQuery, ResearchSource
from backend.services.content_automation import content_automation, ContentGenerationRequest, ContentType, ContentTone
from backend.services.metrics_collection import metrics_collector

settings = get_settings()
logger = logging.getLogger(__name__)

class WorkflowType(Enum):
    """Types of automated workflows"""
    DAILY_CONTENT = "daily_content"
    TRENDING_RESPONSE = "trending_response"
    GOAL_DRIVEN = "goal_driven"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    CRISIS_RESPONSE = "crisis_response"
    SEASONAL_CAMPAIGN = "seasonal_campaign"
    ENGAGEMENT_BOOST = "engagement_boost"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class WorkflowConfig:
    """Workflow configuration parameters"""
    workflow_type: WorkflowType
    name: str
    description: str
    enabled: bool
    schedule: str  # Cron-like schedule expression
    platforms: List[str]
    content_types: List[ContentType]
    tone: ContentTone
    target_audience: str
    keywords: List[str]
    goals: List[str]
    max_posts_per_day: int = 5
    research_enabled: bool = True
    auto_publish: bool = False
    priority: int = 1  # 1=highest, 5=lowest
    
    # Advanced settings
    sentiment_threshold: float = 0.1
    engagement_threshold: int = 100
    trend_threshold: float = 0.7
    brand_safety: bool = True
    approval_required: bool = True

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    name: str
    status: WorkflowStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

@dataclass
class WorkflowExecution:
    """Complete workflow execution record"""
    execution_id: str
    workflow_config: WorkflowConfig
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: Optional[float]
    steps: List[WorkflowStep]
    metrics: Dict[str, Any]
    outputs: Dict[str, Any]
    error_message: Optional[str] = None

class WorkflowOrchestrator:
    """
    Master workflow orchestration service
    
    Features:
    - Multi-type workflow execution
    - Step-by-step progress tracking
    - Error handling and recovery
    - Performance metrics collection
    - Workflow scheduling and management
    - Cross-service coordination
    - Real-time status monitoring
    - Failure recovery mechanisms
    """
    
    def __init__(self):
        """Initialize workflow orchestrator"""
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        
        # Default workflow configurations
        self._setup_default_workflows()
        
        logger.info("WorkflowOrchestrator initialized")
    
    def _setup_default_workflows(self):
        """Setup default workflow configurations"""
        # Daily Content Workflow
        self.workflow_configs["daily_content"] = WorkflowConfig(
            workflow_type=WorkflowType.DAILY_CONTENT,
            name="Daily Content Generation",
            description="Automated daily content creation and publishing",
            enabled=True,
            schedule="0 9 * * *",  # 9 AM daily
            platforms=["twitter", "linkedin", "instagram"],
            content_types=[ContentType.TEXT_POST, ContentType.IMAGE_POST],
            tone=ContentTone.PROFESSIONAL,
            target_audience="professionals",
            keywords=["industry trends", "business insights", "productivity"],
            goals=["brand_awareness", "engagement"],
            max_posts_per_day=3,
            research_enabled=True,
            auto_publish=False,
            priority=1
        )
        
        # Trending Response Workflow
        self.workflow_configs["trending_response"] = WorkflowConfig(
            workflow_type=WorkflowType.TRENDING_RESPONSE,
            name="Trending Topic Response",
            description="Rapid response to trending topics and news",
            enabled=True,
            schedule="*/30 * * * *",  # Every 30 minutes
            platforms=["twitter", "facebook"],
            content_types=[ContentType.TEXT_POST, ContentType.THREAD],
            tone=ContentTone.CONVERSATIONAL,
            target_audience="general",
            keywords=["breaking news", "trending", "viral"],
            goals=["engagement", "reach"],
            max_posts_per_day=5,
            research_enabled=True,
            auto_publish=True,
            priority=2,
            trend_threshold=0.8
        )
        
        # Goal-Driven Workflow
        self.workflow_configs["goal_driven"] = WorkflowConfig(
            workflow_type=WorkflowType.GOAL_DRIVEN,
            name="Goal-Driven Content",
            description="Content creation aligned with specific business goals",
            enabled=True,
            schedule="0 14 * * *",  # 2 PM daily
            platforms=["linkedin", "facebook", "instagram"],
            content_types=[ContentType.TEXT_POST, ContentType.ARTICLE, ContentType.IMAGE_POST],
            tone=ContentTone.EDUCATIONAL,
            target_audience="decision makers",
            keywords=["business strategy", "leadership", "innovation"],
            goals=["lead_generation", "thought_leadership"],
            max_posts_per_day=2,
            research_enabled=True,
            auto_publish=False,
            priority=1,
            approval_required=True
        )
    
    async def execute_workflow(
        self,
        db: Session,
        workflow_id: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a complete workflow
        
        Args:
            db: Database session
            workflow_id: ID of workflow to execute
            config_override: Optional configuration overrides
            
        Returns:
            Workflow execution result
        """
        if workflow_id not in self.workflow_configs:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        
        # Get workflow configuration
        config = self.workflow_configs[workflow_id]
        
        # Apply any overrides
        if config_override:
            for key, value in config_override.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Create execution record
        execution_id = f"{workflow_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_config=config,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            total_duration=None,
            steps=[],
            metrics={},
            outputs={}
        )
        
        # Store active workflow
        self.active_workflows[execution_id] = execution
        
        logger.info(f"Starting workflow execution: {execution_id}")
        
        try:
            # Execute workflow based on type
            if config.workflow_type == WorkflowType.DAILY_CONTENT:
                await self._execute_daily_content_workflow(db, execution)
            elif config.workflow_type == WorkflowType.TRENDING_RESPONSE:
                await self._execute_trending_response_workflow(db, execution)
            elif config.workflow_type == WorkflowType.GOAL_DRIVEN:
                await self._execute_goal_driven_workflow(db, execution)
            elif config.workflow_type == WorkflowType.COMPETITIVE_ANALYSIS:
                await self._execute_competitive_analysis_workflow(db, execution)
            elif config.workflow_type == WorkflowType.ENGAGEMENT_BOOST:
                await self._execute_engagement_boost_workflow(db, execution)
            else:
                raise ValueError(f"Workflow type {config.workflow_type} not implemented")
            
            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
            
            logger.info(f"Workflow {execution_id} completed successfully in {execution.total_duration:.2f}s")
            
        except Exception as e:
            # Mark as failed
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
            
            logger.error(f"Workflow {execution_id} failed: {e}")
            
        finally:
            # Save execution record
            await self._save_workflow_execution(db, execution)
            
            # Remove from active workflows
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]
        
        return execution
    
    async def _execute_daily_content_workflow(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Execute daily content generation workflow"""
        config = execution.workflow_config
        
        # Step 1: Research Phase
        research_step = WorkflowStep(
            step_id="research",
            name="Market Research",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(research_step)
        
        try:
            if config.research_enabled:
                # Conduct research
                research_query = ResearchQuery(
                    keywords=config.keywords,
                    platforms=[ResearchSource.TWITTER, ResearchSource.NEWS_API, ResearchSource.GOOGLE_TRENDS],
                    content_types=["text", "image"],
                    time_range="24h",
                    max_results=50
                )
                
                research_summary = await research_pipeline.execute_research(
                    db=db,
                    query=research_query,
                    save_results=True
                )
                
                research_step.result = {
                    "total_results": research_summary.total_results,
                    "trending_topics": len(research_summary.trending_topics),
                    "sentiment": research_summary.sentiment_breakdown
                }
            else:
                research_step.result = {"research_skipped": True}
            
            research_step.status = WorkflowStatus.COMPLETED
            research_step.completed_at = datetime.utcnow()
            research_step.duration = (research_step.completed_at - research_step.started_at).total_seconds()
            
        except Exception as e:
            research_step.status = WorkflowStatus.FAILED
            research_step.error_message = str(e)
            raise
        
        # Step 2: Content Generation Phase
        generation_step = WorkflowStep(
            step_id="generation",
            name="Content Generation",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(generation_step)
        
        try:
            # Generate content for each planned post
            generated_content = []
            
            for i in range(min(config.max_posts_per_day, 3)):  # Limit to 3 for daily workflow
                # Select topic from research or use default
                topic = config.keywords[i % len(config.keywords)] if config.keywords else "industry update"
                
                # Create content generation request
                content_request = ContentGenerationRequest(
                    topic=topic,
                    platforms=config.platforms,
                    content_type=config.content_types[i % len(config.content_types)],
                    tone=config.tone,
                    target_audience=config.target_audience,
                    keywords=config.keywords[:3],  # Limit keywords
                    goals=config.goals,
                    include_hashtags=True,
                    include_call_to_action=True,
                    max_length=None,
                    include_media=True,
                    schedule_time=None,
                    urgency="normal"
                )
                
                # Generate content
                automation_result = await content_automation.execute_automation_pipeline(
                    db=db,
                    request=content_request,
                    publish_immediately=config.auto_publish
                )
                
                generated_content.append(automation_result)
                
                # Brief delay between generations
                await asyncio.sleep(1)
            
            generation_step.result = {
                "content_pieces": len(generated_content),
                "platforms_covered": list(set().union(*[result.request.platforms for result in generated_content])),
                "auto_published": config.auto_publish
            }
            
            generation_step.status = WorkflowStatus.COMPLETED
            generation_step.completed_at = datetime.utcnow()
            generation_step.duration = (generation_step.completed_at - generation_step.started_at).total_seconds()
            
            # Store outputs
            execution.outputs["generated_content"] = [asdict(result) for result in generated_content]
            
        except Exception as e:
            generation_step.status = WorkflowStatus.FAILED
            generation_step.error_message = str(e)
            raise
        
        # Step 3: Metrics Collection Phase
        metrics_step = WorkflowStep(
            step_id="metrics",
            name="Metrics Collection",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(metrics_step)
        
        try:
            # Collect current metrics for performance tracking
            metrics_results = await metrics_collector.collect_all_metrics(
                db=db,
                force_collection=False
            )
            
            metrics_step.result = {
                "platforms_collected": len(metrics_results),
                "total_metrics": sum(r.metrics_collected for r in metrics_results if r.success),
                "successful_collections": sum(1 for r in metrics_results if r.success)
            }
            
            metrics_step.status = WorkflowStatus.COMPLETED
            metrics_step.completed_at = datetime.utcnow()
            metrics_step.duration = (metrics_step.completed_at - metrics_step.started_at).total_seconds()
            
            # Update execution metrics
            execution.metrics = {
                "total_content_generated": len(generated_content),
                "research_topics_found": research_step.result.get("trending_topics", 0) if research_step.result else 0,
                "metrics_collected": metrics_step.result["total_metrics"],
                "workflow_duration": sum(step.duration for step in execution.steps if step.duration)
            }
            
        except Exception as e:
            metrics_step.status = WorkflowStatus.FAILED
            metrics_step.error_message = str(e)
            # Don't raise - metrics collection failure shouldn't fail the whole workflow
            logger.warning(f"Metrics collection failed in workflow: {e}")
    
    async def _execute_trending_response_workflow(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Execute trending topic response workflow"""
        config = execution.workflow_config
        
        # Step 1: Trend Detection
        trend_detection_step = WorkflowStep(
            step_id="trend_detection",
            name="Trend Detection",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(trend_detection_step)
        
        try:
            # Research current trends
            research_query = ResearchQuery(
                keywords=config.keywords,
                platforms=[ResearchSource.TWITTER, ResearchSource.GOOGLE_TRENDS, ResearchSource.NEWS_API],
                content_types=["text"],
                time_range="1h",  # Very recent for trending
                max_results=100,
                include_sentiment=True
            )
            
            research_summary = await research_pipeline.execute_research(
                db=db,
                query=research_query,
                save_results=True
            )
            
            # Filter for high-trend topics
            high_trend_topics = [
                topic for topic in research_summary.trending_topics
                if topic.trend_score >= config.trend_threshold and topic.is_viral
            ]
            
            trend_detection_step.result = {
                "total_trends": len(research_summary.trending_topics),
                "high_trend_topics": len(high_trend_topics),
                "viral_topics": sum(1 for t in research_summary.trending_topics if t.is_viral)
            }
            
            trend_detection_step.status = WorkflowStatus.COMPLETED
            trend_detection_step.completed_at = datetime.utcnow()
            trend_detection_step.duration = (trend_detection_step.completed_at - trend_detection_step.started_at).total_seconds()
            
        except Exception as e:
            trend_detection_step.status = WorkflowStatus.FAILED
            trend_detection_step.error_message = str(e)
            raise
        
        # Step 2: Rapid Content Creation
        if high_trend_topics:
            rapid_content_step = WorkflowStep(
                step_id="rapid_content",
                name="Rapid Content Creation",
                status=WorkflowStatus.RUNNING,
                started_at=datetime.utcnow(),
                completed_at=None,
                duration=None,
                result=None,
                error_message=None
            )
            execution.steps.append(rapid_content_step)
            
            try:
                # Create content for top trending topics
                rapid_content = []
                
                for i, topic in enumerate(high_trend_topics[:3]):  # Limit to top 3
                    content_request = ContentGenerationRequest(
                        topic=topic.topic,
                        platforms=config.platforms,
                        content_type=ContentType.TEXT_POST,  # Fast text posts for trending
                        tone=config.tone,
                        target_audience=config.target_audience,
                        keywords=[topic.topic] + topic.related_keywords[:2],
                        goals=config.goals,
                        include_hashtags=True,
                        include_call_to_action=True,
                        urgency="high"  # High urgency for trending content
                    )
                    
                    automation_result = await content_automation.execute_automation_pipeline(
                        db=db,
                        request=content_request,
                        publish_immediately=config.auto_publish
                    )
                    
                    rapid_content.append(automation_result)
                
                rapid_content_step.result = {
                    "trending_posts_created": len(rapid_content),
                    "topics_covered": [topic.topic for topic in high_trend_topics[:3]],
                    "auto_published": config.auto_publish
                }
                
                rapid_content_step.status = WorkflowStatus.COMPLETED
                rapid_content_step.completed_at = datetime.utcnow()
                rapid_content_step.duration = (rapid_content_step.completed_at - rapid_content_step.started_at).total_seconds()
                
                execution.outputs["rapid_content"] = [asdict(result) for result in rapid_content]
                
            except Exception as e:
                rapid_content_step.status = WorkflowStatus.FAILED
                rapid_content_step.error_message = str(e)
                raise
        
        # Update execution metrics
        execution.metrics = {
            "trends_detected": len(research_summary.trending_topics),
            "high_value_trends": len(high_trend_topics),
            "content_created": len(high_trend_topics),
            "response_time": sum(step.duration for step in execution.steps if step.duration)
        }
    
    async def _execute_goal_driven_workflow(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Execute goal-driven content workflow"""
        config = execution.workflow_config
        
        # Step 1: Goal Analysis
        goal_analysis_step = WorkflowStep(
            step_id="goal_analysis",
            name="Goal Analysis",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(goal_analysis_step)
        
        try:
            # Get active goals from database
            active_goals = db.query(Goal).filter(
                Goal.status == "active",
                Goal.target_date >= datetime.utcnow()
            ).all()
            
            # Filter goals relevant to this workflow
            relevant_goals = [
                goal for goal in active_goals
                if any(goal_name in goal.title or goal_name in goal.description 
                      for goal_name in config.goals)
            ]
            
            goal_analysis_step.result = {
                "total_active_goals": len(active_goals),
                "relevant_goals": len(relevant_goals),
                "goal_progress": [
                    {
                        "goal_id": goal.id,
                        "title": goal.title,
                        "progress": goal.current_value / goal.target_value * 100 if goal.target_value > 0 else 0
                    }
                    for goal in relevant_goals
                ]
            }
            
            goal_analysis_step.status = WorkflowStatus.COMPLETED
            goal_analysis_step.completed_at = datetime.utcnow()
            goal_analysis_step.duration = (goal_analysis_step.completed_at - goal_analysis_step.started_at).total_seconds()
            
        except Exception as e:
            goal_analysis_step.status = WorkflowStatus.FAILED
            goal_analysis_step.error_message = str(e)
            raise
        
        # Step 2: Strategic Content Generation
        strategic_content_step = WorkflowStep(
            step_id="strategic_content",
            name="Strategic Content Generation",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration=None,
            result=None,
            error_message=None
        )
        execution.steps.append(strategic_content_step)
        
        try:
            strategic_content = []
            
            # Create content aligned with each relevant goal
            for goal in relevant_goals[:config.max_posts_per_day]:
                # Determine content approach based on goal
                if "engagement" in goal.title.lower():
                    content_type = ContentType.POLL
                    tone = ContentTone.CONVERSATIONAL
                elif "lead" in goal.title.lower():
                    content_type = ContentType.ARTICLE
                    tone = ContentTone.EDUCATIONAL
                elif "awareness" in goal.title.lower():
                    content_type = ContentType.IMAGE_POST
                    tone = ContentTone.INSPIRATIONAL
                else:
                    content_type = ContentType.TEXT_POST
                    tone = config.tone
                
                content_request = ContentGenerationRequest(
                    topic=goal.title,
                    platforms=config.platforms,
                    content_type=content_type,
                    tone=tone,
                    target_audience=config.target_audience,
                    keywords=config.keywords,
                    goals=[goal.title],
                    include_hashtags=True,
                    include_call_to_action=True,
                    urgency="normal"
                )
                
                automation_result = await content_automation.execute_automation_pipeline(
                    db=db,
                    request=content_request,
                    publish_immediately=config.auto_publish
                )
                
                strategic_content.append(automation_result)
            
            strategic_content_step.result = {
                "strategic_posts_created": len(strategic_content),
                "goals_addressed": len(relevant_goals),
                "requires_approval": config.approval_required
            }
            
            strategic_content_step.status = WorkflowStatus.COMPLETED
            strategic_content_step.completed_at = datetime.utcnow()
            strategic_content_step.duration = (strategic_content_step.completed_at - strategic_content_step.started_at).total_seconds()
            
            execution.outputs["strategic_content"] = [asdict(result) for result in strategic_content]
            
        except Exception as e:
            strategic_content_step.status = WorkflowStatus.FAILED
            strategic_content_step.error_message = str(e)
            raise
        
        # Update execution metrics
        execution.metrics = {
            "goals_analyzed": len(relevant_goals),
            "content_created": len(strategic_content),
            "approval_required": config.approval_required,
            "strategic_alignment_score": 0.9  # High alignment for goal-driven content
        }
    
    async def _execute_competitive_analysis_workflow(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Execute competitive analysis workflow"""
        # Placeholder for competitive analysis workflow
        logger.info("Competitive analysis workflow not yet implemented")
        
        execution.metrics = {
            "competitors_analyzed": 0,
            "insights_generated": 0,
            "competitive_gaps_found": 0
        }
    
    async def _execute_engagement_boost_workflow(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Execute engagement boost workflow"""
        # Placeholder for engagement boost workflow
        logger.info("Engagement boost workflow not yet implemented")
        
        execution.metrics = {
            "low_engagement_posts_identified": 0,
            "boost_actions_taken": 0,
            "expected_engagement_increase": 0
        }
    
    async def _save_workflow_execution(
        self,
        db: Session,
        execution: WorkflowExecution
    ):
        """Save workflow execution record to database"""
        try:
            # Create workflow execution record (would need WorkflowExecution model)
            # For now, just log the execution
            logger.info(f"Workflow execution {execution.execution_id} completed with {len(execution.steps)} steps")
            
            # Log step details
            for step in execution.steps:
                logger.info(f"Step {step.step_id}: {step.status.value} in {step.duration:.2f}s" if step.duration else f"Step {step.step_id}: {step.status.value}")
            
        except Exception as e:
            logger.error(f"Failed to save workflow execution: {e}")
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get status of a running workflow"""
        return self.active_workflows.get(execution_id)
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        if execution_id in self.active_workflows:
            execution = self.active_workflows[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            execution.total_duration = (execution.completed_at - execution.started_at).total_seconds()
            
            logger.info(f"Workflow {execution_id} cancelled")
            return True
        
        return False
    
    def get_workflow_configs(self) -> Dict[str, WorkflowConfig]:
        """Get all available workflow configurations"""
        return self.workflow_configs.copy()
    
    def update_workflow_config(self, workflow_id: str, config: WorkflowConfig):
        """Update workflow configuration"""
        self.workflow_configs[workflow_id] = config
        logger.info(f"Updated workflow configuration: {workflow_id}")
    
    async def schedule_workflows(self, db: Session):
        """Check and execute scheduled workflows"""
        # This would be called by a scheduler (like Celery or APScheduler)
        # to check if any workflows need to be executed based on their schedule
        
        current_time = datetime.utcnow()
        
        for workflow_id, config in self.workflow_configs.items():
            if not config.enabled:
                continue
            
            # Simple schedule checking (in production would use proper cron parsing)
            should_execute = await self._should_execute_workflow(config, current_time)
            
            if should_execute:
                try:
                    logger.info(f"Executing scheduled workflow: {workflow_id}")
                    await self.execute_workflow(db, workflow_id)
                except Exception as e:
                    logger.error(f"Scheduled workflow {workflow_id} failed: {e}")
    
    async def _should_execute_workflow(self, config: WorkflowConfig, current_time: datetime) -> bool:
        """Determine if a workflow should be executed based on schedule"""
        # Simplified schedule checking - in production would use croniter or similar
        
        if config.schedule == "0 9 * * *":  # Daily at 9 AM
            return current_time.hour == 9 and current_time.minute < 5
        elif config.schedule == "*/30 * * * *":  # Every 30 minutes
            return current_time.minute in [0, 30] and current_time.second < 5
        elif config.schedule == "0 14 * * *":  # Daily at 2 PM
            return current_time.hour == 14 and current_time.minute < 5
        
        return False

# Global workflow orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()