"""
Advanced Similarity Search Service for Content Repurposing and Recommendations
Integration Specialist Component - Coordinates FAISS, embeddings, and content analysis
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

# Lazy import to avoid loading FAISS at startup
# from backend.core.memory import FAISSMemorySystem
from backend.services.embedding_service import embedding_service, EmbeddingResult
from backend.db.models import Memory, Content, ContentLog, MemoryContent
from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

@dataclass
class SimilarityResult:
    """Result from similarity search with enhanced metadata"""
    content_id: str
    content: str
    similarity_score: float
    content_type: str
    platform: Optional[str]
    engagement_metrics: Dict[str, Any]
    created_at: datetime
    tags: List[str]
    performance_tier: str
    repurposing_potential: float
    related_content_ids: List[str]

@dataclass
class ContentRecommendation:
    """Recommendation for content creation or repurposing"""
    recommendation_type: str  # "repurpose", "template", "inspiration", "trend"
    confidence_score: float
    content_suggestions: List[SimilarityResult]
    platform_adaptations: Dict[str, str]
    timing_recommendations: Dict[str, Any]
    hashtag_suggestions: List[str]
    reasoning: str

class SimilarityService:
    """
    Advanced similarity search service for content repurposing and recommendations
    
    Features:
    - Multi-platform content similarity analysis
    - Performance-weighted recommendations
    - Content repurposing optimization
    - Platform-specific adaptations
    - Trend integration and analysis
    - Engagement prediction
    """
    
    def __init__(self):
        """Initialize the similarity service with lazy loading"""
        self._faiss_memory = None
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced workers
        self.supported_platforms = ["twitter", "instagram", "facebook", "tiktok"]
    
    @property
    def faiss_memory(self):
        """Lazy-load FAISS memory system only when needed"""
        if self._faiss_memory is None:
            try:
                from backend.core.memory import FAISSMemorySystem
                self._faiss_memory = FAISSMemorySystem()
                logger.info("FAISS similarity system loaded on-demand")
            except Exception as e:
                logger.warning(f"Failed to load FAISS similarity system: {e}")
                # Create fallback
                class FallbackMemory:
                    def search_similar(self, query, top_k=5):
                        return []
                    def get_content_for_repurposing(self):
                        return []
                    def get_high_performing_content(self):
                        return []
                self._faiss_memory = FallbackMemory()
        return self._faiss_memory
        
        # Content performance thresholds
        self.performance_thresholds = {
            "high": 10.0,
            "medium": 5.0,
            "low": 2.0
        }
        
        # Platform-specific content adaptations
        self.platform_adaptations = {
            "twitter": {
                "max_length": 280,
                "hashtag_limit": 3,
                "style": "concise",
                "tone": "conversational"
            },
            "linkedin": {
                "max_length": 3000,
                "hashtag_limit": 5,
                "style": "professional",
                "tone": "authoritative"
            },
            "instagram": {
                "max_length": 2200,
                "hashtag_limit": 30,
                "style": "visual-focused",
                "tone": "engaging"
            },
            "facebook": {
                "max_length": 63206,
                "hashtag_limit": 5,
                "style": "community-focused",
                "tone": "friendly"
            },
            "tiktok": {
                "max_length": 150,
                "hashtag_limit": 5,
                "style": "trendy",
                "tone": "energetic"
            }
        }
        
        logger.info("SimilarityService initialized with advanced content analysis capabilities")
    
    async def find_similar_content(
        self,
        query: str,
        content_type: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        include_performance_data: bool = True,
        db: Optional[Session] = None
    ) -> List[SimilarityResult]:
        """
        Find similar content with enhanced metadata and performance analysis
        
        Args:
            query: Search query text
            content_type: Filter by content type
            platform: Filter by platform
            limit: Number of results to return
            similarity_threshold: Minimum similarity score
            include_performance_data: Include engagement metrics
            db: Database session for enhanced data
            
        Returns:
            List of SimilarityResult objects
        """
        try:
            # Perform vector similarity search
            loop = asyncio.get_event_loop()
            basic_results = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.search_similar,
                query,
                limit * 2,  # Get extra results for filtering
                similarity_threshold
            )
            
            enhanced_results = []
            
            for result in basic_results:
                # Apply filters
                result_metadata = result.get('metadata', {})
                if content_type and result_metadata.get('type') != content_type:
                    continue
                if platform and result_metadata.get('platform') != platform:
                    continue
                
                # Create enhanced result
                enhanced_result = await self._enhance_similarity_result(result, db, include_performance_data)
                if enhanced_result:
                    enhanced_results.append(enhanced_result)
                
                if len(enhanced_results) >= limit:
                    break
            
            # Sort by combination of similarity and performance
            enhanced_results.sort(
                key=lambda x: (x.similarity_score * 0.7 + x.repurposing_potential * 0.3),
                reverse=True
            )
            
            logger.info(f"Found {len(enhanced_results)} enhanced similar content items")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in find_similar_content: {e}")
            return []
    
    async def _enhance_similarity_result(
        self,
        basic_result: Dict[str, Any],
        db: Optional[Session],
        include_performance_data: bool
    ) -> Optional[SimilarityResult]:
        """
        Enhance basic similarity result with performance data and analysis
        
        Args:
            basic_result: Basic result from FAISS search
            db: Database session
            include_performance_data: Whether to include performance metrics
            
        Returns:
            Enhanced SimilarityResult or None
        """
        try:
            content_id = basic_result.get('content_id')
            metadata = basic_result.get('metadata', {})
            
            # Initialize default values
            engagement_metrics = {}
            performance_tier = "unknown"
            repurposing_potential = 0.5
            related_content_ids = []
            tags = metadata.get('tags', [])
            
            # Get engagement metrics if available
            if include_performance_data and db:
                # Try to find in ContentLog
                content_log = db.query(ContentLog).filter(
                    ContentLog.content.contains(basic_result.get('content', '')[:100])
                ).first()
                
                if content_log:
                    engagement_metrics = content_log.engagement_data or {}
                    
                    # Calculate performance tier
                    engagement_rate = engagement_metrics.get('engagement_rate', 0)
                    if engagement_rate >= self.performance_thresholds["high"]:
                        performance_tier = "high"
                    elif engagement_rate >= self.performance_thresholds["medium"]:
                        performance_tier = "medium"
                    else:
                        performance_tier = "low"
                
                # Find related content
                related_content_ids = await self._find_related_content_ids(
                    content_id, basic_result.get('content', ''), db
                )
            
            # Calculate repurposing potential
            repurposing_potential = self._calculate_repurposing_potential(
                basic_result, engagement_metrics, metadata
            )
            
            # Parse created_at
            created_at_str = basic_result.get('created_at')
            if created_at_str:
                if isinstance(created_at_str, str):
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                else:
                    created_at = created_at_str
            else:
                created_at = datetime.utcnow()
            
            return SimilarityResult(
                content_id=content_id,
                content=basic_result.get('content', ''),
                similarity_score=basic_result.get('similarity_score', 0.0),
                content_type=metadata.get('type', 'content'),
                platform=metadata.get('platform'),
                engagement_metrics=engagement_metrics,
                created_at=created_at,
                tags=tags,
                performance_tier=performance_tier,
                repurposing_potential=repurposing_potential,
                related_content_ids=related_content_ids
            )
            
        except Exception as e:
            logger.error(f"Error enhancing similarity result: {e}")
            return None
    
    def _calculate_repurposing_potential(
        self,
        result: Dict[str, Any],
        engagement_metrics: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate the repurposing potential of content based on multiple factors
        
        Args:
            result: Basic similarity result
            engagement_metrics: Engagement data
            metadata: Content metadata
            
        Returns:
            Repurposing potential score (0.0 to 1.0)
        """
        try:
            potential = 0.5  # Base score
            
            # Factor 1: Similarity score (higher similarity = higher potential)
            similarity_score = result.get('similarity_score', 0.0)
            potential += (similarity_score - 0.5) * 0.3
            
            # Factor 2: Engagement performance
            engagement_rate = engagement_metrics.get('engagement_rate', 0)
            if engagement_rate > 0:
                if engagement_rate >= self.performance_thresholds["high"]:
                    potential += 0.3
                elif engagement_rate >= self.performance_thresholds["medium"]:
                    potential += 0.2
                else:
                    potential += 0.1
            
            # Factor 3: Content age (newer content may be more relevant)
            created_at_str = result.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    days_old = (datetime.utcnow() - created_at).days
                    
                    if days_old < 30:
                        potential += 0.1
                    elif days_old < 90:
                        potential += 0.05
                    elif days_old > 365:
                        potential -= 0.1
                except:
                    pass
            
            # Factor 4: Content type value
            content_type = metadata.get('type', '')
            if content_type in ['template', 'high_performing']:
                potential += 0.2
            elif content_type in ['research', 'insight']:
                potential += 0.1
            
            # Factor 5: Tag relevance
            tags = metadata.get('tags', [])
            trending_tags = ['viral', 'trending', 'popular', 'successful']
            if any(tag in trending_tags for tag in tags):
                potential += 0.1
            
            # Normalize to 0-1 range
            return max(0.0, min(1.0, potential))
            
        except Exception as e:
            logger.error(f"Error calculating repurposing potential: {e}")
            return 0.5
    
    async def _find_related_content_ids(
        self,
        content_id: str,
        content: str,
        db: Session,
        limit: int = 5
    ) -> List[str]:
        """
        Find related content IDs based on similarity and database relationships
        
        Args:
            content_id: Current content ID
            content: Content text for similarity search
            db: Database session
            limit: Number of related IDs to return
            
        Returns:
            List of related content IDs
        """
        try:
            related_ids = []
            
            # Find similar content with lower threshold
            loop = asyncio.get_event_loop()
            similar_content = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.search_similar,
                content[:500],  # Use first 500 chars for similarity
                limit * 2,
                0.6  # Lower threshold for related content
            )
            
            for item in similar_content:
                related_id = item.get('content_id')
                if related_id and related_id != content_id:
                    related_ids.append(related_id)
                
                if len(related_ids) >= limit:
                    break
            
            return related_ids
            
        except Exception as e:
            logger.error(f"Error finding related content IDs: {e}")
            return []
    
    async def get_content_recommendations(
        self,
        topic: str,
        target_platform: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> List[ContentRecommendation]:
        """
        Get comprehensive content recommendations for a topic and platform
        
        Args:
            topic: Content topic or theme
            target_platform: Target social media platform
            user_preferences: User preferences and settings
            db: Database session
            
        Returns:
            List of ContentRecommendation objects
        """
        try:
            if target_platform not in self.supported_platforms:
                raise ValueError(f"Unsupported platform: {target_platform}")
            
            recommendations = []
            
            # 1. Find repurposing opportunities
            repurpose_rec = await self._get_repurposing_recommendations(
                topic, target_platform, db
            )
            if repurpose_rec:
                recommendations.append(repurpose_rec)
            
            # 2. Find template-based recommendations
            template_rec = await self._get_template_recommendations(
                topic, target_platform, db
            )
            if template_rec:
                recommendations.append(template_rec)
            
            # 3. Find inspiration from high-performing content
            inspiration_rec = await self._get_inspiration_recommendations(
                topic, target_platform, db
            )
            if inspiration_rec:
                recommendations.append(inspiration_rec)
            
            # 4. Find trend-based recommendations
            trend_rec = await self._get_trend_recommendations(
                topic, target_platform, db
            )
            if trend_rec:
                recommendations.append(trend_rec)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} content recommendations for {topic} on {target_platform}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting content recommendations: {e}")
            return []
    
    async def _get_repurposing_recommendations(
        self,
        topic: str,
        target_platform: str,
        db: Optional[Session]
    ) -> Optional[ContentRecommendation]:
        """Get recommendations for repurposing existing high-performing content"""
        try:
            # Find high-performing content for repurposing
            loop = asyncio.get_event_loop()
            repurposing_content = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.get_content_for_repurposing,
                30,  # 30 days old
                5.0  # Min engagement rate
            )
            
            if not repurposing_content:
                return None
            
            # Filter and enhance results
            relevant_content = []
            for item in repurposing_content[:5]:
                enhanced = await self._enhance_similarity_result(
                    {
                        'content_id': item.get('content_id'),
                        'content': item.get('content'),
                        'similarity_score': 0.8,  # High for repurposing
                        'metadata': item.get('metadata', {}),
                        'created_at': item.get('created_at')
                    },
                    db,
                    True
                )
                if enhanced:
                    relevant_content.append(enhanced)
            
            if not relevant_content:
                return None
            
            # Generate platform-specific adaptations
            platform_adaptations = {}
            for content in relevant_content:
                adaptation = self._adapt_content_for_platform(
                    content.content, target_platform
                )
                platform_adaptations[content.content_id] = adaptation
            
            return ContentRecommendation(
                recommendation_type="repurpose",
                confidence_score=0.85,
                content_suggestions=relevant_content,
                platform_adaptations=platform_adaptations,
                timing_recommendations=self._get_timing_recommendations(target_platform),
                hashtag_suggestions=self._generate_hashtag_suggestions(topic, target_platform),
                reasoning=f"Found {len(relevant_content)} high-performing content pieces suitable for repurposing on {target_platform}"
            )
            
        except Exception as e:
            logger.error(f"Error getting repurposing recommendations: {e}")
            return None
    
    async def _get_template_recommendations(
        self,
        topic: str,
        target_platform: str,
        db: Optional[Session]
    ) -> Optional[ContentRecommendation]:
        """Get recommendations based on successful templates"""
        try:
            # Search for template content
            template_results = await self.find_similar_content(
                query=f"{topic} template {target_platform}",
                content_type="template",
                platform=target_platform,
                limit=3,
                similarity_threshold=0.6,
                db=db
            )
            
            if not template_results:
                return None
            
            platform_adaptations = {}
            for template in template_results:
                platform_adaptations[template.content_id] = template.content
            
            return ContentRecommendation(
                recommendation_type="template",
                confidence_score=0.75,
                content_suggestions=template_results,
                platform_adaptations=platform_adaptations,
                timing_recommendations=self._get_timing_recommendations(target_platform),
                hashtag_suggestions=self._generate_hashtag_suggestions(topic, target_platform),
                reasoning=f"Found {len(template_results)} proven templates for {topic} content on {target_platform}"
            )
            
        except Exception as e:
            logger.error(f"Error getting template recommendations: {e}")
            return None
    
    async def _get_inspiration_recommendations(
        self,
        topic: str,
        target_platform: str,
        db: Optional[Session]
    ) -> Optional[ContentRecommendation]:
        """Get inspiration from high-performing similar content"""
        try:
            # Find high-performing content similar to topic
            loop = asyncio.get_event_loop()
            high_performing = await loop.run_in_executor(
                self.executor,
                self.faiss_memory.get_high_performing_content,
                8.0,  # High engagement threshold
                5
            )
            
            if not high_performing:
                return None
            
            # Filter for topic relevance using similarity search
            relevant_inspiration = []
            for item in high_performing:
                similarity_results = await self.find_similar_content(
                    query=topic,
                    limit=1,
                    similarity_threshold=0.6,
                    db=db
                )
                
                if similarity_results and similarity_results[0].content_id == item.get('content_id'):
                    enhanced = await self._enhance_similarity_result(
                        {
                            'content_id': item.get('content_id'),
                            'content': item.get('content'),
                            'similarity_score': 0.9,
                            'metadata': item.get('metadata', {}),
                            'created_at': item.get('created_at')
                        },
                        db,
                        True
                    )
                    if enhanced:
                        relevant_inspiration.append(enhanced)
            
            if not relevant_inspiration:
                return None
            
            platform_adaptations = {}
            for content in relevant_inspiration:
                adaptation = self._adapt_content_for_platform(
                    content.content, target_platform
                )
                platform_adaptations[content.content_id] = adaptation
            
            return ContentRecommendation(
                recommendation_type="inspiration",
                confidence_score=0.80,
                content_suggestions=relevant_inspiration,
                platform_adaptations=platform_adaptations,
                timing_recommendations=self._get_timing_recommendations(target_platform),
                hashtag_suggestions=self._generate_hashtag_suggestions(topic, target_platform),
                reasoning=f"Found {len(relevant_inspiration)} high-performing content pieces as inspiration for {topic}"
            )
            
        except Exception as e:
            logger.error(f"Error getting inspiration recommendations: {e}")
            return None
    
    async def _get_trend_recommendations(
        self,
        topic: str,
        target_platform: str,
        db: Optional[Session]
    ) -> Optional[ContentRecommendation]:
        """Get recommendations based on trending content"""
        try:
            # Search for trending content
            trend_results = await self.find_similar_content(
                query=f"{topic} trending viral",
                content_type="trend",
                platform=target_platform,
                limit=3,
                similarity_threshold=0.5,
                db=db
            )
            
            if not trend_results:
                return None
            
            platform_adaptations = {}
            for trend in trend_results:
                adaptation = self._adapt_content_for_platform(
                    trend.content, target_platform
                )
                platform_adaptations[trend.content_id] = adaptation
            
            return ContentRecommendation(
                recommendation_type="trend",
                confidence_score=0.70,
                content_suggestions=trend_results,
                platform_adaptations=platform_adaptations,
                timing_recommendations=self._get_timing_recommendations(target_platform),
                hashtag_suggestions=self._generate_hashtag_suggestions(topic, target_platform),
                reasoning=f"Found {len(trend_results)} trending content pieces related to {topic} on {target_platform}"
            )
            
        except Exception as e:
            logger.error(f"Error getting trend recommendations: {e}")
            return None
    
    def _adapt_content_for_platform(self, content: str, platform: str) -> str:
        """
        Adapt content for a specific platform's requirements
        
        Args:
            content: Original content
            platform: Target platform
            
        Returns:
            Adapted content
        """
        try:
            if platform not in self.platform_adaptations:
                return content
            
            platform_config = self.platform_adaptations[platform]
            max_length = platform_config["max_length"]
            
            # Truncate if too long
            if len(content) > max_length:
                content = content[:max_length - 3] + "..."
            
            # Add platform-specific formatting hints
            if platform == "twitter" and len(content) > 200:
                # Suggest breaking into thread
                content += " [Consider breaking into thread]"
            elif platform == "linkedin" and len(content) < 100:
                # Suggest expanding for LinkedIn
                content += " [Consider expanding with professional insights]"
            elif platform == "instagram":
                # Suggest adding visual elements
                content += " [Consider adding visual elements]"
            
            return content
            
        except Exception as e:
            logger.error(f"Error adapting content for platform: {e}")
            return content
    
    def _get_timing_recommendations(self, platform: str) -> Dict[str, Any]:
        """
        Get optimal timing recommendations for a platform
        
        Args:
            platform: Target platform
            
        Returns:
            Timing recommendations
        """
        # Platform-specific optimal posting times (generalized)
        timing_data = {
            "twitter": {
                "best_hours": [9, 12, 15, 18],
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "frequency": "3-5 times per day"
            },
            "linkedin": {
                "best_hours": [8, 12, 17],
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "frequency": "1-2 times per day"
            },
            "instagram": {
                "best_hours": [11, 13, 17, 19],
                "best_days": ["Wednesday", "Thursday", "Friday"],
                "frequency": "1-2 times per day"
            },
            "facebook": {
                "best_hours": [13, 15, 18],
                "best_days": ["Wednesday", "Thursday", "Friday"],
                "frequency": "1-2 times per day"
            },
            "tiktok": {
                "best_hours": [18, 19, 20, 21],
                "best_days": ["Tuesday", "Thursday", "Sunday"],
                "frequency": "1-3 times per day"
            }
        }
        
        return timing_data.get(platform, {
            "best_hours": [12, 15, 18],
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "frequency": "1-2 times per day"
        })
    
    def _generate_hashtag_suggestions(self, topic: str, platform: str) -> List[str]:
        """
        Generate hashtag suggestions based on topic and platform
        
        Args:
            topic: Content topic
            platform: Target platform
            
        Returns:
            List of suggested hashtags
        """
        try:
            platform_config = self.platform_adaptations.get(platform, {})
            hashtag_limit = platform_config.get("hashtag_limit", 5)
            
            # Basic hashtag generation (in a real implementation, this would use
            # trend analysis and hashtag performance data)
            base_hashtags = []
            
            # Add topic-based hashtags
            topic_words = topic.lower().split()
            for word in topic_words:
                if len(word) > 3:
                    base_hashtags.append(f"#{word}")
            
            # Add platform-specific trending hashtags (simplified)
            platform_hashtags = {
                "twitter": ["#TwitterTips", "#Trending", "#Viral"],
                "linkedin": ["#Professional", "#Career", "#Business"],
                "instagram": ["#InstaGood", "#PhotoOfTheDay", "#Inspiration"],
                "facebook": ["#Community", "#Share", "#Connect"],
                "tiktok": ["#ForYou", "#Trending", "#Viral"]
            }
            
            base_hashtags.extend(platform_hashtags.get(platform, []))
            
            # Return limited number based on platform
            return base_hashtags[:hashtag_limit]
            
        except Exception as e:
            logger.error(f"Error generating hashtag suggestions: {e}")
            return []

# Global similarity service instance
similarity_service = SimilarityService()