"""
Centralized API Quota Management and Rate Limiting Service
Production-ready service for managing API quotas across all social media platforms
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

from backend.core.config import get_settings, get_utc_now
from backend.integrations.performance_optimizer import RateLimiter, PerformanceOptimizer
from backend.integrations.twitter_client import twitter_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client
# LinkedIn integration removed - using stub
linkedin_client = None
# TikTok integration removed - using stub
tiktok_client = None

settings = get_settings()
logger = logging.getLogger(__name__)

class QuotaStatus(Enum):
    """Quota utilization status levels"""
    NORMAL = "normal"        # < 70% utilization
    WARNING = "warning"      # 70-90% utilization
    CRITICAL = "critical"    # 90-100% utilization
    EXCEEDED = "exceeded"    # > 100% utilization

@dataclass
class PlatformQuota:
    """Platform-specific quota information"""
    platform: str
    current_usage: int
    quota_limit: int
    time_window: int  # seconds
    reset_time: datetime
    utilization_percent: float
    status: QuotaStatus
    burst_available: int = 0
    
    def __post_init__(self):
        if self.utilization_percent is None:
            self.utilization_percent = (self.current_usage / self.quota_limit) * 100 if self.quota_limit > 0 else 0
        
        # Determine status based on utilization
        if self.utilization_percent >= 100:
            self.status = QuotaStatus.EXCEEDED
        elif self.utilization_percent >= 90:
            self.status = QuotaStatus.CRITICAL
        elif self.utilization_percent >= 70:
            self.status = QuotaStatus.WARNING
        else:
            self.status = QuotaStatus.NORMAL

@dataclass
class QuotaManagerStats:
    """Statistics for quota management system"""
    total_requests_today: int
    requests_blocked: int
    quota_resets_today: int
    platforms_monitored: int
    average_utilization: float
    critical_platforms: List[str]
    last_updated: datetime

class QuotaManager:
    """
    Centralized quota management for all social media platforms
    
    Features:
    - Real-time quota monitoring
    - Proactive quota management
    - Intelligent request scheduling
    - Automatic quota recovery
    - Cross-platform optimization
    - Production monitoring and alerting
    """
    
    def __init__(self):
        """Initialize quota manager"""
        self.rate_limiter = RateLimiter()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Platform-specific quota configurations
        self.platform_configs = {
            "twitter": {
                "base_quota": 300,        # requests per 15 minutes
                "window_seconds": 900,    # 15 minutes
                "critical_threshold": 270, # 90% utilization
                "warning_threshold": 210   # 70% utilization
            },
            "instagram": {
                "base_quota": 200,        # requests per hour
                "window_seconds": 3600,   # 1 hour
                "critical_threshold": 180,
                "warning_threshold": 140
            },
            "facebook": {
                "base_quota": 600,        # requests per 10 minutes
                "window_seconds": 600,    # 10 minutes
                "critical_threshold": 540,
                "warning_threshold": 420
            },
            "linkedin": {
                "base_quota": 100,        # requests per hour
                "window_seconds": 3600,   # 1 hour
                "critical_threshold": 90,
                "warning_threshold": 70
            },
            "tiktok": {
                "base_quota": 10,         # requests per day (very strict)
                "window_seconds": 86400,  # 24 hours
                "critical_threshold": 9,
                "warning_threshold": 7
            }
        }
        
        self.quota_cache = {}
        self.last_check = {}
        self.blocked_requests = 0
        
        logger.info("Quota manager initialized with production-ready rate limiting")
    
    async def check_quota_availability(
        self,
        platform: str,
        operation: str = "default",
        user_id: Optional[int] = None
    ) -> Tuple[bool, PlatformQuota]:
        """
        Check if request can proceed within quota limits
        
        Args:
            platform: Social media platform
            operation: Type of operation
            user_id: User ID (for user-specific quotas)
            
        Returns:
            Tuple of (can_proceed, quota_info)
        """
        try:
            # Get current quota status
            quota_info = await self.get_platform_quota(platform, user_id)
            
            # Check rate limiter first
            can_proceed_rate = await self.rate_limiter.acquire(platform, operation)
            
            if not can_proceed_rate:
                logger.warning(f"Rate limited: {platform} - {operation}")
                return False, quota_info
            
            # Check quota utilization
            if quota_info.status == QuotaStatus.EXCEEDED:
                logger.error(f"Quota exceeded: {platform} - {quota_info.utilization_percent:.1f}%")
                self.blocked_requests += 1
                return False, quota_info
            
            elif quota_info.status == QuotaStatus.CRITICAL:
                # Allow but log warning
                logger.warning(f"Critical quota usage: {platform} - {quota_info.utilization_percent:.1f}%")
                return True, quota_info
            
            elif quota_info.status == QuotaStatus.WARNING:
                # Allow but track usage
                logger.info(f"High quota usage: {platform} - {quota_info.utilization_percent:.1f}%")
                return True, quota_info
            
            # Normal usage
            return True, quota_info
            
        except Exception as e:
            logger.error(f"Error checking quota availability for {platform}: {e}")
            # Fail safe - allow request but log error
            return True, await self.get_default_quota(platform)
    
    async def get_platform_quota(
        self,
        platform: str,
        user_id: Optional[int] = None
    ) -> PlatformQuota:
        """
        Get current quota status for platform
        
        Args:
            platform: Social media platform
            user_id: User ID for user-specific quotas
            
        Returns:
            Platform quota information
        """
        try:
            # Check cache first
            cache_key = f"{platform}_{user_id or 'global'}"
            if cache_key in self.quota_cache:
                cached_quota = self.quota_cache[cache_key]
                if get_utc_now() < cached_quota.reset_time:
                    return cached_quota
            
            # Get platform-specific quota
            if platform == "instagram" and user_id:
                quota_info = await self._get_instagram_quota(user_id)
            elif platform == "facebook" and user_id:
                quota_info = await self._get_facebook_quota(user_id)
            else:
                # Use rate limiter stats for other platforms
                quota_info = await self._get_rate_limiter_quota(platform)
            
            # Cache the result
            self.quota_cache[cache_key] = quota_info
            
            return quota_info
            
        except Exception as e:
            logger.error(f"Error getting platform quota for {platform}: {e}")
            return await self.get_default_quota(platform)
    
    async def _get_instagram_quota(self, user_id: int) -> PlatformQuota:
        """Get Instagram-specific quota using Graph API"""
        try:
            access_token = await instagram_client.get_user_token(user_id)
            if not access_token:
                return await self.get_default_quota("instagram")
            
            # Get Instagram Business Account ID
            pages = await instagram_client.get_facebook_pages(access_token)
            ig_account_id = None
            
            for page in pages:
                if "instagram_business_account" in page:
                    ig_account_id = page["instagram_business_account"]["id"]
                    break
            
            if not ig_account_id:
                return await self.get_default_quota("instagram")
            
            # Check publishing limits
            limit_info = await instagram_client.check_publishing_limit(access_token, ig_account_id)
            
            current_usage = limit_info.get("quota_usage", 0)
            quota_limit = limit_info.get("quota_total", 25)
            time_window = limit_info.get("quota_duration", 3600)
            
            return PlatformQuota(
                platform="instagram",
                current_usage=current_usage,
                quota_limit=quota_limit,
                time_window=time_window,
                reset_time=get_utc_now() + timedelta(seconds=time_window),
                utilization_percent=(current_usage / quota_limit) * 100 if quota_limit > 0 else 0,
                status=QuotaStatus.NORMAL  # Will be calculated in __post_init__
            )
            
        except Exception as e:
            logger.error(f"Error getting Instagram quota: {e}")
            return await self.get_default_quota("instagram")
    
    async def _get_facebook_quota(self, user_id: int) -> PlatformQuota:
        """Get Facebook-specific quota using Graph API"""
        try:
            access_token = await facebook_client.get_user_token(user_id)
            if not access_token:
                return await self.get_default_quota("facebook")
            
            # Facebook doesn't provide as detailed quota info as Instagram
            # Use rate limiter stats as approximation
            return await self._get_rate_limiter_quota("facebook")
            
        except Exception as e:
            logger.error(f"Error getting Facebook quota: {e}")
            return await self.get_default_quota("facebook")
    
    async def _get_rate_limiter_quota(self, platform: str) -> PlatformQuota:
        """Get quota info from rate limiter statistics"""
        stats = self.rate_limiter.get_stats()
        platform_stats = stats.get(platform, {})
        
        config = self.platform_configs.get(platform, {})
        
        current_usage = platform_stats.get("current_requests", 0)
        quota_limit = config.get("base_quota", 100)
        time_window = config.get("window_seconds", 3600)
        burst_available = platform_stats.get("burst_tokens_remaining", 0)
        
        return PlatformQuota(
            platform=platform,
            current_usage=current_usage,
            quota_limit=quota_limit,
            time_window=time_window,
            reset_time=get_utc_now() + timedelta(seconds=time_window),
            utilization_percent=platform_stats.get("utilization", 0),
            status=QuotaStatus.NORMAL,  # Will be calculated in __post_init__
            burst_available=burst_available
        )
    
    async def get_default_quota(self, platform: str) -> PlatformQuota:
        """Get default quota information for platform"""
        config = self.platform_configs.get(platform, {})
        
        return PlatformQuota(
            platform=platform,
            current_usage=0,
            quota_limit=config.get("base_quota", 100),
            time_window=config.get("window_seconds", 3600),
            reset_time=get_utc_now() + timedelta(seconds=config.get("window_seconds", 3600)),
            utilization_percent=0,
            status=QuotaStatus.NORMAL
        )
    
    async def get_all_platform_quotas(self, user_id: Optional[int] = None) -> Dict[str, PlatformQuota]:
        """
        Get quota status for all platforms
        
        Args:
            user_id: User ID for user-specific quotas
            
        Returns:
            Dictionary of platform quotas
        """
        quotas = {}
        
        for platform in self.platform_configs.keys():
            try:
                quotas[platform] = await self.get_platform_quota(platform, user_id)
            except Exception as e:
                logger.error(f"Error getting quota for {platform}: {e}")
                quotas[platform] = await self.get_default_quota(platform)
        
        return quotas
    
    async def optimize_request_scheduling(
        self,
        requests: List[Dict[str, Any]],
        max_delay: int = 3600
    ) -> List[Dict[str, Any]]:
        """
        Optimize request scheduling to avoid quota exhaustion
        
        Args:
            requests: List of pending requests
            max_delay: Maximum delay in seconds
            
        Returns:
            Optimized request schedule
        """
        optimized_schedule = []
        current_time = get_utc_now()
        
        # Group requests by platform
        platform_requests = {}
        for request in requests:
            platform = request.get("platform", "unknown")
            if platform not in platform_requests:
                platform_requests[platform] = []
            platform_requests[platform].append(request)
        
        # Schedule requests for each platform
        for platform, platform_reqs in platform_requests.items():
            quota = await self.get_platform_quota(platform)
            
            if quota.status in [QuotaStatus.CRITICAL, QuotaStatus.EXCEEDED]:
                # Delay requests until quota resets
                delay_seconds = (quota.reset_time - current_time).total_seconds()
                delay_seconds = min(delay_seconds, max_delay)
                
                for req in platform_reqs:
                    req["scheduled_time"] = current_time + timedelta(seconds=delay_seconds)
                    req["delay_reason"] = f"Quota {quota.status.value} ({quota.utilization_percent:.1f}%)"
                    optimized_schedule.append(req)
            
            else:
                # Schedule with minimal delays
                for i, req in enumerate(platform_reqs):
                    # Spread requests to avoid burst limits
                    delay = i * 2  # 2-second intervals
                    req["scheduled_time"] = current_time + timedelta(seconds=delay)
                    req["delay_reason"] = "Optimized scheduling"
                    optimized_schedule.append(req)
        
        # Sort by scheduled time
        optimized_schedule.sort(key=lambda x: x["scheduled_time"])
        
        return optimized_schedule
    
    async def get_quota_stats(self) -> QuotaManagerStats:
        """Get comprehensive quota management statistics"""
        all_quotas = await self.get_all_platform_quotas()
        
        total_utilization = sum(quota.utilization_percent for quota in all_quotas.values())
        average_utilization = total_utilization / len(all_quotas) if all_quotas else 0
        
        critical_platforms = [
            platform for platform, quota in all_quotas.items()
            if quota.status in [QuotaStatus.CRITICAL, QuotaStatus.EXCEEDED]
        ]
        
        return QuotaManagerStats(
            total_requests_today=sum(quota.current_usage for quota in all_quotas.values()),
            requests_blocked=self.blocked_requests,
            quota_resets_today=0,  # Would need tracking
            platforms_monitored=len(all_quotas),
            average_utilization=round(average_utilization, 1),
            critical_platforms=critical_platforms,
            last_updated=get_utc_now()
        )
    
    async def reset_quota_cache(self, platform: Optional[str] = None):
        """Reset quota cache for platform or all platforms"""
        if platform:
            keys_to_remove = [key for key in self.quota_cache.keys() if key.startswith(platform)]
            for key in keys_to_remove:
                del self.quota_cache[key]
        else:
            self.quota_cache.clear()
        
        logger.info(f"Quota cache reset for {'all platforms' if not platform else platform}")

# Global quota manager instance
quota_manager = QuotaManager()