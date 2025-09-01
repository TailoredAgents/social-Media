"""
Automated Content Generation Pipeline Service
Integration Specialist Component - End-to-end automated content creation and publishing
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import ContentItem, Goal, ContentTemplate
from backend.services.research_automation import research_pipeline, ResearchQuery, ResearchSource
from backend.services.metrics_collection import metrics_collector
from backend.integrations.twitter_client import twitter_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client
from backend.core.vector_store import vector_store

settings = get_settings()
logger = logging.getLogger(__name__)

# Mock SocialMediaAccount for compatibility (since model doesn't exist)
class SocialMediaAccount:
    def __init__(self, platform="mock", account_id="mock123", access_token="mock_token", is_active=True):
        self.platform = platform
        self.account_id = account_id
        self.access_token = access_token
        self.is_active = is_active

class ContentType(Enum):
    """Content types for generation"""
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    VIDEO_POST = "video_post"
    CAROUSEL = "carousel"
    STORY = "story"
    THREAD = "thread"
    ARTICLE = "article"
    POLL = "poll"

class ContentTone(Enum):
    """Content tone options"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    ENTERTAINING = "entertaining"
    INSPIRATIONAL = "inspirational"
    HUMOROUS = "humorous"
    CONVERSATIONAL = "conversational"

@dataclass
class ContentGenerationRequest:
    """Content generation request configuration"""
    topic: str
    platforms: List[str]
    content_type: ContentType
    tone: ContentTone
    target_audience: str
    keywords: List[str]
    goals: List[str]  # Goal IDs or names
    include_hashtags: bool = True
    include_call_to_action: bool = True
    max_length: Optional[int] = None
    include_media: bool = False
    schedule_time: Optional[datetime] = None
    urgency: str = "normal"  # high, normal, low

@dataclass
class GeneratedContent:
    """Generated content result"""
    platform: str
    content_type: ContentType
    title: Optional[str]
    body: str
    hashtags: List[str]
    call_to_action: Optional[str]
    media_suggestions: List[str]
    estimated_engagement: Dict[str, int]
    optimization_score: float
    generated_at: datetime
    template_used: Optional[str] = None
    research_based: bool = False
    
    def get_full_content(self) -> str:
        """Get complete content with hashtags and CTA"""
        content = self.body
        
        if self.call_to_action:
            content += f"\n\n{self.call_to_action}"
        
        if self.hashtags:
            content += f"\n\n{' '.join(self.hashtags)}"
        
        return content

@dataclass
class ContentPublishingResult:
    """Content publishing result"""
    platform: str
    success: bool
    post_id: Optional[str]
    post_url: Optional[str]
    error_message: Optional[str]
    published_at: Optional[datetime]
    scheduled_for: Optional[datetime]

@dataclass
class AutomationPipelineResult:
    """Complete automation pipeline result"""
    request: ContentGenerationRequest
    research_summary: Optional[Dict[str, Any]]
    generated_content: List[GeneratedContent]
    publishing_results: List[ContentPublishingResult]
    total_duration: float
    success_rate: float
    completed_at: datetime

