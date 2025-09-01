"""
Multi-Platform Social Media Metrics Collection Service
Integration Specialist Component - Real-time metrics collection from all social platforms
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

from backend.core.config import get_settings
from backend.integrations.twitter_client import twitter_client, TwitterAnalytics
# LinkedIn integration removed - using stubs
linkedin_client = None
LinkedInAnalytics = None
from backend.integrations.instagram_client import instagram_client, InstagramInsight
from backend.integrations.facebook_client import facebook_client, FacebookInsights
from backend.db.database import get_db_session
from backend.db.models import ContentItem, ContentPerformanceSnapshot

settings = get_settings()
logger = logging.getLogger(__name__)

class MetricsPlatform(Enum):
    """Supported social media platforms for metrics collection"""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"

@dataclass
class UnifiedMetrics:
    """Unified metrics structure across all platforms"""
    platform: str
    content_id: str
    platform_post_id: str
    collected_at: datetime
    
    # Engagement metrics
    impressions: int = 0
    reach: int = 0
    engagement_total: int = 0
    engagement_rate: float = 0.0
    
    # Interaction metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    
    # Platform-specific metrics
    retweets: int = 0  # Twitter
    quote_tweets: int = 0  # Twitter
    bookmarks: int = 0  # Twitter
    reactions: int = 0  # LinkedIn/Facebook
    video_views: int = 0  # Video platforms
    profile_visits: int = 0  # Instagram/LinkedIn
    
    # Performance indicators
    ctr: float = 0.0  # Click-through rate
    completion_rate: float = 0.0  # Video completion rate
    viral_score: float = 0.0  # Custom viral indicator
    
    # Additional data
    raw_data: Dict[str, Any] = None

@dataclass
class MetricsCollectionJob:
    """Metrics collection job configuration"""
    content_id: str
    platform: MetricsPlatform
    platform_post_id: str
    access_token: str
    account_id: str
    collection_interval: int = 3600  # seconds
    last_collected: Optional[datetime] = None
    is_active: bool = True

class SocialMetricsCollector:
    """
    Real-time social media metrics collection system
    
    Features:
    - Multi-platform metrics collection
    - Real-time data synchronization
    - Automated collection scheduling
    - Metrics normalization and analysis
    - Performance trend tracking
    - Anomaly detection for viral content
    - Rate limit handling
    - Error recovery and retry logic
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.collection_jobs: Dict[str, MetricsCollectionJob] = {}
        self.platform_clients = {
            MetricsPlatform.TWITTER: twitter_client,
            # MetricsPlatform.LINKEDIN: removed - LinkedIn integration disabled
            MetricsPlatform.INSTAGRAM: instagram_client,
            MetricsPlatform.FACEBOOK: facebook_client
        }
        self._running = False
        self._collection_task = None
        
        logger.info("SocialMetricsCollector initialized")
    
    async def start_collection(self):
        """Start the metrics collection service"""
        if self._running:
            logger.warning("Metrics collection already running")
            return
        
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Started metrics collection service")
    
    async def stop_collection(self):
        """Stop the metrics collection service"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped metrics collection service")
    
    async def add_collection_job(
        self,
        content_id: str,
        platform: MetricsPlatform,
        platform_post_id: str,
        access_token: str,
        account_id: str,
        collection_interval: int = 3600
    ) -> str:
        """
        Add a new metrics collection job
        
        Args:
            content_id: Internal content ID
            platform: Social media platform
            platform_post_id: Platform-specific post ID
            access_token: Platform access token
            account_id: Platform account ID
            collection_interval: Collection frequency in seconds
            
        Returns:
            Job ID
        """
        job_id = f"{platform.value}_{content_id}_{platform_post_id}"
        
        job = MetricsCollectionJob(
            content_id=content_id,
            platform=platform,
            platform_post_id=platform_post_id,
            access_token=access_token,
            account_id=account_id,
            collection_interval=collection_interval,
            last_collected=None,
            is_active=True
        )
        
        self.collection_jobs[job_id] = job
        logger.info(f"Added metrics collection job: {job_id}")
        
        # Collect initial metrics immediately
        await self._collect_job_metrics(job_id, job)
        
        return job_id
    
    async def remove_collection_job(self, job_id: str) -> bool:
        """
        Remove a metrics collection job
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            Success status
        """
        if job_id in self.collection_jobs:
            del self.collection_jobs[job_id]
            logger.info(f"Removed metrics collection job: {job_id}")
            return True
        return False
    
    async def collect_metrics_now(
        self,
        content_id: str,
        platform: MetricsPlatform,
        platform_post_id: str,
        access_token: str,
        account_id: str
    ) -> Optional[UnifiedMetrics]:
        """
        Collect metrics immediately for a specific post
        
        Args:
            content_id: Internal content ID
            platform: Social media platform
            platform_post_id: Platform-specific post ID
            access_token: Platform access token
            account_id: Platform account ID
            
        Returns:
            Collected metrics or None if failed
        """
        try:
            raw_metrics = await self._fetch_platform_metrics(
                platform, platform_post_id, access_token, account_id
            )
            
            if raw_metrics:
                unified_metrics = self._normalize_metrics(
                    platform, content_id, platform_post_id, raw_metrics
                )
                
                # Store in database
                await self._store_metrics(unified_metrics)
                
                return unified_metrics
                
        except Exception as e:
            logger.error(f"Failed to collect metrics for {platform.value} post {platform_post_id}: {e}")
        
        return None
    
    async def _collection_loop(self):
        """Main collection loop"""
        while self._running:
            try:
                # Collect metrics for all active jobs
                tasks = []
                for job_id, job in self.collection_jobs.items():
                    if job.is_active and self._should_collect(job):
                        task = asyncio.create_task(self._collect_job_metrics(job_id, job))
                        tasks.append(task)
                
                # Wait for all collection tasks to complete
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sleep before next collection cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def _should_collect(self, job: MetricsCollectionJob) -> bool:
        """Check if metrics should be collected for a job"""
        if not job.last_collected:
            return True
        
        time_since_last = datetime.utcnow() - job.last_collected
        return time_since_last.total_seconds() >= job.collection_interval
    
    async def _collect_job_metrics(self, job_id: str, job: MetricsCollectionJob):
        """Collect metrics for a single job"""
        try:
            logger.info(f"Collecting metrics for job: {job_id}")
            
            # Fetch platform-specific metrics
            raw_metrics = await self._fetch_platform_metrics(
                job.platform, job.platform_post_id, job.access_token, job.account_id
            )
            
            if raw_metrics:
                # Normalize to unified format
                unified_metrics = self._normalize_metrics(
                    job.platform, job.content_id, job.platform_post_id, raw_metrics
                )
                
                # Store in database
                await self._store_metrics(unified_metrics)
                
                # Update job timestamp
                job.last_collected = datetime.utcnow()
                
                logger.info(f"Successfully collected metrics for {job_id}")
            else:
                logger.warning(f"No metrics returned for job {job_id}")
                
        except Exception as e:
            logger.error(f"Failed to collect metrics for job {job_id}: {e}")
    
    async def _fetch_platform_metrics(
        self,
        platform: MetricsPlatform,
        post_id: str,
        access_token: str,
        account_id: str
    ) -> Optional[Any]:
        """Fetch metrics from specific platform"""
        try:
            client = self.platform_clients.get(platform)
            if not client:
                logger.error(f"No client available for platform: {platform.value}")
                return None
            
            if platform == MetricsPlatform.TWITTER:
                return await client.get_tweet_analytics(access_token, post_id)
                
            elif platform == MetricsPlatform.LINKEDIN:
                return await client.get_post_analytics(access_token, post_id)
                
            elif platform == MetricsPlatform.INSTAGRAM:
                return await client.get_media_insights(access_token, post_id)
                
            elif platform == MetricsPlatform.FACEBOOK:
                return await client.get_post_insights(access_token, post_id)
                
            else:
                logger.error(f"Unsupported platform: {platform.value}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching metrics from {platform.value}: {e}")
            return None
    
    def _normalize_metrics(
        self,
        platform: MetricsPlatform,
        content_id: str,
        post_id: str,
        raw_metrics: Any
    ) -> UnifiedMetrics:
        """Normalize platform-specific metrics to unified format"""
        unified = UnifiedMetrics(
            platform=platform.value,
            content_id=content_id,
            platform_post_id=post_id,
            collected_at=datetime.utcnow(),
            raw_data=asdict(raw_metrics) if hasattr(raw_metrics, '__dict__') else raw_metrics
        )
        
        if platform == MetricsPlatform.TWITTER:
            metrics: TwitterAnalytics = raw_metrics
            unified.impressions = metrics.impressions
            unified.likes = metrics.likes
            unified.comments = metrics.replies
            unified.shares = metrics.retweets + metrics.quotes
            unified.retweets = metrics.retweets
            unified.quote_tweets = metrics.quotes
            unified.bookmarks = metrics.bookmarks
            unified.clicks = metrics.url_clicks + metrics.profile_clicks
            unified.engagement_total = metrics.likes + metrics.replies + metrics.retweets + metrics.quotes
            unified.engagement_rate = metrics.engagement_rate
            
        elif platform == MetricsPlatform.LINKEDIN:
            metrics: LinkedInAnalytics = raw_metrics
            unified.impressions = metrics.impressions
            unified.clicks = metrics.clicks
            unified.likes = metrics.reactions
            unified.comments = metrics.comments
            unified.shares = metrics.shares
            unified.engagement_total = metrics.engagement
            unified.engagement_rate = metrics.engagement_rate
            unified.ctr = metrics.click_through_rate
            unified.reach = metrics.unique_impressions
            
        elif platform == MetricsPlatform.INSTAGRAM:
            metrics: InstagramInsight = raw_metrics
            unified.impressions = metrics.impressions
            unified.reach = metrics.reach
            unified.likes = metrics.likes
            unified.comments = metrics.comments
            unified.shares = metrics.shares
            unified.saves = metrics.saved
            unified.engagement_total = metrics.engagement
            unified.video_views = metrics.video_views or 0
            unified.profile_visits = metrics.profile_visits
            unified.clicks = metrics.website_clicks
            if unified.impressions > 0:
                unified.engagement_rate = (unified.engagement_total / unified.impressions) * 100
                
        elif platform == MetricsPlatform.FACEBOOK:
            metrics: FacebookInsights = raw_metrics
            unified.impressions = metrics.impressions
            unified.reach = metrics.reach
            unified.likes = metrics.reactions
            unified.comments = metrics.comments
            unified.shares = metrics.shares
            unified.clicks = metrics.clicks
            unified.engagement_total = metrics.engagement
            unified.video_views = metrics.video_views or 0
            if unified.impressions > 0:
                unified.engagement_rate = (unified.engagement_total / unified.impressions) * 100
        
        # Calculate viral score
        unified.viral_score = self._calculate_viral_score(unified)
        
        return unified
    
    def _calculate_viral_score(self, metrics: UnifiedMetrics) -> float:
        """
        Calculate a viral score based on engagement patterns
        
        Args:
            metrics: Unified metrics
            
        Returns:
            Viral score (0-100)
        """
        if metrics.impressions == 0:
            return 0.0
        
        # Base score from engagement rate
        base_score = min(metrics.engagement_rate, 20) * 2  # Cap at 40 points
        
        # Bonus for high reach-to-impression ratio
        if metrics.reach > 0:
            reach_ratio = metrics.reach / metrics.impressions
            reach_bonus = min(reach_ratio * 20, 15)  # Max 15 points
        else:
            reach_bonus = 0
        
        # Bonus for shares (viral indicator)
        if metrics.impressions > 0:
            share_rate = (metrics.shares / metrics.impressions) * 100
            share_bonus = min(share_rate * 50, 25)  # Max 25 points
        else:
            share_bonus = 0
        
        # Bonus for saves/bookmarks (quality indicator)
        if metrics.impressions > 0:
            save_rate = ((metrics.saves + metrics.bookmarks) / metrics.impressions) * 100
            save_bonus = min(save_rate * 100, 20)  # Max 20 points
        else:
            save_bonus = 0
        
        total_score = base_score + reach_bonus + share_bonus + save_bonus
        return min(total_score, 100.0)
    
    async def _store_metrics(self, metrics: UnifiedMetrics):
        """Store metrics in database"""
        try:
            async with get_db_session() as session:
                # Find the content item
                content_item = await session.get(ContentItem, metrics.content_id)
                if not content_item:
                    logger.error(f"Content item not found: {metrics.content_id}")
                    return
                
                # Create performance snapshot
                snapshot = ContentPerformanceSnapshot(
                    content_item_id=metrics.content_id,
                    platform=metrics.platform,
                    platform_post_id=metrics.platform_post_id,
                    collected_at=metrics.collected_at,
                    impressions=metrics.impressions,
                    reach=metrics.reach,
                    engagement_total=metrics.engagement_total,
                    engagement_rate=metrics.engagement_rate,
                    likes=metrics.likes,
                    comments=metrics.comments,
                    shares=metrics.shares,
                    saves=metrics.saves,
                    clicks=metrics.clicks,
                    video_views=metrics.video_views,
                    viral_score=metrics.viral_score,
                    raw_metrics=json.dumps(metrics.raw_data) if metrics.raw_data else None
                )
                
                session.add(snapshot)
                await session.commit()
                
                logger.info(f"Stored metrics for content {metrics.content_id} on {metrics.platform}")
                
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def get_metrics_history(
        self,
        content_id: str,
        platform: Optional[str] = None,
        hours: int = 24
    ) -> List[UnifiedMetrics]:
        """
        Get metrics history for content
        
        Args:
            content_id: Content ID
            platform: Specific platform or None for all
            hours: Hours of history to retrieve
            
        Returns:
            List of metrics snapshots
        """
        try:
            async with get_db_session() as session:
                since_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = session.query(ContentPerformanceSnapshot).filter(
                    ContentPerformanceSnapshot.content_item_id == content_id,
                    ContentPerformanceSnapshot.collected_at >= since_time
                )
                
                if platform:
                    query = query.filter(ContentPerformanceSnapshot.platform == platform)
                
                snapshots = await query.all()
                
                # Convert to UnifiedMetrics
                metrics_list = []
                for snapshot in snapshots:
                    raw_data = json.loads(snapshot.raw_metrics) if snapshot.raw_metrics else {}
                    
                    unified = UnifiedMetrics(
                        platform=snapshot.platform,
                        content_id=snapshot.content_item_id,
                        platform_post_id=snapshot.platform_post_id,
                        collected_at=snapshot.collected_at,
                        impressions=snapshot.impressions,
                        reach=snapshot.reach,
                        engagement_total=snapshot.engagement_total,
                        engagement_rate=snapshot.engagement_rate,
                        likes=snapshot.likes,
                        comments=snapshot.comments,
                        shares=snapshot.shares,
                        saves=snapshot.saves,
                        clicks=snapshot.clicks,
                        video_views=snapshot.video_views,
                        viral_score=snapshot.viral_score,
                        raw_data=raw_data
                    )
                    metrics_list.append(unified)
                
                return metrics_list
                
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return []
    
    async def get_trending_content(
        self,
        platform: Optional[str] = None,
        hours: int = 24,
        min_viral_score: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Get trending content based on viral scores
        
        Args:
            platform: Specific platform or None for all
            hours: Time window to check
            min_viral_score: Minimum viral score threshold
            
        Returns:
            List of trending content with metrics
        """
        try:
            async with get_db_session() as session:
                since_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = session.query(ContentPerformanceSnapshot).filter(
                    ContentPerformanceSnapshot.collected_at >= since_time,
                    ContentPerformanceSnapshot.viral_score >= min_viral_score
                )
                
                if platform:
                    query = query.filter(ContentPerformanceSnapshot.platform == platform)
                
                snapshots = await query.order_by(ContentPerformanceSnapshot.viral_score.desc()).limit(50).all()
                
                trending = []
                for snapshot in snapshots:
                    content_item = await session.get(ContentItem, snapshot.content_item_id)
                    if content_item:
                        trending.append({
                            "content_id": snapshot.content_item_id,
                            "content_text": content_item.content_text[:200] + "..." if len(content_item.content_text) > 200 else content_item.content_text,
                            "platform": snapshot.platform,
                            "viral_score": snapshot.viral_score,
                            "engagement_rate": snapshot.engagement_rate,
                            "impressions": snapshot.impressions,
                            "engagement_total": snapshot.engagement_total,
                            "collected_at": snapshot.collected_at
                        })
                
                return trending
                
        except Exception as e:
            logger.error(f"Failed to get trending content: {e}")
            return []
    
    async def pause_collection_job(self, job_id: str) -> bool:
        """Pause a metrics collection job"""
        if job_id in self.collection_jobs:
            self.collection_jobs[job_id].is_active = False
            logger.info(f"Paused metrics collection job: {job_id}")
            return True
        return False
    
    async def resume_collection_job(self, job_id: str) -> bool:
        """Resume a metrics collection job"""
        if job_id in self.collection_jobs:
            self.collection_jobs[job_id].is_active = True
            logger.info(f"Resumed metrics collection job: {job_id}")
            return True
        return False
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """Get status of metrics collection service"""
        active_jobs = sum(1 for job in self.collection_jobs.values() if job.is_active)
        
        return {
            "is_running": self._running,
            "total_jobs": len(self.collection_jobs),
            "active_jobs": active_jobs,
            "paused_jobs": len(self.collection_jobs) - active_jobs,
            "platforms": list(set(job.platform.value for job in self.collection_jobs.values()))
        }

# Global metrics collector instance
metrics_collector = SocialMetricsCollector()