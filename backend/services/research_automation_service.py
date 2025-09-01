"""
Automated Research Execution Service
Integration Specialist Component - Orchestrates AI research agents and automates research workflows
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from backend.core.config import get_settings
from backend.agents.crew_config import (
    research_agent, create_research_task, create_daily_crew,
    content_agent, create_content_generation_task
)
from backend.tasks.research_tasks import (
    run_daily_research, research_trending_topics, 
    research_competitor_content, research_web_content
)
from backend.services.metrics_collection_service import metrics_collector
from backend.core.vector_store import vector_store
from backend.db.database import get_db_session
from backend.db.models import ContentItem, Goal
from crewai import Crew, Process

settings = get_settings()
logger = logging.getLogger(__name__)

class ResearchType(Enum):
    """Types of research automation"""
    TRENDING_TOPICS = "trending_topics"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    INDUSTRY_INSIGHTS = "industry_insights"
    AUDIENCE_RESEARCH = "audience_research"
    CONTENT_GAPS = "content_gaps"
    HASHTAG_RESEARCH = "hashtag_research"
    INFLUENCER_RESEARCH = "influencer_research"
    MARKET_ANALYSIS = "market_analysis"

@dataclass
class ResearchJob:
    """Research automation job configuration"""
    job_id: str
    research_type: ResearchType
    parameters: Dict[str, Any]
    schedule_interval: int  # seconds
    last_executed: Optional[datetime] = None
    is_active: bool = True
    priority: int = 1  # 1=high, 2=medium, 3=low
    results_count: int = 0
    created_at: datetime = None

@dataclass
class ResearchResult:
    """Research result structure"""
    job_id: str
    research_type: ResearchType
    results: List[Dict[str, Any]]
    insights: List[str]
    content_opportunities: List[str]
    trending_keywords: List[str]
    competitor_strategies: List[str]
    executed_at: datetime
    execution_time: float
    data_points: int
    confidence_score: float

class AutomatedResearchService:
    """
    Automated Research Execution Service
    
    Features:
    - Multi-type research automation
    - CrewAI agent orchestration
    - Scheduled research execution
    - Real-time trend monitoring
    - Competitor intelligence gathering
    - Content gap analysis
    - Research result synthesis
    - Actionable insight generation
    - Performance tracking and optimization
    """
    
    def __init__(self):
        """Initialize research automation service"""
        self.research_jobs: Dict[str, ResearchJob] = {}
        self.research_history: List[ResearchResult] = []
        self._running = False
        self._research_task = None
        
        # Research execution statistics
        self.stats = {
            "total_jobs": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "insights_generated": 0,
            "content_opportunities": 0
        }
        
        logger.info("AutomatedResearchService initialized")
    
    async def start_automation(self):
        """Start the research automation service"""
        if self._running:
            logger.warning("Research automation already running")
            return
        
        self._running = True
        self._research_task = asyncio.create_task(self._automation_loop())
        logger.info("Started research automation service")
    
    async def stop_automation(self):
        """Stop the research automation service"""
        self._running = False
        if self._research_task:
            self._research_task.cancel()
            try:
                await self._research_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped research automation service")
    
    async def add_research_job(
        self,
        research_type: ResearchType,
        parameters: Dict[str, Any],
        schedule_interval: int = 3600,
        priority: int = 1
    ) -> str:
        """
        Add a new automated research job
        
        Args:
            research_type: Type of research to perform
            parameters: Research-specific parameters
            schedule_interval: How often to run (seconds)
            priority: Job priority (1=high, 2=medium, 3=low)
            
        Returns:
            Job ID
        """
        job_id = f"{research_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        job = ResearchJob(
            job_id=job_id,
            research_type=research_type,
            parameters=parameters,
            schedule_interval=schedule_interval,
            is_active=True,
            priority=priority,
            created_at=datetime.utcnow()
        )
        
        self.research_jobs[job_id] = job
        self.stats["total_jobs"] += 1
        
        logger.info(f"Added research job: {job_id} ({research_type.value})")
        
        # Execute immediately if high priority
        if priority == 1:
            await self._execute_research_job(job_id, job)
        
        return job_id
    
    async def execute_research_now(
        self,
        research_type: ResearchType,
        parameters: Dict[str, Any]
    ) -> Optional[ResearchResult]:
        """
        Execute research immediately
        
        Args:
            research_type: Type of research to perform
            parameters: Research parameters
            
        Returns:
            Research result or None if failed
        """
        try:
            start_time = datetime.utcnow()
            execution_start = asyncio.get_event_loop().time()
            
            logger.info(f"Executing immediate research: {research_type.value}")
            
            # Execute research based on type
            results = await self._perform_research(research_type, parameters)
            
            if results:
                # Analyze and synthesize results
                insights = await self._generate_insights(research_type, results)
                content_opportunities = await self._identify_content_opportunities(results)
                trending_keywords = await self._extract_trending_keywords(results)
                competitor_strategies = await self._analyze_competitor_strategies(results) if research_type == ResearchType.COMPETITOR_ANALYSIS else []
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(results, insights)
                
                execution_time = asyncio.get_event_loop().time() - execution_start
                
                research_result = ResearchResult(
                    job_id=f"immediate_{research_type.value}",
                    research_type=research_type,
                    results=results,
                    insights=insights,
                    content_opportunities=content_opportunities,
                    trending_keywords=trending_keywords,
                    competitor_strategies=competitor_strategies,
                    executed_at=start_time,
                    execution_time=execution_time,
                    data_points=len(results),
                    confidence_score=confidence_score
                )
                
                # Store results
                await self._store_research_results(research_result)
                
                self.stats["successful_executions"] += 1
                self.stats["insights_generated"] += len(insights)
                self.stats["content_opportunities"] += len(content_opportunities)
                
                return research_result
            
        except Exception as e:
            logger.error(f"Failed to execute immediate research: {e}")
            self.stats["failed_executions"] += 1
        
        return None
    
    async def _automation_loop(self):
        """Main automation loop"""
        while self._running:
            try:
                # Get jobs ready for execution
                ready_jobs = self._get_ready_jobs()
                
                # Execute jobs by priority
                for job_id, job in sorted(ready_jobs, key=lambda x: x[1].priority):
                    if not self._running:
                        break
                    
                    await self._execute_research_job(job_id, job)
                    
                    # Brief pause between jobs
                    await asyncio.sleep(5)
                
                # Cleanup old results
                await self._cleanup_old_results()
                
                # Sleep before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in research automation loop: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    def _get_ready_jobs(self) -> List[tuple]:
        """Get jobs ready for execution"""
        ready_jobs = []
        current_time = datetime.utcnow()
        
        for job_id, job in self.research_jobs.items():
            if not job.is_active:
                continue
            
            if job.last_executed is None:
                ready_jobs.append((job_id, job))
            else:
                time_since_last = current_time - job.last_executed
                if time_since_last.total_seconds() >= job.schedule_interval:
                    ready_jobs.append((job_id, job))
        
        return ready_jobs
    
    async def _execute_research_job(self, job_id: str, job: ResearchJob):
        """Execute a research job"""
        try:
            start_time = datetime.utcnow()
            execution_start = asyncio.get_event_loop().time()
            
            logger.info(f"Executing research job: {job_id}")
            
            # Perform research
            results = await self._perform_research(job.research_type, job.parameters)
            
            if results:
                # Generate insights and opportunities
                insights = await self._generate_insights(job.research_type, results)
                content_opportunities = await self._identify_content_opportunities(results)
                trending_keywords = await self._extract_trending_keywords(results)
                competitor_strategies = await self._analyze_competitor_strategies(results) if job.research_type == ResearchType.COMPETITOR_ANALYSIS else []
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(results, insights)
                
                execution_time = asyncio.get_event_loop().time() - execution_start
                
                research_result = ResearchResult(
                    job_id=job_id,
                    research_type=job.research_type,
                    results=results,
                    insights=insights,
                    content_opportunities=content_opportunities,
                    trending_keywords=trending_keywords,
                    competitor_strategies=competitor_strategies,
                    executed_at=start_time,
                    execution_time=execution_time,
                    data_points=len(results),
                    confidence_score=confidence_score
                )
                
                # Store results
                await self._store_research_results(research_result)
                
                # Update job
                job.last_executed = start_time
                job.results_count += 1
                
                self.stats["successful_executions"] += 1
                self.stats["insights_generated"] += len(insights)
                self.stats["content_opportunities"] += len(content_opportunities)
                
                logger.info(f"Completed research job: {job_id} ({len(results)} results, {len(insights)} insights)")
            else:
                logger.warning(f"No results from research job: {job_id}")
                
        except Exception as e:
            logger.error(f"Failed to execute research job {job_id}: {e}")
            self.stats["failed_executions"] += 1
    
    async def _perform_research(
        self,
        research_type: ResearchType,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform research based on type"""
        results = []
        
        try:
            if research_type == ResearchType.TRENDING_TOPICS:
                results = await self._research_trending_topics(parameters)
                
            elif research_type == ResearchType.COMPETITOR_ANALYSIS:
                results = await self._research_competitors(parameters)
                
            elif research_type == ResearchType.INDUSTRY_INSIGHTS:
                results = await self._research_industry_insights(parameters)
                
            elif research_type == ResearchType.AUDIENCE_RESEARCH:
                results = await self._research_audience(parameters)
                
            elif research_type == ResearchType.CONTENT_GAPS:
                results = await self._research_content_gaps(parameters)
                
            elif research_type == ResearchType.HASHTAG_RESEARCH:
                results = await self._research_hashtags(parameters)
                
            elif research_type == ResearchType.INFLUENCER_RESEARCH:
                results = await self._research_influencers(parameters)
                
            elif research_type == ResearchType.MARKET_ANALYSIS:
                results = await self._research_market_trends(parameters)
            
        except Exception as e:
            logger.error(f"Research execution failed for {research_type.value}: {e}")
        
        return results
    
    async def _research_trending_topics(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research trending topics using CrewAI agents"""
        topics = parameters.get("topics", ["social media trends", "AI", "marketing"])
        results = []
        
        for topic in topics:
            try:
                # Create research task
                research_task = create_research_task(topic)
                
                # Execute with research agent
                crew = Crew(
                    agents=[research_agent],
                    tasks=[research_task],
                    process=Process.sequential,
                    verbose=False
                )
                
                crew_result = await asyncio.to_thread(crew.kickoff)
                
                result = {
                    "topic": topic,
                    "research_data": str(crew_result),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "crewai_research_agent"
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to research topic '{topic}': {e}")
        
        return results
    
    async def _research_competitors(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research competitor strategies"""
        competitors = parameters.get("competitors", ["@buffer", "@hootsuite", "@hubspot"])
        results = []
        
        try:
            # Use existing Celery task
            task_result = await asyncio.to_thread(
                research_competitor_content.apply_async,
                args=[competitors]
            )
            
            # Wait for result
            celery_result = await asyncio.to_thread(task_result.get, timeout=300)
            
            if celery_result.get("status") == "success":
                for competitor_data in celery_result.get("results", []):
                    result = {
                        "competitor": competitor_data.get("competitor"),
                        "analysis": competitor_data.get("analysis"),
                        "posts_analyzed": competitor_data.get("posts_analyzed"),
                        "sample_content": competitor_data.get("sample_content"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "competitor_analysis_task"
                    }
                    results.append(result)
            
        except Exception as e:
            logger.error(f"Competitor research failed: {e}")
        
        return results
    
    async def _research_industry_insights(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research industry insights and trends"""
        industry = parameters.get("industry", "social media marketing")
        sources = parameters.get("sources", [
            "https://blog.hubspot.com/marketing",
            "https://buffer.com/resources",
            "https://blog.hootsuite.com"
        ])
        
        results = []
        
        try:
            # Use web content research task
            task_result = await asyncio.to_thread(
                research_web_content.apply_async,
                args=[sources]
            )
            
            celery_result = await asyncio.to_thread(task_result.get, timeout=300)
            
            if celery_result.get("status") == "success":
                for web_data in celery_result.get("results", []):
                    result = {
                        "industry": industry,
                        "source_url": web_data.get("url"),
                        "title": web_data.get("title"),
                        "analysis": web_data.get("analysis"),
                        "content_length": web_data.get("content_length"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "web_content_analysis"
                    }
                    results.append(result)
            
        except Exception as e:
            logger.error(f"Industry insights research failed: {e}")
        
        return results
    
    async def _research_audience(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research audience behavior and preferences"""
        # This would integrate with social media APIs to analyze audience data
        # For now, return sample structure
        results = []
        
        audience_segments = parameters.get("segments", ["professionals", "entrepreneurs", "marketers"])
        
        for segment in audience_segments:
            # Simulate audience research
            result = {
                "segment": segment,
                "demographics": {"age_range": "25-45", "interests": ["marketing", "technology", "business"]},
                "engagement_patterns": {"peak_hours": ["9-11 AM", "2-4 PM"], "preferred_content": ["educational", "inspirational"]},
                "platform_preferences": ["LinkedIn", "Twitter", "Instagram"],
                "timestamp": datetime.utcnow().isoformat(),
                "source": "audience_analysis"
            }
            results.append(result)
        
        return results
    
    async def _research_content_gaps(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify content gaps using vector similarity"""
        results = []
        
        try:
            # Get existing content from vector store
            existing_topics = await vector_store.get_all_embeddings()
            
            # Analyze gaps in coverage
            topic_areas = parameters.get("topic_areas", ["AI", "social media", "marketing", "productivity"])
            
            for topic in topic_areas:
                # Search for existing content on this topic
                similar_content = await vector_store.similarity_search(topic, k=10)
                
                content_gap_analysis = {
                    "topic": topic,
                    "existing_content_count": len(similar_content),
                    "coverage_score": min(len(similar_content) * 10, 100),  # Simple scoring
                    "gap_opportunity": 100 - min(len(similar_content) * 10, 100),
                    "recommended_content_types": self._suggest_content_types(topic),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "content_gap_analysis"
                }
                
                results.append(content_gap_analysis)
            
        except Exception as e:
            logger.error(f"Content gap analysis failed: {e}")
        
        return results
    
    async def _research_hashtags(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research trending hashtags"""
        # This would integrate with social media APIs to get hashtag data
        results = []
        
        categories = parameters.get("categories", ["marketing", "AI", "business"])
        
        for category in categories:
            # Simulate hashtag research
            result = {
                "category": category,
                "trending_hashtags": [f"#{category}trends", f"#{category}tips", f"#{category}2025"],
                "engagement_scores": {"high": 85, "medium": 60, "low": 30},
                "recommended_usage": f"Use 3-5 hashtags per post for {category} content",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "hashtag_research"
            }
            results.append(result)
        
        return results
    
    async def _research_influencers(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research relevant influencers"""
        # This would integrate with social media APIs to find influencers
        results = []
        
        industry = parameters.get("industry", "social media marketing")
        
        # Simulate influencer research
        result = {
            "industry": industry,
            "top_influencers": [
                {"name": "Marketing Expert", "handle": "@marketingpro", "followers": 50000, "engagement_rate": 4.2},
                {"name": "Social Media Guru", "handle": "@socialmediaguru", "followers": 75000, "engagement_rate": 3.8}
            ],
            "collaboration_opportunities": ["guest posts", "interviews", "co-created content"],
            "timestamp": datetime.utcnow().isoformat(),
            "source": "influencer_research"
        }
        results.append(result)
        
        return results
    
    async def _research_market_trends(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Research market trends and analysis"""
        market = parameters.get("market", "social media tools")
        results = []
        
        # Simulate market research
        result = {
            "market": market,
            "growth_trends": {"annual_growth": "15%", "market_size": "$25B"},
            "key_players": ["Buffer", "Hootsuite", "Sprout Social"],
            "emerging_trends": ["AI-powered content", "Video-first strategies", "Personalization"],
            "opportunities": ["SMB market", "Video content tools", "Analytics integration"],
            "timestamp": datetime.utcnow().isoformat(),
            "source": "market_analysis"
        }
        results.append(result)
        
        return results
    
    def _suggest_content_types(self, topic: str) -> List[str]:
        """Suggest content types for a topic"""
        content_suggestions = {
            "AI": ["tutorials", "use cases", "comparisons", "predictions"],
            "marketing": ["tips", "case studies", "trends", "tools"],
            "productivity": ["hacks", "workflows", "tools", "strategies"],
            "business": ["insights", "case studies", "trends", "advice"]
        }
        
        return content_suggestions.get(topic.lower(), ["articles", "guides", "tips", "insights"])
    
    async def _generate_insights(self, research_type: ResearchType, results: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from research results"""
        insights = []
        
        try:
            # Use CrewAI content agent to analyze results
            analysis_prompt = f"""
            Analyze the following research results for {research_type.value} and provide 3-5 key actionable insights:
            
            Results: {json.dumps(results[:3], indent=2)}  # Limit for token efficiency
            
            Focus on:
            1. Emerging trends and opportunities
            2. Content strategy recommendations
            3. Audience engagement patterns
            4. Competitive advantages
            5. Action items for content creators
            
            Provide clear, specific insights that can be implemented immediately.
            """
            
            # Create a simple task for analysis
            from crewai import Task
            analysis_task = Task(
                description=analysis_prompt,
                agent=content_agent,
                expected_output="List of 3-5 actionable insights with specific recommendations"
            )
            
            crew = Crew(
                agents=[content_agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=False
            )
            
            result = await asyncio.to_thread(crew.kickoff)
            
            # Parse insights from result
            insight_text = str(result)
            if insight_text:
                # Split into individual insights (assuming numbered list or bullet points)
                import re
                insight_matches = re.findall(r'(?:^\d+\.|\*|\-)\s*(.+)', insight_text, re.MULTILINE)
                insights = [insight.strip() for insight in insight_matches if insight.strip()]
            
            # Fallback: basic insights if parsing fails
            if not insights:
                insights = [
                    f"Research identified {len(results)} key data points for {research_type.value}",
                    "Consider creating content around the most frequently mentioned topics",
                    "Monitor engagement patterns to optimize posting times"
                ]
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            insights = [f"Research completed for {research_type.value} with {len(results)} results"]
        
        return insights[:5]  # Limit to 5 insights
    
    async def _identify_content_opportunities(self, results: List[Dict[str, Any]]) -> List[str]:
        """Identify content creation opportunities"""
        opportunities = []
        
        # Extract topics and themes from results
        topics = set()
        for result in results:
            # Extract potential topics from various fields
            for key, value in result.items():
                if key in ["topic", "category", "industry", "segment"]:
                    topics.add(str(value))
                elif key == "trending_hashtags" and isinstance(value, list):
                    topics.update([tag.replace("#", "") for tag in value])
        
        # Generate content opportunities
        for topic in list(topics)[:10]:  # Limit to 10 topics
            opportunities.extend([
                f"Create educational content about {topic}",
                f"Share industry insights on {topic}",
                f"Develop case studies related to {topic}"
            ])
        
        return opportunities[:15]  # Limit to 15 opportunities
    
    async def _extract_trending_keywords(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract trending keywords from research results"""
        keywords = set()
        
        for result in results:
            # Extract keywords from various fields
            text_fields = ["analysis", "research_data", "description", "title"]
            for field in text_fields:
                if field in result and isinstance(result[field], str):
                    # Simple keyword extraction (in real implementation, use NLP)
                    words = result[field].lower().split()
                    # Filter for meaningful keywords (length > 3)
                    keywords.update([word.strip(".,!?:;") for word in words if len(word) > 3])
        
        # Return top keywords (sorted by frequency would be better)
        return list(keywords)[:20]
    
    async def _analyze_competitor_strategies(self, results: List[Dict[str, Any]]) -> List[str]:
        """Analyze competitor strategies from research results"""
        strategies = []
        
        for result in results:
            if "competitor" in result and "analysis" in result:
                competitor = result["competitor"]
                analysis = result["analysis"]
                
                strategies.append(f"{competitor}: {analysis[:100]}...")
        
        return strategies
    
    def _calculate_confidence_score(self, results: List[Dict[str, Any]], insights: List[str]) -> float:
        """Calculate confidence score for research results"""
        # Simple scoring based on data points and insights
        data_score = min(len(results) * 10, 60)  # Max 60 points for data
        insight_score = min(len(insights) * 8, 40)  # Max 40 points for insights
        
        return data_score + insight_score
    
    async def _store_research_results(self, research_result: ResearchResult):
        """Store research results in vector store and database"""
        try:
            # Store in vector store for similarity search
            content_text = f"Research on {research_result.research_type.value}: "
            content_text += " ".join(research_result.insights)
            content_text += " Opportunities: " + " ".join(research_result.content_opportunities)
            
            metadata = {
                "type": "research_result",
                "research_type": research_result.research_type.value,
                "job_id": research_result.job_id,
                "executed_at": research_result.executed_at.isoformat(),
                "confidence_score": research_result.confidence_score,
                "data_points": research_result.data_points
            }
            
            await vector_store.add_text(
                text=content_text,
                metadata=metadata
            )
            
            # Store in research history
            self.research_history.append(research_result)
            
            # Keep only last 100 results in memory
            if len(self.research_history) > 100:
                self.research_history = self.research_history[-100:]
            
            logger.info(f"Stored research results for job {research_result.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to store research results: {e}")
    
    async def _cleanup_old_results(self):
        """Clean up old research results"""
        try:
            # Remove results older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            self.research_history = [
                result for result in self.research_history
                if result.executed_at > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")
    
    async def get_research_history(
        self,
        research_type: Optional[ResearchType] = None,
        hours: int = 24
    ) -> List[ResearchResult]:
        """Get research history"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_results = []
        for result in self.research_history:
            if result.executed_at < since_time:
                continue
            
            if research_type and result.research_type != research_type:
                continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status and statistics"""
        return {
            "is_running": self._running,
            "active_jobs": sum(1 for job in self.research_jobs.values() if job.is_active),
            "total_jobs": len(self.research_jobs),
            "recent_results": len([r for r in self.research_history if r.executed_at > datetime.utcnow() - timedelta(hours=24)]),
            "statistics": self.stats,
            "job_types": list(set(job.research_type.value for job in self.research_jobs.values()))
        }
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a research job"""
        if job_id in self.research_jobs:
            self.research_jobs[job_id].is_active = False
            logger.info(f"Paused research job: {job_id}")
            return True
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a research job"""
        if job_id in self.research_jobs:
            self.research_jobs[job_id].is_active = True
            logger.info(f"Resumed research job: {job_id}")
            return True
        return False
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove a research job"""
        if job_id in self.research_jobs:
            del self.research_jobs[job_id]
            logger.info(f"Removed research job: {job_id}")
            return True
        return False

# Global research automation service instance
research_automation_service = AutomatedResearchService()