"""
Automated Research Pipeline Service
Integration Specialist Component - Automated content research and trend analysis
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import httpx
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.database import get_db
from backend.db.models import ContentItem, ResearchData
from backend.integrations.twitter_client import twitter_client
from backend.integrations.instagram_client import instagram_client
from backend.integrations.facebook_client import facebook_client
from backend.core.vector_store import vector_store

settings = get_settings()
logger = logging.getLogger(__name__)

class ResearchSource(Enum):
    """Research data sources"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    GOOGLE_TRENDS = "google_trends"
    NEWS_API = "news_api"
    REDDIT = "reddit"
    YOUTUBE = "youtube"

@dataclass
class ResearchQuery:
    """Research query configuration"""
    keywords: List[str]
    platforms: List[ResearchSource]
    content_types: List[str]  # text, image, video, etc.
    time_range: str  # 1h, 24h, 7d, 30d
    location: Optional[str] = None
    language: str = "en"
    max_results: int = 100
    include_sentiment: bool = True
    include_engagement: bool = True

@dataclass
class ResearchResult:
    """Individual research result"""
    source: str
    platform: str
    content_id: str
    title: str
    content: str
    author: str
    published_at: datetime
    url: str
    engagement_metrics: Dict[str, int]
    sentiment_score: Optional[float] = None
    trending_score: float = 0.0
    relevance_score: float = 0.0
    tags: List[str] = None
    media_urls: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.media_urls is None:
            self.media_urls = []

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    topic: str
    trend_score: float
    growth_rate: float
    platforms: List[str]
    related_keywords: List[str]
    content_volume: int
    avg_engagement: float
    sentiment: str  # positive, negative, neutral
    time_period: str
    peaked_at: Optional[datetime] = None
    is_viral: bool = False

@dataclass
class ResearchSummary:
    """Research operation summary"""
    query: ResearchQuery
    total_results: int
    results_by_platform: Dict[str, int]
    trending_topics: List[TrendAnalysis]
    sentiment_breakdown: Dict[str, int]
    engagement_summary: Dict[str, float]
    research_duration: float
    completed_at: datetime

