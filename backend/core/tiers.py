from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

class SubscriptionTier(Enum):
    BASE = "base"
    MID = "mid"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class TierFeatures:
    """Feature configuration for each subscription tier"""
    tier: SubscriptionTier
    max_platforms: int
    max_posts_per_day: int
    max_content_storage: int  # Number of content pieces to store
    research_enabled: bool
    image_generation: bool
    a_b_testing: bool
    advanced_analytics: bool
    custom_integrations: bool
    multi_language: bool
    viral_learning: bool
    human_feedback: bool
    white_labeling: bool
    api_access: bool
    priority_support: bool
    
    # Content features
    content_repurposing: bool
    trend_analysis: bool
    competitor_analysis: bool
    sentiment_monitoring: bool
    
    # Advanced features
    custom_ai_training: bool
    video_generation: bool  # Future: Veo 3
    crm_integration: bool
    advanced_scheduling: bool
    team_collaboration: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'tier': self.tier.value,
            'max_platforms': self.max_platforms,
            'max_posts_per_day': self.max_posts_per_day,
            'max_content_storage': self.max_content_storage,
            'features': {
                'research_enabled': self.research_enabled,
                'image_generation': self.image_generation,
                'a_b_testing': self.a_b_testing,
                'advanced_analytics': self.advanced_analytics,
                'custom_integrations': self.custom_integrations,
                'multi_language': self.multi_language,
                'viral_learning': self.viral_learning,
                'human_feedback': self.human_feedback,
                'white_labeling': self.white_labeling,
                'api_access': self.api_access,
                'priority_support': self.priority_support,
                'content_repurposing': self.content_repurposing,
                'trend_analysis': self.trend_analysis,
                'competitor_analysis': self.competitor_analysis,
                'sentiment_monitoring': self.sentiment_monitoring,
                'custom_ai_training': self.custom_ai_training,
                'video_generation': self.video_generation,
                'crm_integration': self.crm_integration,
                'advanced_scheduling': self.advanced_scheduling,
                'team_collaboration': self.team_collaboration,
            }
        }

