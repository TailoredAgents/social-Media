"""
Social Media Integration Performance Optimizer
Provides caching, connection pooling, and performance enhancements for all integrations
"""
import asyncio
import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from functools import wraps
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with expiration and metadata"""
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    platform: str = ""
    operation: str = ""

class PerformanceCache:
    """
    High-performance cache for social media API responses
    Implements LRU eviction with TTL and intelligent cache warming
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize performance cache
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_times: Dict[str, float] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "cache_size": 0
        }
        
        # Platform-specific TTL overrides
        self.ttl_overrides = {
            "twitter_profile": 3600,  # 1 hour
            "twitter_analytics": 1800,  # 30 minutes
            "linkedin_profile": 7200,  # 2 hours
            "linkedin_posts": 1800,
            "instagram_profile": 3600,
            "instagram_insights": 1800,
            "facebook_profile": 7200,
            "facebook_insights": 1800
        }
        
        logger.info(f"Performance cache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, platform: str, operation: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_data = {
            "platform": platform,
            "operation": operation,
            **kwargs
        }
        
        # Sort for consistent hashing
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_ttl(self, platform: str, operation: str) -> int:
        """Get TTL for specific platform and operation"""
        cache_key = f"{platform}_{operation}"
        return self.ttl_overrides.get(cache_key, self.default_ttl)
    
    def _evict_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.expires_at <= now
        ]
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        
        if expired_keys:
            logger.info(f"Evicted {len(expired_keys)} expired cache entries")
            self.stats["evictions"] += len(expired_keys)
    
    def _evict_lru(self):
        """Evict least recently used entries when cache is full"""
        if len(self.cache) <= self.max_size:
            return
        
        # Sort by access time and remove oldest entries
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        keys_to_remove = [key for key, _ in sorted_keys[:len(self.cache) - self.max_size + 1]]
        
        for key in keys_to_remove:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        
        if keys_to_remove:
            logger.info(f"LRU evicted {len(keys_to_remove)} cache entries")
            self.stats["evictions"] += len(keys_to_remove)
    
    def get(self, platform: str, operation: str, **kwargs) -> Optional[Any]:
        """Get cached value if available and not expired"""
        key = self._generate_key(platform, operation, **kwargs)
        self.stats["total_requests"] += 1
        
        # Clean expired entries periodically
        if self.stats["total_requests"] % 100 == 0:
            self._evict_expired()
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.expires_at <= datetime.utcnow():
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            self.stats["misses"] += 1
            return None
        
        # Update access time and hit count
        self.access_times[key] = time.time()
        entry.hit_count += 1
        self.stats["hits"] += 1
        
        # Cache hit logged at trace level for performance
        return entry.data
    
    def set(self, platform: str, operation: str, data: Any, **kwargs):
        """Set cached value with appropriate TTL"""
        key = self._generate_key(platform, operation, **kwargs)
        ttl = self._get_ttl(platform, operation)
        
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl)
        
        entry = CacheEntry(
            data=data,
            created_at=now,
            expires_at=expires_at,
            platform=platform,
            operation=operation
        )
        
        self.cache[key] = entry
        self.access_times[key] = time.time()
        
        # Evict if cache is full
        self._evict_lru()
        
        self.stats["cache_size"] = len(self.cache)
        # Cache set logged at trace level for performance
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        self.stats["cache_size"] = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (self.stats["hits"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "memory_usage": len(self.cache),
            "max_size": self.max_size
        }
    
    def warm_cache(self, platform: str, operation: str, data: Any, **kwargs):
        """Warm cache with pre-computed data"""
        self.set(platform, operation, data, **kwargs)
        logger.info(f"Cache warmed: {platform}_{operation}")

class ConnectionPool:
    """
    HTTP connection pool manager for social media APIs
    Provides connection reuse and rate limiting coordination
    """
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        """
        Initialize connection pool
        
        Args:
            max_connections: Maximum total connections
            max_keepalive: Maximum keepalive connections per host
        """
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.pools: Dict[str, Any] = {}
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "connection_reuse": 0,
            "connection_timeouts": 0
        }
        
        logger.info(f"Connection pool initialized: max_connections={max_connections}")
    
    async def get_client(self, platform: str, timeout: int = 30):
        """Get optimized HTTP client for platform"""
        import httpx
        
        if platform not in self.pools:
            limits = httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_keepalive
            )
            
            timeout_config = httpx.Timeout(timeout)
            
            self.pools[platform] = httpx.AsyncClient(
                limits=limits,
                timeout=timeout_config,
                http2=True  # Enable HTTP/2 for better performance
            )
            
            logger.info(f"Created new connection pool for {platform}")
        
        return self.pools[platform]
    
    async def close_all(self):
        """Close all connection pools"""
        for platform, client in self.pools.items():
            await client.aclose()
            logger.info(f"Closed connection pool for {platform}")
        
        self.pools.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            **self.connection_stats,
            "active_pools": len(self.pools)
        }