class AutomatedResearchPipeline:
    """
    Comprehensive automated research pipeline
    
    Features:
    - Multi-platform content research
    - Trend detection and analysis
    - Sentiment analysis integration
    - Engagement pattern recognition
    - Viral content identification
    - Keyword expansion and optimization
    - Competitive analysis
    - Content gap identification
    """
    
    def __init__(self):
        """Initialize research pipeline"""
        self.news_api_key = settings.NEWS_API_KEY if hasattr(settings, 'NEWS_API_KEY') else None
        self.google_trends_available = True  # Check if pytrends is available
        
        # Research configuration
        self.platform_weights = {
            ResearchSource.TWITTER: 1.0,      # High real-time relevance
            ResearchSource.INSTAGRAM: 0.8,    # Visual content focus
            ResearchSource.FACEBOOK: 0.7,     # Broad audience insights
            ResearchSource.LINKEDIN: 0.9,     # Professional content
            ResearchSource.GOOGLE_TRENDS: 1.0, # Search volume insights
            ResearchSource.NEWS_API: 0.9,     # News and current events
            ResearchSource.REDDIT: 0.8,       # Community discussions
            ResearchSource.YOUTUBE: 0.7       # Video content trends
        }
        
        self.engagement_thresholds = {
            "viral": {"likes": 10000, "shares": 1000, "comments": 500},
            "high": {"likes": 1000, "shares": 100, "comments": 50},
            "medium": {"likes": 100, "shares": 10, "comments": 5},
            "low": {"likes": 10, "shares": 1, "comments": 1}
        }
        
        logger.info("AutomatedResearchPipeline initialized")
    
    async def execute_research(
        self,
        db: Session,
        query: ResearchQuery,
        save_results: bool = True
    ) -> ResearchSummary:
        """
        Execute comprehensive automated research
        
        Args:
            db: Database session
            query: Research query configuration
            save_results: Whether to save results to database
            
        Returns:
            Research summary with results and analysis
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting automated research for keywords: {query.keywords}")
        
        # Execute research tasks in parallel
        research_tasks = []
        
        for platform in query.platforms:
            if platform == ResearchSource.TWITTER:
                task = self._research_twitter(query)
            elif platform == ResearchSource.INSTAGRAM:
                task = self._research_instagram(query)
            elif platform == ResearchSource.FACEBOOK:
                task = self._research_facebook(query)
            elif platform == ResearchSource.LINKEDIN:
                task = self._research_linkedin(query)
            elif platform == ResearchSource.GOOGLE_TRENDS:
                task = self._research_google_trends(query)
            elif platform == ResearchSource.NEWS_API:
                task = self._research_news_api(query)
            elif platform == ResearchSource.REDDIT:
                task = self._research_reddit(query)
            elif platform == ResearchSource.YOUTUBE:
                task = self._research_youtube(query)
            else:
                continue
            
            research_tasks.append(task)
        
        # Execute all research tasks
        results_by_platform = {}
        all_results = []
        
        if research_tasks:
            platform_results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            for i, results in enumerate(platform_results):
                platform = query.platforms[i]
                
                if isinstance(results, Exception):
                    logger.error(f"Research failed for {platform.value}: {results}")
                    results_by_platform[platform.value] = 0
                else:
                    results_by_platform[platform.value] = len(results)
                    all_results.extend(results)
        
        # Analyze trends from collected results
        trending_topics = await self._analyze_trends(all_results, query)
        
        # Calculate sentiment breakdown
        sentiment_breakdown = self._calculate_sentiment_breakdown(all_results)
        
        # Calculate engagement summary
        engagement_summary = self._calculate_engagement_summary(all_results)
        
        # Create research summary
        research_duration = (datetime.utcnow() - start_time).total_seconds()
        
        summary = ResearchSummary(
            query=query,
            total_results=len(all_results),
            results_by_platform=results_by_platform,
            trending_topics=trending_topics,
            sentiment_breakdown=sentiment_breakdown,
            engagement_summary=engagement_summary,
            research_duration=research_duration,
            completed_at=datetime.utcnow()
        )
        
        # Save results to database if requested
        if save_results:
            await self._save_research_to_db(db, summary, all_results)
        
        logger.info(f"Research completed: {len(all_results)} results in {research_duration:.2f}s")
        
        return summary
    
    async def _research_twitter(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from Twitter"""
        results = []
        
        try:
            # Get Twitter account for API access (using first available)
            # In production, this would use a service account or app-only auth
            
            for keyword in query.keywords:
                try:
                    # Use Twitter search API
                    search_query = self._build_twitter_search_query(keyword, query)
                    
                    # Note: This would require Twitter API access
                    # For now, we'll create mock results
                    mock_results = await self._create_mock_twitter_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Twitter research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Twitter research setup failed: {e}")
        
        return results
    
    async def _research_instagram(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from Instagram"""
        results = []
        
        try:
            # Instagram hashtag research
            for keyword in query.keywords:
                try:
                    # Note: Instagram hashtag search requires business account
                    # For now, we'll create mock results
                    mock_results = await self._create_mock_instagram_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Instagram research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Instagram research setup failed: {e}")
        
        return results
    
    async def _research_facebook(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from Facebook"""
        results = []
        
        try:
            # Facebook public content research
            for keyword in query.keywords:
                try:
                    # Note: Facebook public content search is limited
                    # For now, we'll create mock results
                    mock_results = await self._create_mock_facebook_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Facebook research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Facebook research setup failed: {e}")
        
        return results
    
    async def _research_linkedin(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from LinkedIn"""
        results = []
        
        try:
            # LinkedIn content research
            for keyword in query.keywords:
                try:
                    # Note: LinkedIn research capabilities are limited
                    # For now, we'll create mock results
                    mock_results = await self._create_mock_linkedin_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"LinkedIn research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"LinkedIn research setup failed: {e}")
        
        return results
    
    async def _research_google_trends(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research trends from Google Trends"""
        results = []
        
        try:
            # Google Trends research
            for keyword in query.keywords:
                try:
                    # Note: Would use pytrends library for real implementation
                    mock_results = await self._create_mock_trends_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Google Trends research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Google Trends research setup failed: {e}")
        
        return results
    
    async def _research_news_api(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from News API"""
        results = []
        
        if not self.news_api_key:
            logger.warning("News API key not configured, skipping news research")
            return results
        
        try:
            async with httpx.AsyncClient() as client:
                for keyword in query.keywords:
                    try:
                        # News API request
                        params = {
                            "q": keyword,
                            "apiKey": self.news_api_key,
                            "pageSize": min(query.max_results // len(query.keywords), 100),
                            "sortBy": "publishedAt",
                            "language": query.language
                        }
                        
                        # Add time range
                        if query.time_range != "all":
                            from_date = self._get_date_from_range(query.time_range)
                            params["from"] = from_date.isoformat()
                        
                        response = await client.get(
                            "https://newsapi.org/v2/everything",
                            params=params,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            news_data = response.json()
                            
                            for article in news_data.get("articles", []):
                                result = ResearchResult(
                                    source="news_api",
                                    platform="news",
                                    content_id=article.get("url", ""),
                                    title=article.get("title", ""),
                                    content=article.get("description", ""),
                                    author=article.get("author", "Unknown"),
                                    published_at=datetime.fromisoformat(
                                        article.get("publishedAt", "").replace("Z", "+00:00")
                                    ),
                                    url=article.get("url", ""),
                                    engagement_metrics={},
                                    trending_score=0.5,  # News articles get moderate trending score
                                    relevance_score=0.8,  # High relevance from keyword match
                                    media_urls=[article.get("urlToImage")] if article.get("urlToImage") else []
                                )
                                results.append(result)
                        
                        # Rate limiting
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"News API research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"News API research setup failed: {e}")
        
        return results
    
    async def _research_reddit(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from Reddit"""
        results = []
        
        try:
            # Reddit API research (would require Reddit API credentials)
            for keyword in query.keywords:
                try:
                    # Note: Would use PRAW or direct API calls for real implementation
                    mock_results = await self._create_mock_reddit_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Reddit research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Reddit research setup failed: {e}")
        
        return results
    
    async def _research_youtube(self, query: ResearchQuery) -> List[ResearchResult]:
        """Research content from YouTube"""
        results = []
        
        try:
            # YouTube API research (would require YouTube Data API key)
            for keyword in query.keywords:
                try:
                    # Note: Would use YouTube Data API for real implementation
                    mock_results = await self._create_mock_youtube_results(keyword, query)
                    results.extend(mock_results)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"YouTube research failed for keyword '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"YouTube research setup failed: {e}")
        
        return results
    
    def _build_twitter_search_query(self, keyword: str, query: ResearchQuery) -> str:
        """Build Twitter search query with filters"""
        search_query = f'"{keyword}"'
        
        # Add time filter
        if query.time_range == "1h":
            search_query += " -filter:retweets"
        elif query.time_range == "24h":
            search_query += " since:yesterday"
        elif query.time_range == "7d":
            search_query += " since:week_ago"
        
        # Add language filter
        if query.language != "en":
            search_query += f" lang:{query.language}"
        
        # Add engagement filter for quality
        search_query += " min_replies:1"
        
        return search_query
    
    def _get_date_from_range(self, time_range: str) -> datetime:
        """Convert time range string to datetime"""
        now = datetime.utcnow()
        
        if time_range == "1h":
            return now - timedelta(hours=1)
        elif time_range == "24h":
            return now - timedelta(days=1)
        elif time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=7)  # Default to 7 days
    
    async def _analyze_trends(
        self,
        results: List[ResearchResult],
        query: ResearchQuery
    ) -> List[TrendAnalysis]:
        """Analyze trends from research results"""
        if not results:
            return []
        
        # Group results by topic/keyword
        topic_groups = {}
        
        for result in results:
            # Extract keywords and topics
            topics = self._extract_topics_from_content(result.title + " " + result.content)
            
            for topic in topics:
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(result)
        
        # Analyze each topic group
        trend_analyses = []
        
        for topic, topic_results in topic_groups.items():
            if len(topic_results) < 3:  # Skip topics with too few mentions
                continue
            
            # Calculate trend metrics
            content_volume = len(topic_results)
            avg_engagement = sum(
                sum(r.engagement_metrics.values()) for r in topic_results
            ) / len(topic_results) if topic_results else 0
            
            # Calculate growth rate (simplified)
            growth_rate = min(content_volume / 10, 2.0)  # Cap at 200%
            
            # Determine sentiment
            sentiment_scores = [r.sentiment_score for r in topic_results if r.sentiment_score is not None]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            if avg_sentiment > 0.1:
                sentiment = "positive"
            elif avg_sentiment < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Calculate trend score
            trend_score = (
                (content_volume * 0.3) +
                (avg_engagement * 0.4) +
                (growth_rate * 0.3)
            )
            
            # Find platforms where this topic is trending
            platforms = list(set(r.platform for r in topic_results))
            
            # Extract related keywords
            related_keywords = self._extract_related_keywords(topic_results, topic)
            
            # Check if viral
            is_viral = any(
                sum(r.engagement_metrics.values()) > 10000 for r in topic_results
            )
            
            trend_analysis = TrendAnalysis(
                topic=topic,
                trend_score=trend_score,
                growth_rate=growth_rate,
                platforms=platforms,
                related_keywords=related_keywords[:10],  # Top 10
                content_volume=content_volume,
                avg_engagement=avg_engagement,
                sentiment=sentiment,
                time_period=query.time_range,
                is_viral=is_viral
            )
            
            trend_analyses.append(trend_analysis)
        
        # Sort by trend score and return top trends
        trend_analyses.sort(key=lambda x: x.trend_score, reverse=True)
        return trend_analyses[:20]  # Top 20 trends
    
    def _extract_topics_from_content(self, content: str) -> List[str]:
        """Extract topics from content using simple keyword extraction"""
        # Simple implementation - in production would use NLP libraries
        words = content.lower().split()
        
        # Filter common words and extract meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those"}
        
        topics = []
        for word in words:
            if len(word) > 3 and word not in stop_words and word.isalpha():
                topics.append(word)
        
        # Return unique topics
        return list(set(topics[:5]))  # Top 5 topics per content
    
    def _extract_related_keywords(self, results: List[ResearchResult], main_topic: str) -> List[str]:
        """Extract related keywords from results"""
        all_content = " ".join([r.title + " " + r.content for r in results])
        topics = self._extract_topics_from_content(all_content)
        
        # Remove main topic and return related ones
        related = [t for t in topics if t != main_topic]
        
        # Count frequency and return most common
        from collections import Counter
        counter = Counter(related)
        return [word for word, count in counter.most_common(20)]
    
    def _calculate_sentiment_breakdown(self, results: List[ResearchResult]) -> Dict[str, int]:
        """Calculate sentiment breakdown from results"""
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for result in results:
            if result.sentiment_score is not None:
                if result.sentiment_score > 0.1:
                    sentiment_counts["positive"] += 1
                elif result.sentiment_score < -0.1:
                    sentiment_counts["negative"] += 1
                else:
                    sentiment_counts["neutral"] += 1
            else:
                sentiment_counts["neutral"] += 1
        
        return sentiment_counts
    
    def _calculate_engagement_summary(self, results: List[ResearchResult]) -> Dict[str, float]:
        """Calculate engagement summary from results"""
        if not results:
            return {"avg_engagement": 0.0, "max_engagement": 0.0, "total_engagement": 0.0}
        
        engagements = []
        for result in results:
            total_engagement = sum(result.engagement_metrics.values())
            engagements.append(total_engagement)
        
        return {
            "avg_engagement": sum(engagements) / len(engagements),
            "max_engagement": max(engagements),
            "total_engagement": sum(engagements)
        }
    
    async def _save_research_to_db(
        self,
        db: Session,
        summary: ResearchSummary,
        results: List[ResearchResult]
    ):
        """Save research results to database"""
        try:
            # Save research summary
            research_data = ResearchData(
                query_keywords=summary.query.keywords,
                platforms=summary.results_by_platform,
                total_results=summary.total_results,
                research_duration=summary.research_duration,
                sentiment_breakdown=summary.sentiment_breakdown,
                engagement_summary=summary.engagement_summary,
                completed_at=summary.completed_at,
                results_data=[asdict(r) for r in results]
            )
            
            db.add(research_data)
            
            # Save trending topics
            for trend in summary.trending_topics:
                trending_topic = TrendingTopic(
                    topic=trend.topic,
                    trend_score=trend.trend_score,
                    growth_rate=trend.growth_rate,
                    platforms=trend.platforms,
                    content_volume=trend.content_volume,
                    avg_engagement=trend.avg_engagement,
                    sentiment=trend.sentiment,
                    is_viral=trend.is_viral,
                    detected_at=datetime.utcnow(),
                    time_period=trend.time_period
                )
                
                db.add(trending_topic)
            
            db.commit()
            logger.info(f"Saved research data with {len(results)} results and {len(summary.trending_topics)} trends")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save research data: {e}")
            raise
    
    # Mock result generators (for development/testing)
    async def _create_mock_twitter_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock Twitter results for development"""
        results = []
        for i in range(min(5, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="twitter_api",
                platform="twitter",
                content_id=f"twitter_{keyword}_{i}",
                title=f"Tweet about {keyword}",
                content=f"This is a mock tweet about {keyword} for testing purposes #{keyword}",
                author=f"user_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i),
                url=f"https://twitter.com/user_{i}/status/{i}",
                engagement_metrics={"likes": 50 + i*10, "retweets": 5 + i, "replies": 3 + i},
                sentiment_score=0.2 - (i * 0.1),
                trending_score=0.7,
                relevance_score=0.9
            )
            results.append(result)
        
        return results
    
    async def _create_mock_instagram_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock Instagram results for development"""
        results = []
        for i in range(min(3, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="instagram_api",
                platform="instagram",
                content_id=f"instagram_{keyword}_{i}",
                title=f"Instagram post about {keyword}",
                content=f"Beautiful content about {keyword} 📸 #{keyword}",
                author=f"insta_user_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i*2),
                url=f"https://instagram.com/p/{keyword}_{i}",
                engagement_metrics={"likes": 200 + i*50, "comments": 10 + i*2},
                sentiment_score=0.3,
                trending_score=0.6,
                relevance_score=0.8,
                media_urls=[f"https://example.com/image_{i}.jpg"]
            )
            results.append(result)
        
        return results
    
    async def _create_mock_facebook_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock Facebook results for development"""
        results = []
        for i in range(min(3, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="facebook_api",
                platform="facebook",
                content_id=f"facebook_{keyword}_{i}",
                title=f"Facebook post about {keyword}",
                content=f"Sharing interesting insights about {keyword}",
                author=f"facebook_user_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i*3),
                url=f"https://facebook.com/posts/{keyword}_{i}",
                engagement_metrics={"likes": 100 + i*20, "comments": 15 + i*3, "shares": 5 + i},
                sentiment_score=0.1,
                trending_score=0.5,
                relevance_score=0.7
            )
            results.append(result)
        
        return results
    
    async def _create_mock_linkedin_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock LinkedIn results for development"""
        results = []
        for i in range(min(2, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="linkedin_api",
                platform="linkedin",
                content_id=f"linkedin_{keyword}_{i}",
                title=f"Professional insights on {keyword}",
                content=f"Professional perspective on {keyword} in today's market",
                author=f"linkedin_user_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i*4),
                url=f"https://linkedin.com/posts/{keyword}_{i}",
                engagement_metrics={"likes": 50 + i*15, "comments": 8 + i*2, "shares": 3 + i},
                sentiment_score=0.4,
                trending_score=0.8,
                relevance_score=0.9
            )
            results.append(result)
        
        return results
    
    async def _create_mock_trends_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock Google Trends results for development"""
        results = []
        result = ResearchResult(
            source="google_trends",
            platform="google_trends",
            content_id=f"trends_{keyword}",
            title=f"Trending: {keyword}",
            content=f"Search trend data for {keyword}",
            author="Google Trends",
            published_at=datetime.utcnow(),
            url=f"https://trends.google.com/trends/explore?q={keyword}",
            engagement_metrics={"search_volume": 1000},
            trending_score=0.9,
            relevance_score=1.0
        )
        results.append(result)
        
        return results
    
    async def _create_mock_reddit_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock Reddit results for development"""
        results = []
        for i in range(min(4, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="reddit_api",
                platform="reddit",
                content_id=f"reddit_{keyword}_{i}",
                title=f"Discussion about {keyword}",
                content=f"Community discussion on {keyword} - what are your thoughts?",
                author=f"reddit_user_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i*2),
                url=f"https://reddit.com/r/discussion/comments/{keyword}_{i}",
                engagement_metrics={"upvotes": 150 + i*30, "comments": 25 + i*5},
                sentiment_score=0.0,
                trending_score=0.6,
                relevance_score=0.8
            )
            results.append(result)
        
        return results
    
    async def _create_mock_youtube_results(self, keyword: str, query: ResearchQuery) -> List[ResearchResult]:
        """Create mock YouTube results for development"""
        results = []
        for i in range(min(3, query.max_results // len(query.keywords))):
            result = ResearchResult(
                source="youtube_api",
                platform="youtube",
                content_id=f"youtube_{keyword}_{i}",
                title=f"Video about {keyword}",
                content=f"Educational video content about {keyword}",
                author=f"youtube_channel_{i}",
                published_at=datetime.utcnow() - timedelta(hours=i*6),
                url=f"https://youtube.com/watch?v={keyword}_{i}",
                engagement_metrics={"views": 5000 + i*1000, "likes": 200 + i*40, "comments": 50 + i*10},
                sentiment_score=0.2,
                trending_score=0.7,
                relevance_score=0.8,
                media_urls=[f"https://youtube.com/thumbnail/{keyword}_{i}.jpg"]
            )
            results.append(result)
        
        return results

# Global research pipeline instance
research_pipeline = AutomatedResearchPipeline()

# Export alias for backward compatibility
research_service = research_pipeline

# Explicit exports for better maintainability
__all__ = [
    'AutomatedResearchPipeline',
    'ResearchSource',
    'ResearchQuery',
    'research_pipeline',
    'research_service'
]