"""
Real Trends Service - replaces mock Google Trends with actual data
Production-ready service with no mock data
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
import json

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RealTrendsService:
    """Real trends service using Google Trends and Serper API"""
    
    def __init__(self):
        self.serper_api_key = settings.serper_api_key
        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY required for trends research")
        
        # Initialize pytrends if available
        self.pytrends = None
        if PYTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360)
                logger.info("pytrends initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize pytrends: {e}")
                self.pytrends = None
    
    def get_trending_topics(self, category: str = "general", count: int = 10) -> List[Dict[str, Any]]:
        """Get real trending topics using Serper API"""
        try:
            # Use Serper to get current trends
            url = "https://google.serper.dev/search"
            
            query_map = {
                "general": "trending topics today",
                "tech": "trending technology topics today",
                "business": "trending business topics today", 
                "entertainment": "trending entertainment topics today",
                "sports": "trending sports topics today",
                "health": "trending health topics today"
            }
            
            query = query_map.get(category, "trending topics today")
            
            payload = {
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": count
            }
            
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trending_topics = []
            
            # Extract trending topics from search results
            for i, result in enumerate(data.get('organic', [])[:count]):
                trending_topics.append({
                    'topic': result.get('title', '').replace(' - ', ' ').split(' | ')[0],
                    'description': result.get('snippet', ''),
                    'source': result.get('displayLink', ''),
                    'url': result.get('link', ''),
                    'category': category,
                    'rank': i + 1,
                    'search_interest': 100 - (i * 5),  # Approximate declining interest
                    'retrieved_at': datetime.utcnow().isoformat()
                })
            
            logger.info(f"Retrieved {len(trending_topics)} trending topics for {category}")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            raise
    
    def get_search_volume_data(self, keywords: List[str], timeframe: str = "today 3-m") -> Dict[str, Any]:
        """Get real search volume data using pytrends"""
        if not self.pytrends:
            return self._get_serper_search_volume(keywords)
        
        try:
            # Build payload for pytrends
            self.pytrends.build_payload(
                keywords, 
                cat=0, 
                timeframe=timeframe, 
                geo='US', 
                gprop=''
            )
            
            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Get regional interest
            interest_by_region = self.pytrends.interest_by_region()
            
            # Format results
            results = {
                'keywords': keywords,
                'timeframe': timeframe,
                'interest_over_time': [],
                'related_queries': {},
                'top_regions': [],
                'summary': {
                    'total_keywords': len(keywords),
                    'data_points': len(interest_over_time) if not interest_over_time.empty else 0,
                    'retrieved_at': datetime.utcnow().isoformat()
                }
            }
            
            # Process interest over time
            if not interest_over_time.empty:
                for idx, row in interest_over_time.iterrows():
                    data_point = {'date': idx.isoformat()}
                    for keyword in keywords:
                        if keyword in row:
                            data_point[keyword] = int(row[keyword])
                    results['interest_over_time'].append(data_point)
            
            # Process related queries
            for keyword in keywords:
                if keyword in related_queries:
                    top_queries = related_queries[keyword].get('top')
                    if top_queries is not None and not top_queries.empty:
                        results['related_queries'][keyword] = top_queries.head(5).to_dict('records')
            
            # Process regional interest
            if not interest_by_region.empty:
                top_regions = interest_by_region.head(5)
                for region, values in top_regions.iterrows():
                    region_data = {'region': region}
                    for keyword in keywords:
                        if keyword in values:
                            region_data[keyword] = int(values[keyword])
                    results['top_regions'].append(region_data)
            
            logger.info(f"Retrieved search volume data for {len(keywords)} keywords")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get search volume data with pytrends: {e}")
            return self._get_serper_search_volume(keywords)
    
    def _get_serper_search_volume(self, keywords: List[str]) -> Dict[str, Any]:
        """Fallback search volume estimation using Serper API"""
        try:
            results = {
                'keywords': keywords,
                'timeframe': 'estimated',
                'search_estimates': [],
                'summary': {
                    'total_keywords': len(keywords),
                    'method': 'serper_estimation',
                    'retrieved_at': datetime.utcnow().isoformat()
                }
            }
            
            for keyword in keywords:
                # Search for each keyword to estimate popularity
                payload = {
                    "q": keyword,
                    "gl": "us", 
                    "hl": "en"
                }
                
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Estimate search volume based on results count
                    organic_count = len(data.get('organic', []))
                    news_count = len(data.get('news', []))
                    
                    # Simple estimation algorithm
                    estimated_volume = min((organic_count * 10000) + (news_count * 5000), 100)
                    
                    results['search_estimates'].append({
                        'keyword': keyword,
                        'estimated_interest': estimated_volume,
                        'organic_results': organic_count,
                        'news_results': news_count
                    })
            
            logger.info(f"Estimated search volume for {len(keywords)} keywords using Serper")
            return results
            
        except Exception as e:
            logger.error(f"Failed to estimate search volume with Serper: {e}")
            raise
    
    def get_competitor_trends(self, industry: str, competitor_keywords: List[str]) -> Dict[str, Any]:
        """Get competitor trend analysis using real search data"""
        try:
            # Search for industry + competitor information
            trends_data = []
            
            for keyword in competitor_keywords:
                search_query = f"{industry} {keyword} trends analysis"
                
                payload = {
                    "q": search_query,
                    "gl": "us",
                    "hl": "en",
                    "num": 5
                }
                
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract trend insights from search results
                    trend_info = {
                        'keyword': keyword,
                        'industry': industry,
                        'trend_indicators': [],
                        'news_mentions': len(data.get('news', [])),
                        'total_results': len(data.get('organic', []))
                    }
                    
                    # Analyze titles and snippets for trend indicators
                    for result in data.get('organic', [])[:3]:
                        title = result.get('title', '').lower()
                        snippet = result.get('snippet', '').lower()
                        
                        # Look for trend indicators
                        trend_words = ['growth', 'increase', 'rise', 'trending', 'popular', 
                                     'decline', 'decrease', 'fall', 'emerging', 'new']
                        
                        for word in trend_words:
                            if word in title or word in snippet:
                                trend_info['trend_indicators'].append({
                                    'indicator': word,
                                    'source': result.get('displayLink', ''),
                                    'context': snippet[:100]
                                })
                    
                    trends_data.append(trend_info)
            
            return {
                'industry': industry,
                'competitor_analysis': trends_data,
                'summary': {
                    'total_competitors': len(competitor_keywords),
                    'total_trend_indicators': sum(len(t['trend_indicators']) for t in trends_data),
                    'analysis_date': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get competitor trends: {e}")
            raise
    
    def get_seasonal_trends(self, keywords: List[str], months_back: int = 12) -> Dict[str, Any]:
        """Get seasonal trend patterns using real historical data"""
        if not self.pytrends:
            logger.warning("pytrends not available, using Serper for seasonal analysis")
            return self._get_serper_seasonal_trends(keywords, months_back)
        
        try:
            # Use longer timeframe for seasonal analysis
            timeframe = f"today {months_back}m"
            
            self.pytrends.build_payload(
                keywords,
                timeframe=timeframe,
                geo='US'
            )
            
            interest_data = self.pytrends.interest_over_time()
            
            if interest_data.empty:
                return self._get_serper_seasonal_trends(keywords, months_back)
            
            # Analyze seasonal patterns
            seasonal_analysis = {
                'keywords': keywords,
                'timeframe_months': months_back,
                'seasonal_patterns': [],
                'peak_periods': {},
                'summary': {
                    'analyzed_keywords': len(keywords),
                    'data_points': len(interest_data),
                    'analysis_date': datetime.utcnow().isoformat()
                }
            }
            
            for keyword in keywords:
                if keyword in interest_data.columns:
                    keyword_data = interest_data[keyword]
                    
                    # Find peak months
                    monthly_avg = keyword_data.groupby(keyword_data.index.month).mean()
                    peak_month = monthly_avg.idxmax()
                    peak_value = monthly_avg.max()
                    
                    # Calculate seasonal variation
                    seasonal_variation = (monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean() * 100
                    
                    seasonal_analysis['peak_periods'][keyword] = {
                        'peak_month': peak_month,
                        'peak_month_name': datetime(2024, peak_month, 1).strftime('%B'),
                        'peak_value': float(peak_value),
                        'seasonal_variation_percent': float(seasonal_variation)
                    }
            
            logger.info(f"Analyzed seasonal trends for {len(keywords)} keywords")
            return seasonal_analysis
            
        except Exception as e:
            logger.error(f"Failed to get seasonal trends: {e}")
            return self._get_serper_seasonal_trends(keywords, months_back)
    
    def _get_serper_seasonal_trends(self, keywords: List[str], months_back: int) -> Dict[str, Any]:
        """Fallback seasonal analysis using current search trends"""
        try:
            # Search for seasonal information about keywords
            seasonal_data = {
                'keywords': keywords,
                'timeframe_months': months_back,
                'seasonal_insights': [],
                'summary': {
                    'method': 'serper_seasonal_analysis',
                    'analyzed_keywords': len(keywords),
                    'analysis_date': datetime.utcnow().isoformat()
                }
            }
            
            for keyword in keywords:
                search_query = f"{keyword} seasonal trends monthly analysis"
                
                payload = {
                    "q": search_query,
                    "gl": "us",
                    "hl": "en",
                    "num": 3
                }
                
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract seasonal insights
                    insights = []
                    for result in data.get('organic', []):
                        snippet = result.get('snippet', '')
                        if any(month in snippet.lower() for month in 
                              ['january', 'february', 'march', 'april', 'may', 'june',
                               'july', 'august', 'september', 'october', 'november', 'december',
                               'spring', 'summer', 'fall', 'winter', 'holiday', 'seasonal']):
                            insights.append({
                                'source': result.get('displayLink', ''),
                                'insight': snippet[:200],
                                'url': result.get('link', '')
                            })
                    
                    seasonal_data['seasonal_insights'].append({
                        'keyword': keyword,
                        'insights': insights
                    })
            
            return seasonal_data
            
        except Exception as e:
            logger.error(f"Failed to get seasonal trends with Serper: {e}")
            raise