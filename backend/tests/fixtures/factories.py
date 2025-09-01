"""
Test factories for creating database model instances

These factories use factory_boy pattern to create test data
for database models with realistic and consistent values.
"""
import factory
from datetime import datetime, timezone, timedelta
from factory import fuzzy
from faker import Faker

from backend.db.models import User, ContentItem, Goal, GoalProgress, Memory, Notification

fake = Faker()

class UserFactory(factory.Factory):
    """Factory for creating User instances"""
    class Meta:
        model = User
    
    user_id = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.user_id}@example.com")
    name = factory.Faker('name')
    auth_provider = fuzzy.FuzzyChoice(['auth0', 'local', 'google', 'github'])
    profile_data = factory.LazyFunction(lambda: {
        'picture': fake.image_url(),
        'verified': fake.boolean(),
        'bio': fake.text(max_nb_chars=200),
        'location': fake.city()
    })
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class ContentItemFactory(factory.Factory):
    """Factory for creating ContentItem instances"""
    class Meta:
        model = ContentItem
    
    user_id = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('text', max_nb_chars=280)
    platform = fuzzy.FuzzyChoice(['twitter', 'linkedin', 'instagram', 'facebook'])
    status = fuzzy.FuzzyChoice(['draft', 'scheduled', 'published', 'failed'])
    content_type = fuzzy.FuzzyChoice(['text', 'image', 'video', 'link', 'poll'])
    
    metadata = factory.LazyFunction(lambda: {
        'hashtags': [f"#{fake.word()}" for _ in range(fake.random_int(1, 5))],
        'mentions': [f"@{fake.user_name()}" for _ in range(fake.random_int(0, 3))],
        'target_audience': fake.random_element(['general', 'professional', 'young_adults', 'tech']),
        'tone': fake.random_element(['professional', 'casual', 'humorous', 'informative']),
        'cta': fake.random_element(['visit_website', 'sign_up', 'learn_more', 'contact_us']),
        'image_urls': [fake.image_url() for _ in range(fake.random_int(0, 4))],
        'video_url': fake.url() if fake.boolean() else None
    })
    
    performance_data = factory.LazyFunction(lambda: {
        'likes': fake.random_int(0, 1000),
        'shares': fake.random_int(0, 100),
        'comments': fake.random_int(0, 50),
        'reach': fake.random_int(100, 10000),
        'engagement_rate': round(fake.random.uniform(0.5, 8.0), 2),
        'click_through_rate': round(fake.random.uniform(0.1, 3.0), 2),
        'conversion_rate': round(fake.random.uniform(0.01, 1.0), 2)
    })
    
    ai_analysis = factory.LazyFunction(lambda: {
        'sentiment_score': round(fake.random.uniform(-1.0, 1.0), 2),
        'emotion_scores': {
            'joy': round(fake.random.uniform(0, 1), 2),
            'trust': round(fake.random.uniform(0, 1), 2),
            'fear': round(fake.random.uniform(0, 1), 2),
            'surprise': round(fake.random.uniform(0, 1), 2)
        },
        'topic_classification': fake.random_element(['marketing', 'technology', 'lifestyle', 'business', 'education']),
        'brand_voice_score': round(fake.random.uniform(0.7, 1.0), 2),
        'optimization_suggestions': [fake.sentence() for _ in range(fake.random_int(1, 3))]
    })
    
    scheduled_time = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(days=fake.random_int(1, 30))
    )
    published_at = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class GoalFactory(factory.Factory):
    """Factory for creating Goal instances"""
    class Meta:
        model = Goal
    
    user_id = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('text', max_nb_chars=500)
    target_metric = fuzzy.FuzzyChoice([
        'followers', 'engagement_rate', 'reach', 'website_clicks',
        'leads_generated', 'sales', 'brand_mentions', 'content_shares'
    ])
    target_value = factory.LazyAttribute(
        lambda obj: fake.random_int(100, 10000) if obj.target_metric in ['followers', 'reach'] 
        else fake.random_int(10, 100) if obj.target_metric in ['leads_generated', 'sales']
        else round(fake.random.uniform(3.0, 10.0), 1)
    )
    current_value = factory.LazyAttribute(
        lambda obj: fake.random_int(0, int(obj.target_value * 0.8))
    )
    target_date = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(days=fake.random_int(30, 365))
    )
    category = fuzzy.FuzzyChoice(['growth', 'engagement', 'conversion', 'brand_awareness', 'content'])
    priority = fuzzy.FuzzyChoice(['low', 'medium', 'high', 'critical'])
    status = fuzzy.FuzzyChoice(['active', 'paused', 'completed', 'cancelled'])
    
    metadata = factory.LazyFunction(lambda: {
        'kpis': [fake.word() for _ in range(fake.random_int(2, 5))],
        'milestones': [
            {
                'title': fake.sentence(nb_words=3),
                'target_date': (datetime.now(timezone.utc) + timedelta(days=fake.random_int(7, 180))).isoformat(),
                'completed': fake.boolean()
            } for _ in range(fake.random_int(2, 6))
        ],
        'related_content_types': [fake.random_element(['blog_post', 'video', 'infographic', 'podcast']) for _ in range(fake.random_int(1, 3))],
        'target_platforms': [fake.random_element(['twitter', 'linkedin', 'instagram', 'facebook']) for _ in range(fake.random_int(1, 4))]
    })
    
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class GoalProgressFactory(factory.Factory):
    """Factory for creating GoalProgress instances"""
    class Meta:
        model = GoalProgress
    
    goal_id = factory.SubFactory(GoalFactory)
    progress_value = factory.LazyAttribute(
        lambda obj: fake.random_int(0, 1000)
    )
    progress_percentage = factory.LazyAttribute(
        lambda obj: round(fake.random.uniform(0, 100), 1)
    )
    recorded_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    metadata = factory.LazyFunction(lambda: {
        'source': fake.random_element(['api_sync', 'manual_entry', 'automated_calculation']),
        'platform_breakdown': {
            platform: fake.random_int(0, 200) 
            for platform in fake.random_elements(['twitter', 'linkedin', 'instagram', 'facebook'], length=fake.random_int(1, 4))
        },
        'growth_rate': round(fake.random.uniform(-5.0, 15.0), 2),
        'trend': fake.random_element(['upward', 'downward', 'stable', 'volatile'])
    })

