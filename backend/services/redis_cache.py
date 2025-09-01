"""
Redis-based Caching Service with Intelligent Cache Invalidation
Production-ready Redis implementation for high-performance caching
"""
import asyncio
import json
import logging
import pickle
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from backend.core.config import get_settings
from backend.integrations.performance_optimizer import PerformanceCache

settings = get_settings()
logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"                    # Time-to-live expiration
    MANUAL = "manual"              # Manual invalidation
    WRITE_THROUGH = "write_through" # Invalidate on write
    EVENT_DRIVEN = "event_driven"   # Event-based invalidation

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    avg_response_time: float = 0.0
    hit_ratio: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()
        
        # Calculate hit ratio
        total_requests = self.hits + self.misses
        if total_requests > 0:
            self.hit_ratio = (self.hits / total_requests) * 100

@dataclass
class CacheKey:
    """Structured cache key with metadata"""
    namespace: str
    platform: str
    operation: str
    user_id: Optional[int] = None
    resource_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    def generate(self) -> str:
        """Generate Redis key"""
        components = [self.namespace, self.platform, self.operation]
        
        if self.user_id:
            components.append(f"user:{self.user_id}")
        if self.resource_id:
            components.append(f"resource:{self.resource_id}")
        
        # Add sorted parameters for consistency
        if self.parameters:
            param_str = json.dumps(self.parameters, sort_keys=True)
            components.append(f"params:{hash(param_str)}")
        
        return ":".join(components)

