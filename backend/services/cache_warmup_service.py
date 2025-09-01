"""
Cache Warmup Service for Intelligent Pre-loading
Proactive cache warming based on user behavior patterns and platform activity
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from dataclasses import dataclass

from backend.services.redis_cache import redis_cache
from backend.db.database_optimized import get_db_connection
from backend.db.models import User, ContentItem

logger = logging.getLogger(__name__)

@dataclass
class WarmupPattern:
    """Cache warmup pattern based on user behavior"""
    platform: str
    operation: str
    priority: int  # 1-10, higher = more important
    frequency_score: float  # How often this is accessed
    recency_score: float  # How recently this was accessed
    
class CacheWarmupService:
    """
    Intelligent cache warming service that analyzes user patterns
    and proactively loads frequently accessed data
    """
    
    def __init__(self):
        self.cache = redis_cache
        self.warmup_patterns = {}
        self.user_access_patterns = defaultdict(Counter)
        self.warmup_in_progress = set()
        
    async def analyze_user_patterns(self, user_id: int, days_back: int = 30) -> List[WarmupPattern]:
        """
        Analyze user access patterns to determine optimal cache warmup
        
        Args:
            user_id: User to analyze
            days_back: How many days of history to analyze
            
        Returns:
            List of warmup patterns sorted by priority
        """
        patterns = []
        
        try:
            with get_db_connection() as db:
                # Analyze content creation patterns
                content_query = (
                    db.query(ContentItem)
                    .filter(ContentItem.user_id == user_id)
                    .filter(ContentItem.created_at >= datetime.now(timezone.utc) - timedelta(days=days_back))
                )
                
                platform_usage = Counter()
                recent_activity = defaultdict(list)
                
                for content in content_query.all():
                    platform_usage[content.platform] += 1
                    recent_activity[content.platform].append(content.created_at)
                
                # Generate warmup patterns based on usage
                for platform, count in platform_usage.most_common():
                    # Calculate frequency and recency scores
                    recent_dates = recent_activity[platform]
                    avg_recency = sum(
                        (datetime.now(timezone.utc) - date).days for date in recent_dates
                    ) / len(recent_dates)
                    
                    frequency_score = min(count / days_back, 1.0)  # Normalize to 0-1
                    recency_score = max(0, 1.0 - (avg_recency / days_back))  # More recent = higher score
                    
                    # Essential operations for active platforms
                    essential_ops = {
                        "twitter": ["profile", "recent_tweets", "analytics"],
                        "instagram": ["profile", "recent_posts", "insights"],
                        "facebook": ["profile", "page_info", "insights"],
                        "linkedin": ["profile", "recent_posts", "analytics"],
                        "tiktok": ["profile", "recent_videos", "analytics"]
                    }
                    
                    operations = essential_ops.get(platform, ["profile"])
                    
                    for i, operation in enumerate(operations):
                        priority = int((frequency_score + recency_score) * 10) - i
                        priority = max(1, min(10, priority))  # Clamp to 1-10
                        
                        patterns.append(WarmupPattern(
                            platform=platform,
                            operation=operation,
                            priority=priority,
                            frequency_score=frequency_score,
                            recency_score=recency_score
                        ))
                
                # Sort by priority (highest first)
                patterns.sort(key=lambda x: x.priority, reverse=True)
                
                logger.info(f"Generated {len(patterns)} warmup patterns for user {user_id}")
                return patterns
                
        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            return []
    
    async def warmup_user_cache(self, user_id: int, force: bool = False) -> Dict[str, int]:
        """
        Warm cache for a specific user based on their patterns
        
        Args:
            user_id: User ID to warm cache for
            force: Force warmup even if recently done
            
        Returns:
            Dict with warmup statistics
        """
        warmup_key = f"warmup_user_{user_id}"
        
        # Check if warmup is already in progress
        if warmup_key in self.warmup_in_progress and not force:
            logger.info(f"Cache warmup already in progress for user {user_id}")
            return {"status": "in_progress"}
        
        # Check if recently warmed (unless forced)
        if not force:
            last_warmup = await self.cache.get("system", "warmup", user_id=user_id, resource_id="last_warmup")
            if last_warmup:
                last_time = datetime.fromisoformat(last_warmup)
                if datetime.now(timezone.utc) - last_time < timedelta(hours=6):
                    logger.info(f"User {user_id} cache recently warmed, skipping")
                    return {"status": "recently_warmed", "last_warmup": last_warmup}
        
        self.warmup_in_progress.add(warmup_key)
        
        try:
            # Analyze user patterns
            patterns = await self.analyze_user_patterns(user_id)
            
            if not patterns:
                logger.info(f"No patterns found for user {user_id}, using default warmup")
                patterns = self._get_default_patterns()
            
            # Warm cache based on patterns
            warmed_count = 0
            failed_count = 0
            
            for pattern in patterns[:20]:  # Limit to top 20 patterns
                try:
                    # Create placeholder data for warmup
                    # In a real implementation, this would call actual platform APIs
                    warmup_data = {
                        "platform": pattern.platform,
                        "operation": pattern.operation,
                        "warmed_at": datetime.now(timezone.utc).isoformat(),
                        "priority": pattern.priority,
                        "user_id": user_id,
                        "warmup_session": warmup_key
                    }
                    
                    success = await self.cache.set(
                        platform=pattern.platform,
                        operation=pattern.operation,
                        data=warmup_data,
                        user_id=user_id,
                        ttl=self._get_warmup_ttl(pattern.platform, pattern.operation)
                    )
                    
                    if success:
                        warmed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to warm cache for {pattern.platform}:{pattern.operation}: {e}")
                    failed_count += 1
            
            # Update last warmup time
            await self.cache.set(
                "system", "warmup", 
                datetime.now(timezone.utc).isoformat(),
                user_id=user_id,
                resource_id="last_warmup",
                ttl=86400  # 24 hours
            )
            
            result = {
                "status": "completed",
                "warmed_count": warmed_count,
                "failed_count": failed_count,
                "patterns_analyzed": len(patterns),
                "warmup_time": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Cache warmup completed for user {user_id}: {warmed_count} items warmed, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Cache warmup failed for user {user_id}: {e}")
            return {"status": "failed", "error": str(e)}
        
        finally:
            self.warmup_in_progress.discard(warmup_key)
    
    async def warmup_popular_content(self, limit: int = 100) -> Dict[str, int]:
        """
        Warm cache with popular/trending content across all users
        
        Args:
            limit: Maximum number of items to warm
            
        Returns:
            Warmup statistics
        """
        try:
            with get_db_connection() as db:
                # Get most engaged-with content from last 7 days
                popular_content = (
                    db.query(ContentItem)
                    .filter(ContentItem.published_at >= datetime.now(timezone.utc) - timedelta(days=7))
                    .filter(ContentItem.engagement_count > 0)
                    .order_by(ContentItem.engagement_count.desc())
                    .limit(limit)
                    .all()
                )
                
                warmed_count = 0
                platforms = set()
                
                for content in popular_content:
                    platforms.add(content.platform)
                    
                    # Cache popular content metadata
                    await self.cache.set(
                        platform=content.platform,
                        operation="popular_content",
                        data={
                            "content_id": content.id,
                            "platform": content.platform,
                            "engagement_count": content.engagement_count,
                            "cached_at": datetime.now(timezone.utc).isoformat()
                        },
                        resource_id=str(content.id),
                        ttl=3600  # 1 hour for popular content
                    )
                    
                    warmed_count += 1
                
                logger.info(f"Warmed cache with {warmed_count} popular content items across {len(platforms)} platforms")
                
                return {
                    "status": "completed",
                    "warmed_count": warmed_count,
                    "platforms": list(platforms),
                    "warmup_time": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Popular content warmup failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def schedule_warmup_tasks(self):
        """Schedule automatic cache warmup tasks"""
        logger.info("Starting scheduled cache warmup tasks")
        
        try:
            # Get active users (users who have created content in last 30 days)
            with get_db_connection() as db:
                active_users = (
                    db.query(User.id)
                    .join(ContentItem)
                    .filter(ContentItem.created_at >= datetime.now(timezone.utc) - timedelta(days=30))
                    .distinct()
                    .limit(50)  # Limit to prevent overwhelming the system
                    .all()
                )
                
                user_ids = [user.id for user in active_users]
                logger.info(f"Found {len(user_ids)} active users for warmup")
                
                # Warmup in batches to avoid overwhelming Redis
                batch_size = 10
                for i in range(0, len(user_ids), batch_size):
                    batch = user_ids[i:i + batch_size]
                    
                    # Run warmup tasks concurrently for batch
                    tasks = [self.warmup_user_cache(user_id) for user_id in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
                    logger.info(f"Batch {i//batch_size + 1}: {successful}/{len(batch)} users warmed successfully")
                    
                    # Small delay between batches
                    await asyncio.sleep(2)
                
                # Also warm popular content
                await self.warmup_popular_content()
                
                logger.info("Scheduled warmup tasks completed")
                
        except Exception as e:
            logger.error(f"Scheduled warmup failed: {e}")
    
    def _get_default_patterns(self) -> List[WarmupPattern]:
        """Get default warmup patterns for new users"""
        return [
            WarmupPattern("twitter", "profile", 8, 0.8, 0.9),
            WarmupPattern("instagram", "profile", 8, 0.8, 0.9),
            WarmupPattern("facebook", "profile", 7, 0.7, 0.8),
            WarmupPattern("linkedin", "profile", 7, 0.7, 0.8),
            WarmupPattern("twitter", "recent_tweets", 6, 0.6, 0.7),
            WarmupPattern("instagram", "recent_posts", 6, 0.6, 0.7),
        ]
    
    def _get_warmup_ttl(self, platform: str, operation: str) -> int:
        """Get appropriate TTL for warmed cache entries"""
        # Longer TTL for warmup entries since they're proactively loaded
        base_ttls = {
            "profile": 7200,      # 2 hours
            "recent_tweets": 1800, # 30 minutes
            "recent_posts": 1800,  # 30 minutes
            "analytics": 3600,     # 1 hour
            "insights": 3600,      # 1 hour
        }
        
        return base_ttls.get(operation, 3600)  # Default 1 hour
    
    async def get_warmup_stats(self) -> Dict[str, any]:
        """Get cache warmup statistics"""
        try:
            # Get warmup status from cache
            warmup_stats = await self.cache.get("system", "warmup_stats")
            
            if not warmup_stats:
                warmup_stats = {
                    "total_warmups": 0,
                    "successful_warmups": 0,
                    "failed_warmups": 0,
                    "last_warmup": None,
                    "active_users_warmed": 0
                }
            
            # Add current status
            warmup_stats["warmup_in_progress"] = len(self.warmup_in_progress)
            warmup_stats["last_checked"] = datetime.now(timezone.utc).isoformat()
            
            return warmup_stats
            
        except Exception as e:
            logger.error(f"Error getting warmup stats: {e}")
            return {"error": str(e)}

# Global cache warmup service
cache_warmup_service = CacheWarmupService()