class MemoryFactory(factory.Factory):
    """Factory for creating Memory instances"""
    class Meta:
        model = Memory
    
    user_id = factory.SubFactory(UserFactory)
    content_text = factory.Faker('text', max_nb_chars=1000)
    content_type = fuzzy.FuzzyChoice(['research', 'generated_content', 'trend_analysis', 'optimization_insight'])
    source_url = factory.Faker('url')
    
    metadata = factory.LazyFunction(lambda: {
        'topic': fake.random_element(['social_media_marketing', 'content_strategy', 'ai_automation', 'brand_building']),
        'relevance_score': round(fake.random.uniform(0.5, 1.0), 3),
        'keywords': [fake.word() for _ in range(fake.random_int(3, 8))],
        'entities': [fake.word() for _ in range(fake.random_int(1, 5))],
        'sentiment': fake.random_element(['positive', 'neutral', 'negative']),
        'language': 'en',
        'author': fake.name(),
        'publication_date': fake.date_time_between(start_date='-1y', end_date='now').isoformat()
    })
    
    vector_id = factory.LazyFunction(lambda: f"vec_{fake.uuid4()}")  
    embedding_model = 'text-embedding-3-large'
    similarity_threshold = factory.LazyFunction(lambda: round(fake.random.uniform(0.7, 0.95), 3))
    
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class NotificationFactory(factory.Factory):
    """Factory for creating Notification instances"""
    class Meta:
        model = Notification
    
    user_id = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=6)
    message = factory.Faker('text', max_nb_chars=200)
    notification_type = fuzzy.FuzzyChoice([
        'goal_milestone', 'content_published', 'engagement_spike', 
        'system_alert', 'workflow_complete', 'integration_error'
    ])
    priority = fuzzy.FuzzyChoice(['low', 'medium', 'high', 'urgent'])
    is_read = factory.Faker('boolean')
    
    metadata = factory.LazyFunction(lambda: {
        'action_url': fake.url(),
        'related_entity_id': fake.uuid4(),
        'related_entity_type': fake.random_element(['goal', 'content', 'workflow', 'integration']),
        'platform': fake.random_element(['twitter', 'linkedin', 'instagram', 'facebook']),
        'auto_dismiss': fake.boolean(),
        'requires_action': fake.boolean()
    })
    
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    read_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) if fake.boolean() else None
    )

# Specialized factory methods for common test scenarios

class PublishedContentFactory(ContentItemFactory):
    """Factory for published content with performance data"""
    status = 'published'
    published_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) - timedelta(days=fake.random_int(1, 30))
    )
    performance_data = factory.LazyFunction(lambda: {
        'likes': fake.random_int(50, 1000),
        'shares': fake.random_int(10, 200),
        'comments': fake.random_int(5, 100),
        'reach': fake.random_int(1000, 50000),
        'engagement_rate': round(fake.random.uniform(2.0, 8.0), 2),
        'click_through_rate': round(fake.random.uniform(0.5, 4.0), 2)
    })

class HighPerformingContentFactory(ContentItemFactory):
    """Factory for high-performing content"""
    status = 'published'
    performance_data = factory.LazyFunction(lambda: {
        'likes': fake.random_int(500, 2000),
        'shares': fake.random_int(100, 500),
        'comments': fake.random_int(50, 200),
        'reach': fake.random_int(10000, 100000),
        'engagement_rate': round(fake.random.uniform(5.0, 12.0), 2),
        'click_through_rate': round(fake.random.uniform(2.0, 6.0), 2)
    })

class ActiveGoalFactory(GoalFactory):
    """Factory for active goals with recent progress"""
    status = 'active'
    current_value = factory.LazyAttribute(
        lambda obj: fake.random_int(int(obj.target_value * 0.3), int(obj.target_value * 0.8))
    )

class CompletedGoalFactory(GoalFactory):
    """Factory for completed goals"""
    status = 'completed'
    current_value = factory.LazyAttribute(lambda obj: obj.target_value)

# Batch creation helpers
def create_user_with_content(content_count=5):
    """Create a user with associated content items"""
    user = UserFactory()
    contents = [ContentItemFactory(user_id=user.user_id) for _ in range(content_count)]
    return user, contents

def create_user_with_goals(goal_count=3):
    """Create a user with associated goals"""
    user = UserFactory()
    goals = [GoalFactory(user_id=user.user_id) for _ in range(goal_count)]
    return user, goals

def create_complete_user_profile():
    """Create a user with content, goals, and memories"""
    user = UserFactory()
    contents = [ContentItemFactory(user_id=user.user_id) for _ in range(10)]
    goals = [GoalFactory(user_id=user.user_id) for _ in range(3)]
    memories = [MemoryFactory(user_id=user.user_id) for _ in range(15)]
    notifications = [NotificationFactory(user_id=user.user_id) for _ in range(5)]
    
    return {
        'user': user,
        'contents': contents,
        'goals': goals,
        'memories': memories,
        'notifications': notifications
    }
EOF < /dev/null