class ContentGenerationAutomation:
    """
    Comprehensive automated content generation and publishing pipeline
    
    Features:
    - Research-driven content generation
    - Multi-platform content optimization
    - AI-powered content creation
    - Automated hashtag generation
    - Engagement prediction
    - Smart scheduling
    - Performance optimization
    - Template-based generation
    - Brand voice consistency
    """
    
    def __init__(self):
        """Initialize content automation pipeline"""
        self.openai_api_key = settings.openai_api_key if hasattr(settings, 'openai_api_key') else None
        
        # Platform-specific content limits with 50-char safety buffer (LinkedIn and TikTok removed)
        self.platform_limits = {
            "twitter": {"text": 280 - 50, "hashtags": 2, "thread_max": 10},
            "instagram": {"text": 2200 - 50, "hashtags": 30, "carousel_max": 10},
            "facebook": {"text": 63206 - 50, "hashtags": 10, "images_max": 10}
        }
        
        # Content templates by type and platform
        self.content_templates = {
            ContentType.TEXT_POST: {
                "professional": "Professional insight about {topic}: {body}",
                "casual": "Quick thought on {topic}: {body}",
                "educational": "Did you know about {topic}? {body}",
                "entertaining": "Fun fact about {topic}: {body}"
            },
            ContentType.IMAGE_POST: {
                "professional": "{body}\n\nImage: Professional visual about {topic}",
                "casual": "{body} 📸\n\nVisual content for {topic}",
                "educational": "Visual guide: {topic}\n\n{body}",
                "entertaining": "{body} 🎨\n\nCreative take on {topic}"
            }
        }
        
        # Hashtag generation prompts
        self.hashtag_prompts = {
            "general": "Generate relevant hashtags for content about {topic} targeting {audience}",
            "trending": "Generate trending hashtags for {topic} based on current social media trends",
            "niche": "Generate niche-specific hashtags for {topic} in the {industry} industry"
        }
        
        logger.info("ContentGenerationAutomation initialized")
    
    async def generate_content(self, platform: str, topic: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Public interface for content generation"""
        try:
            # Import here to avoid circular imports
            from backend.db.database import get_db
            
            # Create a proper content generation request
            request = ContentGenerationRequest(
                topic=topic,
                platforms=[platform],
                content_type=ContentType.TEXT_POST,
                tone=ContentTone.PROFESSIONAL,
                target_audience=context.get("target_audience", "general audience") if context else "general audience",
                keywords=context.get("keywords", []) if context else [],
                goals=context.get("goals", []) if context else [],
                include_hashtags=context.get("include_hashtags", True) if context else True,
                include_call_to_action=context.get("include_call_to_action", True) if context else True,
                max_length=context.get("max_length") if context else None,
                include_media=context.get("include_media", False) if context else False
            )
            
            # Get database session
            db = next(get_db())
            
            try:
                # Use the real content generation pipeline
                generated_content = await self._generate_content(db, request, None)
                
                if generated_content:
                    content_item = generated_content[0]  # Get first result
                    return {
                        "status": "success",
                        "content": content_item.content,
                        "platform": platform,
                        "topic": topic,
                        "context": context or {},
                        "generated_at": datetime.utcnow().isoformat(),
                        "hashtags": getattr(content_item, 'hashtags', []),
                        "call_to_action": getattr(content_item, 'call_to_action', None)
                    }
                else:
                    return {
                        "status": "error",
                        "error": "No content was generated",
                        "platform": platform,
                        "topic": topic
                    }
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "platform": platform,
                "topic": topic
            }
    
    async def execute_automation_pipeline(
        self,
        db: Session,
        request: ContentGenerationRequest,
        publish_immediately: bool = False
    ) -> AutomationPipelineResult:
        """
        Execute complete automated content generation and publishing pipeline
        
        Args:
            db: Database session
            request: Content generation request
            publish_immediately: Whether to publish content immediately
            
        Returns:
            Complete pipeline result
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting automation pipeline for topic: {request.topic}")
        
        try:
            # Phase 1: Research (if needed)
            research_summary = None
            if request.urgency != "high":
                research_summary = await self._conduct_research(request)
            
            # Phase 2: Content Generation
            generated_content = await self._generate_content(db, request, research_summary)
            
            # Phase 3: Content Publishing (if requested)
            publishing_results = []
            if publish_immediately:
                publishing_results = await self._publish_content(db, generated_content, request)
            elif request.schedule_time:
                publishing_results = await self._schedule_content(db, generated_content, request)
            
            # Calculate success metrics
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            success_rate = len([r for r in publishing_results if r.success]) / len(publishing_results) if publishing_results else 1.0
            
            result = AutomationPipelineResult(
                request=request,
                research_summary=research_summary,
                generated_content=generated_content,
                publishing_results=publishing_results,
                total_duration=total_duration,
                success_rate=success_rate,
                completed_at=datetime.utcnow()
            )
            
            # Save automation result to database
            await self._save_automation_result(db, result)
            
            logger.info(f"Automation pipeline completed in {total_duration:.2f}s with {success_rate:.1%} success rate")
            
            return result
            
        except Exception as e:
            logger.error(f"Automation pipeline failed: {e}")
            raise
    
    async def _conduct_research(self, request: ContentGenerationRequest) -> Dict[str, Any]:
        """Conduct research for content generation"""
        try:
            # Create research query
            research_query = ResearchQuery(
                keywords=[request.topic] + request.keywords,
                platforms=[ResearchSource.TWITTER, ResearchSource.INSTAGRAM, ResearchSource.NEWS_API],
                content_types=["text", "image"],
                time_range="24h",
                max_results=50,
                include_sentiment=True,
                include_engagement=True
            )
            
            # Execute research
            research_summary = await research_pipeline.execute_research(
                db=None,  # Research pipeline handles its own DB session
                query=research_query,
                save_results=True
            )
            
            return {
                "total_results": research_summary.total_results,
                "trending_topics": [asdict(t) for t in research_summary.trending_topics[:5]],
                "sentiment_breakdown": research_summary.sentiment_breakdown,
                "research_duration": research_summary.research_duration
            }
            
        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            return {"error": str(e)}
    
    async def _generate_content(
        self,
        db: Session,
        request: ContentGenerationRequest,
        research_summary: Optional[Dict[str, Any]]
    ) -> List[GeneratedContent]:
        """Generate content for all requested platforms"""
        generated_content = []
        
        for platform in request.platforms:
            try:
                # Generate platform-specific content
                content = await self._generate_platform_content(
                    db, request, platform, research_summary
                )
                
                if content:
                    generated_content.append(content)
                    
                # Brief delay between generations
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Content generation failed for {platform}: {e}")
        
        return generated_content
    
    async def _generate_platform_content(
        self,
        db: Session,
        request: ContentGenerationRequest,
        platform: str,
        research_summary: Optional[Dict[str, Any]]
    ) -> Optional[GeneratedContent]:
        """Generate content for a specific platform"""
        try:
            # Get platform limits
            limits = self.platform_limits.get(platform, {"text": 1000, "hashtags": 5})
            
            # Generate main content
            body = await self._generate_content_body(request, platform, research_summary, limits)
            
            # Generate hashtags
            hashtags = await self._generate_hashtags(request, platform, limits)
            
            # Generate call-to-action
            call_to_action = await self._generate_call_to_action(request, platform) if request.include_call_to_action else None
            
            # Generate media suggestions
            media_suggestions = await self._generate_media_suggestions(request, platform)
            
            # Estimate engagement
            estimated_engagement = await self._estimate_engagement(body, platform, hashtags)
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                body, hashtags, call_to_action, platform, limits
            )
            
            # Generate title if needed
            title = await self._generate_title(request, platform) if platform in ["facebook"] else None
            
            content = GeneratedContent(
                platform=platform,
                content_type=request.content_type,
                title=title,
                body=body,
                hashtags=hashtags,
                call_to_action=call_to_action,
                media_suggestions=media_suggestions,
                estimated_engagement=estimated_engagement,
                optimization_score=optimization_score,
                generated_at=datetime.utcnow(),
                research_based=research_summary is not None
            )
            
            logger.info(f"Generated content for {platform} with {optimization_score:.2f} optimization score")
            
            return content
            
        except Exception as e:
            logger.error(f"Platform content generation failed for {platform}: {e}")
            return None
    
    async def _generate_content_body(
        self,
        request: ContentGenerationRequest,
        platform: str,
        research_summary: Optional[Dict[str, Any]],
        limits: Dict[str, int]
    ) -> str:
        """Generate main content body using AI"""
        try:
            # Build context from research
            research_context = ""
            if research_summary and research_summary.get("trending_topics"):
                trending = research_summary["trending_topics"][0]
                research_context = f"Based on current trends: {trending.get('topic', '')} is trending with {trending.get('sentiment', 'neutral')} sentiment."
            
            # Create generation prompt
            max_chars = min(limits.get("text", 1000), request.max_length or 1000)
            
            if self.openai_api_key:
                # Use OpenAI API for content generation
                body = await self._generate_with_openai(request, platform, research_context, max_chars)
            else:
                # Use template-based generation
                body = await self._generate_with_template(request, platform, research_context, max_chars)
            
            return body
            
        except Exception as e:
            logger.error(f"Content body generation failed: {e}")
            # Fallback to simple template
            return f"Sharing insights about {request.topic}. {research_context}"
    
    async def _generate_with_openai(
        self,
        request: ContentGenerationRequest,
        platform: str,
        research_context: str,
        max_chars: int
    ) -> str:
        """Generate content using OpenAI API"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not configured, falling back to template")
                return await self._generate_with_template(request, platform, research_context, max_chars)
            
            from openai import AsyncOpenAI
            
            # Initialize async OpenAI client
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Build strict prompt
            strict_limit = max_chars - 10  # Extra safety margin
            prompt = f"""
            Create engaging {platform} content about {request.topic}.
            
            🚨 CRITICAL CHARACTER LIMIT: {strict_limit} characters maximum
            - COUNT EVERY CHARACTER including spaces, punctuation, hashtags
            - YOUR RESPONSE MUST BE UNDER {strict_limit} CHARACTERS (strict limit)
            - This is for {platform} - exceeding the limit will break the post
            - AIM for {strict_limit - 20} characters to be safe
            
            Requirements:
            - Tone: {request.tone.value}
            - Target audience: {request.target_audience}
            - Content type: {request.content_type.value}
            - Keywords to include: {', '.join(request.keywords)}
            
            Context: {research_context}
            
            IMPORTANT: Count characters as you write. Write concisely. Quality over quantity.
            Return ONLY the final content text under {strict_limit} characters. No explanations or extra text.
            """
            
            # Build messages
            messages = [
                {"role": "system", "content": "You are an expert social media content creator with web search capabilities. Use current information when relevant."},
                {"role": "user", "content": prompt}
            ]
            
            # Create chat completion using openai_utils for correct parameters
            from backend.core.openai_utils import get_openai_completion_params
            
            params = get_openai_completion_params(
                model="gpt-4.1-mini",
                max_tokens=min(max_chars // 3, 500),
                temperature=0.7,
                messages=messages
            )
            
            # Web search tool not supported - removed to prevent API errors
            # Using research context in prompts instead
            
            response = await client.chat.completions.create(**params)
            
            content = response.choices[0].message.content.strip()
            
            # Ensure content fits within limits with extra safety
            if len(content) > max_chars:
                logger.warning(f"Content exceeded {max_chars} chars ({len(content)}), truncating")
                # Truncate more aggressively to stay well under limit
                safe_limit = max_chars - 20  # 20 char safety buffer
                content = content[:safe_limit].rsplit(' ', 1)[0] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"OpenAI content generation failed: {e}")
            # Fallback to template
            return await self._generate_with_template(request, platform, research_context, max_chars)
    
    async def _generate_with_template(
        self,
        request: ContentGenerationRequest,
        platform: str,
        research_context: str,
        max_chars: int
    ) -> str:
        """Generate content using templates"""
        try:
            # Get template
            template_key = request.tone.value
            template = self.content_templates.get(request.content_type, {}).get(
                template_key, 
                f"Sharing valuable insights about {{topic}}: {{body}}"
            )
            
            # Generate content based on topic and research
            if research_context:
                body_content = f"{research_context} Here's what this means for {request.target_audience}."
            else:
                body_content = f"Important update about {request.topic} for {request.target_audience}."
            
            # Format template
            content = template.format(
                topic=request.topic,
                body=body_content
            )
            
            # Ensure content fits within limits
            if len(content) > max_chars:
                content = content[:max_chars-3] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"Template content generation failed: {e}")
            return f"Update about {request.topic}"
    
    async def _generate_hashtags(
        self,
        request: ContentGenerationRequest,
        platform: str,
        limits: Dict[str, int]
    ) -> List[str]:
        """Generate relevant hashtags"""
        if not request.include_hashtags:
            return []
        
        try:
            max_hashtags = limits.get("hashtags", 5)
            
            # Start with keywords as hashtags
            hashtags = [f"#{keyword.replace(' ', '')}" for keyword in request.keywords[:max_hashtags//2]]
            
            # Add topic-based hashtags
            topic_tags = [f"#{request.topic.replace(' ', '')}"]
            
            # Add platform-specific popular hashtags
            platform_tags = self._get_platform_hashtags(platform, request.topic)
            
            # Combine and deduplicate
            all_hashtags = hashtags + topic_tags + platform_tags
            unique_hashtags = list(dict.fromkeys(all_hashtags))  # Preserve order, remove duplicates
            
            return unique_hashtags[:max_hashtags]
            
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return [f"#{request.topic.replace(' ', '')}"]
    
    def _get_platform_hashtags(self, platform: str, topic: str) -> List[str]:
        """Get platform-specific hashtags"""
        platform_hashtags = {
            "twitter": ["#TwitterChat", "#Thread", "#Insights"],
            "instagram": ["#InstaGood", "#PhotoOfTheDay", "#MotivationMonday"],
            "facebook": ["#Community", "#Discussion", "#Share"]
        }
        
        base_tags = platform_hashtags.get(platform, [])
        
        # Add topic-specific variations
        topic_variations = [
            f"#{topic.title().replace(' ', '')}Tips",
            f"#{topic.title().replace(' ', '')}News",
            f"#{topic.title().replace(' ', '')}Insights"
        ]
        
        return base_tags + topic_variations
    
    async def _generate_call_to_action(self, request: ContentGenerationRequest, platform: str) -> Optional[str]:
        """Generate platform-specific call-to-action"""
        try:
            cta_templates = {
                "twitter": [
                    "What are your thoughts? Reply below! 👇",
                    "Retweet if you agree! 🔄",
                    "Share your experience in the comments! 💬"
                ],
                "instagram": [
                    "Double tap if you love this! ❤️",
                    "Tag someone who needs to see this! 👆",
                    "Save this post for later! 📱"
                ],
                "facebook": [
                    "What do you think? Let us know in the comments!",
                    "Share this with your friends!",
                    "Join the conversation below! 👇"
                ],
            }
            
            platform_ctas = cta_templates.get(platform, ["Let us know what you think!"])
            
            # Simple selection - in production would use more sophisticated logic
            import random
            return random.choice(platform_ctas)
            
        except Exception as e:
            logger.error(f"CTA generation failed: {e}")
            return "Let us know what you think!"
    
    async def _generate_media_suggestions(self, request: ContentGenerationRequest, platform: str) -> List[str]:
        """Generate media suggestions for content"""
        if not request.include_media:
            return []
        
        try:
            media_suggestions = []
            
            if request.content_type == ContentType.IMAGE_POST:
                media_suggestions = [
                    f"Professional image related to {request.topic}",
                    f"Infographic about {request.topic}",
                    f"Quote graphic for {request.topic}"
                ]
            elif request.content_type == ContentType.VIDEO_POST:
                media_suggestions = [
                    f"Short video explaining {request.topic}",
                    f"Behind-the-scenes content about {request.topic}",
                    f"Tutorial video on {request.topic}"
                ]
            elif request.content_type == ContentType.CAROUSEL:
                media_suggestions = [
                    f"Step-by-step carousel about {request.topic}",
                    f"Before/after carousel for {request.topic}",
                    f"Tips carousel related to {request.topic}"
                ]
            
            return media_suggestions
            
        except Exception as e:
            logger.error(f"Media suggestions generation failed: {e}")
            return []
    
    async def _estimate_engagement(
        self,
        content: str,
        platform: str,
        hashtags: List[str]
    ) -> Dict[str, int]:
        """Estimate engagement metrics for content"""
        try:
            # Simple engagement estimation based on content characteristics
            # In production, this would use ML models trained on historical data
            
            base_engagement = {
                "twitter": {"likes": 10, "retweets": 2, "replies": 1},
                "instagram": {"likes": 50, "comments": 5, "shares": 1},
                "facebook": {"likes": 25, "comments": 3, "shares": 2}
            }
            
            platform_base = base_engagement.get(platform, {"likes": 10, "comments": 1, "shares": 1})
            
            # Adjust based on content characteristics
            multiplier = 1.0
            
            # More hashtags = potentially more reach
            if len(hashtags) > 3:
                multiplier += 0.2
            
            # Longer content might get more engagement on some platforms
            if len(content) > 100 and platform in ["facebook"]:
                multiplier += 0.1
            
            # Question in content increases engagement
            if "?" in content:
                multiplier += 0.3
            
            # Apply multiplier
            estimated = {}
            for metric, value in platform_base.items():
                estimated[metric] = int(value * multiplier)
            
            return estimated
            
        except Exception as e:
            logger.error(f"Engagement estimation failed: {e}")
            return {"likes": 10, "comments": 1, "shares": 1}
    
    def _calculate_optimization_score(
        self,
        content: str,
        hashtags: List[str],
        call_to_action: Optional[str],
        platform: str,
        limits: Dict[str, int]
    ) -> float:
        """Calculate content optimization score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Content length optimization
            content_length = len(content)
            optimal_length = limits.get("text", 1000) * 0.7  # 70% of max is often optimal
            
            if content_length <= optimal_length:
                score += 2.0
            elif content_length <= limits.get("text", 1000):
                score += 1.5
            else:
                score += 0.5  # Over limit penalty
            
            # Hashtag optimization
            optimal_hashtags = min(limits.get("hashtags", 5), 5)
            if len(hashtags) >= optimal_hashtags * 0.5:
                score += 2.0
            elif len(hashtags) > 0:
                score += 1.0
            
            # Call-to-action presence
            if call_to_action:
                score += 2.0
            
            # Content engagement indicators
            if "?" in content:  # Questions engage
                score += 1.0
            if any(word in content.lower() for word in ["you", "your", "we", "us"]):  # Personal pronouns
                score += 1.0
            if any(emoji in content for emoji in ["👇", "💬", "🔄", "❤️", "📱"]):  # Engaging emojis
                score += 1.0
            
            # Platform-specific optimizations
            if platform == "twitter" and len(content.split()) < 20:  # Concise for Twitter
                score += 1.0
            elif platform == "instagram" and len(hashtags) >= 5:  # More hashtags for Instagram
                score += 1.0
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Optimization score calculation failed: {e}")
            return 5.0  # Default middle score
    
    async def _generate_title(self, request: ContentGenerationRequest, platform: str) -> Optional[str]:
        """Generate title for platforms that support it"""
        if platform not in ["facebook"]:
            return None
        
        try:
            # Simple title generation
            if request.content_type == ContentType.ARTICLE:
                return f"Insights on {request.topic}: What {request.target_audience} Need to Know"
            else:
                return f"{request.topic}: Key Updates for {request.target_audience}"
                
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return request.topic
    
    async def _publish_content(
        self,
        db: Session,
        content_list: List[GeneratedContent],
        request: ContentGenerationRequest
    ) -> List[ContentPublishingResult]:
        """Publish content to social media platforms"""
        publishing_results = []
        
        for content in content_list:
            try:
                result = await self._publish_to_platform(db, content, request)
                publishing_results.append(result)
                
                # Delay between publications
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Publishing failed for {content.platform}: {e}")
                publishing_results.append(ContentPublishingResult(
                    platform=content.platform,
                    success=False,
                    post_id=None,
                    post_url=None,
                    error_message=str(e),
                    published_at=None,
                    scheduled_for=None
                ))
        
        return publishing_results
    
    async def _publish_to_platform(
        self,
        db: Session,
        content: GeneratedContent,
        request: ContentGenerationRequest
    ) -> ContentPublishingResult:
        """Publish content to a specific platform"""
        try:
            # Get active account for platform (use mock for testing)
            account = SocialMediaAccount(
                platform=content.platform,
                account_id=f"mock_{content.platform}_123",
                access_token="mock_token_for_testing",
                is_active=True
            )
            
            # Publish based on platform
            if content.platform == "twitter":
                return await self._publish_to_twitter(account, content)
            elif content.platform == "instagram":
                return await self._publish_to_instagram(account, content)
            elif content.platform == "facebook":
                return await self._publish_to_facebook(account, content)
            else:
                raise Exception(f"Platform {content.platform} not supported for publishing")
                
        except Exception as e:
            logger.error(f"Platform publishing failed: {e}")
            raise
    
    async def _publish_to_twitter(
        self,
        account: SocialMediaAccount,
        content: GeneratedContent
    ) -> ContentPublishingResult:
        """Publish content to Twitter"""
        try:
            full_content = content.get_full_content()
            
            # Handle content that's too long for Twitter
            if len(full_content) > 280:
                # Create thread if content is too long
                tweets = self._split_content_for_thread(full_content, 280)
                thread_result = await twitter_client.post_thread(
                    access_token=account.access_token,
                    tweets=tweets
                )
                
                post_id = thread_result.thread_id
                post_url = f"https://twitter.com/{account.username}/status/{post_id}"
            else:
                # Single tweet
                tweet_result = await twitter_client.post_tweet(
                    access_token=account.access_token,
                    text=full_content
                )
                
                post_id = tweet_result.id
                post_url = f"https://twitter.com/{account.username}/status/{post_id}"
            
            return ContentPublishingResult(
                platform="twitter",
                success=True,
                post_id=post_id,
                post_url=post_url,
                error_message=None,
                published_at=datetime.utcnow(),
                scheduled_for=None
            )
            
        except Exception as e:
            logger.error(f"Twitter publishing failed: {e}")
            return ContentPublishingResult(
                platform="twitter",
                success=False,
                post_id=None,
                post_url=None,
                error_message=str(e),
                published_at=None,
                scheduled_for=None
            )
    
    async def _publish_to_instagram(
        self,
        account: SocialMediaAccount,
        content: GeneratedContent
    ) -> ContentPublishingResult:
        """Publish content to Instagram"""
        try:
            # Instagram requires media, so this is a placeholder
            # In production, would need to handle media upload
            raise Exception("Instagram publishing requires media upload implementation")
            
        except Exception as e:
            logger.error(f"Instagram publishing failed: {e}")
            return ContentPublishingResult(
                platform="instagram",
                success=False,
                post_id=None,
                post_url=None,
                error_message=str(e),
                published_at=None,
                scheduled_for=None
            )
    
    async def _publish_to_facebook(
        self,
        account: SocialMediaAccount,
        content: GeneratedContent
    ) -> ContentPublishingResult:
        """Publish content to Facebook"""
        try:
            full_content = content.get_full_content()
            
            post_result = await facebook_client.create_text_post(
                page_access_token=account.access_token,
                page_id=account.account_id,
                message=full_content
            )
            
            post_id = post_result.id
            post_url = f"https://facebook.com/{post_id}"
            
            return ContentPublishingResult(
                platform="facebook",
                success=True,
                post_id=post_id,
                post_url=post_url,
                error_message=None,
                published_at=datetime.utcnow(),
                scheduled_for=None
            )
            
        except Exception as e:
            logger.error(f"Facebook publishing failed: {e}")
            return ContentPublishingResult(
                platform="facebook",
                success=False,
                post_id=None,
                post_url=None,
                error_message=str(e),
                published_at=None,
                scheduled_for=None
            )
    
    def _split_content_for_thread(self, content: str, max_length: int) -> List[str]:
        """Split long content into thread-appropriate chunks"""
        tweets = []
        words = content.split()
        current_tweet = ""
        
        for word in words:
            if len(current_tweet + " " + word) <= max_length - 10:  # Leave room for thread numbering
                current_tweet += " " + word if current_tweet else word
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = word
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        # Add thread numbering if more than one tweet
        if len(tweets) > 1:
            for i, tweet in enumerate(tweets):
                tweets[i] = f"{i+1}/{len(tweets)} {tweet}"
        
        return tweets
    
    async def _schedule_content(
        self,
        db: Session,
        content_list: List[GeneratedContent],
        request: ContentGenerationRequest
    ) -> List[ContentPublishingResult]:
        """Schedule content for future publishing"""
        scheduling_results = []
        
        for content in content_list:
            try:
                # Save content to database for scheduled publishing
                content_item = ContentItem(
                    title=content.title,
                    content=content.get_full_content(),
                    platform=content.platform,
                    content_type=content.content_type.value,
                    status="scheduled",
                    scheduled_for=request.schedule_time,
                    hashtags=content.hashtags,
                    generated_by="automation",
                    optimization_score=content.optimization_score
                )
                
                db.add(content_item)
                db.commit()
                
                scheduling_results.append(ContentPublishingResult(
                    platform=content.platform,
                    success=True,
                    post_id=None,
                    post_url=None,
                    error_message=None,
                    published_at=None,
                    scheduled_for=request.schedule_time
                ))
                
            except Exception as e:
                logger.error(f"Content scheduling failed for {content.platform}: {e}")
                scheduling_results.append(ContentPublishingResult(
                    platform=content.platform,
                    success=False,
                    post_id=None,
                    post_url=None,
                    error_message=str(e),
                    published_at=None,
                    scheduled_for=None
                ))
        
        return scheduling_results
    
    async def _save_automation_result(
        self,
        db: Session,
        result: AutomationPipelineResult
    ):
        """Save automation pipeline result to database"""
        try:
            # Create summary record (would need to add AutomationLog model)
            # For now, just log the results
            logger.info(f"Automation completed: {len(result.generated_content)} content pieces, {result.success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"Failed to save automation result: {e}")

# Global content automation instance
content_automation = ContentGenerationAutomation()

# Export alias for backward compatibility
content_automation_service = content_automation

# Explicit exports for better maintainability
__all__ = [
    'ContentGenerationAutomation',
    'content_automation',
    'content_automation_service'
]