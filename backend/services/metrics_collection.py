"""
Real-time Social Media Metrics Collection Service
Integration Specialist Component - Comprehensive metrics aggregation from all platforms
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import ContentItem, ContentPerformanceSnapshot

# Mock classes for compatibility (since models don't exist)
class SocialMediaAccount:
    def __init__(self, platform="mock", account_id="mock123", access_token="mock_token", is_active=True):
        self.platform = platform
        self.account_id = account_id
        self.access_token = access_token
        self.is_active = is_active

class TwitterAnalytics:
    def __init__(self):
        pass

class InstagramInsight:
    def __init__(self):
        pass

class FacebookInsights:
    def __init__(self):
        pass
from backend.integrations.twitter_client import twitter_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client

settings = get_settings()
logger = logging.getLogger(__name__)

class Platform(Enum):
    """Supported social media platforms"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"

@dataclass
class UnifiedMetrics:
    """Unified metrics structure across all platforms"""
    platform: str
    content_id: str
    post_id: str
    impressions: int
    reach: int
    engagement: int
    likes: int
    comments: int
    shares: int
    clicks: int
    video_views: Optional[int] = None
    saves: Optional[int] = None
    engagement_rate: float = 0.0
    collected_at: datetime = None
    
    def __post_init__(self):
        if self.collected_at is None:
            self.collected_at = datetime.now(timezone.utc)
        
        # Calculate engagement rate if not provided
        if self.engagement_rate == 0.0 and self.impressions > 0:
            total_engagement = self.likes + self.comments + self.shares + self.clicks
            if self.saves:
                total_engagement += self.saves
            self.engagement_rate = (total_engagement / self.impressions) * 100

@dataclass
class MetricsCollectionResult:
    """Result of metrics collection operation"""
    success: bool
    platform: str
    metrics_collected: int
    errors: List[str]
    collection_time: datetime
    next_collection: Optional[datetime] = None