class RedisCache:
    """
    Production-ready Redis cache with intelligent invalidation
    
    Features:
    - Distributed caching with Redis
    - Intelligent cache invalidation strategies
    - Automatic failover to in-memory cache
    - Compression for large objects
    - Batch operations for performance
    - Real-time metrics and monitoring
    - Platform-specific optimizations
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache"""
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.fallback_cache = PerformanceCache(max_size=5000)  # Larger fallback
        self.is_connected = False
        
        # Cache configuration
        self.namespace = "socialmedia_cache"
        self.default_ttl = 300  # 5 minutes
        self.compression_threshold = 1024  # Compress objects > 1KB
        self.batch_size = 100
        
        # Platform-specific TTL settings
        self.platform_ttls = {
            "twitter": {
                "profile": 3600,      # 1 hour
                "tweet": 1800,        # 30 minutes
                "analytics": 900,     # 15 minutes
                "trending": 600       # 10 minutes
            },
            "instagram": {
                "profile": 3600,      # 1 hour
                "post": 1800,         # 30 minutes
                "insights": 1800,     # 30 minutes
                "stories": 3600       # 1 hour
            },
            "facebook": {
                "profile": 7200,      # 2 hours
                "post": 1800,         # 30 minutes
                "insights": 1800,     # 30 minutes
                "page_insights": 3600 # 1 hour
            },
            "youtube": {
                "profile": 7200,      # 2 hours
                "video": 3600,        # 1 hour
                "analytics": 1800     # 30 minutes
            },
            "tiktok": {
                "profile": 3600,      # 1 hour
                "video": 1800,        # 30 minutes
                "analytics": 1800     # 30 minutes
            }
        }
        
        # Metrics tracking
        self.metrics = CacheMetrics()
        
        # Initialize connection will be done lazily when first accessed
        self._connection_initialized = False
        
        logger.info(f"Redis cache initialized: fallback_enabled=True, compression_threshold={self.compression_threshold}")
    
    async def _ensure_connection(self):
        """Ensure Redis connection is initialized"""
        if not self._connection_initialized:
            await self._initialize_connection()
            self._connection_initialized = True
    
    async def _initialize_connection(self):
        """Initialize Redis connection with error handling"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using fallback cache only")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=False,  # We handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
    
    def _get_ttl(self, platform: str, operation: str) -> int:
        """Get TTL for platform and operation"""
        platform_config = self.platform_ttls.get(platform, {})
        return platform_config.get(operation, self.default_ttl)
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data with optional compression"""
        try:
            serialized = pickle.dumps(data)
            
            # Compress if over threshold
            if len(serialized) > self.compression_threshold:
                import gzip
                serialized = gzip.compress(serialized)
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data with compression detection"""
        try:
            # Check if compressed (gzip magic number)
            if data.startswith(b'\x1f\x8b'):
                import gzip
                data = gzip.decompress(data)
            
            return pickle.loads(data)
            
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    def _create_cache_key(
        self,
        platform: str,
        operation: str,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create structured cache key"""
        cache_key = CacheKey(
            namespace=self.namespace,
            platform=platform,
            operation=operation,
            user_id=user_id,
            resource_id=resource_id,
            parameters=kwargs if kwargs else None
        )
        
        return cache_key.generate()
    
    async def get(
        self,
        platform: str,
        operation: str,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            platform: Social media platform
            operation: Cache operation type
            user_id: User ID for user-specific cache
            resource_id: Resource identifier
            **kwargs: Additional parameters
            
        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        key = self._create_cache_key(platform, operation, user_id, resource_id, **kwargs)
        
        try:
            # Ensure connection is initialized
            await self._ensure_connection()
            
            # Try Redis first if connected
            if self.is_connected and self.redis_client:
                try:
                    cached_data = await self.redis_client.get(key)
                    
                    if cached_data:
                        result = self._deserialize_data(cached_data)
                        self.metrics.hits += 1
                        self.metrics.avg_response_time = (time.time() - start_time) * 1000
                        return result
                    
                except Exception as e:
                    logger.warning(f"Redis get error: {e}, falling back to memory cache")
                    self.is_connected = False
            
            # Fallback to in-memory cache
            result = self.fallback_cache.get(platform, operation, user_id=user_id, resource_id=resource_id, **kwargs)
            
            if result:
                self.metrics.hits += 1
            else:
                self.metrics.misses += 1
            
            self.metrics.avg_response_time = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.metrics.misses += 1
            return None
    
    async def set(
        self,
        platform: str,
        operation: str,
        data: Any,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Set cached value
        
        Args:
            platform: Social media platform
            operation: Cache operation type
            data: Data to cache
            user_id: User ID for user-specific cache
            resource_id: Resource identifier
            ttl: Time-to-live override
            **kwargs: Additional parameters
            
        Returns:
            Success status
        """
        key = self._create_cache_key(platform, operation, user_id, resource_id, **kwargs)
        cache_ttl = ttl or self._get_ttl(platform, operation)
        
        try:
            # Try Redis first if connected
            if self.is_connected and self.redis_client:
                try:
                    serialized_data = self._serialize_data(data)
                    await self.redis_client.setex(key, cache_ttl, serialized_data)
                    self.metrics.sets += 1
                    
                    # Also update fallback cache
                    self.fallback_cache.set(platform, operation, data, user_id=user_id, resource_id=resource_id, **kwargs)
                    
                    return True
                    
                except Exception as e:
                    logger.warning(f"Redis set error: {e}, using memory cache only")
                    self.is_connected = False
            
            # Fallback to in-memory cache
            self.fallback_cache.set(platform, operation, data, user_id=user_id, resource_id=resource_id, **kwargs)
            self.metrics.sets += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(
        self,
        platform: str,
        operation: str,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Delete cached value"""
        key = self._create_cache_key(platform, operation, user_id, resource_id, **kwargs)
        
        success = True
        
        try:
            # Delete from Redis if connected
            if self.is_connected and self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")
                    success = False
            
            # Delete from fallback cache (this doesn't have a direct delete method)
            # We'll rely on TTL expiration for the fallback cache
            
            if success:
                self.metrics.deletes += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "socialmedia_cache:twitter:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected or not self.redis_client:
            logger.warning("Redis not connected, cannot invalidate pattern")
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.metrics.deletes += deleted
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0
    
    async def invalidate_user_cache(self, user_id: int, platform: Optional[str] = None) -> int:
        """Invalidate all cache entries for a user"""
        if platform:
            pattern = f"{self.namespace}:{platform}:*:user:{user_id}*"
        else:
            pattern = f"{self.namespace}:*:*:user:{user_id}*"
        
        return await self.invalidate_pattern(pattern)
    
    async def invalidate_platform_cache(self, platform: str, operation: Optional[str] = None) -> int:
        """Invalidate cache entries for a platform"""
        if operation:
            pattern = f"{self.namespace}:{platform}:{operation}:*"
        else:
            pattern = f"{self.namespace}:{platform}:*"
        
        return await self.invalidate_pattern(pattern)
    
    async def batch_get(self, keys: List[Tuple[str, str, dict]]) -> Dict[str, Any]:
        """
        Batch get multiple cache entries
        
        Args:
            keys: List of (platform, operation, kwargs) tuples
            
        Returns:
            Dictionary of results
        """
        results = {}
        
        if self.is_connected and self.redis_client:
            try:
                # Build Redis keys
                redis_keys = []
                key_mapping = {}
                
                for i, (platform, operation, kwargs) in enumerate(keys):
                    redis_key = self._create_cache_key(platform, operation, **kwargs)
                    redis_keys.append(redis_key)
                    key_mapping[redis_key] = i
                
                # Batch get from Redis
                cached_values = await self.redis_client.mget(redis_keys)
                
                for redis_key, cached_data in zip(redis_keys, cached_values):
                    if cached_data:
                        index = key_mapping[redis_key]
                        platform, operation, kwargs = keys[index]
                        
                        try:
                            results[f"{platform}:{operation}"] = self._deserialize_data(cached_data)
                            self.metrics.hits += 1
                        except Exception as e:
                            logger.error(f"Batch get deserialization error: {e}")
                            self.metrics.misses += 1
                    else:
                        self.metrics.misses += 1
                
                return results
                
            except Exception as e:
                logger.warning(f"Batch get error: {e}, falling back to individual gets")
        
        # Fallback to individual gets
        for platform, operation, kwargs in keys:
            result = await self.get(platform, operation, **kwargs)
            if result is not None:
                results[f"{platform}:{operation}"] = result
        
        return results
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = asdict(self.metrics)
        
        # Add Redis-specific stats if connected
        if self.is_connected and self.redis_client:
            try:
                redis_info = await self.redis_client.info('memory')
                stats.update({
                    "redis_memory_used": redis_info.get('used_memory', 0),
                    "redis_memory_peak": redis_info.get('used_memory_peak', 0),
                    "redis_connected": True
                })
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
                stats["redis_connected"] = False
        else:
            stats["redis_connected"] = False
        
        # Add fallback cache stats
        fallback_stats = self.fallback_cache.get_stats()
        stats["fallback_cache"] = fallback_stats
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache systems"""
        health = {
            "redis_connected": False,
            "fallback_cache_available": True,
            "total_operations": self.metrics.hits + self.metrics.misses,
            "hit_ratio": self.metrics.hit_ratio,
            "status": "degraded"  # Will be updated based on checks
        }
        
        # Check Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis_connected"] = True
                health["status"] = "healthy"
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                health["redis_error"] = str(e)
        
        # If Redis is down but fallback works, status is degraded
        if not health["redis_connected"] and health["fallback_cache_available"]:
            health["status"] = "degraded"
        elif not health["redis_connected"] and not health["fallback_cache_available"]:
            health["status"] = "unhealthy"
        
        return health
    
    async def warm_cache(self, platform: str, operations: List[str], user_ids: List[int]):
        """
        Warm cache with common data
        
        Args:
            platform: Platform to warm cache for
            operations: List of operations to pre-cache
            user_ids: List of user IDs to pre-cache data for
        """
        logger.info(f"Starting cache warming for {platform}: {len(operations)} operations, {len(user_ids)} users")
        
        # This would be implemented based on specific platform clients
        # For now, we'll create placeholder entries to demonstrate the concept
        
        for user_id in user_ids:
            for operation in operations:
                # In a real implementation, you would call the actual API here
                # and cache the results
                cache_key = f"warm_cache_placeholder_{platform}_{operation}_{user_id}"
                await self.set(platform, operation, {"warmed": True, "timestamp": datetime.utcnow().isoformat()}, user_id=user_id)
        
        logger.info(f"Cache warming completed for {platform}")
    
    async def close(self):
        """Close Redis connection gracefully"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

# Global Redis cache instance
redis_cache = RedisCache()