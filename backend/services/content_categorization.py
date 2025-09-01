"""
AI-powered Content Categorization System
Handles automatic categorization by topic, platform, engagement levels, and sentiment analysis
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from openai import OpenAI, AsyncOpenAI
import json

from backend.core.config import get_settings
from backend.db.models import ContentItem, ContentCategory
from backend.services.embedding_service import embedding_service

# Get logger (use application's logging configuration)
logger = logging.getLogger(__name__)

settings = get_settings()

@dataclass
class CategoryResult:
    """Result of content categorization"""
    topic_category: str
    confidence: float
    sentiment: str
    tone: str
    reading_level: str
    keywords: List[str]
    hashtags: List[str]
    mentions: List[str]
    links: List[str]

class ContentCategorizer:
    """
    AI-powered Content Categorization System
    
    Features:
    - Automatic topic categorization using OpenAI
    - Sentiment analysis (positive, negative, neutral)
    - Tone detection (professional, casual, humorous, etc.)
    - Reading level assessment
    - Keyword and hashtag extraction
    - Platform-specific optimization suggestions
    - Engagement level prediction
    """
    
    def __init__(self):
        """Initialize the content categorizer"""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Predefined categories (can be extended)
        self.base_categories = {
            "technology": {
                "keywords": ["AI", "machine learning", "software", "tech", "digital", "innovation", "automation"],
                "description": "Technology trends, AI, software development, digital innovation"
            },
            "marketing": {
                "keywords": ["marketing", "branding", "advertising", "campaigns", "social media", "SEO"],
                "description": "Marketing strategies, branding, advertising, social media marketing"
            },
            "business": {
                "keywords": ["business", "entrepreneurship", "strategy", "leadership", "growth", "startup"],
                "description": "Business insights, entrepreneurship, strategy, leadership"
            },
            "industry_news": {
                "keywords": ["news", "announcement", "update", "breaking", "industry", "report"],
                "description": "Latest industry news, updates, and announcements"
            },
            "educational": {
                "keywords": ["tutorial", "how-to", "guide", "tips", "learn", "education", "training"],
                "description": "Educational content, tutorials, how-to guides"
            },
            "personal": {
                "keywords": ["personal", "story", "experience", "behind-the-scenes", "team", "culture"],
                "description": "Personal insights, company culture, behind-the-scenes content"
            },
            "finance": {
                "keywords": ["finance", "investment", "money", "economy", "budget", "financial"],
                "description": "Financial advice, investment insights, economic trends"
            },
            "health": {
                "keywords": ["health", "wellness", "fitness", "medical", "lifestyle", "nutrition"],
                "description": "Health and wellness, fitness, lifestyle content"
            }
        }
        
        # Platform-specific categorization rules
        self.platform_rules = {
            "twitter": {
                "max_length": 280,
                "hashtag_limit": 2,
                "tone_preferences": ["casual", "conversational", "witty"]
            },
            "linkedin": {
                "max_length": 3000,
                "hashtag_limit": 5,
                "tone_preferences": ["professional", "insightful", "thought-provoking"]
            },
            "instagram": {
                "max_length": 2200,
                "hashtag_limit": 30,
                "tone_preferences": ["visual", "inspiring", "creative"]
            },
            "facebook": {
                "max_length": 63206,
                "hashtag_limit": 5,
                "tone_preferences": ["friendly", "community", "engaging"]
            },
            "tiktok": {
                "max_length": 150,
                "hashtag_limit": 5,
                "tone_preferences": ["trendy", "energetic", "fun"]
            }
        }
        
        logger.info("ContentCategorizer initialized with base categories and platform rules")
    
    def _extract_text_elements(self, content: str) -> Dict[str, List[str]]:
        """Extract hashtags, mentions, and links from content"""
        # Extract hashtags
        hashtags = re.findall(r'#\w+', content)
        
        # Extract mentions
        mentions = re.findall(r'@\w+', content)
        
        # Extract URLs
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        links = url_pattern.findall(content)
        
        return {
            "hashtags": hashtags,
            "mentions": mentions,
            "links": links
        }
    
    def _keyword_based_categorization(self, content: str) -> Tuple[str, float]:
        """Fallback categorization based on keyword matching"""
        content_lower = content.lower()
        
        category_scores = {}
        for category, info in self.base_categories.items():
            score = 0
            for keyword in info["keywords"]:
                # Count keyword occurrences (case-insensitive)
                occurrences = content_lower.count(keyword.lower())
                score += occurrences
            
            # Normalize by content length
            if len(content) > 0:
                category_scores[category] = score / (len(content) / 100)  # Per 100 characters
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(category_scores[best_category] * 0.3, 1.0)  # Scale confidence
            return best_category, confidence
        
        return "general", 0.5
    
    async def _ai_categorization(self, content: str, platform: str) -> CategoryResult:
        """Use OpenAI to categorize content with detailed analysis"""
        try:
            # Create comprehensive categorization prompt
            prompt = f"""
            Analyze the following social media content and provide detailed categorization:

            Content: "{content}"
            Platform: {platform}

            Please analyze and respond with a JSON object containing:
            {{
                "topic_category": "one of: technology, marketing, business, industry_news, educational, personal, finance, health, or general",
                "confidence": 0.0-1.0,
                "sentiment": "positive, negative, or neutral",
                "tone": "professional, casual, humorous, inspiring, educational, promotional, or conversational",
                "reading_level": "beginner, intermediate, or advanced",
                "keywords": ["5-10 most important keywords"],
                "explanation": "brief explanation of categorization reasoning"
            }}

            Focus on:
            1. Main topic and theme
            2. Emotional tone and sentiment
            3. Target audience level
            4. Key concepts and terms
            5. Content purpose and intent
            """
            
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content analyst specializing in social media categorization. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse AI response
            ai_result = json.loads(response.choices[0].message.content)
            
            # Extract text elements
            text_elements = self._extract_text_elements(content)
            
            # Create result object
            return CategoryResult(
                topic_category=ai_result.get("topic_category", "general"),
                confidence=float(ai_result.get("confidence", 0.5)),
                sentiment=ai_result.get("sentiment", "neutral"),
                tone=ai_result.get("tone", "conversational"),
                reading_level=ai_result.get("reading_level", "intermediate"),
                keywords=ai_result.get("keywords", []),
                hashtags=text_elements["hashtags"],
                mentions=text_elements["mentions"],
                links=text_elements["links"]
            )
            
        except Exception as e:
            logger.error(f"AI categorization failed: {e}")
            # Fallback to keyword-based categorization
            return await self._fallback_categorization(content, platform)
    
    async def _fallback_categorization(self, content: str, platform: str) -> CategoryResult:
        """Fallback categorization when AI fails"""
        category, confidence = self._keyword_based_categorization(content)
        text_elements = self._extract_text_elements(content)
        
        # Simple sentiment analysis based on keywords
        positive_words = ["great", "amazing", "excellent", "love", "best", "awesome", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "disappointing"]
        
        content_lower = content.lower()
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)
        
        if positive_score > negative_score:
            sentiment = "positive"
        elif negative_score > positive_score:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Determine tone based on platform and content
        tone = "conversational"
        if platform == "linkedin":
            tone = "professional"
        elif "?" in content or "tips" in content_lower:
            tone = "educational"
        elif any(word in content_lower for word in ["buy", "sale", "offer", "discount"]):
            tone = "promotional"
        
        return CategoryResult(
            topic_category=category,
            confidence=confidence,
            sentiment=sentiment,
            tone=tone,
            reading_level="intermediate",
            keywords=self._extract_keywords(content),
            hashtags=text_elements["hashtags"],
            mentions=text_elements["mentions"],
            links=text_elements["links"]
        )
    
    def _extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content using simple NLP"""
        import string
        
        # Remove punctuation and convert to lowercase
        content_clean = content.translate(str.maketrans('', '', string.punctuation)).lower()
        words = content_clean.split()
        
        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might", "can",
            "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they"
        }
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    async def categorize_content(
        self, 
        content: str, 
        platform: str,
        use_ai: bool = True
    ) -> CategoryResult:
        """
        Categorize content using AI or fallback methods
        
        Args:
            content: Text content to categorize
            platform: Social media platform
            use_ai: Whether to use AI categorization
            
        Returns:
            CategoryResult with detailed analysis
        """
        try:
            if use_ai and settings.openai_api_key:
                result = await self._ai_categorization(content, platform)
            else:
                result = await self._fallback_categorization(content, platform)
            
            # Validate platform compatibility
            platform_rules = self.platform_rules.get(platform, {})
            if platform_rules:
                # Check content length
                max_length = platform_rules.get("max_length", 10000)
                if len(content) > max_length:
                    logger.warning(f"Content exceeds {platform} max length ({len(content)}/{max_length})")
                
                # Check hashtag limits
                hashtag_limit = platform_rules.get("hashtag_limit", 10)
                if len(result.hashtags) > hashtag_limit:
                    logger.warning(f"Too many hashtags for {platform} ({len(result.hashtags)}/{hashtag_limit})")
            
            logger.info(f"Categorized content as '{result.topic_category}' with {result.confidence:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Content categorization failed: {e}")
            # Return basic categorization
            return CategoryResult(
                topic_category="general",
                confidence=0.3,
                sentiment="neutral",
                tone="conversational",
                reading_level="intermediate",
                keywords=[],
                hashtags=[],
                mentions=[],
                links=[]
            )
    
    async def categorize_batch(
        self, 
        content_list: List[Tuple[str, str]], 
        use_ai: bool = True
    ) -> List[CategoryResult]:
        """
        Categorize multiple content items efficiently
        
        Args:
            content_list: List of (content, platform) tuples
            use_ai: Whether to use AI categorization
            
        Returns:
            List of CategoryResult objects
        """
        try:
            # Process in parallel for better performance
            tasks = [
                self.categorize_content(content, platform, use_ai)
                for content, platform in content_list
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error categorizing item {i}: {result}")
                    # Create fallback result
                    processed_results.append(CategoryResult(
                        topic_category="general",
                        confidence=0.3,
                        sentiment="neutral",
                        tone="conversational",
                        reading_level="intermediate",
                        keywords=[],
                        hashtags=[],
                        mentions=[],
                        links=[]
                    ))
                else:
                    processed_results.append(result)
            
            logger.info(f"Batch categorized {len(processed_results)} content items")
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch categorization failed: {e}")
            # Return fallback results for all items
            return [
                CategoryResult(
                    topic_category="general",
                    confidence=0.3,
                    sentiment="neutral",
                    tone="conversational",
                    reading_level="intermediate",
                    keywords=[],
                    hashtags=[],
                    mentions=[],
                    links=[]
                )
                for _ in content_list
            ]
    
    def predict_engagement_level(
        self, 
        category_result: CategoryResult, 
        platform: str,
        historical_data: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Predict engagement level based on categorization and historical data
        
        Args:
            category_result: Categorization result
            platform: Social media platform
            historical_data: Historical performance data for similar content
            
        Returns:
            Engagement prediction with confidence
        """
        try:
            base_score = 0.5  # Default baseline
            
            # Category-based scoring
            category_scores = {
                "technology": {"twitter": 0.7, "linkedin": 0.8, "instagram": 0.5},
                "marketing": {"twitter": 0.6, "linkedin": 0.7, "instagram": 0.8},
                "business": {"twitter": 0.6, "linkedin": 0.9, "instagram": 0.4},
                "educational": {"twitter": 0.7, "linkedin": 0.8, "instagram": 0.6},
                "personal": {"twitter": 0.8, "linkedin": 0.6, "instagram": 0.9}
            }
            
            category_score = category_scores.get(
                category_result.topic_category, {}
            ).get(platform, base_score)
            
            # Sentiment boost
            sentiment_multiplier = {
                "positive": 1.2,
                "neutral": 1.0,
                "negative": 0.8
            }
            sentiment_boost = sentiment_multiplier.get(category_result.sentiment, 1.0)
            
            # Tone adjustment
            tone_multiplier = {
                "humorous": 1.3,
                "inspiring": 1.2,
                "educational": 1.1,
                "promotional": 0.9,
                "controversial": 1.4  # High engagement but risky
            }
            tone_boost = tone_multiplier.get(category_result.tone, 1.0)
            
            # Hashtag optimization
            hashtag_boost = 1.0
            if category_result.hashtags:
                platform_rules = self.platform_rules.get(platform, {})
                optimal_hashtags = platform_rules.get("hashtag_limit", 5) // 2
                if len(category_result.hashtags) <= optimal_hashtags:
                    hashtag_boost = 1.1
            
            # Calculate final score
            predicted_score = category_score * sentiment_boost * tone_boost * hashtag_boost
            predicted_score = min(predicted_score, 1.0)  # Cap at 1.0
            
            # Use historical data if available
            if historical_data:
                historical_avg = historical_data.get(category_result.topic_category, base_score)
                # Weighted average with historical data
                predicted_score = (predicted_score * 0.7) + (historical_avg * 0.3)
            
            # Determine engagement tier
            if predicted_score >= 0.8:
                engagement_tier = "high"
            elif predicted_score >= 0.6:
                engagement_tier = "medium"
            elif predicted_score >= 0.4:
                engagement_tier = "low"
            else:
                engagement_tier = "poor"
            
            return {
                "predicted_engagement_score": predicted_score,
                "engagement_tier": engagement_tier,
                "confidence": category_result.confidence,
                "factors": {
                    "category_score": category_score,
                    "sentiment_boost": sentiment_boost,
                    "tone_boost": tone_boost,
                    "hashtag_optimization": hashtag_boost
                },
                "recommendations": self._generate_engagement_recommendations(
                    category_result, platform, predicted_score
                )
            }
            
        except Exception as e:
            logger.error(f"Engagement prediction failed: {e}")
            return {
                "predicted_engagement_score": 0.5,
                "engagement_tier": "medium",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _generate_engagement_recommendations(
        self, 
        category_result: CategoryResult, 
        platform: str, 
        predicted_score: float
    ) -> List[str]:
        """Generate recommendations to improve engagement"""
        recommendations = []
        
        # Low engagement recommendations
        if predicted_score < 0.5:
            recommendations.append("🔄 Consider rephrasing with more engaging language")
            recommendations.append("❓ Add questions to encourage interaction")
            
            if not category_result.hashtags and platform != "linkedin":
                recommendations.append("# Add relevant hashtags to increase discoverability")
        
        # Platform-specific recommendations
        if platform == "twitter":
            if len(category_result.hashtags) > 2:
                recommendations.append("🐦 Reduce hashtags (max 2 for Twitter)")
            if category_result.tone == "professional":
                recommendations.append("💬 Consider a more conversational tone for Twitter")
        
        elif platform == "linkedin":
            if category_result.tone not in ["professional", "educational"]:
                recommendations.append("💼 Use more professional tone for LinkedIn")
            if not category_result.keywords:
                recommendations.append("🔍 Add industry keywords for better reach")
        
        elif platform == "instagram":
            if len(category_result.hashtags) < 5:
                recommendations.append("📸 Add more hashtags (up to 30 for Instagram)")
            if category_result.tone not in ["inspiring", "creative"]:
                recommendations.append("✨ Use more visual and inspiring language")
        
        # Sentiment recommendations
        if category_result.sentiment == "negative":
            recommendations.append("😊 Consider more positive framing")
        
        # Content quality recommendations
        if category_result.confidence < 0.7:
            recommendations.append("🎯 Content topic could be more focused")
        
        return recommendations
    
    def get_category_statistics(
        self, 
        content_items: List[CategoryResult]
    ) -> Dict[str, Any]:
        """Generate statistics for categorized content"""
        if not content_items:
            return {"error": "No content items provided"}
        
        # Category distribution
        categories = [item.topic_category for item in content_items]
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sentiment distribution
        sentiments = [item.sentiment for item in content_items]
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Average confidence
        confidences = [item.confidence for item in content_items]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Tone distribution
        tones = [item.tone for item in content_items]
        tone_counts = {}
        for tone in tones:
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
        
        return {
            "total_items": len(content_items),
            "category_distribution": category_counts,
            "sentiment_distribution": sentiment_counts,
            "tone_distribution": tone_counts,
            "average_confidence": avg_confidence,
            "most_common_category": max(category_counts, key=category_counts.get),
            "most_common_sentiment": max(sentiment_counts, key=sentiment_counts.get),
            "most_common_tone": max(tone_counts, key=tone_counts.get)
        }

# Global content categorizer instance - lazy loaded
_content_categorizer = None

def get_content_categorizer():
    """Get the global content categorizer instance (lazy initialization)"""
    global _content_categorizer
    if _content_categorizer is None:
        _content_categorizer = ContentCategorizer()
    return _content_categorizer

# For backward compatibility, create a property-like access
class ContentCategorizerProxy:
    """Proxy object that provides lazy access to content categorizer"""
    def __getattr__(self, name):
        return getattr(get_content_categorizer(), name)

content_categorizer = ContentCategorizerProxy()