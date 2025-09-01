"""
Facebook Graph API Integration Client (Updated for Meta Graph API v22.0)
Integration Specialist Component - Complete Facebook API integration for comprehensive social content

UPDATED 2025: Now uses unified Meta Graph API configuration.
Uses meta_app_id, meta_app_secret, and meta_access_token from settings.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import json
import httpx
from dataclasses import dataclass
from enum import Enum

from backend.core.config import get_settings
from backend.auth.social_oauth import oauth_manager

settings = get_settings()
logger = logging.getLogger(__name__)

class FacebookPostType(Enum):
    """Facebook post types"""
    STATUS = "status"
    PHOTO = "photo"
    VIDEO = "video"
    LINK = "link"
    EVENT = "event"
    POLL = "poll"

@dataclass
class FacebookPost:
    """Facebook post data structure"""
    id: str
    message: str
    story: str
    created_time: datetime
    updated_time: datetime
    from_user: Dict[str, Any]
    privacy: Dict[str, str]
    status_type: str
    type: str
    link: Optional[str] = None
    picture: Optional[str] = None
    full_picture: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = None
    reactions: Optional[Dict[str, int]] = None
    comments_count: int = 0
    shares_count: int = 0

@dataclass
class FacebookPage:
    """Facebook page data structure"""
    id: str
    name: str
    about: str
    category: str
    followers_count: int
    fan_count: int
    picture_url: str
    cover_photo_url: str
    website: str
    phone: str
    location: Dict[str, Any]
    hours: Dict[str, Any]
    is_verified: bool
    can_post: bool
    access_token: str

@dataclass
class FacebookInsights:
    """Facebook insights data structure"""
    post_id: str
    impressions: int
    reach: int
    engagement: int
    reactions: int
    comments: int
    shares: int
    clicks: int
    fetched_at: datetime
    video_views: Optional[int] = None
    story_completions: Optional[int] = None
    post_consumptions: int = 0
    post_engaged_users: int = 0
    negative_feedback: int = 0

@dataclass
class FacebookEvent:
    """Facebook event data structure"""
    id: str
    name: str
    description: str
    start_time: datetime
    end_time: Optional[datetime]
    location: str
    attending_count: int
    interested_count: int
    maybe_count: int
    cover_photo_url: str
    event_url: str
    is_online: bool

class FacebookAPIClient:
    """
    Facebook Graph API Client with comprehensive posting and analytics capabilities
    
    Features:
    - Text, photo, and video posting
    - Page management
    - Event creation and management
    - Poll creation
    - Link sharing with previews
    - Comprehensive insights and analytics
    - Comment and reaction management
    - Story posting
    - Live video streaming
    """
    
    def __init__(self):
        """Initialize Facebook API client with unified Meta Graph API v22.0"""
        # Use unified Meta configuration (2025 approach)
        self.app_id = settings.meta_app_id or settings.facebook_app_id  # Fallback to legacy
        self.app_secret = settings.meta_app_secret or settings.facebook_app_secret
        self.access_token = settings.meta_access_token or settings.facebook_page_access_token
        self.api_version = settings.meta_api_version or "v22.0"
        self.api_base = f"https://graph.facebook.com/{self.api_version}"
        
        # API endpoints
        self.endpoints = {
            "me": "/me",
            "accounts": "/me/accounts",
            "page_posts": "/{page_id}/feed",
            "page_photos": "/{page_id}/photos",
            "page_videos": "/{page_id}/videos",
            "page_events": "/{page_id}/events",
            "page_insights": "/{page_id}/insights",
            "post_insights": "/{post_id}/insights",
            "post_info": "/{post_id}",
            "post_comments": "/{post_id}/comments",
            "post_reactions": "/{post_id}/reactions",
            "post_shares": "/{post_id}/sharedposts",
            "upload_video": "/{page_id}/videos",
            "upload_photo": "/{page_id}/photos",
            "page_info": "/{page_id}",
            "live_videos": "/{page_id}/live_videos"
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            "page_posts": {"requests": 600, "window": 600},  # 600 per 10 minutes
            "api_calls": {"requests": 4800, "window": 3600},  # 4800 per hour
            "insights": {"requests": 200, "window": 3600},
            "video_upload": {"requests": 75, "window": 3600}
        }
        
        # Content limits
        self.content_limits = {
            "post_message": 63206,  # Characters
            "link_caption": 2000,
            "photo_caption": 2000,
            "video_caption": 2000,
            "event_description": 5000,
            "hashtags": 30,  # Recommended maximum
            "video_size": 10 * 1024 * 1024 * 1024,  # 10GB
            "photo_size": 4 * 1024 * 1024,  # 4MB
            "video_duration": 7200  # 2 hours in seconds
        }
        
        # Supported media formats
        self.supported_formats = {
            "image": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            "video": ["mp4", "mov", "avi", "mkv", "wmv", "flv", "webm"],
            "aspect_ratios": {
                "landscape": (16, 9),
                "square": (1, 1),
                "portrait": (9, 16)
            }
        }
        
        logger.info("FacebookAPIClient initialized with Graph API v18.0")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Facebook Graph API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            access_token: Facebook access token
            data: Request data
            params: Query parameters
            files: File uploads
            
        Returns:
            API response data
        """
        url = f"{self.api_base}{endpoint}"
        
        # Add access token to params
        if not params:
            params = {}
        params["access_token"] = access_token
        
        headers = {
            "User-Agent": "AI-Social-Media-Agent/1.0"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    if files:
                        response = await client.post(url, headers=headers, data=data, files=files, params=params)
                    elif data:
                        response = await client.post(url, headers=headers, data=data, params=params)
                    else:
                        response = await client.post(url, headers=headers, params=params)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    usage_header = response.headers.get("X-Business-Use-Case-Usage", "{}")
                    try:
                        usage_data = json.loads(usage_header)
                        call_count = usage_data.get("call_count", 100)
                        retry_after = min(3600, call_count * 10)  # Max 1 hour wait
                    except:
                        retry_after = 3600
                    
                    logger.warning(f"Facebook API rate limited. Waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(method, endpoint, access_token, data, params, files)
                
                # Handle API errors
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error = error_data.get("error", {})
                    error_message = error.get("message", response.text)
                    error_code = error.get("code", response.status_code)
                    
                    logger.error(f"Facebook API error {error_code}: {error_message}")
                    raise Exception(f"Facebook API error ({error_code}): {error_message}")
                
                return response.json() if response.content else {}
                
            except httpx.RequestError as e:
                logger.error(f"HTTP request error: {e}")
                raise Exception(f"Network error: {str(e)}")
            except Exception as e:
                logger.error(f"Facebook API request failed: {e}")
                raise
    
    async def get_user_pages(self, access_token: str) -> List[FacebookPage]:
        """
        Get Facebook Pages that user manages
        
        Args:
            access_token: Facebook user access token
            
        Returns:
            List of Facebook Pages
        """
        params = {
            "fields": "id,name,about,category,followers_count,fan_count,picture,cover,website,phone,location,hours,verification_status,access_token"
        }
        
        response = await self._make_request("GET", self.endpoints["accounts"], access_token, params=params)
        
        pages = []
        for page_data in response.get("data", []):
            page = FacebookPage(
                id=page_data.get("id"),
                name=page_data.get("name", ""),
                about=page_data.get("about", ""),
                category=page_data.get("category", ""),
                followers_count=page_data.get("followers_count", 0),
                fan_count=page_data.get("fan_count", 0),
                picture_url=page_data.get("picture", {}).get("data", {}).get("url", ""),
                cover_photo_url=page_data.get("cover", {}).get("source", ""),
                website=page_data.get("website", ""),
                phone=page_data.get("phone", ""),
                location=page_data.get("location", {}),
                hours=page_data.get("hours", {}),
                is_verified=page_data.get("verification_status") == "blue_verified",
                can_post=True,  # Assume true if we have access
                access_token=page_data.get("access_token", "")
            )
            pages.append(page)
        
        return pages
    
    async def get_page_info(self, page_access_token: str, page_id: str) -> FacebookPage:
        """
        Get detailed information about a Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            
        Returns:
            Facebook Page information
        """
        endpoint = self.endpoints["page_info"].format(page_id=page_id)
        params = {
            "fields": "id,name,about,category,followers_count,fan_count,picture,cover,website,phone,location,hours,verification_status"
        }
        
        response = await self._make_request("GET", endpoint, page_access_token, params=params)
        
        return FacebookPage(
            id=response.get("id"),
            name=response.get("name", ""),
            about=response.get("about", ""),
            category=response.get("category", ""),
            followers_count=response.get("followers_count", 0),
            fan_count=response.get("fan_count", 0),
            picture_url=response.get("picture", {}).get("data", {}).get("url", ""),
            cover_photo_url=response.get("cover", {}).get("source", ""),
            website=response.get("website", ""),
            phone=response.get("phone", ""),
            location=response.get("location", {}),
            hours=response.get("hours", {}),
            is_verified=response.get("verification_status") == "blue_verified",
            can_post=True,
            access_token=page_access_token
        )
    
    async def create_text_post(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        link: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[datetime] = None
    ) -> FacebookPost:
        """
        Create a text post on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            message: Post message
            link: Optional link to share
            published: Whether to publish immediately
            scheduled_publish_time: Time to publish (for scheduled posts)
            
        Returns:
            Created post data
        """
        if len(message) > self.content_limits["post_message"]:
            raise ValueError(f"Message exceeds {self.content_limits['post_message']} characters")
        
        endpoint = self.endpoints["page_posts"].format(page_id=page_id)
        
        post_data = {
            "message": message,
            "published": published
        }
        
        if link:
            post_data["link"] = link
        
        if scheduled_publish_time and not published:
            post_data["scheduled_publish_time"] = int(scheduled_publish_time.timestamp())
        
        response = await self._make_request("POST", endpoint, page_access_token, data=post_data)
        
        post_id = response.get("id")
        if not post_id:
            raise Exception("Failed to create Facebook post")
        
        # Get full post details
        return await self.get_post_info(page_access_token, post_id)
    
    async def create_photo_post(
        self,
        page_access_token: str,
        page_id: str,
        photo_url: str,
        caption: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[datetime] = None
    ) -> FacebookPost:
        """
        Create a photo post on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            photo_url: URL of the photo to post
            caption: Photo caption
            published: Whether to publish immediately
            scheduled_publish_time: Time to publish (for scheduled posts)
            
        Returns:
            Created post data
        """
        endpoint = self.endpoints["page_photos"].format(page_id=page_id)
        
        post_data = {
            "url": photo_url,
            "published": published
        }
        
        if caption:
            if len(caption) > self.content_limits["photo_caption"]:
                raise ValueError(f"Caption exceeds {self.content_limits['photo_caption']} characters")
            post_data["caption"] = caption
        
        if scheduled_publish_time and not published:
            post_data["scheduled_publish_time"] = int(scheduled_publish_time.timestamp())
        
        response = await self._make_request("POST", endpoint, page_access_token, data=post_data)
        
        post_id = response.get("post_id") or response.get("id")
        if not post_id:
            raise Exception("Failed to create Facebook photo post")
        
        # Get full post details
        return await self.get_post_info(page_access_token, post_id)
    
    async def create_video_post(
        self,
        page_access_token: str,
        page_id: str,
        video_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[datetime] = None,
        thumb_url: Optional[str] = None
    ) -> FacebookPost:
        """
        Create a video post on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            video_url: URL of the video to post
            title: Video title
            description: Video description
            published: Whether to publish immediately
            scheduled_publish_time: Time to publish (for scheduled posts)
            thumb_url: Thumbnail image URL
            
        Returns:
            Created post data
        """
        endpoint = self.endpoints["page_videos"].format(page_id=page_id)
        
        post_data = {
            "file_url": video_url,
            "published": published
        }
        
        if title:
            post_data["title"] = title
        
        if description:
            if len(description) > self.content_limits["video_caption"]:
                raise ValueError(f"Description exceeds {self.content_limits['video_caption']} characters")
            post_data["description"] = description
        
        if thumb_url:
            post_data["thumb"] = thumb_url
        
        if scheduled_publish_time and not published:
            post_data["scheduled_publish_time"] = int(scheduled_publish_time.timestamp())
        
        response = await self._make_request("POST", endpoint, page_access_token, data=post_data)
        
        post_id = response.get("id")
        if not post_id:
            raise Exception("Failed to create Facebook video post")
        
        # Wait for video processing
        await asyncio.sleep(10)
        
        # Get full post details
        return await self.get_post_info(page_access_token, post_id)
    
    async def create_link_post(
        self,
        page_access_token: str,
        page_id: str,
        link: str,
        message: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[datetime] = None
    ) -> FacebookPost:
        """
        Create a link post on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            link: URL to share
            message: Post message
            published: Whether to publish immediately
            scheduled_publish_time: Time to publish (for scheduled posts)
            
        Returns:
            Created post data
        """
        endpoint = self.endpoints["page_posts"].format(page_id=page_id)
        
        post_data = {
            "link": link,
            "published": published
        }
        
        if message:
            if len(message) > self.content_limits["link_caption"]:
                raise ValueError(f"Message exceeds {self.content_limits['link_caption']} characters")
            post_data["message"] = message
        
        if scheduled_publish_time and not published:
            post_data["scheduled_publish_time"] = int(scheduled_publish_time.timestamp())
        
        response = await self._make_request("POST", endpoint, page_access_token, data=post_data)
        
        post_id = response.get("id")
        if not post_id:
            raise Exception("Failed to create Facebook link post")
        
        # Get full post details
        return await self.get_post_info(page_access_token, post_id)
    
    async def create_event(
        self,
        page_access_token: str,
        page_id: str,
        name: str,
        start_time: datetime,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        location: Optional[str] = None,
        is_online: bool = False,
        cover_photo_url: Optional[str] = None
    ) -> FacebookEvent:
        """
        Create an event on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            name: Event name
            start_time: Event start time
            description: Event description
            end_time: Event end time
            location: Event location
            is_online: Whether event is online
            cover_photo_url: Cover photo URL
            
        Returns:
            Created event data
        """
        endpoint = self.endpoints["page_events"].format(page_id=page_id)
        
        event_data = {
            "name": name,
            "start_time": start_time.isoformat(),
            "is_online_event": is_online
        }
        
        if description:
            if len(description) > self.content_limits["event_description"]:
                raise ValueError(f"Description exceeds {self.content_limits['event_description']} characters")
            event_data["description"] = description
        
        if end_time:
            event_data["end_time"] = end_time.isoformat()
        
        if location and not is_online:
            event_data["location"] = location
        
        if cover_photo_url:
            event_data["cover_url"] = cover_photo_url
        
        response = await self._make_request("POST", endpoint, page_access_token, data=event_data)
        
        event_id = response.get("id")
        if not event_id:
            raise Exception("Failed to create Facebook event")
        
        # Get full event details
        return await self.get_event_info(page_access_token, event_id)
    
    async def get_post_info(self, access_token: str, post_id: str) -> FacebookPost:
        """
        Get detailed information about a Facebook post
        
        Args:
            access_token: Facebook access token
            post_id: Facebook post ID
            
        Returns:
            Post information
        """
        endpoint = self.endpoints["post_info"].format(post_id=post_id)
        params = {
            "fields": "id,message,story,created_time,updated_time,from,privacy,status_type,type,link,picture,full_picture,attachments,reactions.summary(total_count),comments.summary(total_count),shares"
        }
        
        response = await self._make_request("GET", endpoint, access_token, params=params)
        
        # Extract reaction counts
        reactions = {}
        reactions_data = response.get("reactions", {}).get("data", [])
        for reaction in reactions_data:
            reaction_type = reaction.get("type", "like")
            reactions[reaction_type] = reactions.get(reaction_type, 0) + 1
        
        return FacebookPost(
            id=response.get("id"),
            message=response.get("message", ""),
            story=response.get("story", ""),
            created_time=datetime.fromisoformat(response.get("created_time", "").replace("+0000", "+00:00")),
            updated_time=datetime.fromisoformat(response.get("updated_time", "").replace("+0000", "+00:00")),
            from_user=response.get("from", {}),
            privacy=response.get("privacy", {}),
            status_type=response.get("status_type", ""),
            type=response.get("type", ""),
            link=response.get("link"),
            picture=response.get("picture"),
            full_picture=response.get("full_picture"),
            attachments=response.get("attachments"),
            reactions=reactions,
            comments_count=response.get("comments", {}).get("summary", {}).get("total_count", 0),
            shares_count=response.get("shares", {}).get("count", 0)
        )
    
    async def get_event_info(self, access_token: str, event_id: str) -> FacebookEvent:
        """
        Get detailed information about a Facebook event
        
        Args:
            access_token: Facebook access token
            event_id: Facebook event ID
            
        Returns:
            Event information
        """
        endpoint = f"/{event_id}"
        params = {
            "fields": "id,name,description,start_time,end_time,place,attending_count,interested_count,maybe_count,cover,is_online_event"
        }
        
        response = await self._make_request("GET", endpoint, access_token, params=params)
        
        return FacebookEvent(
            id=response.get("id"),
            name=response.get("name", ""),
            description=response.get("description", ""),
            start_time=datetime.fromisoformat(response.get("start_time", "").replace("+0000", "+00:00")),
            end_time=datetime.fromisoformat(response.get("end_time", "").replace("+0000", "+00:00")) if response.get("end_time") else None,
            location=response.get("place", {}).get("name", ""),
            attending_count=response.get("attending_count", 0),
            interested_count=response.get("interested_count", 0),
            maybe_count=response.get("maybe_count", 0),
            cover_photo_url=response.get("cover", {}).get("source", ""),
            event_url=f"https://www.facebook.com/events/{response.get('id')}",
            is_online=response.get("is_online_event", False)
        )
    
    async def get_post_insights(
        self,
        access_token: str,
        post_id: str,
        metrics: Optional[List[str]] = None
    ) -> FacebookInsights:
        """
        Get insights for a Facebook post
        
        Args:
            access_token: Facebook access token
            post_id: Facebook post ID
            metrics: Specific metrics to retrieve
            
        Returns:
            Post insights
        """
        endpoint = self.endpoints["post_insights"].format(post_id=post_id)
        
        # Default metrics
        if not metrics:
            metrics = [
                "post_impressions",
                "post_reach",
                "post_engaged_users",
                "post_reactions_by_type_total",
                "post_clicks",
                "post_consumptions",
                "post_negative_feedback"
            ]
        
        params = {
            "metric": ",".join(metrics),
            "period": "lifetime"
        }
        
        try:
            response = await self._make_request("GET", endpoint, access_token, params=params)
            
            # Parse insights data
            insights_data = {}
            for insight in response.get("data", []):
                metric_name = insight.get("name")
                values = insight.get("values", [])
                if values:
                    value = values[0].get("value")
                    if isinstance(value, dict):
                        # For metrics like reactions_by_type
                        insights_data[metric_name] = sum(value.values()) if value else 0
                    else:
                        insights_data[metric_name] = value or 0
            
            # Calculate total engagement
            reactions = insights_data.get("post_reactions_by_type_total", 0)
            comments = 0  # Will need separate API call for comments
            shares = 0    # Will need separate API call for shares
            engagement = reactions + comments + shares
            
            return FacebookInsights(
                post_id=post_id,
                impressions=insights_data.get("post_impressions", 0),
                reach=insights_data.get("post_reach", 0),
                engagement=engagement,
                reactions=reactions,
                comments=comments,
                shares=shares,
                clicks=insights_data.get("post_clicks", 0),
                video_views=insights_data.get("post_video_views"),
                story_completions=insights_data.get("post_story_completions"),
                post_consumptions=insights_data.get("post_consumptions", 0),
                post_engaged_users=insights_data.get("post_engaged_users", 0),
                negative_feedback=insights_data.get("post_negative_feedback", 0),
                fetched_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.warning(f"Failed to get Facebook insights: {e}")
            # Return empty insights
            return FacebookInsights(
                post_id=post_id,
                impressions=0,
                reach=0,
                engagement=0,
                reactions=0,
                comments=0,
                shares=0,
                clicks=0,
                video_views=None,
                story_completions=None,
                post_consumptions=0,
                post_engaged_users=0,
                negative_feedback=0,
                fetched_at=datetime.utcnow()
            )
    
    async def get_page_posts(
        self,
        page_access_token: str,
        page_id: str,
        limit: int = 25,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> List[FacebookPost]:
        """
        Get posts from a Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            limit: Number of posts to retrieve
            since_date: Start date filter
            until_date: End date filter
            
        Returns:
            List of Facebook posts
        """
        endpoint = self.endpoints["page_posts"].format(page_id=page_id)
        params = {
            "fields": "id,message,story,created_time,type,link,picture,reactions.summary(total_count),comments.summary(total_count),shares",
            "limit": min(limit, 100)
        }
        
        if since_date:
            params["since"] = since_date.isoformat()
        if until_date:
            params["until"] = until_date.isoformat()
        
        response = await self._make_request("GET", endpoint, page_access_token, params=params)
        
        posts = []
        for post_data in response.get("data", []):
            try:
                # Get full post details
                post = await self.get_post_info(page_access_token, post_data["id"])
                posts.append(post)
            except Exception as e:
                logger.error(f"Failed to get post info for {post_data['id']}: {e}")
        
        return posts
    
    async def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete a Facebook post
        
        Args:
            access_token: Facebook access token
            post_id: Facebook post ID
            
        Returns:
            Success status
        """
        try:
            endpoint = f"/{post_id}"
            response = await self._make_request("DELETE", endpoint, access_token)
            
            success = response.get("success", False)
            if success:
                logger.info(f"Successfully deleted Facebook post {post_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete Facebook post {post_id}: {e}")
            return False
    
    async def create_live_video(
        self,
        page_access_token: str,
        page_id: str,
        title: str,
        description: Optional[str] = None,
        planned_start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a live video broadcast on Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            title: Live video title
            description: Live video description
            planned_start_time: Planned start time for scheduled live
            
        Returns:
            Live video details including stream URL
        """
        endpoint = self.endpoints["live_videos"].format(page_id=page_id)
        
        live_data = {
            "title": title,
            "status": "SCHEDULED_UNPUBLISHED" if planned_start_time else "UNPUBLISHED"
        }
        
        if description:
            live_data["description"] = description
        
        if planned_start_time:
            live_data["planned_start_time"] = int(planned_start_time.timestamp())
        
        response = await self._make_request("POST", endpoint, page_access_token, data=live_data)
        
        return {
            "id": response.get("id"),
            "stream_url": response.get("stream_url"),
            "secure_stream_url": response.get("secure_stream_url"),
            "status": response.get("status"),
            "planned_start_time": planned_start_time
        }
    
    async def get_page_insights(
        self,
        page_access_token: str,
        page_id: str,
        metrics: Optional[List[str]] = None,
        period: str = "day",
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get insights for a Facebook Page
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            metrics: Specific metrics to retrieve
            period: Time period (day, week, days_28)
            since_date: Start date
            until_date: End date
            
        Returns:
            Page insights data
        """
        endpoint = self.endpoints["page_insights"].format(page_id=page_id)
        
        # Default metrics
        if not metrics:
            metrics = [
                "page_impressions",
                "page_reach",
                "page_engaged_users",
                "page_fan_adds",
                "page_fan_removes",
                "page_views_total",
                "page_posts_impressions",
                "page_video_views"
            ]
        
        params = {
            "metric": ",".join(metrics),
            "period": period
        }
        
        if since_date:
            params["since"] = since_date.strftime("%Y-%m-%d")
        if until_date:
            params["until"] = until_date.strftime("%Y-%m-%d")
        
        try:
            response = await self._make_request("GET", endpoint, page_access_token, params=params)
            
            # Parse insights data
            insights = {}
            for insight in response.get("data", []):
                metric_name = insight.get("name")
                values = insight.get("values", [])
                
                # Aggregate values for the period
                total_value = 0
                for value_entry in values:
                    value = value_entry.get("value", 0)
                    if isinstance(value, (int, float)):
                        total_value += value
                    elif isinstance(value, dict):
                        total_value += sum(value.values())
                
                insights[metric_name] = total_value
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get Facebook page insights: {e}")
            return {}
    
    def validate_post_content(self, content: str, content_type: str = "post") -> Tuple[bool, str]:
        """
        Validate Facebook post content
        
        Args:
            content: Content to validate
            content_type: Type of content (post, photo_caption, video_caption, etc.)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        limit_key = f"{content_type}_message" if content_type == "post" else f"{content_type}_caption"
        max_length = self.content_limits.get(limit_key, self.content_limits["post_message"])
        
        if len(content) > max_length:
            return False, f"Content too long ({len(content)}/{max_length} characters)"
        
        return True, ""
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag.lower() for tag in hashtags]
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        import re
        mentions = re.findall(r'@[\w\.]+', text)
        return [mention.lower() for mention in mentions]
    
    def optimize_for_facebook(self, content: str, post_type: str = "text") -> str:
        """
        Optimize content for Facebook's algorithm and audience
        
        Args:
            content: Original content
            post_type: Type of post (text, photo, video, link)
            
        Returns:
            Optimized content
        """
        # Facebook favors posts that encourage engagement
        engagement_starters = [
            "What do you think?",
            "Share your thoughts!",
            "Tag someone who",
            "Double tap if you agree",
            "Comment below with"
        ]
        
        # Check if content already has engagement encouragement
        has_engagement = any(starter.lower() in content.lower() for starter in engagement_starters)
        
        # Add engagement encouragement if missing and content is not too long
        if not has_engagement and len(content) < self.content_limits["post_message"] - 50:
            if post_type == "photo":
                content += "\n\nWhat do you think of this?"
            elif post_type == "video":
                content += "\n\nLet us know your thoughts in the comments!"
            elif post_type == "link":
                content += "\n\nShare your opinion below!"
            else:
                content += "\n\nWhat's your take on this?"
        
        return content.strip()
    
    async def schedule_post(
        self,
        page_access_token: str,
        page_id: str,
        content: Dict[str, Any],
        publish_time: datetime,
        post_type: str = "text"
    ) -> str:
        """
        Schedule a post for future publication
        
        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            content: Post content dictionary
            publish_time: When to publish the post
            post_type: Type of post to create
            
        Returns:
            Scheduled post ID
        """
        # Create unpublished post first
        if post_type == "text":
            post = await self.create_text_post(
                page_access_token, page_id, 
                content["message"], 
                content.get("link"),
                published=False,
                scheduled_publish_time=publish_time
            )
        elif post_type == "photo":
            post = await self.create_photo_post(
                page_access_token, page_id,
                content["photo_url"],
                content.get("caption"),
                published=False,
                scheduled_publish_time=publish_time
            )
        elif post_type == "video":
            post = await self.create_video_post(
                page_access_token, page_id,
                content["video_url"],
                content.get("title"),
                content.get("description"),
                published=False,
                scheduled_publish_time=publish_time
            )
        else:
            raise ValueError(f"Unsupported post type for scheduling: {post_type}")
        
        logger.info(f"Scheduled Facebook post {post.id} for {publish_time}")
        return post.id
    
    async def get_user_token(self, user_id: int) -> Optional[str]:
        """
        Get stored Facebook access token for user
        
        Args:
            user_id: User ID
            
        Returns:
            Facebook access token or None if not found
        """
        try:
            return await oauth_manager.get_user_access_token(user_id, "facebook")
        except Exception as e:
            logger.error(f"Failed to get Facebook token for user {user_id}: {e}")
            return None
    
    async def create_post(
        self,
        access_token: str,
        message: str,
        media_urls: Optional[List[str]] = None,
        link: Optional[str] = None,
        scheduled_publish_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create Facebook post (wrapper method for integration API compatibility)
        
        Args:
            access_token: Facebook access token
            message: Post message
            media_urls: List of media URLs (optional)
            link: Link to include (optional)
            scheduled_publish_time: When to publish (optional)
            
        Returns:
            Post creation result
        """
        # Get user's Facebook pages
        pages = await self.get_user_pages(access_token)
        if not pages:
            raise Exception("No Facebook pages found for user")
        
        # Use the first page (could be enhanced to let user choose)
        page = pages[0]
        page_id = page.id
        page_access_token = page.access_token
        
        # Optimize content for Facebook
        optimized_message = self.optimize_for_facebook(message)
        
        if media_urls and len(media_urls) > 0:
            # Create photo/video post
            if self._is_video_url(media_urls[0]):
                result = await self.create_video_post(
                    page_access_token=page_access_token,
                    page_id=page_id,
                    video_url=media_urls[0],
                    title=optimized_message[:100],  # Use first part as title
                    description=optimized_message,
                    published=scheduled_publish_time is None,
                    scheduled_publish_time=scheduled_publish_time
                )
            else:
                result = await self.create_photo_post(
                    page_access_token=page_access_token,
                    page_id=page_id,
                    photo_url=media_urls[0],
                    caption=optimized_message,
                    published=scheduled_publish_time is None,
                    scheduled_publish_time=scheduled_publish_time
                )
        else:
            # Create text post
            result = await self.create_text_post(
                page_access_token=page_access_token,
                page_id=page_id,
                message=optimized_message,
                link=link,
                published=scheduled_publish_time is None,
                scheduled_publish_time=scheduled_publish_time
            )
        
        return {
            "id": result.id,
            "created_time": result.created_time.isoformat() if result.created_time else None
        }
    
    def _is_video_url(self, url: str) -> bool:
        """Check if URL points to a video file"""
        video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm']
        return any(url.lower().endswith(ext) for ext in video_extensions)

# Global Facebook client instance
facebook_client = FacebookAPIClient()