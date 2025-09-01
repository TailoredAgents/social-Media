"""
Automated Content Generation Pipeline
Integration Specialist Component - AI-powered content creation and optimization system
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

from backend.core.config import get_settings
from backend.agents.crew_config import (
    content_agent, create_content_generation_task, create_daily_crew
)
from backend.services.research_automation_service import research_automation_service, ResearchType
from backend.services.metrics_collection_service import metrics_collector
from backend.integrations.twitter_client import twitter_client
# LinkedIn integration removed - using stub
linkedin_client = None
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client
from backend.core.vector_store import vector_store
from backend.db.database import get_db_session
from backend.db.models import ContentItem, Goal
from crewai import Crew, Process, Task
from openai import OpenAI

settings = get_settings()
logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content types for generation"""
    SOCIAL_POST = "social_post"
    THREAD = "thread"
    ARTICLE = "article"
    VIDEO_SCRIPT = "video_script"
    CAROUSEL = "carousel"
    STORY = "story"
    NEWSLETTER = "newsletter"

class Platform(Enum):
    """Target platforms"""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    ALL = "all"

class ContentTone(Enum):
    """Content tone options"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INSPIRING = "inspiring"
    EDUCATIONAL = "educational"
    HUMOROUS = "humorous"
    AUTHORITATIVE = "authoritative"

@dataclass
class ContentPrompt:
    """Content generation prompt configuration"""
    prompt_id: str
    content_type: ContentType
    platform: Platform
    tone: ContentTone
    topic: str
    keywords: List[str]
    target_audience: str
    goals: List[str]
    constraints: Dict[str, Any]
    research_context: Optional[str] = None
    brand_voice: str = "professional"
    call_to_action: Optional[str] = None

@dataclass
class GeneratedContent:
    """Generated content structure"""
    content_id: str
    prompt_id: str
    content_type: ContentType
    platform: Platform
    
    # Content data
    title: Optional[str]
    body: str
    hashtags: List[str]
    mentions: List[str]
    media_suggestions: List[str]
    
    # Metadata
    generated_at: datetime
    tone: ContentTone
    topic: str
    keywords: List[str]
    word_count: int
    character_count: int
    
    # Performance predictions
    predicted_engagement_rate: float
    predicted_reach: int
    viral_potential: float
    
    # Platform-specific versions
    platform_versions: Dict[str, str]
    
    # Quality metrics
    originality_score: float
    brand_alignment_score: float
    seo_score: float

@dataclass
class ContentPipeline:
    """Content generation pipeline configuration"""
    pipeline_id: str
    name: str
    content_types: List[ContentType]
    platforms: List[Platform]
    generation_frequency: int  # seconds
    topics: List[str]
    tone: ContentTone
    research_enabled: bool
    auto_publish: bool
    quality_threshold: float
    is_active: bool
    last_generated: Optional[datetime] = None

class ContentGenerationService:
    """
    Automated Content Generation Service
    
    Features:
    - Multi-platform content generation
    - AI-powered content creation with CrewAI
    - Research-driven content topics
    - Brand voice consistency
    - Performance prediction
    - Quality scoring and filtering
    - Platform-specific optimization
    - Automated publishing pipeline
    - Content variation and A/B testing
    - Trend-based content adaptation
    """
    
    def __init__(self):
        """Initialize content generation service"""
        self.content_pipelines: Dict[str, ContentPipeline] = {}
        self.generated_content: List[GeneratedContent] = []
        self.content_templates: Dict[str, Dict[str, Any]] = {}
        
        # AI clients
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Platform clients
        self.platform_clients = {
            Platform.TWITTER: twitter_client,
            # Platform.LINKEDIN: removed - LinkedIn integration disabled
            Platform.INSTAGRAM: instagram_client,
            Platform.FACEBOOK: facebook_client
        }
        
        # Generation statistics
        self.stats = {
            "total_generated": 0,
            "published_content": 0,
            "high_quality_content": 0,
            "viral_predictions": 0,
            "pipeline_executions": 0
        }
        
        # Service state
        self._running = False
        self._generation_task = None
        
        # Load content templates
        self._initialize_templates()
        
        logger.info("ContentGenerationService initialized")
    
    def _initialize_templates(self):
        """Initialize content templates for different types"""
        self.content_templates = {
            ContentType.SOCIAL_POST.value: {
                "structure": "Hook + Value + CTA",
                "max_length": {"twitter": 280, "linkedin": 3000, "instagram": 2200, "facebook": 63206},
                "hashtag_count": {"twitter": 2, "linkedin": 5, "instagram": 10, "facebook": 5},
                "best_practices": ["Start with a hook", "Provide clear value", "Include relevant hashtags", "End with CTA"]
            },
            ContentType.THREAD.value: {
                "structure": "Introduction + Points + Conclusion",
                "tweet_count": {"min": 3, "max": 10},
                "numbering": True,
                "conclusion_cta": True
            },
            ContentType.ARTICLE.value: {
                "structure": "Title + Introduction + Body + Conclusion",
                "word_count": {"min": 800, "max": 2000},
                "sections": 3,
                "include_examples": True
            }
        }
    
    async def start_automation(self):
        """Start the content generation automation"""
        if self._running:
            logger.warning("Content generation already running")
            return
        
        self._running = True
        self._generation_task = asyncio.create_task(self._generation_loop())
        logger.info("Started content generation automation")
    
    async def stop_automation(self):
        """Stop the content generation automation"""
        self._running = False
        if self._generation_task:
            self._generation_task.cancel()
            try:
                await self._generation_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped content generation automation")
    
    async def create_content_pipeline(
        self,
        name: str,
        content_types: List[ContentType],
        platforms: List[Platform],
        topics: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        generation_frequency: int = 3600,
        research_enabled: bool = True,
        auto_publish: bool = False,
        quality_threshold: float = 70.0
    ) -> str:
        """
        Create a new content generation pipeline
        
        Args:
            name: Pipeline name
            content_types: Types of content to generate
            platforms: Target platforms
            topics: Content topics
            tone: Content tone
            generation_frequency: Generation frequency in seconds
            research_enabled: Whether to use research data
            auto_publish: Whether to auto-publish content
            quality_threshold: Minimum quality score for content
            
        Returns:
            Pipeline ID
        """
        pipeline_id = f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        pipeline = ContentPipeline(
            pipeline_id=pipeline_id,
            name=name,
            content_types=content_types,
            platforms=platforms,
            generation_frequency=generation_frequency,
            topics=topics,
            tone=tone,
            research_enabled=research_enabled,
            auto_publish=auto_publish,
            quality_threshold=quality_threshold,
            is_active=True
        )
        
        self.content_pipelines[pipeline_id] = pipeline
        logger.info(f"Created content pipeline: {pipeline_id}")
        
        # Generate initial content
        await self._execute_pipeline(pipeline_id, pipeline)
        
        return pipeline_id
    
    async def generate_content_now(
        self,
        content_type: ContentType,
        platform: Platform,
        topic: str,
        tone: ContentTone = ContentTone.PROFESSIONAL,
        keywords: Optional[List[str]] = None,
        research_context: Optional[str] = None
    ) -> Optional[GeneratedContent]:
        """
        Generate content immediately
        
        Args:
            content_type: Type of content to generate
            platform: Target platform
            topic: Content topic
            tone: Content tone
            keywords: Target keywords
            research_context: Research context to use
            
        Returns:
            Generated content or None if failed
        """
        try:
            # Create content prompt
            prompt = ContentPrompt(
                prompt_id=f"immediate_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                content_type=content_type,
                platform=platform,
                tone=tone,
                topic=topic,
                keywords=keywords or [],
                target_audience="professional audience",
                goals=["engagement", "brand_awareness"],
                constraints=self._get_platform_constraints(platform),
                research_context=research_context,
                brand_voice=tone.value
            )
            
            # Generate content
            generated_content = await self._generate_content_from_prompt(prompt)
            
            if generated_content:
                # Store content
                await self._store_generated_content(generated_content)
                self.generated_content.append(generated_content)
                self.stats["total_generated"] += 1
                
                if generated_content.originality_score >= 70:
                    self.stats["high_quality_content"] += 1
                
                return generated_content
            
        except Exception as e:
            logger.error(f"Failed to generate immediate content: {e}")
        
        return None
    
    async def _generation_loop(self):
        """Main content generation loop"""
        while self._running:
            try:
                # Execute ready pipelines
                ready_pipelines = self._get_ready_pipelines()
                
                for pipeline_id, pipeline in ready_pipelines:
                    if not self._running:
                        break
                    
                    await self._execute_pipeline(pipeline_id, pipeline)
                    await asyncio.sleep(10)  # Brief pause between pipelines
                
                # Clean up old content
                await self._cleanup_old_content()
                
                # Sleep before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in content generation loop: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    def _get_ready_pipelines(self) -> List[Tuple[str, ContentPipeline]]:
        """Get pipelines ready for execution"""
        ready_pipelines = []
        current_time = datetime.utcnow()
        
        for pipeline_id, pipeline in self.content_pipelines.items():
            if not pipeline.is_active:
                continue
            
            if pipeline.last_generated is None:
                ready_pipelines.append((pipeline_id, pipeline))
            else:
                time_since_last = current_time - pipeline.last_generated
                if time_since_last.total_seconds() >= pipeline.generation_frequency:
                    ready_pipelines.append((pipeline_id, pipeline))
        
        return ready_pipelines
    
    async def _execute_pipeline(self, pipeline_id: str, pipeline: ContentPipeline):
        """Execute a content generation pipeline"""
        try:
            logger.info(f"Executing content pipeline: {pipeline_id}")
            
            # Get research context if enabled
            research_context = None
            if pipeline.research_enabled:
                research_context = await self._get_research_context(pipeline.topics)
            
            # Generate content for each type and platform combination
            for content_type in pipeline.content_types:
                for platform in pipeline.platforms:
                    if platform == Platform.ALL:
                        # Generate for all platforms
                        for p in [Platform.TWITTER, Platform.LINKEDIN, Platform.INSTAGRAM, Platform.FACEBOOK]:
                            await self._generate_pipeline_content(
                                pipeline, content_type, p, research_context
                            )
                    else:
                        await self._generate_pipeline_content(
                            pipeline, content_type, platform, research_context
                        )
            
            # Update pipeline
            pipeline.last_generated = datetime.utcnow()
            self.stats["pipeline_executions"] += 1
            
            logger.info(f"Completed content pipeline: {pipeline_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute pipeline {pipeline_id}: {e}")
    
    async def _generate_pipeline_content(
        self,
        pipeline: ContentPipeline,
        content_type: ContentType,
        platform: Platform,
        research_context: Optional[str]
    ):
        """Generate content for a specific pipeline, type, and platform"""
        try:
            # Select topic (rotate through topics)
            topic = pipeline.topics[self.stats["total_generated"] % len(pipeline.topics)]
            
            # Create content prompt
            prompt = ContentPrompt(
                prompt_id=f"{pipeline.pipeline_id}_{content_type.value}_{platform.value}",
                content_type=content_type,
                platform=platform,
                tone=pipeline.tone,
                topic=topic,
                keywords=await self._extract_trending_keywords(topic),
                target_audience="professional audience",
                goals=["engagement", "brand_awareness", "thought_leadership"],
                constraints=self._get_platform_constraints(platform),
                research_context=research_context,
                brand_voice=pipeline.tone.value
            )
            
            # Generate content
            generated_content = await self._generate_content_from_prompt(prompt)
            
            if generated_content and generated_content.originality_score >= pipeline.quality_threshold:
                # Store content
                await self._store_generated_content(generated_content)
                self.generated_content.append(generated_content)
                self.stats["total_generated"] += 1
                
                if generated_content.originality_score >= 80:
                    self.stats["high_quality_content"] += 1
                
                if generated_content.viral_potential >= 70:
                    self.stats["viral_predictions"] += 1
                
                # Auto-publish if enabled
                if pipeline.auto_publish:
                    await self._publish_content(generated_content)
            
        except Exception as e:
            logger.error(f"Failed to generate pipeline content: {e}")
    
    async def _generate_content_from_prompt(self, prompt: ContentPrompt) -> Optional[GeneratedContent]:
        """Generate content from a prompt using AI"""
        try:
            # Build generation prompt
            generation_prompt = self._build_generation_prompt(prompt)
            
            # Use CrewAI content agent
            content_task = Task(
                description=generation_prompt,
                agent=content_agent,
                expected_output="Complete content piece with title, body, hashtags, and platform-specific versions"
            )
            
            crew = Crew(
                agents=[content_agent],
                tasks=[content_task],
                process=Process.sequential,
                verbose=False
            )
            
            # Generate content
            crew_result = await asyncio.to_thread(crew.kickoff)
            content_text = str(crew_result)
            
            # Parse generated content
            parsed_content = self._parse_generated_content(content_text, prompt)
            
            if parsed_content:
                # Create platform-specific versions
                platform_versions = await self._create_platform_versions(parsed_content, prompt)
                
                # Calculate quality scores
                originality_score = await self._calculate_originality_score(parsed_content["body"])
                brand_alignment_score = self._calculate_brand_alignment_score(parsed_content["body"], prompt.tone)
                seo_score = self._calculate_seo_score(parsed_content["body"], prompt.keywords)
                
                # Predict performance
                predicted_engagement, predicted_reach, viral_potential = await self._predict_performance(
                    parsed_content, prompt.platform
                )
                
                # Create GeneratedContent object
                content_id = hashlib.md5(
                    f"{prompt.prompt_id}_{parsed_content['body'][:50]}".encode()
                ).hexdigest()[:12]
                
                generated_content = GeneratedContent(
                    content_id=content_id,
                    prompt_id=prompt.prompt_id,
                    content_type=prompt.content_type,
                    platform=prompt.platform,
                    title=parsed_content.get("title"),
                    body=parsed_content["body"],
                    hashtags=parsed_content.get("hashtags", []),
                    mentions=parsed_content.get("mentions", []),
                    media_suggestions=parsed_content.get("media_suggestions", []),
                    generated_at=datetime.utcnow(),
                    tone=prompt.tone,
                    topic=prompt.topic,
                    keywords=prompt.keywords,
                    word_count=len(parsed_content["body"].split()),
                    character_count=len(parsed_content["body"]),
                    predicted_engagement_rate=predicted_engagement,
                    predicted_reach=predicted_reach,
                    viral_potential=viral_potential,
                    platform_versions=platform_versions,
                    originality_score=originality_score,
                    brand_alignment_score=brand_alignment_score,
                    seo_score=seo_score
                )
                
                return generated_content
            
        except Exception as e:
            logger.error(f"Failed to generate content from prompt: {e}")
        
        return None
    
    def _build_generation_prompt(self, prompt: ContentPrompt) -> str:
        """Build the AI generation prompt"""
        template = self.content_templates.get(prompt.content_type.value, {})
        constraints = prompt.constraints
        
        generation_prompt = f"""
        Create a {prompt.content_type.value} for {prompt.platform.value} with the following specifications:
        
        Topic: {prompt.topic}
        Tone: {prompt.tone.value}
        Target Audience: {prompt.target_audience}
        Brand Voice: {prompt.brand_voice}
        
        Keywords to include: {', '.join(prompt.keywords)}
        Goals: {', '.join(prompt.goals)}
        
        Platform Constraints:
        - Character limit: {constraints.get('character_limit', 'No limit')}
        - Hashtag limit: {constraints.get('hashtag_limit', 'No limit')}
        - Best practices: {constraints.get('best_practices', [])}
        
        {f"Research Context: {prompt.research_context}" if prompt.research_context else ""}
        
        Content Structure: {template.get('structure', 'Standard format')}
        
        Requirements:
        1. Create engaging, original content
        2. Include relevant hashtags
        3. Optimize for the target platform
        4. Maintain brand voice consistency
        5. Include a clear call-to-action
        6. Suggest visual content ideas
        
        {f"Call-to-action: {prompt.call_to_action}" if prompt.call_to_action else ""}
        
        Return the content in this format:
        TITLE: [if applicable]
        BODY: [main content]
        HASHTAGS: [comma-separated hashtags]
        MENTIONS: [comma-separated mentions if relevant]
        MEDIA_SUGGESTIONS: [visual content suggestions]
        """
        
        return generation_prompt
    
    def _parse_generated_content(self, content_text: str, prompt: ContentPrompt) -> Optional[Dict[str, Any]]:
        """Parse generated content from AI response"""
        try:
            parsed = {}
            
            # Extract sections using simple parsing
            lines = content_text.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('TITLE:'):
                    if current_section:
                        parsed[current_section.lower()] = '\n'.join(current_content).strip()
                    current_section = 'TITLE'
                    current_content = [line.replace('TITLE:', '').strip()]
                elif line.startswith('BODY:'):
                    if current_section:
                        parsed[current_section.lower()] = '\n'.join(current_content).strip()
                    current_section = 'BODY'
                    current_content = [line.replace('BODY:', '').strip()]
                elif line.startswith('HASHTAGS:'):
                    if current_section:
                        parsed[current_section.lower()] = '\n'.join(current_content).strip()
                    current_section = 'HASHTAGS'
                    hashtag_text = line.replace('HASHTAGS:', '').strip()
                    parsed['hashtags'] = [tag.strip() for tag in hashtag_text.split(',') if tag.strip()]
                    current_section = None
                elif line.startswith('MENTIONS:'):
                    mentions_text = line.replace('MENTIONS:', '').strip()
                    parsed['mentions'] = [mention.strip() for mention in mentions_text.split(',') if mention.strip()]
                elif line.startswith('MEDIA_SUGGESTIONS:'):
                    media_text = line.replace('MEDIA_SUGGESTIONS:', '').strip()
                    parsed['media_suggestions'] = [suggestion.strip() for suggestion in media_text.split(',') if suggestion.strip()]
                elif current_section and line:
                    current_content.append(line)
            
            # Handle last section
            if current_section:
                parsed[current_section.lower()] = '\n'.join(current_content).strip()
            
            # Ensure body exists
            if 'body' not in parsed or not parsed['body']:
                # Use entire content as body if parsing failed
                parsed['body'] = content_text.strip()
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse generated content: {e}")
            return None
    
    async def _create_platform_versions(
        self,
        content: Dict[str, Any],
        prompt: ContentPrompt
    ) -> Dict[str, str]:
        """Create platform-specific versions of content"""
        platform_versions = {}
        base_content = content["body"]
        
        # If generating for all platforms, create versions for each
        if prompt.platform == Platform.ALL:
            platforms = [Platform.TWITTER, Platform.LINKEDIN, Platform.INSTAGRAM, Platform.FACEBOOK]
        else:
            platforms = [prompt.platform]
        
        for platform in platforms:
            constraints = self._get_platform_constraints(platform)
            char_limit = constraints.get("character_limit")
            
            if char_limit and len(base_content) > char_limit:
                # Truncate and add ellipsis
                truncated = base_content[:char_limit-3] + "..."
                platform_versions[platform.value] = truncated
            else:
                platform_versions[platform.value] = base_content
        
        return platform_versions
    
    def _get_platform_constraints(self, platform: Platform) -> Dict[str, Any]:
        """Get platform-specific constraints"""
        constraints = {
            Platform.TWITTER: {
                "character_limit": 280,
                "hashtag_limit": 2,
                "best_practices": ["Use threads for longer content", "Include visuals", "Ask questions"]
            },
            Platform.LINKEDIN: {
                "character_limit": 3000,
                "hashtag_limit": 5,
                "best_practices": ["Professional tone", "Industry insights", "Engagement questions"]
            },
            Platform.INSTAGRAM: {
                "character_limit": 2200,
                "hashtag_limit": 10,
                "best_practices": ["Visual-first", "Hashtags at end", "Call-to-action"]
            },
            Platform.FACEBOOK: {
                "character_limit": 63206,
                "hashtag_limit": 5,
                "best_practices": ["Engaging questions", "Visual content", "Community building"]
            }
        }
        
        return constraints.get(platform, {})
    
    async def _get_research_context(self, topics: List[str]) -> Optional[str]:
        """Get research context for content generation"""
        try:
            # Get recent research results for topics
            context_parts = []
            
            for topic in topics[:3]:  # Limit to 3 topics
                # Search vector store for research on this topic
                similar_research = await vector_store.similarity_search(
                    f"research {topic}",
                    k=2,
                    filter={"type": "research_result"}
                )
                
                for result in similar_research:
                    context_parts.append(result.page_content[:200])
            
            return " ".join(context_parts) if context_parts else None
            
        except Exception as e:
            logger.error(f"Failed to get research context: {e}")
            return None
    
    async def _extract_trending_keywords(self, topic: str) -> List[str]:
        """Extract trending keywords for a topic"""
        try:
            # Get recent research data
            research_results = await research_automation_service.get_research_history(hours=24)
            
            keywords = set()
            for result in research_results:
                if topic.lower() in result.insights[0].lower() if result.insights else False:
                    keywords.update(result.trending_keywords[:5])
            
            return list(keywords)[:10]
            
        except Exception as e:
            logger.warning(f"Failed to extract trending keywords: {e}")
            return [topic.replace(" ", "").lower()]
    
    async def _calculate_originality_score(self, content: str) -> float:
        """Calculate content originality score"""
        try:
            # Search for similar content in vector store
            similar_content = await vector_store.similarity_search(content[:200], k=5)
            
            # Calculate similarity scores
            if similar_content:
                # Higher similarity means lower originality
                avg_similarity = sum(result.metadata.get("similarity_score", 0.5) for result in similar_content) / len(similar_content)
                originality_score = max(0, 100 - (avg_similarity * 100))
            else:
                originality_score = 90.0  # High originality if no similar content found
            
            return min(originality_score, 100.0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate originality score: {e}")
            return 75.0  # Default score
    
    def _calculate_brand_alignment_score(self, content: str, tone: ContentTone) -> float:
        """Calculate brand alignment score"""
        # Simple scoring based on tone keywords
        tone_keywords = {
            ContentTone.PROFESSIONAL: ["insight", "strategy", "professional", "expertise", "industry"],
            ContentTone.CASUAL: ["easy", "simple", "friendly", "relatable", "everyday"],
            ContentTone.INSPIRING: ["inspire", "motivate", "achieve", "success", "growth"],
            ContentTone.EDUCATIONAL: ["learn", "understand", "knowledge", "tips", "guide"],
            ContentTone.HUMOROUS: ["fun", "funny", "humor", "laugh", "entertaining"],
            ContentTone.AUTHORITATIVE: ["expert", "research", "data", "proven", "authoritative"]
        }
        
        content_lower = content.lower()
        tone_words = tone_keywords.get(tone, [])
        
        matches = sum(1 for word in tone_words if word in content_lower)
        score = min((matches / len(tone_words)) * 100, 100) if tone_words else 75
        
        return score
    
    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate SEO score based on keyword usage"""
        if not keywords:
            return 50.0
        
        content_lower = content.lower()
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in content_lower)
        
        score = (keyword_matches / len(keywords)) * 100
        return min(score, 100.0)
    
    async def _predict_performance(
        self,
        content: Dict[str, Any],
        platform: Platform
    ) -> Tuple[float, int, float]:
        """Predict content performance"""
        try:
            # Get historical performance data
            recent_metrics = await metrics_collector.get_metrics_history(
                content_id="",  # We don't have content_id yet
                platform=platform.value if platform != Platform.ALL else None,
                hours=168  # 1 week
            )
            
            if recent_metrics:
                # Calculate averages
                avg_engagement_rate = sum(m.engagement_rate for m in recent_metrics) / len(recent_metrics)
                avg_reach = sum(m.reach for m in recent_metrics) / len(recent_metrics)
                avg_viral_score = sum(m.viral_score for m in recent_metrics) / len(recent_metrics)
                
                # Adjust based on content characteristics
                word_count = len(content["body"].split())
                hashtag_count = len(content.get("hashtags", []))
                
                # Engagement rate adjustment
                engagement_modifier = 1.0
                if word_count > 50:  # Longer content might get less engagement
                    engagement_modifier *= 0.9
                if hashtag_count > 5:  # Too many hashtags might reduce engagement
                    engagement_modifier *= 0.8
                
                predicted_engagement = avg_engagement_rate * engagement_modifier
                predicted_reach = int(avg_reach * engagement_modifier)
                viral_potential = avg_viral_score * engagement_modifier
                
                return predicted_engagement, predicted_reach, viral_potential
            
        except Exception as e:
            logger.warning(f"Failed to predict performance: {e}")
        
        # Default predictions
        return 3.5, 1000, 25.0
    
    async def _store_generated_content(self, content: GeneratedContent):
        """Store generated content in database and vector store"""
        try:
            # Store in vector store
            content_text = f"{content.title or ''} {content.body}"
            metadata = {
                "type": "generated_content",
                "content_type": content.content_type.value,
                "platform": content.platform.value,
                "topic": content.topic,
                "tone": content.tone.value,
                "generated_at": content.generated_at.isoformat(),
                "originality_score": content.originality_score,
                "viral_potential": content.viral_potential
            }
            
            await vector_store.add_text(
                text=content_text,
                metadata=metadata
            )
            
            # Store in database
            async with get_db_session() as session:
                content_item = ContentItem(
                    content_text=content.body,
                    content_type=content.content_type.value,
                    platform=content.platform.value,
                    status="generated",
                    metadata=json.dumps(asdict(content)),
                    created_at=content.generated_at
                )
                
                session.add(content_item)
                await session.commit()
            
            logger.info(f"Stored generated content: {content.content_id}")
            
        except Exception as e:
            logger.error(f"Failed to store generated content: {e}")
    
    async def _publish_content(self, content: GeneratedContent):
        """Publish content to social media platform"""
        try:
            client = self.platform_clients.get(content.platform)
            if not client:
                logger.error(f"No client available for platform: {content.platform.value}")
                return
            
            # Get access token (this would need to be implemented)
            # access_token = await self._get_access_token(content.platform)
            
            # For now, just log the publishing attempt
            logger.info(f"Would publish content {content.content_id} to {content.platform.value}")
            self.stats["published_content"] += 1
            
        except Exception as e:
            logger.error(f"Failed to publish content: {e}")
    
    async def _cleanup_old_content(self):
        """Clean up old generated content"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            self.generated_content = [
                content for content in self.generated_content
                if content.generated_at > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old content: {e}")
    
    async def get_generated_content(
        self,
        hours: int = 24,
        content_type: Optional[ContentType] = None,
        platform: Optional[Platform] = None,
        min_quality_score: float = 0.0
    ) -> List[GeneratedContent]:
        """Get generated content with filters"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_content = []
        for content in self.generated_content:
            if content.generated_at < since_time:
                continue
            
            if content_type and content.content_type != content_type:
                continue
            
            if platform and content.platform != platform:
                continue
            
            if content.originality_score < min_quality_score:
                continue
            
            filtered_content.append(content)
        
        return filtered_content
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status and statistics"""
        return {
            "is_running": self._running,
            "active_pipelines": sum(1 for p in self.content_pipelines.values() if p.is_active),
            "total_pipelines": len(self.content_pipelines),
            "recent_content": len([c for c in self.generated_content if c.generated_at > datetime.utcnow() - timedelta(hours=24)]),
            "statistics": self.stats,
            "content_types": list(set(p.content_types[0].value for p in self.content_pipelines.values() if p.content_types))
        }
    
    async def pause_pipeline(self, pipeline_id: str) -> bool:
        """Pause a content pipeline"""
        if pipeline_id in self.content_pipelines:
            self.content_pipelines[pipeline_id].is_active = False
            logger.info(f"Paused content pipeline: {pipeline_id}")
            return True
        return False
    
    async def resume_pipeline(self, pipeline_id: str) -> bool:
        """Resume a content pipeline"""
        if pipeline_id in self.content_pipelines:
            self.content_pipelines[pipeline_id].is_active = True
            logger.info(f"Resumed content pipeline: {pipeline_id}")
            return True
        return False

# Global content generation service instance
content_generation_service = ContentGenerationService()