class TierManager:
    """Manages subscription tiers and feature access"""
    
    def __init__(self):
        self.tier_configs = self._initialize_tier_configs()
    
    def _initialize_tier_configs(self) -> Dict[SubscriptionTier, TierFeatures]:
        """Initialize tier feature configurations"""
        return {
            SubscriptionTier.BASE: TierFeatures(
                tier=SubscriptionTier.BASE,
                max_platforms=3,  # Twitter, LinkedIn, Instagram
                max_posts_per_day=5,
                max_content_storage=100,
                research_enabled=True,
                image_generation=False,
                a_b_testing=False,
                advanced_analytics=False,
                custom_integrations=False,
                multi_language=False,
                viral_learning=False,
                human_feedback=False,
                white_labeling=False,
                api_access=False,
                priority_support=False,
                content_repurposing=True,
                trend_analysis=True,
                competitor_analysis=False,
                sentiment_monitoring=False,
                custom_ai_training=False,
                video_generation=False,
                crm_integration=False,
                advanced_scheduling=True,
                team_collaboration=False,
            ),
            
            SubscriptionTier.MID: TierFeatures(
                tier=SubscriptionTier.MID,
                max_platforms=4,  # + Facebook
                max_posts_per_day=15,
                max_content_storage=500,
                research_enabled=True,
                image_generation=True,
                a_b_testing=True,
                advanced_analytics=True,
                custom_integrations=False,
                multi_language=True,
                viral_learning=True,
                human_feedback=True,
                white_labeling=False,
                api_access=False,
                priority_support=False,
                content_repurposing=True,
                trend_analysis=True,
                competitor_analysis=True,
                sentiment_monitoring=True,
                custom_ai_training=False,
                video_generation=False,
                crm_integration=False,
                advanced_scheduling=True,
                team_collaboration=True,
            ),
            
            SubscriptionTier.PRO: TierFeatures(
                tier=SubscriptionTier.PRO,
                max_platforms=8,  # + YouTube, Pinterest, Snapchat
                max_posts_per_day=50,
                max_content_storage=2000,
                research_enabled=True,
                image_generation=True,
                a_b_testing=True,
                advanced_analytics=True,
                custom_integrations=True,
                multi_language=True,
                viral_learning=True,
                human_feedback=True,
                white_labeling=True,
                api_access=True,
                priority_support=True,
                content_repurposing=True,
                trend_analysis=True,
                competitor_analysis=True,
                sentiment_monitoring=True,
                custom_ai_training=True,
                video_generation=True,  # Veo 3 when available
                crm_integration=True,
                advanced_scheduling=True,
                team_collaboration=True,
            ),
            
            SubscriptionTier.ENTERPRISE: TierFeatures(
                tier=SubscriptionTier.ENTERPRISE,
                max_platforms=15,  # All supported platforms
                max_posts_per_day=200,
                max_content_storage=10000,
                research_enabled=True,
                image_generation=True,
                a_b_testing=True,
                advanced_analytics=True,
                custom_integrations=True,
                multi_language=True,
                viral_learning=True,
                human_feedback=True,
                white_labeling=True,
                api_access=True,
                priority_support=True,
                content_repurposing=True,
                trend_analysis=True,
                competitor_analysis=True,
                sentiment_monitoring=True,
                custom_ai_training=True,
                video_generation=True,
                crm_integration=True,
                advanced_scheduling=True,
                team_collaboration=True,
            )
        }
    
    def get_tier_config(self, tier: SubscriptionTier) -> TierFeatures:
        """Get feature configuration for a tier"""
        return self.tier_configs[tier]
    
    def check_feature_access(self, user_tier: SubscriptionTier, feature: str) -> bool:
        """Check if user tier has access to a feature"""
        tier_config = self.tier_configs[user_tier]
        return getattr(tier_config, feature, False)
    
    def check_usage_limit(self, user_tier: SubscriptionTier, usage_type: str, current_usage: int) -> bool:
        """Check if usage is within tier limits"""
        tier_config = self.tier_configs[user_tier]
        
        limits = {
            'platforms': tier_config.max_platforms,
            'posts_per_day': tier_config.max_posts_per_day,
            'content_storage': tier_config.max_content_storage
        }
        
        limit = limits.get(usage_type)
        return limit is None or current_usage < limit
    
    def get_upgrade_suggestions(self, current_tier: SubscriptionTier, usage_data: Dict[str, int]) -> List[Dict]:
        """Suggest upgrades based on usage patterns"""
        suggestions = []
        current_config = self.tier_configs[current_tier]
        
        # Check if hitting limits
        if usage_data.get('platforms', 0) >= current_config.max_platforms:
            suggestions.append({
                'reason': 'Platform limit reached',
                'description': f'You\'re using {usage_data["platforms"]} platforms (limit: {current_config.max_platforms})',
                'recommended_tier': self._get_next_tier(current_tier).value,
                'benefit': 'Support for more social media platforms'
            })
        
        if usage_data.get('daily_posts', 0) >= current_config.max_posts_per_day * 0.8:  # 80% threshold
            suggestions.append({
                'reason': 'High posting volume',
                'description': f'You\'re posting {usage_data["daily_posts"]} times per day',
                'recommended_tier': self._get_next_tier(current_tier).value,
                'benefit': 'Higher posting limits and advanced features'
            })
        
        # Feature-based suggestions
        missing_features = self._get_missing_features(current_tier)
        if missing_features:
            suggestions.append({
                'reason': 'Access to advanced features',
                'description': 'Unlock premium features for better performance',
                'recommended_tier': self._get_next_tier(current_tier).value,
                'benefit': f'Get {", ".join(missing_features[:3])}'
            })
        
        return suggestions
    
    def _get_next_tier(self, current_tier: SubscriptionTier) -> SubscriptionTier:
        """Get the next tier up from current tier"""
        tier_order = [SubscriptionTier.BASE, SubscriptionTier.MID, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]
        
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        
        return SubscriptionTier.PRO  # Default upgrade target
    
    def _get_missing_features(self, current_tier: SubscriptionTier) -> List[str]:
        """Get list of features not available in current tier"""
        current_config = self.tier_configs[current_tier]
        next_tier = self._get_next_tier(current_tier)
        next_config = self.tier_configs[next_tier]
        
        missing_features = []
        
        # Feature mapping for user-friendly names
        feature_names = {
            'image_generation': 'AI Image Generation',
            'a_b_testing': 'A/B Testing',
            'advanced_analytics': 'Advanced Analytics',
            'multi_language': 'Multi-language Support',
            'viral_learning': 'Viral Pattern Learning',
            'custom_integrations': 'Custom Integrations',
            'white_labeling': 'White Labeling',
            'api_access': 'API Access',
            'video_generation': 'AI Video Generation',
            'crm_integration': 'CRM Integration'
        }
        
        for feature, name in feature_names.items():
            if not getattr(current_config, feature) and getattr(next_config, feature):
                missing_features.append(name)
        
        return missing_features
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison of all tiers for pricing page"""
        comparison = {}
        
        for tier in SubscriptionTier:
            config = self.tier_configs[tier]
            comparison[tier.value] = {
                'name': tier.value.title(),
                'limits': {
                    'platforms': config.max_platforms,
                    'posts_per_day': config.max_posts_per_day,
                    'content_storage': config.max_content_storage
                },
                'key_features': self._get_key_features(config),
                'best_for': self._get_tier_description(tier)
            }
        
        return comparison
    
    def _get_key_features(self, config: TierFeatures) -> List[str]:
        """Get key features for tier display"""
        features = []
        
        if config.research_enabled:
            features.append("AI Research & Trend Analysis")
        if config.image_generation:
            features.append("AI Image Generation")
        if config.a_b_testing:
            features.append("A/B Testing")
        if config.advanced_analytics:
            features.append("Advanced Analytics")
        if config.multi_language:
            features.append("Multi-language Support")
        if config.viral_learning:
            features.append("Viral Pattern Learning")
        if config.custom_integrations:
            features.append("Custom Integrations")
        if config.white_labeling:
            features.append("White Labeling")
        if config.video_generation:
            features.append("AI Video Generation")
        
        return features
    
    def _get_tier_description(self, tier: SubscriptionTier) -> str:
        """Get description of who the tier is best for"""
        descriptions = {
            SubscriptionTier.BASE: "Small businesses and personal brands getting started",
            SubscriptionTier.MID: "Growing businesses with regular content needs",
            SubscriptionTier.PRO: "Marketing agencies and established brands",
            SubscriptionTier.ENTERPRISE: "Large organizations with complex requirements"
        }
        return descriptions[tier]

# Global tier manager instance
tier_manager = TierManager()

# Decorator for feature access control
def requires_feature(feature_name: str):
    """Decorator to check feature access based on user tier"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # In a real implementation, you'd get the user's tier from their session/token
            # For now, we'll assume it's passed as a parameter or available in context
            user_tier = kwargs.get('user_tier', SubscriptionTier.BASE)
            
            if not tier_manager.check_feature_access(user_tier, feature_name):
                return {
                    'error': f'Feature {feature_name} not available in your current tier',
                    'required_tier': tier_manager._get_next_tier(user_tier).value,
                    'upgrade_url': f'/upgrade?feature={feature_name}'
                }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator