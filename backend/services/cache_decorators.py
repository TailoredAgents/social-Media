"""
Cache Decorators for Social Media Integration APIs
Production-ready caching decorators with intelligent invalidation
"""
import asyncio
import functools
import logging
from typing import Any, Callable, Optional, Dict, List, Tuple
from datetime import datetime

from backend.services.redis_cache import redis_cache, CacheStrategy

logger = logging.getLogger(__name__)

async def _extract_user_id_from_token(access_token: str, platform: str) -> Optional[int]:
    """
    Extract user_id from access_token for proper cache scoping
    
    Args:
        access_token: OAuth access token
        platform: Social media platform
        
    Returns:
        User ID if successfully extracted, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from backend.auth.social_oauth import social_oauth_manager as oauth_manager
        from backend.db.database import get_db
        
        async for db in get_db():
            # Look up the user_id associated with this access_token
            user_id = await oauth_manager.get_user_id_by_token(access_token, platform, db)
            return user_id
            
    except Exception as e:
        logger.error(f"Failed to extract user_id from token for {platform}: {e}")
        return None

def cached(
    platform: str,
    operation: str,
    ttl: Optional[int] = None,
    strategy: CacheStrategy = CacheStrategy.TTL,
    user_specific: bool = True,
    invalidate_on_error: bool = True
):
    """
    Cache decorator for social media API methods
    
    Args:
        platform: Social media platform name
        operation: Operation type (profile, posts, analytics, etc.)
        ttl: Cache time-to-live in seconds (None for platform default)
        strategy: Cache invalidation strategy
        user_specific: Whether cache is user-specific
        invalidate_on_error: Whether to invalidate cache on API errors
    
    Usage:
        @cached("twitter", "profile", ttl=3600)
        async def get_twitter_profile(self, access_token: str, user_id: str):
            # API call implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id if available
            user_id = None
            if user_specific:
                # Try to get user_id from various places
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif len(args) > 1 and hasattr(args[0], '__class__'):
                    # Check if it's a method call with self and access_token
                    if 'access_token' in kwargs:
                        user_id = await _extract_user_id_from_token(kwargs['access_token'], platform)
                    elif len(args) > 1 and isinstance(args[1], str):
                        # access_token might be the second argument
                        user_id = await _extract_user_id_from_token(args[1], platform)
                
                # Security: If user_specific is True but no user_id found, skip caching
                if user_id is None:
                    logger.warning(f"Cache decorator: user_specific=True but no user_id found for {platform}:{operation}")
                    # Execute function without caching to prevent cross-user data leakage
                    return await func(*args, **kwargs)
            
            # Create cache key parameters
            cache_kwargs = {k: v for k, v in kwargs.items() if k not in ['access_token']}
            
            # Try to get from cache first
            try:
                cached_result = await redis_cache.get(
                    platform=platform,
                    operation=operation,
                    user_id=user_id,
                    **cache_kwargs
                )
                
                if cached_result is not None:
                    logger.debug(f"Cache hit: {platform}:{operation}")
                    return cached_result
                    
            except Exception as e:
                logger.warning(f"Cache get error: {e}")
            
            # Execute the actual function
            try:
                result = await func(*args, **kwargs)
                
                # Cache the result
                try:
                    await redis_cache.set(
                        platform=platform,
                        operation=operation,
                        data=result,
                        user_id=user_id,
                        ttl=ttl,
                        **cache_kwargs
                    )
                    logger.debug(f"Cached result: {platform}:{operation}")
                    
                except Exception as e:
                    logger.warning(f"Cache set error: {e}")
                
                return result
                
            except Exception as e:
                # Invalidate cache on error if configured
                if invalidate_on_error:
                    try:
                        await redis_cache.delete(
                            platform=platform,
                            operation=operation,
                            user_id=user_id,
                            **cache_kwargs
                        )
                    except Exception as cache_error:
                        logger.warning(f"Cache invalidation error: {cache_error}")
                
                # Re-raise the original error
                raise e
        
        return wrapper
    return decorator

def cache_invalidate(
    platform: str,
    operation: Optional[str] = None,
    user_specific: bool = True
):
    """
    Cache invalidation decorator
    
    Args:
        platform: Platform to invalidate cache for
        operation: Specific operation to invalidate (None for all)
        user_specific: Whether to invalidate user-specific cache
    
    Usage:
        @cache_invalidate("twitter", "profile")
        async def update_twitter_profile(self, access_token: str, profile_data: dict):
            # Update implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache after successful execution
            try:
                user_id = None
                if user_specific and 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if operation:
                    await redis_cache.delete(
                        platform=platform,
                        operation=operation,
                        user_id=user_id
                    )
                else:
                    # Invalidate all operations for platform/user
                    if user_id:
                        await redis_cache.invalidate_user_cache(user_id, platform)
                    else:
                        await redis_cache.invalidate_platform_cache(platform)
                
                logger.info(f"Cache invalidated: {platform}:{operation or 'all'}")
                
            except Exception as e:
                logger.warning(f"Cache invalidation error: {e}")
            
            return result
        
        return wrapper
    return decorator

def batch_cached(
    platform: str,
    operation: str,
    batch_key_func: Callable,
    ttl: Optional[int] = None
):
    """
    Batch caching decorator for operations that can retrieve multiple items
    
    Args:
        platform: Social media platform name
        operation: Operation type
        batch_key_func: Function to generate individual cache keys from batch items
        ttl: Cache time-to-live in seconds
    
    Usage:
        @batch_cached("twitter", "tweets", lambda tweet_id: {"tweet_id": tweet_id})
        async def get_multiple_tweets(self, access_token: str, tweet_ids: List[str]):
            # Batch API call implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a more complex implementation for batch operations
            # For now, we'll use the simple cached decorator
            return await cached(platform, operation, ttl)(func)(*args, **kwargs)
        
        return wrapper
    return decorator

class CacheManager:
    """
    Centralized cache management for social media integrations
    """
    
    def __init__(self):
        self.cache = redis_cache
    
    async def warm_common_caches(self, user_id: int, platforms: List[str]):
        """
        Warm cache with commonly accessed data
        
        Args:
            user_id: User ID to warm cache for
            platforms: List of platforms to warm
        """
        common_operations = {
            "twitter": ["profile", "recent_tweets"],
            "instagram": ["profile", "recent_posts"],
            "facebook": ["profile", "page_info"],
            "youtube": ["profile", "recent_videos"],
            "tiktok": ["profile", "recent_videos"]
        }
        
        for platform in platforms:
            operations = common_operations.get(platform, [])
            if operations:
                await self.cache.warm_cache(platform, operations, [user_id])
    
    async def invalidate_user_data(self, user_id: int, platforms: Optional[List[str]] = None):
        """
        Invalidate all cached data for a user
        
        Args:
            user_id: User ID to invalidate cache for
            platforms: Specific platforms to invalidate (None for all)
        """
        if platforms:
            for platform in platforms:
                await self.cache.invalidate_user_cache(user_id, platform)
        else:
            await self.cache.invalidate_user_cache(user_id)
        
        logger.info(f"Invalidated cache for user {user_id}")
    
    async def invalidate_platform_data(self, platform: str, operation: Optional[str] = None):
        """
        Invalidate cached data for a platform
        
        Args:
            platform: Platform to invalidate
            operation: Specific operation to invalidate (None for all)
        """
        await self.cache.invalidate_platform_cache(platform, operation)
        logger.info(f"Invalidated {platform} cache{f' for {operation}' if operation else ''}")
    
    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache system health status"""
        return await self.cache.health_check()
    
    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        return await self.cache.get_cache_stats()
    
    async def preload_user_essentials(self, user_id: int):
        """
        Preload essential data for a user session
        
        Args:
            user_id: User ID to preload data for
        """
        # This would implement preloading of commonly accessed data
        # such as user profiles, recent content, and analytics summaries
        
        essential_data = [
            ("twitter", "profile", {"user_id": user_id}),
            ("instagram", "profile", {"user_id": user_id}),
            ("facebook", "profile", {"user_id": user_id}),
            ("youtube", "profile", {"user_id": user_id}),
            ("tiktok", "profile", {"user_id": user_id})
        ]
        
        # Batch check what's already cached
        cache_keys = [(platform, operation, kwargs) for platform, operation, kwargs in essential_data]
        cached_results = await self.cache.batch_get(cache_keys)
        
        # Log what we found in cache
        cached_count = len([k for k, v in cached_results.items() if v is not None])
        total_count = len(essential_data)
        
        logger.info(f"User {user_id} cache preload: {cached_count}/{total_count} items already cached")
        
        return cached_results

# Global cache manager instance
cache_manager = CacheManager()