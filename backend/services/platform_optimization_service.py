"""
Platform-Specific Optimization Service
Advanced optimization features tailored for each social media platform
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.services.redis_cache import redis_cache
from backend.services.error_recovery_service import with_circuit_breaker, with_retry, RetryConfig
from backend.db.database_optimized import get_db_connection
from backend.db.models import ContentItem, ContentPerformanceSnapshot

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Optimization strategies"""
    ENGAGEMENT_MAXIMIZATION = "engagement_maximization"
    REACH_OPTIMIZATION = "reach_optimization"
    CONVERSION_FOCUS = "conversion_focus"
    BRAND_AWARENESS = "brand_awareness"
    COST_EFFICIENCY = "cost_efficiency"

@dataclass
class PlatformOptimization:
    """Platform-specific optimization configuration"""
    platform: str
    strategy: OptimizationStrategy
    max_requests_per_hour: int
    optimal_posting_times: List[str]
    content_type_preferences: Dict[str, float]
    hashtag_limits: Dict[str, int]
    character_limits: Dict[str, int]
    media_specifications: Dict[str, Any]

class PlatformOptimizationService:
    """
    Service for platform-specific optimizations and best practices
    """
    
    def __init__(self):
        self.platform_configs = {}
        self.optimization_cache = {}
        self._initialize_platform_configs()
    
    def _initialize_platform_configs(self):
        """Initialize platform-specific optimization configurations"""
        
        # Twitter/X optimizations
        self.platform_configs['twitter'] = PlatformOptimization(
            platform='twitter',
            strategy=OptimizationStrategy.ENGAGEMENT_MAXIMIZATION,
            max_requests_per_hour=300,  # API v2 limits
            optimal_posting_times=['09:00', '13:00', '17:00', '20:00'],
            content_type_preferences={
                'text': 1.0,
                'image': 1.2,
                'video': 1.5,
                'gif': 1.3,
                'poll': 1.4,
                'thread': 1.6
            },
            hashtag_limits={'max_hashtags': 3, 'optimal_hashtags': 2},
            character_limits={'text': 280, 'bio': 160},
            media_specifications={
                'image': {'max_size': '5MB', 'formats': ['jpg', 'png', 'gif'], 'dimensions': '1200x675'},
                'video': {'max_size': '512MB', 'formats': ['mp4', 'mov'], 'max_duration': 140}
            }
        )
        
        # Instagram optimizations
        self.platform_configs['instagram'] = PlatformOptimization(
            platform='instagram',
            strategy=OptimizationStrategy.ENGAGEMENT_MAXIMIZATION,
            max_requests_per_hour=200,
            optimal_posting_times=['11:00', '14:00', '17:00', '19:00'],
            content_type_preferences={
                'image': 1.0,
                'carousel': 1.3,
                'video': 1.4,
                'reels': 1.8,
                'story': 1.2,
                'igtv': 1.1
            },
            hashtag_limits={'max_hashtags': 30, 'optimal_hashtags': 11},
            character_limits={'caption': 2200, 'bio': 150},
            media_specifications={
                'image': {'aspect_ratios': ['1:1', '4:5', '9:16'], 'min_resolution': '320x320'},
                'video': {'max_size': '4GB', 'max_duration': 60, 'min_duration': 3},
                'reels': {'max_duration': 90, 'aspect_ratio': '9:16'}
            }
        )
        
        # Facebook optimizations
        self.platform_configs['facebook'] = PlatformOptimization(
            platform='facebook',
            strategy=OptimizationStrategy.REACH_OPTIMIZATION,
            max_requests_per_hour=200,
            optimal_posting_times=['12:00', '15:00', '18:00', '21:00'],
            content_type_preferences={
                'text': 0.8,
                'image': 1.0,
                'video': 1.5,
                'link': 0.9,
                'event': 1.2,
                'live': 1.7
            },
            hashtag_limits={'max_hashtags': 30, 'optimal_hashtags': 5},
            character_limits={'post': 63206, 'bio': 101},
            media_specifications={
                'image': {'recommended_size': '1200x630', 'formats': ['jpg', 'png']},
                'video': {'max_size': '10GB', 'recommended_duration': '15-60s'}
            }
        )
        
        # LinkedIn optimizations
        self.platform_configs['linkedin'] = PlatformOptimization(
            platform='linkedin',
            strategy=OptimizationStrategy.BRAND_AWARENESS,
            max_requests_per_hour=100,
            optimal_posting_times=['08:00', '12:00', '17:00', '18:00'],
            content_type_preferences={
                'text': 1.0,
                'image': 1.1,
                'video': 1.3,
                'document': 1.2,
                'article': 1.4,
                'poll': 1.5
            },
            hashtag_limits={'max_hashtags': 5, 'optimal_hashtags': 3},
            character_limits={'post': 3000, 'headline': 120},
            media_specifications={
                'image': {'recommended_size': '1200x627', 'formats': ['jpg', 'png']},
                'video': {'max_size': '5GB', 'max_duration': 600}
            }
        )
    
    @with_circuit_breaker("content_optimization")
    async def optimize_content_for_platform(
        self,
        content: str,
        platform: str,
        content_type: str = "text",
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize content for a specific platform
        
        Args:
            content: Original content
            platform: Target platform
            content_type: Type of content
            target_audience: Target audience demographics
            
        Returns:
            Optimized content with recommendations
        """
        try:
            config = self.platform_configs.get(platform)
            if not config:
                return {'error': f'Platform {platform} not supported'}
            
            optimization_result = {
                'platform': platform,
                'original_content': content,
                'optimized_content': content,
                'recommendations': [],
                'score': 0.0,
                'character_usage': {},
                'hashtag_analysis': {},
                'timing_recommendations': config.optimal_posting_times
            }
            
            # Character limit optimization
            char_limit = config.character_limits.get('text', config.character_limits.get('post', 280))
            content_length = len(content)
            
            optimization_result['character_usage'] = {
                'current': content_length,
                'limit': char_limit,
                'percentage': (content_length / char_limit) * 100,
                'remaining': char_limit - content_length
            }
            
            if content_length > char_limit:
                # Truncate content
                truncated_content = content[:char_limit-10] + "..."
                optimization_result['optimized_content'] = truncated_content
                optimization_result['recommendations'].append({
                    'type': 'character_limit',
                    'message': f'Content truncated to fit {platform} character limit',
                    'priority': 'high'
                })
            
            # Hashtag optimization
            hashtag_analysis = await self._analyze_hashtags(content, platform)
            optimization_result['hashtag_analysis'] = hashtag_analysis
            
            # Content type optimization
            content_score = config.content_type_preferences.get(content_type, 1.0)
            optimization_result['score'] = content_score
            
            # Platform-specific recommendations
            platform_recommendations = await self._get_platform_recommendations(
                content, platform, content_type, target_audience
            )
            optimization_result['recommendations'].extend(platform_recommendations)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_hashtags(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze hashtags in content for platform optimization"""
        try:
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', content)
            
            config = self.platform_configs.get(platform)
            if not config:
                return {'error': 'Platform not configured'}
            
            max_hashtags = config.hashtag_limits.get('max_hashtags', 10)
            optimal_hashtags = config.hashtag_limits.get('optimal_hashtags', 5)
            
            analysis = {
                'current_count': len(hashtags),
                'max_allowed': max_hashtags,
                'optimal_count': optimal_hashtags,
                'hashtags': hashtags,
                'recommendations': []
            }
            
            if len(hashtags) > max_hashtags:
                analysis['recommendations'].append({
                    'type': 'hashtag_limit',
                    'message': f'Reduce hashtags to {max_hashtags} or fewer',
                    'priority': 'high'
                })
            elif len(hashtags) < optimal_hashtags:
                analysis['recommendations'].append({
                    'type': 'hashtag_optimization',
                    'message': f'Consider adding more hashtags (optimal: {optimal_hashtags})',
                    'priority': 'medium'
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Hashtag analysis failed: {e}")
            return {'error': str(e)}
    
    async def _get_platform_recommendations(
        self,
        content: str,
        platform: str,
        content_type: str,
        target_audience: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get platform-specific content recommendations"""
        recommendations = []
        
        try:
            if platform == 'twitter':
                recommendations.extend([
                    {
                        'type': 'engagement',
                        'message': 'Consider adding a question to increase engagement',
                        'priority': 'medium'
                    },
                    {
                        'type': 'timing',
                        'message': 'Post during peak hours for maximum visibility',
                        'priority': 'medium'
                    }
                ])
                
                if content_type == 'text' and len(content) < 100:
                    recommendations.append({
                        'type': 'content_length',
                        'message': 'Consider expanding content for better engagement',
                        'priority': 'low'
                    })
            
            elif platform == 'instagram':
                recommendations.extend([
                    {
                        'type': 'visual_content',
                        'message': 'Add high-quality images or videos for better performance',
                        'priority': 'high'
                    },
                    {
                        'type': 'story_integration',
                        'message': 'Cross-promote in Instagram Stories',
                        'priority': 'medium'
                    }
                ])
            
            elif platform == 'linkedin':
                recommendations.extend([
                    {
                        'type': 'professional_tone',
                        'message': 'Ensure content maintains professional tone',
                        'priority': 'high'
                    },
                    {
                        'type': 'industry_hashtags',
                        'message': 'Use industry-specific hashtags for reach',
                        'priority': 'medium'
                    }
                ])
            
            elif platform == 'facebook':
                recommendations.extend([
                    {
                        'type': 'engagement_bait',
                        'message': 'Avoid engagement bait tactics (algorithm penalty)',
                        'priority': 'high'
                    },
                    {
                        'type': 'native_content',
                        'message': 'Native content performs better than shared links',
                        'priority': 'medium'
                    }
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get platform recommendations: {e}")
            return []
    
    @with_retry(RetryConfig(max_attempts=3), "posting_time_optimization")
    async def get_optimal_posting_schedule(
        self,
        platform: str,
        user_id: int,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Get optimal posting schedule based on platform and user data
        
        Args:
            platform: Social media platform
            user_id: User ID for personalization
            timezone: User timezone
            
        Returns:
            Optimal posting schedule
        """
        try:
            # Get platform configuration
            config = self.platform_configs.get(platform)
            if not config:
                return {'error': f'Platform {platform} not supported'}
            
            # Get user's historical performance data
            user_performance = await self._analyze_user_performance(user_id, platform)
            
            # Combine platform defaults with user data
            optimal_schedule = {
                'platform': platform,
                'timezone': timezone,
                'recommended_times': config.optimal_posting_times,
                'personalized_times': [],
                'frequency_recommendations': {},
                'performance_insights': user_performance
            }
            
            # Personalize based on user performance
            if user_performance.get('best_performing_hours'):
                optimal_schedule['personalized_times'] = user_performance['best_performing_hours'][:4]
            
            # Frequency recommendations
            optimal_schedule['frequency_recommendations'] = {
                'daily_posts': self._get_platform_frequency_recommendation(platform),
                'peak_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday'],
                'avoid_times': ['01:00', '02:00', '03:00', '04:00', '05:00']
            }
            
            return optimal_schedule
            
        except Exception as e:
            logger.error(f"Posting schedule optimization failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_user_performance(self, user_id: int, platform: str) -> Dict[str, Any]:
        """Analyze user's historical performance data"""
        try:
            with get_db_connection() as db:
                # Get user's content performance from last 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                performance_data = (
                    db.query(ContentItem, ContentPerformanceSnapshot)
                    .join(ContentPerformanceSnapshot)
                    .filter(ContentItem.user_id == user_id)
                    .filter(ContentItem.platform == platform)
                    .filter(ContentItem.published_at >= cutoff_date)
                    .all()
                )
                
                if not performance_data:
                    return {'message': 'No historical data available'}
                
                # Analyze posting times vs engagement
                hour_performance = {}
                total_engagement = 0
                
                for content, snapshot in performance_data:
                    if content.published_at:
                        hour = content.published_at.hour
                        engagement = (snapshot.like_count + snapshot.share_count + 
                                    snapshot.comment_count + snapshot.view_count)
                        
                        if hour not in hour_performance:
                            hour_performance[hour] = {'total_engagement': 0, 'post_count': 0}
                        
                        hour_performance[hour]['total_engagement'] += engagement
                        hour_performance[hour]['post_count'] += 1
                        total_engagement += engagement
                
                # Calculate average engagement per hour
                best_hours = []
                for hour, data in hour_performance.items():
                    if data['post_count'] > 0:
                        avg_engagement = data['total_engagement'] / data['post_count']
                        best_hours.append((hour, avg_engagement))
                
                # Sort by engagement and get top hours
                best_hours.sort(key=lambda x: x[1], reverse=True)
                best_performing_hours = [f"{hour:02d}:00" for hour, _ in best_hours[:5]]
                
                return {
                    'total_posts': len(performance_data),
                    'total_engagement': total_engagement,
                    'avg_engagement_per_post': total_engagement / len(performance_data) if performance_data else 0,
                    'best_performing_hours': best_performing_hours,
                    'hourly_performance': hour_performance
                }
                
        except Exception as e:
            logger.error(f"User performance analysis failed: {e}")
            return {'error': str(e)}
    
    def _get_platform_frequency_recommendation(self, platform: str) -> Dict[str, Any]:
        """Get posting frequency recommendations for platform"""
        frequency_map = {
            'twitter': {'min': 3, 'max': 15, 'optimal': 7},
            'instagram': {'min': 1, 'max': 3, 'optimal': 1},
            'facebook': {'min': 1, 'max': 2, 'optimal': 1},
            'linkedin': {'min': 2, 'max': 5, 'optimal': 3}
        }
        
        return frequency_map.get(platform, {'min': 1, 'max': 3, 'optimal': 1})
    
    async def optimize_hashtags_for_platform(
        self,
        content: str,
        platform: str,
        niche: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize hashtags for specific platform and niche
        
        Args:
            content: Content text
            platform: Target platform
            niche: Content niche/category
            
        Returns:
            Hashtag optimization results
        """
        try:
            # Platform-specific hashtag strategies
            hashtag_strategies = {
                'instagram': {
                    'trending_hashtags': ['#instagood', '#photooftheday', '#love', '#instadaily'],
                    'niche_hashtags': {
                        'fitness': ['#fitness', '#workout', '#health', '#fitnessmotivation'],
                        'food': ['#foodie', '#delicious', '#foodporn', '#instafood'],
                        'travel': ['#travel', '#wanderlust', '#adventure', '#explore']
                    }
                },
                'twitter': {
                    'trending_hashtags': ['#TwitterTips', '#MondayMotivation', '#ThrowbackThursday'],
                    'engagement_hashtags': ['#RT', '#Follow', '#Like']
                },
                'linkedin': {
                    'professional_hashtags': ['#LinkedInTips', '#CareerAdvice', '#Leadership', '#Innovation'],
                    'industry_hashtags': {
                        'tech': ['#Technology', '#AI', '#DigitalTransformation'],
                        'marketing': ['#Marketing', '#DigitalMarketing', '#ContentMarketing']
                    }
                }
            }
            
            platform_strategy = hashtag_strategies.get(platform, {})
            config = self.platform_configs.get(platform)
            
            if not config:
                return {'error': f'Platform {platform} not supported'}
            
            # Extract existing hashtags
            import re
            existing_hashtags = re.findall(r'#\w+', content)
            
            # Generate recommendations
            recommended_hashtags = []
            
            # Add trending hashtags
            trending = platform_strategy.get('trending_hashtags', [])
            recommended_hashtags.extend(trending[:2])
            
            # Add niche-specific hashtags
            if niche:
                niche_hashtags = platform_strategy.get('niche_hashtags', {}).get(niche, [])
                recommended_hashtags.extend(niche_hashtags[:3])
            
            # Remove duplicates and existing hashtags
            recommended_hashtags = [h for h in recommended_hashtags if h not in existing_hashtags]
            
            # Respect platform limits
            max_hashtags = config.hashtag_limits.get('max_hashtags', 10)
            optimal_hashtags = config.hashtag_limits.get('optimal_hashtags', 5)
            
            total_hashtags = len(existing_hashtags) + len(recommended_hashtags)
            if total_hashtags > max_hashtags:
                recommended_hashtags = recommended_hashtags[:max_hashtags - len(existing_hashtags)]
            
            return {
                'platform': platform,
                'existing_hashtags': existing_hashtags,
                'recommended_hashtags': recommended_hashtags,
                'total_hashtags': len(existing_hashtags) + len(recommended_hashtags),
                'optimal_count': optimal_hashtags,
                'max_allowed': max_hashtags,
                'strategy_used': f'{platform}_optimization'
            }
            
        except Exception as e:
            logger.error(f"Hashtag optimization failed: {e}")
            return {'error': str(e)}
    
    async def get_platform_performance_metrics(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific performance metrics and benchmarks"""
        try:
            # Platform benchmarks (industry averages)
            benchmarks = {
                'instagram': {
                    'engagement_rate': 1.22,  # Average engagement rate
                    'optimal_post_length': 125,
                    'best_content_types': ['carousel', 'reels', 'video'],
                    'peak_engagement_hours': [11, 13, 17, 19]
                },
                'twitter': {
                    'engagement_rate': 0.045,
                    'optimal_post_length': 100,
                    'best_content_types': ['video', 'images', 'polls'],
                    'peak_engagement_hours': [9, 13, 17, 20]
                },
                'facebook': {
                    'engagement_rate': 0.18,
                    'optimal_post_length': 80,
                    'best_content_types': ['video', 'images', 'live'],
                    'peak_engagement_hours': [12, 15, 18, 21]
                },
                'linkedin': {
                    'engagement_rate': 2.0,
                    'optimal_post_length': 150,
                    'best_content_types': ['video', 'document', 'article'],
                    'peak_engagement_hours': [8, 12, 17, 18]
                }
            }
            
            platform_benchmarks = benchmarks.get(platform)
            if not platform_benchmarks:
                return {'error': f'No benchmarks available for {platform}'}
            
            # Add current optimization settings
            config = self.platform_configs.get(platform)
            result = {
                'platform': platform,
                'benchmarks': platform_benchmarks,
                'optimization_config': {
                    'strategy': config.strategy.value if config else 'unknown',
                    'max_requests_per_hour': config.max_requests_per_hour if config else 'unknown',
                    'optimal_posting_times': config.optimal_posting_times if config else [],
                    'character_limits': config.character_limits if config else {}
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get platform metrics: {e}")
            return {'error': str(e)}

# Global platform optimization service
platform_optimization_service = PlatformOptimizationService()