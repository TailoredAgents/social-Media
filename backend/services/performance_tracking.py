"""
Content Performance Tracking System
Handles engagement metrics collection, analysis, and performance categorization
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import numpy as np
from statistics import mean, median

from backend.db.database import get_db
from backend.db.models import ContentItem, ContentPerformanceSnapshot, User
from backend.core.config import get_settings

# Get logger (use application's logging configuration)
logger = logging.getLogger(__name__)

settings = get_settings()

@dataclass
class PerformanceMetrics:
    """Standard performance metrics structure"""
    likes_count: int = 0
    shares_count: int = 0
    comments_count: int = 0
    reach_count: int = 0
    click_count: int = 0
    engagement_rate: float = 0.0
    viral_score: float = 0.0
    performance_tier: str = "unknown"

@dataclass
class PerformanceAnalysis:
    """Comprehensive performance analysis result"""
    content_id: str
    current_metrics: PerformanceMetrics
    growth_metrics: Dict[str, int]
    performance_comparison: Dict[str, float]
    recommendations: List[str]
    tier_change: Optional[str] = None

class PerformanceTracker:
    """
    Content Performance Tracking System
    
    Features:
    - Real-time engagement metrics calculation
    - Performance tier classification (viral, high, medium, low, poor)
    - Growth trend analysis
    - Comparative performance analysis
    - Automated performance snapshots
    - Performance-based recommendations
    """
    
    def __init__(self):
        """Initialize the performance tracker"""
        # Performance tier thresholds (configurable per platform)
        self.tier_thresholds = {
            "twitter": {
                "viral": {"likes": 1000, "shares": 100, "engagement_rate": 0.10},
                "high": {"likes": 100, "shares": 10, "engagement_rate": 0.05},
                "medium": {"likes": 20, "shares": 2, "engagement_rate": 0.02},
                "low": {"likes": 5, "shares": 1, "engagement_rate": 0.01}
            },
            "linkedin": {
                "viral": {"likes": 500, "shares": 50, "engagement_rate": 0.08},
                "high": {"likes": 50, "shares": 5, "engagement_rate": 0.04},
                "medium": {"likes": 10, "shares": 2, "engagement_rate": 0.02},
                "low": {"likes": 3, "shares": 1, "engagement_rate": 0.01}
            },
            "instagram": {
                "viral": {"likes": 2000, "shares": 200, "engagement_rate": 0.12},
                "high": {"likes": 200, "shares": 20, "engagement_rate": 0.06},
                "medium": {"likes": 50, "shares": 5, "engagement_rate": 0.03},
                "low": {"likes": 10, "shares": 2, "engagement_rate": 0.015}
            },
            "facebook": {
                "viral": {"likes": 800, "shares": 80, "engagement_rate": 0.09},
                "high": {"likes": 80, "shares": 8, "engagement_rate": 0.045},
                "medium": {"likes": 20, "shares": 3, "engagement_rate": 0.025},
                "low": {"likes": 5, "shares": 1, "engagement_rate": 0.01}
            },
            "tiktok": {
                "viral": {"likes": 5000, "shares": 500, "engagement_rate": 0.15},
                "high": {"likes": 500, "shares": 50, "engagement_rate": 0.08},
                "medium": {"likes": 100, "shares": 10, "engagement_rate": 0.04},
                "low": {"likes": 20, "shares": 3, "engagement_rate": 0.02}
            }
        }
        
        logger.info("PerformanceTracker initialized with platform-specific thresholds")
    
    def calculate_engagement_rate(
        self, 
        likes: int, 
        shares: int, 
        comments: int, 
        reach: int
    ) -> float:
        """
        Calculate engagement rate based on total interactions vs reach
        
        Args:
            likes: Number of likes
            shares: Number of shares/retweets
            comments: Number of comments
            reach: Total reach/impressions
            
        Returns:
            Engagement rate as a percentage (0.0 to 1.0)
        """
        if reach == 0:
            return 0.0
        
        total_engagements = likes + shares + comments
        return total_engagements / reach
    
    def calculate_viral_score(
        self, 
        metrics: PerformanceMetrics, 
        platform: str,
        time_since_publish: timedelta
    ) -> float:
        """
        Calculate viral potential score based on engagement velocity and reach
        
        Args:
            metrics: Current performance metrics
            platform: Social media platform
            time_since_publish: Time elapsed since publication
            
        Returns:
            Viral score (0.0 to 1.0)
        """
        if time_since_publish.total_seconds() == 0:
            return 0.0
        
        # Calculate engagement per hour
        hours_elapsed = max(time_since_publish.total_seconds() / 3600, 0.1)
        engagements_per_hour = (metrics.likes_count + metrics.shares_count + metrics.comments_count) / hours_elapsed
        
        # Get platform-specific viral threshold
        platform_thresholds = self.tier_thresholds.get(platform, self.tier_thresholds["twitter"])
        viral_threshold = platform_thresholds["viral"]["likes"] / 24  # Expected per hour for viral
        
        # Calculate viral score
        viral_score = min(engagements_per_hour / viral_threshold, 1.0)
        
        # Boost score for high share rate (indicates viral potential)
        if metrics.likes_count > 0:
            share_ratio = metrics.shares_count / metrics.likes_count
            if share_ratio > 0.1:  # High share ratio
                viral_score *= 1.5
        
        return min(viral_score, 1.0)
    
    def classify_performance_tier(
        self, 
        metrics: PerformanceMetrics, 
        platform: str
    ) -> str:
        """
        Classify content performance into tiers
        
        Args:
            metrics: Performance metrics
            platform: Social media platform
            
        Returns:
            Performance tier: viral, high, medium, low, poor
        """
        platform_thresholds = self.tier_thresholds.get(platform, self.tier_thresholds["twitter"])
        
        # Check viral tier
        viral_criteria = platform_thresholds["viral"]
        if (metrics.likes_count >= viral_criteria["likes"] or
            metrics.shares_count >= viral_criteria["shares"] or
            metrics.engagement_rate >= viral_criteria["engagement_rate"]):
            return "viral"
        
        # Check high tier
        high_criteria = platform_thresholds["high"]
        if (metrics.likes_count >= high_criteria["likes"] or
            metrics.shares_count >= high_criteria["shares"] or
            metrics.engagement_rate >= high_criteria["engagement_rate"]):
            return "high"
        
        # Check medium tier
        medium_criteria = platform_thresholds["medium"]
        if (metrics.likes_count >= medium_criteria["likes"] or
            metrics.shares_count >= medium_criteria["shares"] or
            metrics.engagement_rate >= medium_criteria["engagement_rate"]):
            return "medium"
        
        # Check low tier
        low_criteria = platform_thresholds["low"]
        if (metrics.likes_count >= low_criteria["likes"] or
            metrics.shares_count >= low_criteria["shares"] or
            metrics.engagement_rate >= low_criteria["engagement_rate"]):
            return "low"
        
        return "poor"
    
    def update_content_performance(
        self, 
        db: Session,
        content_id: str,
        new_metrics: Dict[str, Any],
        platform_specific_data: Optional[Dict[str, Any]] = None
    ) -> PerformanceAnalysis:
        """
        Update performance metrics for a content item
        
        Args:
            db: Database session
            content_id: Content item ID
            new_metrics: New performance metrics
            platform_specific_data: Additional platform-specific metrics
            
        Returns:
            Performance analysis result
        """
        try:
            # Get content item
            content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if not content_item:
                raise ValueError(f"Content item {content_id} not found")
            
            # Store previous metrics for comparison
            old_metrics = PerformanceMetrics(
                likes_count=content_item.likes_count or 0,
                shares_count=content_item.shares_count or 0,
                comments_count=content_item.comments_count or 0,
                reach_count=content_item.reach_count or 0,
                click_count=content_item.click_count or 0,
                engagement_rate=content_item.engagement_rate or 0.0,
                viral_score=content_item.viral_score or 0.0,
                performance_tier=content_item.performance_tier or "unknown"
            )
            
            # Create new metrics object
            current_metrics = PerformanceMetrics(
                likes_count=new_metrics.get("likes_count", 0),
                shares_count=new_metrics.get("shares_count", 0),
                comments_count=new_metrics.get("comments_count", 0),
                reach_count=new_metrics.get("reach_count", 0),
                click_count=new_metrics.get("click_count", 0)
            )
            
            # Calculate engagement rate
            current_metrics.engagement_rate = self.calculate_engagement_rate(
                current_metrics.likes_count,
                current_metrics.shares_count,
                current_metrics.comments_count,
                current_metrics.reach_count
            )
            
            # Calculate viral score
            if content_item.published_at:
                time_since_publish = datetime.utcnow() - content_item.published_at.replace(tzinfo=None)
                current_metrics.viral_score = self.calculate_viral_score(
                    current_metrics, 
                    content_item.platform,
                    time_since_publish
                )
            
            # Classify performance tier
            current_metrics.performance_tier = self.classify_performance_tier(
                current_metrics, 
                content_item.platform
            )
            
            # Update content item
            content_item.likes_count = current_metrics.likes_count
            content_item.shares_count = current_metrics.shares_count
            content_item.comments_count = current_metrics.comments_count
            content_item.reach_count = current_metrics.reach_count
            content_item.click_count = current_metrics.click_count
            content_item.engagement_rate = current_metrics.engagement_rate
            content_item.viral_score = current_metrics.viral_score
            content_item.performance_tier = current_metrics.performance_tier
            content_item.last_performance_update = datetime.utcnow()
            
            # Create performance snapshot
            snapshot = ContentPerformanceSnapshot(
                content_item_id=content_id,
                likes_count=current_metrics.likes_count,
                shares_count=current_metrics.shares_count,
                comments_count=current_metrics.comments_count,
                reach_count=current_metrics.reach_count,
                click_count=current_metrics.click_count,
                engagement_rate=current_metrics.engagement_rate,
                likes_growth=current_metrics.likes_count - old_metrics.likes_count,
                shares_growth=current_metrics.shares_count - old_metrics.shares_count,
                comments_growth=current_metrics.comments_count - old_metrics.comments_count,
                reach_growth=current_metrics.reach_count - old_metrics.reach_count,
                platform_metrics=platform_specific_data or {}
            )
            
            # Calculate engagement velocity (engagements per hour)
            if content_item.published_at:
                time_diff = datetime.utcnow() - content_item.published_at.replace(tzinfo=None)
                hours = max(time_diff.total_seconds() / 3600, 0.1)
                total_engagements = (current_metrics.likes_count + 
                                   current_metrics.shares_count + 
                                   current_metrics.comments_count)
                snapshot.engagement_velocity = total_engagements / hours
                
                # Calculate viral coefficient (shares per like)
                if current_metrics.likes_count > 0:
                    snapshot.viral_coefficient = current_metrics.shares_count / current_metrics.likes_count
            
            db.add(snapshot)
            db.commit()
            
            # Calculate growth metrics
            growth_metrics = {
                "likes_growth": current_metrics.likes_count - old_metrics.likes_count,
                "shares_growth": current_metrics.shares_count - old_metrics.shares_count,
                "comments_growth": current_metrics.comments_count - old_metrics.comments_count,
                "reach_growth": current_metrics.reach_count - old_metrics.reach_count
            }
            
            # Generate performance comparison and recommendations
            performance_comparison = self._generate_performance_comparison(
                db, content_item, current_metrics
            )
            recommendations = self._generate_recommendations(
                content_item, current_metrics, old_metrics, growth_metrics
            )
            
            # Determine tier change
            tier_change = None
            if old_metrics.performance_tier != current_metrics.performance_tier:
                tier_change = f"{old_metrics.performance_tier} → {current_metrics.performance_tier}"
            
            logger.info(f"Updated performance for content {content_id}: " +
                       f"{current_metrics.performance_tier} tier, " +
                       f"{current_metrics.engagement_rate:.2%} engagement")
            
            return PerformanceAnalysis(
                content_id=content_id,
                current_metrics=current_metrics,
                growth_metrics=growth_metrics,
                performance_comparison=performance_comparison,
                recommendations=recommendations,
                tier_change=tier_change
            )
            
        except Exception as e:
            logger.error(f"Error updating performance for content {content_id}: {e}")
            db.rollback()
            raise
    
    def _generate_performance_comparison(
        self, 
        db: Session, 
        content_item: ContentItem, 
        current_metrics: PerformanceMetrics
    ) -> Dict[str, float]:
        """Generate performance comparison against user's other content"""
        try:
            # Get user's recent content for comparison
            recent_content = db.query(ContentItem).filter(
                and_(
                    ContentItem.user_id == content_item.user_id,
                    ContentItem.platform == content_item.platform,
                    ContentItem.published_at.isnot(None),
                    ContentItem.engagement_rate.isnot(None)
                )
            ).order_by(desc(ContentItem.published_at)).limit(50).all()
            
            if len(recent_content) < 2:
                return {"percentile": 50.0, "avg_comparison": 1.0}
            
            # Calculate percentiles
            engagement_rates = [c.engagement_rate for c in recent_content if c.engagement_rate]
            likes_counts = [c.likes_count for c in recent_content if c.likes_count]
            
            if engagement_rates:
                engagement_percentile = (
                    sum(1 for rate in engagement_rates if rate <= current_metrics.engagement_rate) /
                    len(engagement_rates) * 100
                )
                avg_engagement = mean(engagement_rates)
                engagement_comparison = current_metrics.engagement_rate / avg_engagement if avg_engagement > 0 else 1.0
            else:
                engagement_percentile = 50.0
                engagement_comparison = 1.0
            
            if likes_counts:
                likes_percentile = (
                    sum(1 for count in likes_counts if count <= current_metrics.likes_count) /
                    len(likes_counts) * 100
                )
            else:
                likes_percentile = 50.0
            
            return {
                "engagement_percentile": engagement_percentile,
                "likes_percentile": likes_percentile,
                "avg_engagement_comparison": engagement_comparison
            }
            
        except Exception as e:
            logger.error(f"Error generating performance comparison: {e}")
            return {"percentile": 50.0, "avg_comparison": 1.0}
    
    def _generate_recommendations(
        self,
        content_item: ContentItem,
        current_metrics: PerformanceMetrics,
        old_metrics: PerformanceMetrics,
        growth_metrics: Dict[str, int]
    ) -> List[str]:
        """Generate performance-based recommendations"""
        recommendations = []
        
        # Viral content recommendations
        if current_metrics.performance_tier == "viral":
            recommendations.append("🚀 Viral content detected! Consider creating similar content or repurposing this across other platforms.")
            recommendations.append("📈 Engage with comments quickly to maintain momentum.")
        
        # High performing content
        elif current_metrics.performance_tier == "high":
            recommendations.append("✨ High-performing content! Consider boosting with paid promotion.")
            recommendations.append("🔄 This content type is resonating well - create variations of this theme.")
        
        # Growth analysis
        if growth_metrics["likes_growth"] > 10:
            recommendations.append("📊 Strong like growth indicates good content resonance.")
        
        if growth_metrics["shares_growth"] > 2:
            recommendations.append("🔗 High share rate suggests viral potential - monitor closely.")
        
        # Low performance recommendations
        if current_metrics.performance_tier in ["low", "poor"]:
            recommendations.append("💡 Consider revising content strategy for this platform.")
            recommendations.append("🎯 Analyze top-performing content to identify successful patterns.")
            
            if current_metrics.reach_count > 0 and current_metrics.engagement_rate < 0.01:
                recommendations.append("👀 Good reach but low engagement - review content quality and relevance.")
        
        # Platform-specific recommendations
        if content_item.platform == "twitter" and current_metrics.shares_count == 0:
            recommendations.append("🐦 Consider adding hashtags or asking questions to encourage retweets.")
        
        if content_item.platform == "linkedin" and current_metrics.comments_count == 0:
            recommendations.append("💼 Professional content performs better with thought-provoking questions.")
        
        # Time-based recommendations
        if content_item.published_at:
            hours_since_publish = (datetime.utcnow() - content_item.published_at.replace(tzinfo=None)).total_seconds() / 3600
            if hours_since_publish > 24 and current_metrics.performance_tier in ["medium", "high"]:
                recommendations.append("⏰ Content is performing well after 24h - consider repurposing.")
        
        return recommendations
    
    def get_performance_trends(
        self, 
        db: Session, 
        content_id: str, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get performance trends over time for a content item
        
        Args:
            db: Database session
            content_id: Content item ID
            days: Number of days to analyze
            
        Returns:
            Performance trends data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            snapshots = db.query(ContentPerformanceSnapshot).filter(
                and_(
                    ContentPerformanceSnapshot.content_item_id == content_id,
                    ContentPerformanceSnapshot.snapshot_time >= cutoff_date
                )
            ).order_by(ContentPerformanceSnapshot.snapshot_time).all()
            
            if not snapshots:
                return {"error": "No performance data available"}
            
            # Extract time series data
            timestamps = [s.snapshot_time for s in snapshots]
            likes_data = [s.likes_count for s in snapshots]
            shares_data = [s.shares_count for s in snapshots]
            comments_data = [s.comments_count for s in snapshots]
            engagement_data = [s.engagement_rate for s in snapshots]
            
            # Calculate trends
            return {
                "total_snapshots": len(snapshots),
                "date_range": {
                    "start": timestamps[0].isoformat(),
                    "end": timestamps[-1].isoformat()
                },
                "trends": {
                    "likes": {
                        "data": likes_data,
                        "growth": likes_data[-1] - likes_data[0] if len(likes_data) > 1 else 0,
                        "peak": max(likes_data),
                        "avg_growth_rate": (likes_data[-1] - likes_data[0]) / max(len(likes_data) - 1, 1)
                    },
                    "shares": {
                        "data": shares_data,
                        "growth": shares_data[-1] - shares_data[0] if len(shares_data) > 1 else 0,
                        "peak": max(shares_data),
                        "avg_growth_rate": (shares_data[-1] - shares_data[0]) / max(len(shares_data) - 1, 1)
                    },
                    "comments": {
                        "data": comments_data,
                        "growth": comments_data[-1] - comments_data[0] if len(comments_data) > 1 else 0,
                        "peak": max(comments_data)
                    },
                    "engagement_rate": {
                        "data": engagement_data,
                        "current": engagement_data[-1],
                        "peak": max(engagement_data),
                        "average": mean(engagement_data)
                    }
                },
                "velocity_analysis": {
                    "peak_velocity": max([s.engagement_velocity or 0 for s in snapshots]),
                    "current_velocity": snapshots[-1].engagement_velocity or 0,
                    "viral_coefficient": snapshots[-1].viral_coefficient or 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends for {content_id}: {e}")
            return {"error": str(e)}
    
    def get_user_performance_summary(
        self, 
        db: Session, 
        user_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get overall performance summary for a user
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Performance summary
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user's content from the period
            content_items = db.query(ContentItem).filter(
                and_(
                    ContentItem.user_id == user_id,
                    ContentItem.published_at >= cutoff_date,
                    ContentItem.published_at.isnot(None)
                )
            ).all()
            
            if not content_items:
                return {"error": "No content found for the specified period"}
            
            # Calculate aggregate metrics
            total_content = len(content_items)
            platforms = list(set(item.platform for item in content_items))
            
            # Performance tier distribution
            tier_distribution = {}
            total_metrics = {
                "likes": 0, "shares": 0, "comments": 0, 
                "reach": 0, "clicks": 0
            }
            engagement_rates = []
            
            for item in content_items:
                tier = item.performance_tier or "unknown"
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
                
                total_metrics["likes"] += item.likes_count or 0
                total_metrics["shares"] += item.shares_count or 0
                total_metrics["comments"] += item.comments_count or 0
                total_metrics["reach"] += item.reach_count or 0
                total_metrics["clicks"] += item.click_count or 0
                
                if item.engagement_rate:
                    engagement_rates.append(item.engagement_rate)
            
            # Calculate averages
            avg_engagement = mean(engagement_rates) if engagement_rates else 0.0
            avg_likes = total_metrics["likes"] / total_content
            avg_shares = total_metrics["shares"] / total_content
            
            # Find top performers
            top_content = sorted(
                content_items, 
                key=lambda x: x.engagement_rate or 0, 
                reverse=True
            )[:5]
            
            return {
                "period_days": days,
                "total_content": total_content,
                "platforms": platforms,
                "performance_summary": {
                    "avg_engagement_rate": avg_engagement,
                    "total_likes": total_metrics["likes"],
                    "total_shares": total_metrics["shares"],
                    "total_comments": total_metrics["comments"],
                    "total_reach": total_metrics["reach"],
                    "avg_likes_per_post": avg_likes,
                    "avg_shares_per_post": avg_shares
                },
                "tier_distribution": tier_distribution,
                "top_performers": [
                    {
                        "id": item.id,
                        "content": item.content[:100] + "..." if len(item.content) > 100 else item.content,
                        "platform": item.platform,
                        "engagement_rate": item.engagement_rate,
                        "performance_tier": item.performance_tier,
                        "published_at": item.published_at.isoformat() if item.published_at else None
                    }
                    for item in top_content
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary for user {user_id}: {e}")
            return {"error": str(e)}

# Global performance tracker instance
performance_tracker = PerformanceTracker()