class RateLimiter:
    """
    Advanced rate limiter with platform-specific limits and burst handling
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        self.limits = {
            "twitter": {"requests": 300, "window": 900, "burst": 50},
            "linkedin": {"requests": 100, "window": 3600, "burst": 20},
            "instagram": {"requests": 200, "window": 3600, "burst": 25},
            "facebook": {"requests": 600, "window": 600, "burst": 100}
        }
        
        self.request_history: Dict[str, list] = {}
        self.burst_tokens: Dict[str, int] = {}
        
        # Initialize burst tokens
        for platform in self.limits:
            self.burst_tokens[platform] = self.limits[platform]["burst"]
        
        logger.info("Rate limiter initialized with platform-specific limits")
    
    async def acquire(self, platform: str, operation: str = "default") -> bool:
        """
        Acquire rate limit token
        
        Args:
            platform: Social media platform
            operation: Specific operation type
            
        Returns:
            True if request can proceed, False if rate limited
        """
        if platform not in self.limits:
            return True  # Allow unknown platforms
        
        now = time.time()
        key = f"{platform}_{operation}"
        
        # Initialize history if needed
        if key not in self.request_history:
            self.request_history[key] = []
        
        # Clean old requests outside window
        window = self.limits[platform]["window"]
        cutoff = now - window
        self.request_history[key] = [
            req_time for req_time in self.request_history[key]
            if req_time > cutoff
        ]
        
        # Check if under limit
        current_requests = len(self.request_history[key])
        max_requests = self.limits[platform]["requests"]
        
        if current_requests < max_requests:
            self.request_history[key].append(now)
            return True
        
        # Check burst tokens
        if self.burst_tokens[platform] > 0:
            self.burst_tokens[platform] -= 1
            self.request_history[key].append(now)
            logger.warning(f"Used burst token for {platform} (remaining: {self.burst_tokens[platform]})")
            return True
        
        # Rate limited
        wait_time = min(self.request_history[key]) + window - now
        logger.warning(f"Rate limited for {platform}: wait {wait_time:.1f}s")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        stats = {}
        for platform in self.limits:
            current_requests = len(self.request_history.get(f"{platform}_default", []))
            max_requests = self.limits[platform]["requests"]
            burst_remaining = self.burst_tokens[platform]
            
            stats[platform] = {
                "current_requests": current_requests,
                "max_requests": max_requests,
                "utilization": round((current_requests / max_requests) * 100, 1),
                "burst_tokens_remaining": burst_remaining
            }
        
        return stats

class PerformanceOptimizer:
    """
    Main performance optimizer combining caching, connection pooling, and rate limiting
    """
    
    def __init__(self, cache_size: int = 1000, max_connections: int = 100):
        """Initialize performance optimizer"""
        self.cache = PerformanceCache(max_size=cache_size)
        self.connection_pool = ConnectionPool(max_connections=max_connections)
        self.rate_limiter = RateLimiter()
        
        # Performance metrics
        self.metrics = {
            "requests_total": 0,
            "requests_cached": 0,
            "requests_rate_limited": 0,
            "average_response_time": 0,
            "response_times": []
        }
        
        logger.info("Performance optimizer initialized")
    
    def cached_request(self, platform: str, operation: str, cache_ttl: Optional[int] = None):
        """
        Decorator for caching API requests
        
        Args:
            platform: Social media platform
            operation: API operation name
            cache_ttl: Custom cache TTL (optional)
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_key_data = {
                    "args": [str(arg) for arg in args if not hasattr(arg, '__dict__')],
                    "kwargs": {k: str(v) for k, v in kwargs.items() if not callable(v)}
                }
                
                # Check cache first
                cached_result = self.cache.get(platform, operation, **cache_key_data)
                if cached_result is not None:
                    self.metrics["requests_cached"] += 1
                    return cached_result
                
                # Check rate limit
                if not await self.rate_limiter.acquire(platform, operation):
                    self.metrics["requests_rate_limited"] += 1
                    raise Exception(f"Rate limited for {platform} {operation}")
                
                # Execute request with timing
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    
                    # Cache successful result
                    if cache_ttl:
                        # Custom TTL override
                        original_ttl = self.cache.ttl_overrides.get(f"{platform}_{operation}")
                        self.cache.ttl_overrides[f"{platform}_{operation}"] = cache_ttl
                        self.cache.set(platform, operation, result, **cache_key_data)
                        if original_ttl:
                            self.cache.ttl_overrides[f"{platform}_{operation}"] = original_ttl
                    else:
                        self.cache.set(platform, operation, result, **cache_key_data)
                    
                    return result
                
                finally:
                    # Record metrics
                    response_time = time.time() - start_time
                    self.metrics["requests_total"] += 1
                    self.metrics["response_times"].append(response_time)
                    
                    # Keep only last 1000 response times for average calculation
                    if len(self.metrics["response_times"]) > 1000:
                        self.metrics["response_times"] = self.metrics["response_times"][-1000:]
                    
                    self.metrics["average_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            
            return wrapper
        return decorator
    
    async def batch_request(self, requests: list, max_concurrent: int = 10) -> list:
        """
        Execute multiple requests concurrently with rate limiting
        
        Args:
            requests: List of (function, args, kwargs) tuples
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of results in same order as requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_request(func, args, kwargs):
            async with semaphore:
                return await func(*args, **kwargs)
        
        tasks = [
            execute_request(func, args, kwargs)
            for func, args, kwargs in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Batch executed {len(requests)} requests with max_concurrent={max_concurrent}")
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.cache.get_stats()
        connection_stats = self.connection_pool.get_stats()
        rate_limiter_stats = self.rate_limiter.get_stats()
        
        return {
            "cache": cache_stats,
            "connections": connection_stats,
            "rate_limiting": rate_limiter_stats,
            "performance": self.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "cache": "healthy" if len(self.cache.cache) < self.cache.max_size * 0.9 else "near_capacity",
            "connections": "healthy" if len(self.connection_pool.pools) < 10 else "high_usage",
            "rate_limiting": "healthy",
            "overall": "healthy"
        }
        
        # Check if any platform is heavily rate limited
        rate_stats = self.rate_limiter.get_stats()
        for platform, stats in rate_stats.items():
            if stats["utilization"] > 90:
                health_status["rate_limiting"] = "warning"
                health_status["overall"] = "warning"
        
        return health_status
    
    async def cleanup(self):
        """Clean up resources"""
        await self.connection_pool.close_all()
        self.cache.clear()
        logger.info("Performance optimizer cleaned up")

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorator shortcuts for common use cases
def cached_twitter_request(operation: str, cache_ttl: Optional[int] = None):
    """Decorator for cached Twitter requests"""
    return performance_optimizer.cached_request("twitter", operation, cache_ttl)

def cached_linkedin_request(operation: str, cache_ttl: Optional[int] = None):
    """Decorator for cached LinkedIn requests"""
    return performance_optimizer.cached_request("linkedin", operation, cache_ttl)

def cached_instagram_request(operation: str, cache_ttl: Optional[int] = None):
    """Decorator for cached Instagram requests"""
    return performance_optimizer.cached_request("instagram", operation, cache_ttl)

def cached_facebook_request(operation: str, cache_ttl: Optional[int] = None):
    """Decorator for cached Facebook requests"""
    return performance_optimizer.cached_request("facebook", operation, cache_ttl)

