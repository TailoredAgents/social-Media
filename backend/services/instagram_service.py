"""
Instagram Service Layer
Integration Specialist Component - Service layer for Instagram operations with visual content focus
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import asdict

from backend.integrations.instagram_client import instagram_client, InstagramMedia, InstagramStory, InstagramAnalytics, InstagramAccount
from backend.auth.social_oauth import oauth_manager
from backend.db.models import User, ContentItem, ContentPerformanceSnapshot, UserSetting
from backend.services.similarity_service import similarity_service
from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class InstagramService:
    """
    Instagram service layer with visual content optimization and story management
    
    Features:
    - Visual content posting with hashtag optimization
    - Instagram Stories automation
    - Hashtag research and performance tracking
    - Visual analytics and engagement monitoring
    - Carousel post creation
    - Story sticker integration
    """
    
    def __init__(self):
        """Initialize Instagram service"""
        self.platform = "instagram"
        self.optimal_posting_hours = [11, 13, 17, 19]  # Peak engagement hours
        self.optimal_posting_days = ["Wednesday", "Thursday", "Friday", "Sunday"]  # Best engagement days
        
        # Visual content strategy parameters
        self.visual_strategies = {
            "feed_post": {
                "aspect_ratios": [(1, 1), (4, 5)],  # Square and portrait preferred
                "hashtag_range": (5, 30),
                "caption_length": (50, 300),
                "posting_frequency": "1-2 per day"
            },
            "story": {
                "aspect_ratios": [(9, 16)],  # Vertical only
                "duration": 15,  # seconds
                "sticker_limit": 5,
                "posting_frequency": "3-5 per day"
            },
            "carousel": {
                "min_images": 2,
                "max_images": 10,
                "consistent_aspect_ratio": True
            }
        }
        
        # Instagram-specific engagement thresholds
        self.engagement_thresholds = {
            "viral": 15.0,     # Very high for Instagram
            "high": 8.0,
            "medium": 3.0,
            "low": 1.0
        }
        
        # Popular content categories for Instagram
        self.content_categories = [
            "lifestyle", "fashion", "food", "travel", "fitness", "beauty",
            "art", "photography", "business", "inspiration", "behind_the_scenes"
        ]
        
        logger.info("InstagramService initialized with visual content focus")
    
    async def post_content(
        self,
        user_id: int,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None,
        location_id: Optional[str] = None,
        user_tags: Optional[List[Dict]] = None,
        auto_hashtags: bool = True,
        ig_account_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Post visual content to Instagram
        
        Args:
            user_id: User ID
            media_url: URL of media to post
            media_type: "image" or "video"
            caption: Post caption
            location_id: Location ID for tagging
            user_tags: List of user tags
            auto_hashtags: Automatically suggest hashtags
            ig_account_id: Specific Instagram account ID
            db: Database session
            
        Returns:
            Posting result with engagement insights
        """
        try:
            # Get valid access token
            access_token = await oauth_manager.get_valid_token(user_id, "facebook", db)  # Instagram uses Facebook token
            if not access_token:
                raise Exception("No valid Facebook/Instagram connection found")
            
            # Get Instagram account if not specified
            if not ig_account_id:
                accounts = await instagram_client.get_instagram_accounts(access_token)
                if not accounts:
                    raise Exception("No Instagram Business accounts found")
                ig_account_id = accounts[0].id
            
            # Optimize caption for Instagram
            if caption and auto_hashtags:
                optimized_caption = await self._optimize_caption_for_instagram(
                    caption, media_type, user_id, db
                )
            else:
                optimized_caption = caption
            
            # Create media container
            container_id = await instagram_client.create_media_container(
                access_token=access_token,
                ig_user_id=ig_account_id,
                image_url=media_url if media_type == "image" else None,
                video_url=media_url if media_type == "video" else None,
                caption=optimized_caption,
                location_id=location_id,
                user_tags=user_tags
            )
            
            # Publish media
            media = await instagram_client.publish_media(
                access_token=access_token,
                ig_user_id=ig_account_id,
                creation_id=container_id
            )
            
            # Store in database
            content_item = await self._store_content_item(
                user_id=user_id,
                content=optimized_caption or "",
                media_url=media_url,
                media_type=media_type,
                platform_post_id=media.id,
                media_data=media,
                ig_account_id=ig_account_id,
                db=db
            )
            
            # Schedule analytics collection
            await self._schedule_analytics_collection(media.id, user_id, db)
            
            # Generate Instagram-specific insights
            visual_insights = await self._generate_visual_insights(
                optimized_caption or "", media_type, media, db
            )
            
            return {
                "status": "success",
                "media_id": media.id,
                "content_item_id": content_item.id,
                "media_url": media.permalink,
                "posted_at": media.timestamp.isoformat(),
                "media_type": media.media_type,
                "ig_account_id": ig_account_id,
                "visual_insights": visual_insights,
                "hashtags_applied": instagram_client.extract_hashtags(optimized_caption or ""),
                "optimization_applied": auto_hashtags
            }
            
        except Exception as e:
            logger.error(f"Failed to post Instagram content: {e}")
            raise
    
    async def create_story(
        self,
        user_id: int,
        media_url: str,
        media_type: str,
        stickers: Optional[List[Dict]] = None,
        ig_account_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Create an Instagram Story
        
        Args:
            user_id: User ID
            media_url: Story media URL
            media_type: "image" or "video"
            stickers: Story stickers (poll, question, etc.)
            ig_account_id: Instagram account ID
            db: Database session
            
        Returns:
            Story creation result
        """
        try:
            # Get valid access token
            access_token = await oauth_manager.get_valid_token(user_id, "facebook", db)
            if not access_token:
                raise Exception("No valid Facebook/Instagram connection found")
            
            # Get Instagram account if not specified
            if not ig_account_id:
                accounts = await instagram_client.get_instagram_accounts(access_token)
                if not accounts:
                    raise Exception("No Instagram Business accounts found")
                ig_account_id = accounts[0].id
            
            # Create story
            story = await instagram_client.create_story(
                access_token=access_token,
                ig_user_id=ig_account_id,
                image_url=media_url if media_type == "image" else None,
                video_url=media_url if media_type == "video" else None,
                stickers=stickers
            )
            
            # Store story in database
            content_item = await self._store_content_item(
                user_id=user_id,
                content="Instagram Story",
                media_url=media_url,
                media_type=media_type,
                content_format="story",
                platform_post_id=story.id,
                story_data=story,
                ig_account_id=ig_account_id,
                db=db
            )
            
            return {
                "status": "success",
                "story_id": story.id,
                "content_item_id": content_item.id,
                "media_type": story.media_type,
                "expires_at": story.expires_at.isoformat(),
                "stickers_applied": len(stickers) if stickers else 0,
                "ig_account_id": ig_account_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create Instagram story: {e}")
            raise
    
    async def create_carousel_post(
        self,
        user_id: int,
        media_urls: List[str],
        media_types: List[str],
        caption: Optional[str] = None,
        location_id: Optional[str] = None,
        auto_hashtags: bool = True,
        ig_account_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Create Instagram carousel post with multiple media
        
        Args:
            user_id: User ID
            media_urls: List of media URLs
            media_types: List of media types
            caption: Post caption
            location_id: Location ID
            auto_hashtags: Auto-generate hashtags
            ig_account_id: Instagram account ID
            db: Database session
            
        Returns:
            Carousel post result
        """
        try:
            if len(media_urls) < 2 or len(media_urls) > 10:
                raise ValueError("Carousel must have 2-10 media items")
            
            if len(media_urls) != len(media_types):
                raise ValueError("Media URLs and types must have same length")
            
            # Get valid access token
            access_token = await oauth_manager.get_valid_token(user_id, "facebook", db)
            if not access_token:
                raise Exception("No valid Facebook/Instagram connection found")
            
            # Get Instagram account if not specified
            if not ig_account_id:
                accounts = await instagram_client.get_instagram_accounts(access_token)
                if not accounts:
                    raise Exception("No Instagram Business accounts found")
                ig_account_id = accounts[0].id
            
            # Create media containers for each item
            child_containers = []
            for media_url, media_type in zip(media_urls, media_types):
                container_id = await instagram_client.create_media_container(
                    access_token=access_token,
                    ig_user_id=ig_account_id,
                    image_url=media_url if media_type == "image" else None,
                    video_url=media_url if media_type == "video" else None
                )
                child_containers.append(container_id)
            
            # Optimize caption for carousel
            if caption and auto_hashtags:
                optimized_caption = await self._optimize_caption_for_instagram(
                    caption, "carousel", user_id, db
                )
            else:
                optimized_caption = caption
            
            # Create carousel container
            carousel_container = await instagram_client.create_media_container(
                access_token=access_token,
                ig_user_id=ig_account_id,
                caption=optimized_caption,
                location_id=location_id,
                is_carousel=True,
                carousel_children=child_containers
            )
            
            # Publish carousel
            media = await instagram_client.publish_media(
                access_token=access_token,
                ig_user_id=ig_account_id,
                creation_id=carousel_container
            )
            
            # Store in database
            content_item = await self._store_content_item(
                user_id=user_id,
                content=optimized_caption or "",
                media_url=media_urls[0],  # Primary media
                media_type="carousel",
                content_format="carousel",
                platform_post_id=media.id,
                media_data=media,
                ig_account_id=ig_account_id,
                db=db
            )
            
            # Store carousel metadata
            content_item.content_metadata = {
                **content_item.content_metadata,
                "carousel_items": len(media_urls),
                "media_urls": media_urls,
                "media_types": media_types
            }
            
            if db:
                db.commit()
            
            return {
                "status": "success",
                "carousel_id": media.id,
                "content_item_id": content_item.id,
                "media_url": media.permalink,
                "carousel_items": len(media_urls),
                "posted_at": media.timestamp.isoformat(),
                "ig_account_id": ig_account_id,
                "optimization_applied": auto_hashtags
            }
            
        except Exception as e:
            logger.error(f"Failed to create Instagram carousel: {e}")
            raise
    
    async def _optimize_caption_for_instagram(
        self,
        caption: str,
        media_type: str,
        user_id: int,
        db: Session
    ) -> str:
        """
        Optimize caption for Instagram with hashtag suggestions
        
        Args:
            caption: Original caption
            media_type: Type of media
            user_id: User ID for personalization
            db: Database session
            
        Returns:
            Optimized caption with hashtags
        """
        try:
            # Get user account type for targeting
            user_settings = db.query(UserSetting).filter(
                UserSetting.user_id == user_id
            ).first() if db else None
            
            account_type = "BUSINESS"  # Default
            if user_settings and user_settings.connected_accounts:
                ig_data = user_settings.connected_accounts.get("instagram", {})
                account_type = ig_data.get("account_type", "BUSINESS")
            
            # Generate hashtag suggestions
            suggested_hashtags = instagram_client.suggest_hashtags(caption, account_type)
            
            # Combine with existing hashtags
            existing_hashtags = instagram_client.extract_hashtags(caption)
            
            # Add new hashtags if under limit
            current_hashtag_count = len(existing_hashtags)
            hashtag_limit = 30
            
            if current_hashtag_count < hashtag_limit:
                new_hashtags = []
                for hashtag in suggested_hashtags:
                    if hashtag not in existing_hashtags and len(new_hashtags) + current_hashtag_count < hashtag_limit:
                        new_hashtags.append(hashtag)
                
                # Add hashtags to caption
                if new_hashtags:
                    if not caption.endswith('\n'):
                        caption += '\n\n'
                    caption += ' '.join(new_hashtags)
            
            # Optimize caption structure for Instagram
            caption = self._structure_instagram_caption(caption)
            
            return caption
            
        except Exception as e:
            logger.error(f"Failed to optimize Instagram caption: {e}")
            return caption
    
    def _structure_instagram_caption(self, caption: str) -> str:
        """Structure caption for optimal Instagram engagement"""
        # Ensure proper line breaks for readability
        lines = caption.split('\n')
        
        # Add hook at the beginning if not present
        if len(lines) > 0 and len(lines[0]) > 50:
            first_sentence = lines[0].split('.')[0]
            if len(first_sentence) > 100:
                lines[0] = first_sentence[:100] + "...\n\n" + lines[0]
        
        # Separate hashtags to end
        hashtag_lines = []
        content_lines = []
        
        for line in lines:
            if line.strip().startswith('#') or '#' in line:
                hashtag_lines.append(line)
            else:
                content_lines.append(line)
        
        # Reconstruct caption
        structured_caption = '\n'.join(content_lines)
        if hashtag_lines:
            structured_caption += '\n\n' + '\n'.join(hashtag_lines)
        
        return structured_caption.strip()
    
    async def _store_content_item(
        self,
        user_id: int,
        content: str,
        media_url: str,
        media_type: str,
        platform_post_id: str,
        media_data: Optional[InstagramMedia] = None,
        story_data: Optional[InstagramStory] = None,
        content_format: str = "post",
        ig_account_id: Optional[str] = None,
        db: Session = None
    ) -> ContentItem:
        """Store Instagram content item in database"""
        try:
            # Extract Instagram-specific elements
            hashtags = instagram_client.extract_hashtags(content)
            mentions = instagram_client.extract_mentions(content)
            
            # Create content item
            content_item = ContentItem(
                user_id=user_id,
                content=content,
                platform=self.platform,
                content_type=media_type,
                content_format=content_format,
                status="published",
                platform_post_id=platform_post_id,
                platform_url=media_data.permalink if media_data else f"https://instagram.com/p/{platform_post_id}",
                published_at=media_data.timestamp if media_data else story_data.timestamp,
                hashtags=hashtags,
                mentions=mentions,
                tone="engaging",  # Instagram default
                reading_level="beginner"  # Visual content accessibility
            )
            
            # Add Instagram-specific metadata
            instagram_metadata = {
                "ig_account_id": ig_account_id,
                "media_url": media_url,
                "visual_content": True,
                "content_category": self._categorize_visual_content(content),
                "hashtag_strategy": self._analyze_hashtag_strategy(hashtags),
                "visual_appeal_score": self._assess_visual_appeal(media_type, content),
                "story_content": content_format == "story"
            }
            
            if media_data:
                instagram_metadata.update({
                    "thumbnail_url": media_data.thumbnail_url,
                    "media_type_ig": media_data.media_type
                })
            
            if story_data:
                instagram_metadata.update({
                    "expires_at": story_data.expires_at.isoformat(),
                    "story_duration": 24  # hours
                })
            
            content_item.content_metadata = instagram_metadata
            
            if db:
                db.add(content_item)
                db.commit()
                db.refresh(content_item)
            
            logger.info(f"Stored Instagram content item {content_item.id}")
            return content_item
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Failed to store Instagram content item: {e}")
            raise
    
    def _categorize_visual_content(self, content: str) -> str:
        """Categorize Instagram content by visual theme"""
        content_lower = content.lower()
        
        # Instagram-specific categories
        category_keywords = {
            "lifestyle": ["lifestyle", "daily", "life", "routine", "day"],
            "fashion": ["fashion", "outfit", "style", "ootd", "clothing", "wear"],
            "food": ["food", "recipe", "cooking", "delicious", "yummy", "eat"],
            "travel": ["travel", "vacation", "adventure", "explore", "trip", "journey"],
            "fitness": ["fitness", "workout", "gym", "healthy", "exercise", "training"],
            "beauty": ["beauty", "makeup", "skincare", "cosmetics", "beautiful"],
            "art": ["art", "creative", "design", "artist", "artwork", "drawing"],
            "business": ["business", "entrepreneur", "work", "professional", "career"],
            "inspiration": ["inspiration", "motivation", "quote", "inspire", "motivate"],
            "behind_the_scenes": ["behind", "scenes", "process", "making", "work", "studio"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _analyze_hashtag_strategy(self, hashtags: List[str]) -> Dict[str, Any]:
        """Analyze hashtag strategy effectiveness"""
        if not hashtags:
            return {"strategy": "none", "count": 0, "recommendations": ["Add relevant hashtags"]}
        
        hashtag_count = len(hashtags)
        
        # Analyze hashtag types
        branded_tags = [tag for tag in hashtags if any(brand in tag for brand in ["brand", "company", "business"])]
        community_tags = [tag for tag in hashtags if any(comm in tag for comm in ["community", "love", "share", "together"])]
        niche_tags = [tag for tag in hashtags if len(tag) > 15]  # Longer, specific hashtags
        
        strategy = "balanced"
        if hashtag_count < 5:
            strategy = "minimal"
        elif hashtag_count > 20:
            strategy = "aggressive"
        
        recommendations = []
        if hashtag_count < 10:
            recommendations.append("Consider adding more relevant hashtags")
        if not branded_tags and hashtag_count > 5:
            recommendations.append("Add branded hashtags for brand awareness")
        if not niche_tags:
            recommendations.append("Include niche hashtags for targeted reach")
        
        return {
            "strategy": strategy,
            "count": hashtag_count,
            "branded_count": len(branded_tags),
            "community_count": len(community_tags),
            "niche_count": len(niche_tags),
            "recommendations": recommendations
        }
    
    def _assess_visual_appeal(self, media_type: str, content: str) -> float:
        """Assess visual appeal potential (0-1 score)"""
        score = 0.5  # Base score
        
        # Media type factor
        if media_type == "video":
            score += 0.2  # Videos generally perform better
        elif media_type == "carousel":
            score += 0.3  # Carousels have high engagement
        
        # Content indicators
        visual_indicators = ["beautiful", "stunning", "amazing", "gorgeous", "incredible", "wow"]
        if any(indicator in content.lower() for indicator in visual_indicators):
            score += 0.1
        
        # Engagement prompts
        engagement_prompts = ["?", "comment", "tell me", "what do you think", "share"]
        if any(prompt in content.lower() for prompt in engagement_prompts):
            score += 0.1
        
        # Story elements
        story_elements = ["story", "journey", "experience", "process", "behind"]
        if any(element in content.lower() for element in story_elements):
            score += 0.1
        
        return min(1.0, score)
    
    async def _generate_visual_insights(
        self,
        caption: str,
        media_type: str,
        media: InstagramMedia,
        db: Session
    ) -> Dict[str, Any]:
        """Generate insights about visual content performance potential"""
        try:
            insights = {
                "content_category": self._categorize_visual_content(caption),
                "visual_appeal_score": self._assess_visual_appeal(media_type, caption),
                "hashtag_analysis": self._analyze_hashtag_strategy(instagram_client.extract_hashtags(caption)),
                "engagement_potential": self._calculate_engagement_potential(caption, media_type),
                "optimization_suggestions": []
            }
            
            # Generate optimization suggestions
            suggestions = []
            
            if insights["visual_appeal_score"] < 0.6:
                suggestions.append("Consider adding more visually descriptive language")
            
            if insights["hashtag_analysis"]["count"] < 10:
                suggestions.append("Add more relevant hashtags to increase discoverability")
            
            if "?" not in caption:
                suggestions.append("Add a question to encourage comments and engagement")
            
            if media_type == "image" and len(caption) < 50:
                suggestions.append("Expand caption with storytelling elements for better engagement")
            
            if not any(word in caption.lower() for word in ["story", "behind", "process"]):
                suggestions.append("Share the story behind the content for deeper connection")
            
            insights["optimization_suggestions"] = suggestions
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate visual insights: {e}")
            return {}
    
    def _calculate_engagement_potential(self, caption: str, media_type: str) -> float:
        """Calculate engagement potential based on content analysis"""
        potential = 0.5  # Base potential
        
        # Media type bonus
        media_bonus = {
            "video": 0.3,
            "carousel": 0.4,
            "image": 0.2
        }
        potential += media_bonus.get(media_type, 0.1)
        
        # Caption engagement factors
        if "?" in caption:
            potential += 0.1
        
        if len(caption.split()) > 20:  # Substantial caption
            potential += 0.1
        
        hashtag_count = len(instagram_client.extract_hashtags(caption))
        if 10 <= hashtag_count <= 25:  # Optimal hashtag range
            potential += 0.1
        
        # Story/personal elements
        personal_indicators = ["my", "i", "me", "personal", "story", "experience"]
        if any(indicator in caption.lower() for indicator in personal_indicators):
            potential += 0.1
        
        return min(1.0, potential)
    
    async def _schedule_analytics_collection(self, media_id: str, user_id: int, db: Session):
        """Schedule analytics collection for Instagram media"""
        try:
            # Instagram analytics take longer to populate
            await asyncio.sleep(15)  # Brief delay
            await self.collect_media_analytics(user_id, media_id, db)
        except Exception as e:
            logger.error(f"Failed to schedule Instagram analytics collection: {e}")
    
    async def collect_media_analytics(
        self,
        user_id: int,
        media_id: str,
        db: Session
    ) -> InstagramAnalytics:
        """
        Collect and store analytics for Instagram media
        
        Args:
            user_id: User ID
            media_id: Media ID
            db: Database session
            
        Returns:
            Analytics data
        """
        try:
            # Get valid access token
            access_token = await oauth_manager.get_valid_token(user_id, "facebook", db)
            if not access_token:
                raise Exception("No valid Facebook/Instagram connection found")
            
            # Get analytics from Instagram
            analytics = await instagram_client.get_media_insights(access_token, media_id)
            
            # Update content item with latest metrics
            content_item = db.query(ContentItem).filter(
                ContentItem.platform_post_id == media_id,
                ContentItem.user_id == user_id
            ).first()
            
            if content_item:
                content_item.likes_count = analytics.likes
                content_item.shares_count = analytics.shares
                content_item.comments_count = analytics.comments
                content_item.reach_count = analytics.reach
                content_item.engagement_rate = analytics.engagement_rate
                content_item.last_performance_update = datetime.utcnow()
                
                # Update performance tier based on Instagram engagement patterns
                content_item.performance_tier = self._calculate_performance_tier(analytics.engagement_rate)
                
                # Create performance snapshot
                snapshot = ContentPerformanceSnapshot(
                    content_item_id=content_item.id,
                    likes_count=analytics.likes,
                    shares_count=analytics.shares,
                    comments_count=analytics.comments,
                    reach_count=analytics.reach,
                    engagement_rate=analytics.engagement_rate,
                    platform_metrics={
                        "saves": analytics.saves,
                        "video_views": analytics.video_views,
                        "hashtag_impressions": analytics.hashtag_impressions,
                        "profile_visits": analytics.profile_visits,
                        "website_clicks": analytics.website_clicks,
                        "visual_content": True
                    }
                )
                
                db.add(snapshot)
                db.commit()
            
            logger.info(f"Collected Instagram analytics for media {media_id}")
            return analytics
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Failed to collect Instagram analytics: {e}")
            raise
    
    def _calculate_performance_tier(self, engagement_rate: float) -> str:
        """Calculate performance tier for Instagram content"""
        if engagement_rate >= self.engagement_thresholds["viral"]:
            return "viral"
        elif engagement_rate >= self.engagement_thresholds["high"]:
            return "high"
        elif engagement_rate >= self.engagement_thresholds["medium"]:
            return "medium"
        elif engagement_rate >= self.engagement_thresholds["low"]:
            return "low"
        else:
            return "poor"
    
    async def get_hashtag_suggestions(
        self,
        user_id: int,
        content: str,
        limit: int = 15,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get Instagram hashtag suggestions for content
        
        Args:
            user_id: User ID
            content: Content to analyze
            limit: Number of suggestions
            db: Database session
            
        Returns:
            Hashtag suggestions with performance data
        """
        try:
            # Get basic suggestions from client
            suggested_hashtags = instagram_client.suggest_hashtags(content, "BUSINESS")
            
            # Get user's Instagram account type if available
            user_settings = db.query(UserSetting).filter(
                UserSetting.user_id == user_id
            ).first() if db else None
            
            account_type = "BUSINESS"
            if user_settings and user_settings.connected_accounts:
                ig_data = user_settings.connected_accounts.get("instagram", {})
                account_type = ig_data.get("account_type", "BUSINESS")
            
            # Enhance suggestions with performance predictions
            enhanced_suggestions = []
            for hashtag in suggested_hashtags[:limit]:
                # Simplified performance prediction
                popularity_score = 0.7  # Default
                if hashtag in ["#instagood", "#photooftheday", "#instadaily"]:
                    popularity_score = 0.9
                elif hashtag.startswith("#business") or hashtag.startswith("#entrepreneur"):
                    popularity_score = 0.6
                
                enhanced_suggestions.append({
                    "hashtag": hashtag,
                    "popularity_score": popularity_score,
                    "category": self._categorize_hashtag(hashtag),
                    "recommended_for": account_type.lower()
                })
            
            return {
                "status": "success",
                "content_analyzed": content[:100] + "..." if len(content) > 100 else content,
                "account_type": account_type,
                "hashtag_suggestions": enhanced_suggestions,
                "total_suggestions": len(enhanced_suggestions),
                "usage_tips": [
                    "Use 10-15 hashtags for optimal reach",
                    "Mix popular and niche hashtags",
                    "Include branded hashtags for consistency",
                    "Avoid banned or flagged hashtags"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get hashtag suggestions: {e}")
            raise
    
    def _categorize_hashtag(self, hashtag: str) -> str:
        """Categorize hashtag by type"""
        hashtag_lower = hashtag.lower()
        
        if any(word in hashtag_lower for word in ["good", "daily", "photo", "pic"]):
            return "engagement"
        elif any(word in hashtag_lower for word in ["business", "entrepreneur", "work"]):
            return "business"
        elif any(word in hashtag_lower for word in ["food", "travel", "fashion", "fitness"]):
            return "niche"
        elif len(hashtag) > 15:
            return "specific"
        else:
            return "general"
    
    async def get_account_insights(
        self,
        user_id: int,
        ig_account_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get Instagram account insights and recommendations
        
        Args:
            user_id: User ID
            ig_account_id: Instagram account ID
            db: Database session
            
        Returns:
            Account insights and optimization recommendations
        """
        try:
            # Get valid access token
            access_token = await oauth_manager.get_valid_token(user_id, "facebook", db)
            if not access_token:
                raise Exception("No valid Facebook/Instagram connection found")
            
            # Get Instagram accounts if not specified
            if not ig_account_id:
                accounts = await instagram_client.get_instagram_accounts(access_token)
                if not accounts:
                    raise Exception("No Instagram Business accounts found")
                account = accounts[0]
                ig_account_id = account.id
            else:
                account = await instagram_client._get_account_info(access_token, ig_account_id)
            
            if not account:
                raise Exception("Could not retrieve account information")
            
            # Get recent media for analysis
            recent_media = await instagram_client.get_user_media(
                access_token, ig_account_id, limit=20
            )
            
            # Analyze account performance
            insights = {
                "account_info": {
                    "username": account.username,
                    "name": account.name,
                    "followers_count": account.followers_count,
                    "following_count": account.follows_count,
                    "posts_count": account.media_count,
                    "account_type": account.account_type,
                    "biography": account.biography
                },
                "content_analysis": {
                    "recent_posts": len(recent_media),
                    "avg_likes": sum(m.like_count for m in recent_media) / len(recent_media) if recent_media else 0,
                    "avg_comments": sum(m.comments_count for m in recent_media) / len(recent_media) if recent_media else 0,
                    "content_types": self._analyze_content_types(recent_media),
                    "posting_consistency": self._analyze_posting_consistency(recent_media)
                },
                "recommendations": self._generate_account_recommendations(account, recent_media)
            }
            
            return {
                "status": "success",
                "ig_account_id": ig_account_id,
                "insights": insights,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Instagram account insights: {e}")
            raise
    
    def _analyze_content_types(self, media: List[InstagramMedia]) -> Dict[str, Any]:
        """Analyze content type distribution"""
        if not media:
            return {}
        
        type_counts = {}
        for item in media:
            media_type = item.media_type
            type_counts[media_type] = type_counts.get(media_type, 0) + 1
        
        total = len(media)
        return {
            media_type: {
                "count": count,
                "percentage": (count / total) * 100
            }
            for media_type, count in type_counts.items()
        }
    
    def _analyze_posting_consistency(self, media: List[InstagramMedia]) -> Dict[str, Any]:
        """Analyze posting consistency and frequency"""
        if len(media) < 2:
            return {"consistency": "insufficient_data"}
        
        # Calculate days between posts
        dates = [m.timestamp.date() for m in media]
        dates.sort()
        
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        consistency_score = 1.0 / (1.0 + abs(avg_interval - 1))  # Optimal is daily posting
        
        return {
            "avg_days_between_posts": avg_interval,
            "consistency_score": consistency_score,
            "posting_frequency": "daily" if avg_interval <= 1.5 else "irregular",
            "recommendation": "Post more consistently" if consistency_score < 0.7 else "Good posting consistency"
        }
    
    def _generate_account_recommendations(
        self,
        account: InstagramAccount,
        recent_media: List[InstagramMedia]
    ) -> List[str]:
        """Generate account optimization recommendations"""
        recommendations = []
        
        # Biography recommendations
        if not account.biography or len(account.biography) < 50:
            recommendations.append("Optimize your bio with a clear description and call-to-action")
        
        # Posting frequency
        if len(recent_media) < 10:
            recommendations.append("Increase posting frequency for better engagement")
        
        # Content variety
        content_types = self._analyze_content_types(recent_media)
        if len(content_types) < 2:
            recommendations.append("Diversify content types (images, videos, carousels)")
        
        # Engagement rate
        if recent_media:
            avg_engagement = sum(
                (m.like_count + m.comments_count) / max(account.followers_count, 1) * 100
                for m in recent_media
            ) / len(recent_media)
            
            if avg_engagement < 2.0:
                recommendations.append("Focus on creating more engaging content to improve engagement rate")
        
        # Account type optimization
        if account.account_type == "PERSONAL":
            recommendations.append("Consider switching to a Business account for access to analytics and insights")
        
        return recommendations

# Global Instagram service instance
instagram_service = InstagramService()