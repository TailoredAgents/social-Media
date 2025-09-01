"""
Unified Meta Graph API Client for Facebook and Instagram (2025)

This client uses the unified Meta Graph API v22.0 to handle both Facebook and Instagram
through a single integration point, replacing separate Facebook/Instagram clients.
"""
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MetaGraphAPIClient:
    """
    Unified Meta Graph API client for Facebook and Instagram integration.
    
    Based on Meta Graph API v22.0 (2025) unified approach.
    Handles both Facebook Pages and Instagram Business accounts.
    """
    
    def __init__(self):
        self.app_id = settings.meta_app_id
        self.app_secret = settings.meta_app_secret  
        self.access_token = settings.meta_access_token
        self.api_version = settings.meta_api_version or "v22.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # Platform-specific IDs
        self.facebook_page_id = settings.facebook_page_id
        self.facebook_page_token = settings.facebook_page_access_token
        self.instagram_business_id = settings.instagram_business_account_id
        
        logger.info(f"Meta Graph API client initialized (v{self.api_version})")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                           params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Meta Graph API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add access token to params
        if not params:
            params = {}
        params['access_token'] = self.access_token
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(url, params=params) as response:
                        result = await response.json()
                else:
                    async with session.request(method, url, params=params, data=data) as response:
                        result = await response.json()
                
                # Check for API errors
                if 'error' in result:
                    error_msg = result['error'].get('message', 'Unknown API error')
                    logger.error(f"Meta API error: {error_msg}")
                    raise Exception(f"Meta API error: {error_msg}")
                
                return result
                
        except Exception as e:
            logger.error(f"Meta API request failed: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    # FACEBOOK METHODS
    async def get_facebook_page_info(self) -> Dict[str, Any]:
        """Get Facebook page information"""
        if not self.facebook_page_id:
            return {"error": "Facebook page ID not configured", "status": "failed"}
        
        fields = "id,name,username,followers_count,fan_count,about,website,category"
        result = await self._make_request('GET', f"/{self.facebook_page_id}", 
                                         params={'fields': fields})
        
        if 'error' not in result:
            result['platform'] = 'facebook'
            result['status'] = 'success'
        
        return result
    
    async def post_to_facebook(self, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Post content to Facebook page"""
        if not self.facebook_page_id or not self.facebook_page_token:
            return {"error": "Facebook page credentials not configured", "status": "failed"}
        
        data = {
            'message': content,
            'access_token': self.facebook_page_token
        }
        
        if image_url:
            data['link'] = image_url
        
        result = await self._make_request('POST', f"/{self.facebook_page_id}/feed", data=data)
        
        if 'error' not in result:
            result['platform'] = 'facebook'
            result['status'] = 'success'
            result['post_url'] = f"https://www.facebook.com/{result.get('id', '')}"
        
        return result
    
    # INSTAGRAM METHODS
    async def get_instagram_account_info(self) -> Dict[str, Any]:
        """Get Instagram business account information"""
        if not self.instagram_business_id:
            return {"error": "Instagram business account ID not configured", "status": "failed"}
        
        fields = "id,username,followers_count,follows_count,media_count,profile_picture_url,biography"
        result = await self._make_request('GET', f"/{self.instagram_business_id}", 
                                         params={'fields': fields})
        
        if 'error' not in result:
            result['platform'] = 'instagram'
            result['status'] = 'success'
        
        return result
    
    async def post_to_instagram(self, content: str, image_url: str) -> Dict[str, Any]:
        """
        Post content to Instagram (requires image)
        Instagram posts always require media via Graph API
        """
        if not self.instagram_business_id:
            return {"error": "Instagram business account ID not configured", "status": "failed"}
        
        if not image_url:
            return {"error": "Instagram posts require an image", "status": "failed"}
        
        try:
            # Step 1: Create media container
            container_data = {
                'image_url': image_url,
                'caption': content,
                'access_token': self.access_token
            }
            
            container_result = await self._make_request('POST', 
                f"/{self.instagram_business_id}/media", data=container_data)
            
            if 'error' in container_result:
                return container_result
            
            container_id = container_result.get('id')
            if not container_id:
                return {"error": "Failed to create media container", "status": "failed"}
            
            # Step 2: Publish the media
            publish_data = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            result = await self._make_request('POST', 
                f"/{self.instagram_business_id}/media_publish", data=publish_data)
            
            if 'error' not in result:
                result['platform'] = 'instagram'
                result['status'] = 'success'
                result['post_url'] = f"https://www.instagram.com/p/{result.get('id', '')}"
            
            return result
            
        except Exception as e:
            logger.error(f"Instagram posting failed: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    # UNIFIED METHODS
    async def get_platform_info(self, platform: str) -> Dict[str, Any]:
        """Get platform information (unified method)"""
        if platform.lower() == 'facebook':
            return await self.get_facebook_page_info()
        elif platform.lower() == 'instagram':
            return await self.get_instagram_account_info()
        else:
            return {"error": f"Platform '{platform}' not supported", "status": "failed"}
    
    async def post_content(self, platform: str, content: str, 
                          image_url: Optional[str] = None) -> Dict[str, Any]:
        """Post content to specified platform (unified method)"""
        if platform.lower() == 'facebook':
            return await self.post_to_facebook(content, image_url)
        elif platform.lower() == 'instagram':
            if not image_url:
                return {"error": "Instagram requires an image", "status": "failed"}
            return await self.post_to_instagram(content, image_url)
        else:
            return {"error": f"Platform '{platform}' not supported", "status": "failed"}
    
    async def get_insights(self, platform: str, metric: str = 'impressions',
                          period: str = 'day') -> Dict[str, Any]:
        """Get insights/analytics for platform"""
        try:
            if platform.lower() == 'facebook':
                endpoint = f"/{self.facebook_page_id}/insights/{metric}"
                params = {'period': period}
            elif platform.lower() == 'instagram':
                endpoint = f"/{self.instagram_business_id}/insights"  
                params = {'metric': metric, 'period': period}
            else:
                return {"error": f"Platform '{platform}' not supported", "status": "failed"}
            
            result = await self._make_request('GET', endpoint, params=params)
            
            if 'error' not in result:
                result['platform'] = platform
                result['status'] = 'success'
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get insights for {platform}: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Meta Graph API connection and permissions"""
        try:
            # Test basic API access
            me_result = await self._make_request('GET', '/me', params={'fields': 'id,name'})
            
            if 'error' in me_result:
                return {
                    "status": "failed",
                    "error": "Basic API access failed",
                    "details": me_result
                }
            
            # Test platform access
            platforms = {}
            
            if self.facebook_page_id:
                fb_result = await self.get_facebook_page_info()
                platforms['facebook'] = fb_result.get('status', 'unknown')
            
            if self.instagram_business_id:
                ig_result = await self.get_instagram_account_info()
                platforms['instagram'] = ig_result.get('status', 'unknown')
            
            return {
                "status": "success",
                "api_version": self.api_version,
                "user": me_result,
                "platforms": platforms,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Meta API connection test failed: {str(e)}")
            return {
                "status": "failed", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global instance
meta_client = MetaGraphAPIClient()