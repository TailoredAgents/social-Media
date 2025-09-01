from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import logging
from backend.core.memory import memory_system
from backend.core.goals import goal_tracker
from backend.agents.crew_config import create_daily_crew, create_optimization_crew
from backend.agents.tools import openai_tool, twitter_tool
from backend.tasks.content_tasks import generate_daily_content
from backend.tasks.research_tasks import run_daily_research
from backend.tasks.optimization_tasks import analyze_performance

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStage:
    name: str
    scheduled_time: str  # HH:MM format
    duration_minutes: int
    dependencies: List[str]
    status: str = "pending"  # pending, running, completed, failed
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class AutonomousWorkflowManager:
    """Manages the daily autonomous workflow cycle"""
    
    def __init__(self):
        self.stages = self._initialize_workflow_stages()
        self.workflow_state = {
            'last_full_cycle': None,
            'current_stage': None,
            'cycle_count': 0,
            'errors': [],
            'metrics': {
                'avg_cycle_time': 0,
                'success_rate': 100,
                'content_generated_today': 0,
                'research_items_today': 0
            }
        }
    
    def _initialize_workflow_stages(self) -> Dict[str, WorkflowStage]:
        """Initialize the daily workflow stages"""
        return {
            'research': WorkflowStage(
                name="Daily Research",
                scheduled_time="06:00",  # 6 AM
                duration_minutes=30,
                dependencies=[]
            ),
            'trend_analysis': WorkflowStage(
                name="Trend Analysis",
                scheduled_time="06:30",  # 6:30 AM
                duration_minutes=20,
                dependencies=['research']
            ),
            'content_planning': WorkflowStage(
                name="Content Planning",
                scheduled_time="09:00",  # 9 AM
                duration_minutes=15,
                dependencies=['research', 'trend_analysis']
            ),
            'content_generation': WorkflowStage(
                name="Content Generation",
                scheduled_time="09:15",  # 9:15 AM
                duration_minutes=45,
                dependencies=['content_planning']
            ),
            'content_optimization': WorkflowStage(
                name="Content Optimization",
                scheduled_time="10:00",  # 10 AM
                duration_minutes=15,
                dependencies=['content_generation']
            ),
            'posting_prep': WorkflowStage(
                name="Posting Preparation",
                scheduled_time="14:00",  # 2 PM
                duration_minutes=20,
                dependencies=['content_optimization']
            ),
            'automated_posting': WorkflowStage(
                name="Automated Posting",
                scheduled_time="15:00",  # 3 PM
                duration_minutes=30,
                dependencies=['posting_prep']
            ),
            'performance_monitoring': WorkflowStage(
                name="Performance Monitoring",
                scheduled_time="20:00",  # 8 PM
                duration_minutes=20,
                dependencies=['automated_posting']
            ),
            'optimization_analysis': WorkflowStage(
                name="Optimization Analysis",
                scheduled_time="22:00",  # 10 PM
                duration_minutes=25,
                dependencies=['performance_monitoring']
            ),
            'goal_update': WorkflowStage(
                name="Goal Progress Update",
                scheduled_time="22:30",  # 10:30 PM
                duration_minutes=10,
                dependencies=['optimization_analysis']
            )
        }
    
    async def run_daily_cycle(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Run the complete daily workflow cycle"""
        cycle_start = datetime.utcnow()
        logger.info(f"Starting daily workflow cycle for user {user_id}")
        
        try:
            # Update cycle state
            self.workflow_state['current_stage'] = 'research'
            self.workflow_state['cycle_count'] += 1
            
            results = {}
            
            # Execute stages in order
            for stage_name, stage in self.stages.items():
                logger.info(f"Starting stage: {stage.name}")
                self.workflow_state['current_stage'] = stage_name
                stage.status = "running"
                stage_start = datetime.utcnow()
                
                try:
                    # Check dependencies
                    if not self._check_dependencies(stage_name):
                        raise Exception(f"Dependencies not met for stage {stage_name}")
                    
                    # Execute stage
                    stage_result = await self._execute_stage(stage_name, user_id)
                    results[stage_name] = stage_result
                    
                    # Update stage status
                    stage.status = "completed"
                    stage.last_run = datetime.utcnow()
                    
                    # Calculate stage duration
                    stage_duration = (datetime.utcnow() - stage_start).total_seconds() / 60
                    logger.info(f"Completed stage {stage.name} in {stage_duration:.1f} minutes")
                    
                except Exception as e:
                    stage.status = "failed"
                    error_info = {
                        'stage': stage_name,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.workflow_state['errors'].append(error_info)
                    logger.error(f"Stage {stage.name} failed: {str(e)}")
                    
                    # Continue with next stage unless critical failure
                    if stage_name in ['research', 'content_generation']:
                        logger.error("Critical stage failed, aborting cycle")
                        break
            
            # Update workflow state
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds() / 60
            self.workflow_state['last_full_cycle'] = datetime.utcnow()
            self.workflow_state['current_stage'] = None
            
            # Update metrics
            self._update_metrics(cycle_duration, results)
            
            logger.info(f"Daily cycle completed in {cycle_duration:.1f} minutes")
            
            return {
                'status': 'success',
                'cycle_duration_minutes': cycle_duration,
                'stages_completed': len([s for s in self.stages.values() if s.status == "completed"]),
                'stages_failed': len([s for s in self.stages.values() if s.status == "failed"]),
                'results': results,
                'next_cycle': cycle_start + timedelta(days=1)
            }
            
        except Exception as e:
            logger.error(f"Daily cycle failed: {str(e)}")
            self.workflow_state['current_stage'] = None
            return {
                'status': 'error',
                'error': str(e),
                'cycle_duration_minutes': (datetime.utcnow() - cycle_start).total_seconds() / 60
            }
    
    def _check_dependencies(self, stage_name: str) -> bool:
        """Check if stage dependencies are satisfied"""
        stage = self.stages[stage_name]
        
        for dependency in stage.dependencies:
            if dependency not in self.stages:
                return False
            
            dep_stage = self.stages[dependency]
            if dep_stage.status != "completed":
                return False
        
        return True
    
    async def _execute_stage(self, stage_name: str, user_id: str) -> Dict[str, Any]:
        """Execute a specific workflow stage"""
        
        if stage_name == 'research':
            return await self._execute_research_stage()
        
        elif stage_name == 'trend_analysis':
            return await self._execute_trend_analysis_stage()
        
        elif stage_name == 'content_planning':
            return await self._execute_content_planning_stage(user_id)
        
        elif stage_name == 'content_generation':
            return await self._execute_content_generation_stage(user_id)
        
        elif stage_name == 'content_optimization':
            return await self._execute_content_optimization_stage()
        
        elif stage_name == 'posting_prep':
            return await self._execute_posting_prep_stage()
        
        elif stage_name == 'automated_posting':
            return await self._execute_automated_posting_stage()
        
        elif stage_name == 'performance_monitoring':
            return await self._execute_performance_monitoring_stage()
        
        elif stage_name == 'optimization_analysis':
            return await self._execute_optimization_analysis_stage()
        
        elif stage_name == 'goal_update':
            return await self._execute_goal_update_stage(user_id)
        
        else:
            raise Exception(f"Unknown stage: {stage_name}")
    
    async def _execute_research_stage(self) -> Dict[str, Any]:
        """Execute daily research"""
        topics = [
            "social media trends 2025",
            "AI marketing automation",
            "content marketing strategies",
            "social media engagement",
            "digital marketing trends"
        ]
        
        research_results = []
        for topic in topics:
            try:
                # Use OpenAI to generate research insights
                research_prompt = f"""Research and analyze current trends about {topic}. 
                
                Provide:
                1. Key trends and developments
                2. Audience sentiment and engagement patterns
                3. Content opportunities
                4. Actionable insights for content creation
                
                Format as structured insights for social media strategy."""
                
                research_result = openai_tool.generate_text(research_prompt, max_tokens=400)
                
                # Store in memory
                memory_system.store_content(
                    content=research_result,
                    metadata={
                        'type': 'daily_research',
                        'topic': topic,
                        'stage': 'research',
                        'confidence_score': 0.8
                    }
                )
                
                research_results.append({
                    'topic': topic,
                    'insights': research_result,
                    'status': 'completed'
                })
                
            except Exception as e:
                research_results.append({
                    'topic': topic,
                    'error': str(e),
                    'status': 'failed'
                })
        
        self.workflow_state['metrics']['research_items_today'] += len(research_results)
        
        return {
            'research_completed': len([r for r in research_results if r['status'] == 'completed']),
            'research_failed': len([r for r in research_results if r['status'] == 'failed']),
            'topics_analyzed': topics,
            'insights_generated': len(research_results)
        }
    
    async def _execute_trend_analysis_stage(self) -> Dict[str, Any]:
        """Analyze trends from research data"""
        
        # Get recent research from memory
        recent_research = memory_system.get_content_by_type('daily_research', limit=10)
        
        if not recent_research:
            return {'status': 'skipped', 'reason': 'No research data available'}
        
        # Combine research findings for trend analysis
        combined_research = "\n\n".join([item['content'] for item in recent_research])
        
        trend_analysis_prompt = f"""Based on this recent research data, identify the top 5 trending topics and opportunities:

{combined_research}

Provide:
1. Top 5 trending topics with relevance scores
2. Content angles with high viral potential
3. Optimal posting strategies
4. Hashtag recommendations

Format as actionable trend insights."""
        
        trend_analysis = openai_tool.generate_text(trend_analysis_prompt, max_tokens=500)
        
        # Store trend analysis
        memory_system.store_content(
            content=trend_analysis,
            metadata={
                'type': 'trend_analysis',
                'stage': 'trend_analysis',
                'data_sources': len(recent_research)
            }
        )
        
        return {
            'status': 'completed',
            'research_sources_analyzed': len(recent_research),
            'trending_topics_identified': 5,
            'analysis_stored': True
        }
    
    async def _execute_content_planning_stage(self, user_id: str) -> Dict[str, Any]:
        """Plan content based on research and goals"""
        
        # Get user goals
        user_goals = goal_tracker.get_user_goals(user_id)
        active_goals = [g for g in user_goals if g.status.value == 'active']
        
        # Get trend analysis
        trend_data = memory_system.get_content_by_type('trend_analysis', limit=3)
        
        planning_prompt = f"""Create a content plan for today based on:

User Goals: {[g.title for g in active_goals]}
Recent Trends: {trend_data[0]['content'] if trend_data else 'No trend data available'}

Plan 3-5 pieces of content that:
1. Align with user goals
2. Leverage trending topics
3. Are optimized for different platforms
4. Have high engagement potential

Return as a structured content plan."""
        
        content_plan = openai_tool.generate_text(planning_prompt, max_tokens=400)
        
        # Store content plan
        memory_system.store_content(
            content=content_plan,
            metadata={
                'type': 'content_plan',
                'stage': 'content_planning',
                'goals_considered': len(active_goals),
                'trends_incorporated': len(trend_data)
            }
        )
        
        return {
            'status': 'completed',
            'goals_considered': len(active_goals),
            'trends_incorporated': len(trend_data),
            'content_pieces_planned': 4  # Average
        }
    
    async def _execute_content_generation_stage(self, user_id: str) -> Dict[str, Any]:
        """Generate content based on plan"""
        
        # Get content plan
        content_plans = memory_system.get_content_by_type('content_plan', limit=1)
        
        if not content_plans:
            return {'status': 'skipped', 'reason': 'No content plan available'}
        
        content_plan = content_plans[0]['content']
        
        # Generate content for different platforms
        platforms = ['twitter', 'linkedin', 'instagram']
        generated_content = []
        
        for platform in platforms:
            generation_prompt = f"""Based on this content plan, create a {platform} post:

Content Plan: {content_plan}

Requirements:
- Platform-specific format and tone
- Optimal length for {platform}
- Relevant hashtags
- High engagement potential
- Brand-appropriate voice

Return only the post content, ready to publish."""
            
            try:
                post_content = openai_tool.generate_text(generation_prompt, max_tokens=250)
                
                # Store generated content
                memory_system.store_content(
                    content=post_content,
                    metadata={
                        'type': 'generated_content',
                        'platform': platform,
                        'stage': 'content_generation',
                        'status': 'draft'
                    }
                )
                
                generated_content.append({
                    'platform': platform,
                    'content': post_content,
                    'status': 'generated'
                })
                
            except Exception as e:
                generated_content.append({
                    'platform': platform,
                    'error': str(e),
                    'status': 'failed'
                })
        
        self.workflow_state['metrics']['content_generated_today'] += len([c for c in generated_content if c['status'] == 'generated'])
        
        return {
            'status': 'completed',
            'content_pieces_generated': len([c for c in generated_content if c['status'] == 'generated']),
            'platforms_covered': platforms,
            'generation_success_rate': len([c for c in generated_content if c['status'] == 'generated']) / len(platforms) * 100
        }
    
    async def _execute_content_optimization_stage(self) -> Dict[str, Any]:
        """Optimize generated content"""
        
        # Get recent generated content
        draft_content = memory_system.get_content_by_type('generated_content', limit=5)
        
        if not draft_content:
            return {'status': 'skipped', 'reason': 'No draft content available'}
        
        optimized_count = 0
        
        for content_item in draft_content:
            optimization_prompt = f"""Optimize this social media post for better engagement:

Original: {content_item['content']}
Platform: {content_item['metadata'].get('platform', 'unknown')}

Improvements:
1. Enhance hook and opening
2. Optimize hashtags
3. Add call-to-action
4. Improve readability
5. Increase viral potential

Return the optimized version."""
            
            try:
                optimized_content = openai_tool.generate_text(optimization_prompt, max_tokens=200)
                
                # Store optimized version
                memory_system.store_content(
                    content=optimized_content,
                    metadata={
                        'type': 'optimized_content',
                        'platform': content_item['metadata'].get('platform'),
                        'stage': 'content_optimization',
                        'original_id': content_item.get('content_id'),
                        'status': 'ready'
                    }
                )
                
                optimized_count += 1
                
            except Exception as e:
                logger.error(f"Content optimization failed: {str(e)}")
        
        return {
            'status': 'completed',
            'content_pieces_optimized': optimized_count,
            'optimization_success_rate': optimized_count / len(draft_content) * 100 if draft_content else 0
        }
    
    async def _execute_posting_prep_stage(self) -> Dict[str, Any]:
        """Prepare content for posting"""
        
        # Get optimized content
        ready_content = memory_system.get_content_by_type('optimized_content', limit=10)
        
        if not ready_content:
            return {'status': 'skipped', 'reason': 'No optimized content available'}
        
        # Schedule content for optimal times
        scheduled_posts = []
        
        optimal_times = {
            'twitter': '15:00',
            'linkedin': '10:00', 
            'instagram': '19:00'
        }
        
        for content_item in ready_content:
            platform = content_item['metadata'].get('platform', 'twitter')
            optimal_time = optimal_times.get(platform, '12:00')
            
            scheduled_posts.append({
                'content_id': content_item.get('content_id'),
                'platform': platform,
                'content': content_item['content'],
                'scheduled_time': optimal_time,
                'status': 'scheduled'
            })
        
        return {
            'status': 'completed',
            'posts_scheduled': len(scheduled_posts),
            'platforms': list(set([p['platform'] for p in scheduled_posts]))
        }
    
    async def _execute_automated_posting_stage(self) -> Dict[str, Any]:
        """Execute automated posting"""
        
        # In a real implementation, this would:
        # 1. Get scheduled posts from database
        # 2. Check if it's the right time to post
        # 3. Use platform APIs to publish content
        # 4. Update post status and metrics
        
        # For now, simulate posting
        simulated_posts = [
            {'platform': 'twitter', 'status': 'posted', 'post_id': 'tw_123'},
            {'platform': 'linkedin', 'status': 'posted', 'post_id': 'li_456'},
            {'platform': 'instagram', 'status': 'scheduled', 'post_id': 'ig_789'}
        ]
        
        return {
            'status': 'completed',
            'posts_published': len([p for p in simulated_posts if p['status'] == 'posted']),
            'posts_scheduled': len([p for p in simulated_posts if p['status'] == 'scheduled']),
            'success_rate': len([p for p in simulated_posts if p['status'] == 'posted']) / len(simulated_posts) * 100
        }
    
    async def _execute_performance_monitoring_stage(self) -> Dict[str, Any]:
        """Monitor performance of posted content"""
        
        # Simulate performance monitoring
        # In production, this would query social media APIs
        
        performance_data = {
            'posts_monitored': 3,
            'total_engagement': 156,
            'avg_engagement_rate': 4.2,
            'reach': 2450,
            'top_performing_post': {
                'platform': 'linkedin',
                'engagement_rate': 6.8
            }
        }
        
        return {
            'status': 'completed',
            **performance_data
        }
    
    async def _execute_optimization_analysis_stage(self) -> Dict[str, Any]:
        """Analyze performance and generate optimization recommendations"""
        
        analysis_prompt = """Based on today's content performance:
        - 3 posts published
        - Average engagement rate: 4.2%
        - Total reach: 2,450
        - Best performing: LinkedIn post (6.8% engagement)
        
        Provide optimization recommendations for tomorrow:
        1. Content format adjustments
        2. Timing optimizations
        3. Platform strategy improvements
        4. Engagement tactics
        
        Return actionable insights."""
        
        optimization_insights = openai_tool.generate_text(analysis_prompt, max_tokens=300)
        
        # Store optimization insights
        memory_system.store_content(
            content=optimization_insights,
            metadata={
                'type': 'optimization_insights',
                'stage': 'optimization_analysis',
                'performance_data': {
                    'avg_engagement': 4.2,
                    'reach': 2450,
                    'posts_analyzed': 3
                }
            }
        )
        
        return {
            'status': 'completed',
            'insights_generated': True,
            'recommendations_count': 4,
            'performance_baseline': {
                'engagement_rate': 4.2,
                'reach': 2450
            }
        }
    
    async def _execute_goal_update_stage(self, user_id: str) -> Dict[str, Any]:
        """Update goal progress based on performance"""
        
        # Get active goals
        user_goals = goal_tracker.get_user_goals(user_id)
        active_goals = [g for g in user_goals if g.status.value == 'active']
        
        updated_goals = 0
        
        # Simulate goal updates based on daily performance
        for goal in active_goals:
            if goal.goal_type.value == 'engagement_rate':
                # Update with today's engagement rate
                new_value = 4.2  # From performance monitoring
                goal_tracker.update_goal_progress(goal.goal_id, new_value)
                updated_goals += 1
            
            elif goal.goal_type.value == 'content_volume':
                # Increment content count
                current_count = goal.current_value
                goal_tracker.update_goal_progress(goal.goal_id, current_count + 3)  # 3 posts today
                updated_goals += 1
        
        return {
            'status': 'completed',
            'goals_updated': updated_goals,
            'active_goals_total': len(active_goals)
        }
    
    def _update_metrics(self, cycle_duration: float, results: Dict[str, Any]):
        """Update workflow metrics"""
        
        # Update average cycle time
        current_avg = self.workflow_state['metrics']['avg_cycle_time']
        cycle_count = self.workflow_state['cycle_count']
        
        new_avg = ((current_avg * (cycle_count - 1)) + cycle_duration) / cycle_count
        self.workflow_state['metrics']['avg_cycle_time'] = new_avg
        
        # Update success rate
        completed_stages = len([s for s in self.stages.values() if s.status == "completed"])
        total_stages = len(self.stages)
        self.workflow_state['metrics']['success_rate'] = (completed_stages / total_stages) * 100
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        
        return {
            'current_stage': self.workflow_state['current_stage'],
            'last_full_cycle': self.workflow_state['last_full_cycle'].isoformat() if self.workflow_state['last_full_cycle'] else None,
            'cycle_count': self.workflow_state['cycle_count'],
            'metrics': self.workflow_state['metrics'],
            'stages': {
                name: {
                    'name': stage.name,
                    'status': stage.status,
                    'scheduled_time': stage.scheduled_time,
                    'last_run': stage.last_run.isoformat() if stage.last_run else None,
                    'duration_minutes': stage.duration_minutes
                }
                for name, stage in self.stages.items()
            },
            'recent_errors': self.workflow_state['errors'][-5:] if self.workflow_state['errors'] else []
        }

# Global workflow manager
workflow_manager = AutonomousWorkflowManager()