class SocialMediaMetricsCollector:
    """
    Comprehensive social media metrics collection service
    
    Features:
    - Real-time metrics collection from all platforms
    - Unified metrics structure for consistency
    - Batch processing for efficiency
    - Error handling and retry logic
    - Rate limit management
    - Historical data preservation
    - Performance trend analysis
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.collection_intervals = {
            Platform.TWITTER: timedelta(minutes=15),    # Twitter has good real-time data
            Platform.INSTAGRAM: timedelta(hours=1),     # Instagram updates less frequently
            Platform.FACEBOOK: timedelta(hours=1),      # Facebook similar to Instagram
            Platform.LINKEDIN: timedelta(hours=2)       # LinkedIn updates even less frequently
        }
        
        self.retry_config = {
            "max_retries": 3,
            "backoff_factor": 2,
            "base_delay": 60  # seconds
        }
        
        self.batch_sizes = {
            Platform.TWITTER: 50,      # Twitter API allows good batch sizes
            Platform.INSTAGRAM: 25,    # Instagram is more restrictive
            Platform.FACEBOOK: 25,     # Facebook similar to Instagram
            Platform.LINKEDIN: 20      # LinkedIn most restrictive
        }
        
        logger.info("SocialMediaMetricsCollector initialized")
    
    async def collect_all_metrics(
        self,
        db: Session,
        force_collection: bool = False,
        platforms: Optional[List[Platform]] = None
    ) -> List[MetricsCollectionResult]:
        """
        Collect metrics from all connected social media platforms
        
        Args:
            db: Database session
            force_collection: Force collection regardless of intervals
            platforms: Specific platforms to collect from (if None, collect all)
            
        Returns:
            List of collection results
        """
        if platforms is None:
            platforms = list(Platform)
        
        results = []
        
        # Collect metrics from each platform in parallel
        tasks = []
        for platform in platforms:
            if platform == Platform.TWITTER:
                task = self._collect_twitter_metrics(db, force_collection)
            elif platform == Platform.INSTAGRAM:
                task = self._collect_instagram_metrics(db, force_collection)
            elif platform == Platform.FACEBOOK:
                task = self._collect_facebook_metrics(db, force_collection)
            elif platform == Platform.LINKEDIN:
                task = self._collect_linkedin_metrics(db, force_collection)
            else:
                continue
            
            tasks.append(task)
        
        # Execute all collection tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    platform_name = platforms[i].value
                    logger.error(f"Failed to collect metrics for {platform_name}: {result}")
                    results[i] = MetricsCollectionResult(
                        success=False,
                        platform=platform_name,
                        metrics_collected=0,
                        errors=[str(result)],
                        collection_time=datetime.now(timezone.utc)
                    )
        
        # Log collection summary
        total_metrics = sum(r.metrics_collected for r in results if r.success)
        successful_platforms = sum(1 for r in results if r.success)
        
        logger.info(f"Metrics collection complete: {total_metrics} metrics from {successful_platforms} platforms")
        
        return results
    
    async def _collect_twitter_metrics(
        self,
        db: Session,
        force_collection: bool = False
    ) -> MetricsCollectionResult:
        """Collect metrics from Twitter"""
        try:
            # Get Twitter accounts
            twitter_accounts = db.query(SocialMediaAccount).filter(
                SocialMediaAccount.platform == "twitter",
                SocialMediaAccount.is_active == True
            ).all()
            
            if not twitter_accounts:
                return MetricsCollectionResult(
                    success=True,
                    platform="twitter",
                    metrics_collected=0,
                    errors=[],
                    collection_time=datetime.now(timezone.utc)
                )
            
            total_metrics = 0
            errors = []
            
            for account in twitter_accounts:
                try:
                    # Get recent content items for this account
                    content_items = db.query(ContentItem).filter(
                        ContentItem.platform == "twitter",
                        ContentItem.account_id == account.account_id,
                        ContentItem.status == "published"
                    ).order_by(ContentItem.published_at.desc()).limit(self.batch_sizes[Platform.TWITTER]).all()
                    
                    # Collect metrics for each content item
                    for content_item in content_items:
                        if not self._should_collect_metrics(content_item, Platform.TWITTER, force_collection):
                            continue
                        
                        try:
                            # Get Twitter analytics
                            analytics = await twitter_client.get_tweet_analytics(
                                access_token=account.access_token,
                                tweet_id=content_item.platform_post_id
                            )
                            
                            # Convert to unified metrics
                            unified_metrics = self._twitter_to_unified_metrics(analytics, content_item)
                            
                            # Save to database
                            await self._save_metrics_to_db(db, unified_metrics, content_item)
                            
                            total_metrics += 1
                            
                            # Brief delay to respect rate limits
                            await asyncio.sleep(0.1)
                            
                        except Exception as e:
                            error_msg = f"Failed to collect Twitter metrics for content {content_item.id}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Failed to process Twitter account {account.account_id}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return MetricsCollectionResult(
                success=len(errors) == 0,
                platform="twitter",
                metrics_collected=total_metrics,
                errors=errors,
                collection_time=datetime.now(timezone.utc),
                next_collection=datetime.now(timezone.utc) + self.collection_intervals[Platform.TWITTER]
            )
            
        except Exception as e:
            logger.error(f"Twitter metrics collection failed: {e}")
            return MetricsCollectionResult(
                success=False,
                platform="twitter",
                metrics_collected=0,
                errors=[str(e)],
                collection_time=datetime.now(timezone.utc)
            )
    
    async def _collect_instagram_metrics(
        self,
        db: Session,
        force_collection: bool = False
    ) -> MetricsCollectionResult:
        """Collect metrics from Instagram"""
        try:
            # Get Instagram accounts
            instagram_accounts = db.query(SocialMediaAccount).filter(
                SocialMediaAccount.platform == "instagram",
                SocialMediaAccount.is_active == True
            ).all()
            
            if not instagram_accounts:
                return MetricsCollectionResult(
                    success=True,
                    platform="instagram",
                    metrics_collected=0,
                    errors=[],
                    collection_time=datetime.now(timezone.utc)
                )
            
            total_metrics = 0
            errors = []
            
            for account in instagram_accounts:
                try:
                    # Get recent content items for this account
                    content_items = db.query(ContentItem).filter(
                        ContentItem.platform == "instagram",
                        ContentItem.account_id == account.account_id,
                        ContentItem.status == "published"
                    ).order_by(ContentItem.published_at.desc()).limit(self.batch_sizes[Platform.INSTAGRAM]).all()
                    
                    # Collect metrics for each content item
                    for content_item in content_items:
                        if not self._should_collect_metrics(content_item, Platform.INSTAGRAM, force_collection):
                            continue
                        
                        try:
                            # Get Instagram insights
                            insights = await instagram_client.get_media_insights(
                                access_token=account.access_token,
                                media_id=content_item.platform_post_id
                            )
                            
                            # Convert to unified metrics
                            unified_metrics = self._instagram_to_unified_metrics(insights, content_item)
                            
                            # Save to database
                            await self._save_metrics_to_db(db, unified_metrics, content_item)
                            
                            total_metrics += 1
                            
                            # Brief delay to respect rate limits
                            await asyncio.sleep(0.2)
                            
                        except Exception as e:
                            error_msg = f"Failed to collect Instagram metrics for content {content_item.id}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Failed to process Instagram account {account.account_id}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return MetricsCollectionResult(
                success=len(errors) == 0,
                platform="instagram",
                metrics_collected=total_metrics,
                errors=errors,
                collection_time=datetime.now(timezone.utc),
                next_collection=datetime.now(timezone.utc) + self.collection_intervals[Platform.INSTAGRAM]
            )
            
        except Exception as e:
            logger.error(f"Instagram metrics collection failed: {e}")
            return MetricsCollectionResult(
                success=False,
                platform="instagram",
                metrics_collected=0,
                errors=[str(e)],
                collection_time=datetime.now(timezone.utc)
            )
    
    async def _collect_facebook_metrics(
        self,
        db: Session,
        force_collection: bool = False
    ) -> MetricsCollectionResult:
        """Collect metrics from Facebook"""
        try:
            # Get Facebook accounts
            facebook_accounts = db.query(SocialMediaAccount).filter(
                SocialMediaAccount.platform == "facebook",
                SocialMediaAccount.is_active == True
            ).all()
            
            if not facebook_accounts:
                return MetricsCollectionResult(
                    success=True,
                    platform="facebook",
                    metrics_collected=0,
                    errors=[],
                    collection_time=datetime.now(timezone.utc)
                )
            
            total_metrics = 0
            errors = []
            
            for account in facebook_accounts:
                try:
                    # Get recent content items for this account
                    content_items = db.query(ContentItem).filter(
                        ContentItem.platform == "facebook",
                        ContentItem.account_id == account.account_id,
                        ContentItem.status == "published"
                    ).order_by(ContentItem.published_at.desc()).limit(self.batch_sizes[Platform.FACEBOOK]).all()
                    
                    # Collect metrics for each content item
                    for content_item in content_items:
                        if not self._should_collect_metrics(content_item, Platform.FACEBOOK, force_collection):
                            continue
                        
                        try:
                            # Get Facebook insights
                            insights = await facebook_client.get_post_insights(
                                access_token=account.access_token,
                                post_id=content_item.platform_post_id
                            )
                            
                            # Convert to unified metrics
                            unified_metrics = self._facebook_to_unified_metrics(insights, content_item)
                            
                            # Save to database
                            await self._save_metrics_to_db(db, unified_metrics, content_item)
                            
                            total_metrics += 1
                            
                            # Brief delay to respect rate limits
                            await asyncio.sleep(0.2)
                            
                        except Exception as e:
                            error_msg = f"Failed to collect Facebook metrics for content {content_item.id}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Failed to process Facebook account {account.account_id}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return MetricsCollectionResult(
                success=len(errors) == 0,
                platform="facebook",
                metrics_collected=total_metrics,
                errors=errors,
                collection_time=datetime.now(timezone.utc),
                next_collection=datetime.now(timezone.utc) + self.collection_intervals[Platform.FACEBOOK]
            )
            
        except Exception as e:
            logger.error(f"Facebook metrics collection failed: {e}")
            return MetricsCollectionResult(
                success=False,
                platform="facebook",
                metrics_collected=0,
                errors=[str(e)],
                collection_time=datetime.now(timezone.utc)
            )
    
    async def _collect_linkedin_metrics(
        self,
        db: Session,
        force_collection: bool = False
    ) -> MetricsCollectionResult:
        """Collect metrics from LinkedIn"""
        try:
            # Get LinkedIn accounts
            linkedin_accounts = db.query(SocialMediaAccount).filter(
                SocialMediaAccount.platform == "linkedin",
                SocialMediaAccount.is_active == True
            ).all()
            
            if not linkedin_accounts:
                return MetricsCollectionResult(
                    success=True,
                    platform="linkedin",
                    metrics_collected=0,
                    errors=[],
                    collection_time=datetime.now(timezone.utc)
                )
            
            total_metrics = 0
            errors = []
            
            for account in linkedin_accounts:
                try:
                    # Get recent content items for this account
                    content_items = db.query(ContentItem).filter(
                        ContentItem.platform == "linkedin",
                        ContentItem.account_id == account.account_id,
                        ContentItem.status == "published"
                    ).order_by(ContentItem.published_at.desc()).limit(self.batch_sizes[Platform.LINKEDIN]).all()
                    
                    # Collect metrics for each content item
                    for content_item in content_items:
                        if not self._should_collect_metrics(content_item, Platform.LINKEDIN, force_collection):
                            continue
                        
                        try:
                            # Get LinkedIn analytics (using existing client method)
                            analytics = await linkedin_client.get_post_analytics(
                                access_token=account.access_token,
                                post_id=content_item.platform_post_id
                            )
                            
                            # Convert to unified metrics
                            unified_metrics = self._linkedin_to_unified_metrics(analytics, content_item)
                            
                            # Save to database
                            await self._save_metrics_to_db(db, unified_metrics, content_item)
                            
                            total_metrics += 1
                            
                            # Brief delay to respect rate limits
                            await asyncio.sleep(0.3)
                            
                        except Exception as e:
                            error_msg = f"Failed to collect LinkedIn metrics for content {content_item.id}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Failed to process LinkedIn account {account.account_id}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return MetricsCollectionResult(
                success=len(errors) == 0,
                platform="linkedin",
                metrics_collected=total_metrics,
                errors=errors,
                collection_time=datetime.now(timezone.utc),
                next_collection=datetime.now(timezone.utc) + self.collection_intervals[Platform.LINKEDIN]
            )
            
        except Exception as e:
            logger.error(f"LinkedIn metrics collection failed: {e}")
            return MetricsCollectionResult(
                success=False,
                platform="linkedin",
                metrics_collected=0,
                errors=[str(e)],
                collection_time=datetime.now(timezone.utc)
            )
    
    
    def _should_collect_metrics(
        self,
        content_item: ContentItem,
        platform: Platform,
        force_collection: bool
    ) -> bool:
        """Determine if metrics should be collected for a content item"""
        if force_collection:
            return True
        
        # Check if enough time has passed since last collection
        if content_item.last_metrics_update:
            time_since_last = datetime.now(timezone.utc) - content_item.last_metrics_update
            if time_since_last < self.collection_intervals[platform]:
                return False
        
        # Always collect for recently published content (within 24 hours)
        if content_item.published_at:
            time_since_publish = datetime.now(timezone.utc) - content_item.published_at
            if time_since_publish < timedelta(hours=24):
                return True
        
        # Collect for content that hasn't been updated recently
        return True
    
    def _twitter_to_unified_metrics(
        self,
        analytics: TwitterAnalytics,
        content_item: ContentItem
    ) -> UnifiedMetrics:
        """Convert Twitter analytics to unified metrics"""
        return UnifiedMetrics(
            platform="twitter",
            content_id=str(content_item.id),
            post_id=analytics.tweet_id,
            impressions=analytics.impressions,
            reach=analytics.impressions,  # Twitter doesn't separate reach from impressions
            engagement=analytics.retweets + analytics.likes + analytics.replies + analytics.quotes,
            likes=analytics.likes,
            comments=analytics.replies,
            shares=analytics.retweets + analytics.quotes,
            clicks=analytics.url_clicks + analytics.profile_clicks,
            video_views=None,  # Not available in basic analytics
            saves=analytics.bookmarks,
            engagement_rate=analytics.engagement_rate,
            collected_at=analytics.fetched_at
        )
    
    def _instagram_to_unified_metrics(
        self,
        insights: InstagramInsight,
        content_item: ContentItem
    ) -> UnifiedMetrics:
        """Convert Instagram insights to unified metrics"""
        return UnifiedMetrics(
            platform="instagram",
            content_id=str(content_item.id),
            post_id=insights.media_id,
            impressions=insights.impressions,
            reach=insights.reach,
            engagement=insights.engagement,
            likes=insights.likes,
            comments=insights.comments,
            shares=insights.shares,
            clicks=insights.website_clicks,
            video_views=insights.video_views,
            saves=insights.saved,
            engagement_rate=0.0,  # Will be calculated in __post_init__
            collected_at=insights.fetched_at
        )
    
    def _facebook_to_unified_metrics(
        self,
        insights: FacebookInsights,
        content_item: ContentItem
    ) -> UnifiedMetrics:
        """Convert Facebook insights to unified metrics"""
        return UnifiedMetrics(
            platform="facebook",
            content_id=str(content_item.id),
            post_id=insights.post_id,
            impressions=insights.impressions,
            reach=insights.reach,
            engagement=insights.engagement,
            likes=insights.reactions,  # Facebook uses reactions instead of likes
            comments=insights.comments,
            shares=insights.shares,
            clicks=insights.clicks,
            video_views=insights.video_views,
            saves=None,  # Facebook doesn't have saves
            engagement_rate=0.0,  # Will be calculated in __post_init__
            collected_at=insights.fetched_at
        )
    
    def _linkedin_to_unified_metrics(
        self,
        analytics: Dict[str, Any],
        content_item: ContentItem
    ) -> UnifiedMetrics:
        """Convert LinkedIn analytics to unified metrics"""
        # LinkedIn analytics structure varies, adapt as needed
        return UnifiedMetrics(
            platform="linkedin",
            content_id=str(content_item.id),
            post_id=str(content_item.platform_post_id),
            impressions=analytics.get("impressions", 0),
            reach=analytics.get("reach", 0),
            engagement=analytics.get("engagement", 0),
            likes=analytics.get("likes", 0),
            comments=analytics.get("comments", 0),
            shares=analytics.get("shares", 0),
            clicks=analytics.get("clicks", 0),
            video_views=analytics.get("video_views"),
            saves=None,  # LinkedIn doesn't have saves
            engagement_rate=0.0,  # Will be calculated in __post_init__
            collected_at=datetime.now(timezone.utc)
        )
    
    async def _save_metrics_to_db(
        self,
        db: Session,
        metrics: UnifiedMetrics,
        content_item: ContentItem
    ):
        """Save unified metrics to database"""
        try:
            # Create performance snapshot
            snapshot = ContentPerformanceSnapshot(
                content_item_id=content_item.id,
                timestamp=metrics.collected_at,
                impressions=metrics.impressions,
                reach=metrics.reach,
                engagement=metrics.engagement,
                likes=metrics.likes,
                comments=metrics.comments,
                shares=metrics.shares,
                clicks=metrics.clicks,
                video_views=metrics.video_views,
                saves=metrics.saves,
                engagement_rate=metrics.engagement_rate,
                platform_specific_data=asdict(metrics)
            )
            
            db.add(snapshot)
            
            # Update content item with latest metrics
            content_item.total_impressions = metrics.impressions
            content_item.total_engagement = metrics.engagement
            content_item.engagement_rate = metrics.engagement_rate
            content_item.last_metrics_update = metrics.collected_at
            
            db.commit()
            
            logger.info(f"Saved metrics for content {content_item.id} on {metrics.platform}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save metrics to database: {e}")
            raise
    
    async def get_metrics_summary(
        self,
        db: Session,
        platform: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get summary of collected metrics
        
        Args:
            db: Database session
            platform: Specific platform to summarize (if None, all platforms)
            days: Number of days to include in summary
            
        Returns:
            Metrics summary
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = db.query(ContentPerformanceSnapshot).filter(
            ContentPerformanceSnapshot.timestamp >= since_date
        )
        
        if platform:
            # Join with ContentItem to filter by platform
            query = query.join(ContentItem).filter(ContentItem.platform == platform)
        
        snapshots = query.all()
        
        if not snapshots:
            return {
                "total_content": 0,
                "total_impressions": 0,
                "total_engagement": 0,
                "average_engagement_rate": 0.0,
                "platforms": {}
            }
        
        # Calculate aggregated metrics
        total_impressions = sum(s.impressions for s in snapshots)
        total_engagement = sum(s.engagement for s in snapshots)
        avg_engagement_rate = sum(s.engagement_rate for s in snapshots) / len(snapshots)
        
        # Group by platform
        platforms = {}
        for snapshot in snapshots:
            platform_name = snapshot.content_item.platform
            if platform_name not in platforms:
                platforms[platform_name] = {
                    "content_count": 0,
                    "impressions": 0,
                    "engagement": 0,
                    "engagement_rate": 0.0
                }
            
            platforms[platform_name]["content_count"] += 1
            platforms[platform_name]["impressions"] += snapshot.impressions
            platforms[platform_name]["engagement"] += snapshot.engagement
            platforms[platform_name]["engagement_rate"] += snapshot.engagement_rate
        
        # Calculate averages for each platform
        for platform_name, data in platforms.items():
            if data["content_count"] > 0:
                data["engagement_rate"] /= data["content_count"]
        
        return {
            "total_content": len(snapshots),
            "total_impressions": total_impressions,
            "total_engagement": total_engagement,
            "average_engagement_rate": avg_engagement_rate,
            "platforms": platforms,
            "collection_period_days": days,
            "last_updated": datetime.now(timezone.utc)
        }

# Global metrics collector instance
metrics_collector = SocialMediaMetricsCollector()