# Social Media Integration API Documentation

**Integration Specialist Component - Complete API Documentation and Setup Guide**

## Overview

This document provides comprehensive documentation for all social media platform integrations, API endpoints, setup instructions, and usage examples for the AI Social Media Content Agent.

## Supported Platforms

- **Twitter/X** - API v2 with full posting and analytics capabilities
- **** - Professional content publishing with company page support  
- **Instagram** - Visual content posting with insights collection
- **Facebook** - Post creation and page management capabilities

---

## Twitter/X Integration

### Setup Instructions

1. **Create Twitter Developer Account**
   ```bash
   # Visit https://developer.twitter.com/
   # Apply for developer access
   # Create a new app in the developer portal
   ```

2. **Configure Environment Variables**
   ```bash
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   ```

3. **OAuth 2.0 Setup**
   ```python
   from backend.auth.social_oauth import oauth_manager
   
   # Configure OAuth
   oauth_manager.setup_twitter_oauth(
       client_id="your_client_id",
       client_secret="your_client_secret",
       redirect_uri="https://your-app.com/callback/twitter"
   )
   ```

### API Endpoints

#### POST /api/integrations/twitter/post
Create a new tweet.

**Request Body:**
```json
{
  "text": "Your tweet content #hashtag",
  "media_ids": ["optional_media_id"],
  "reply_to_tweet_id": "optional_tweet_id",
  "poll_options": ["Option 1", "Option 2"],
  "poll_duration_minutes": 1440
}
```

**Response:**
```json
{
  "success": true,
  "tweet_id": "1234567890",
  "url": "https://twitter.com/user/status/1234567890",
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### POST /api/integrations/twitter/thread
Create a Twitter thread.

**Request Body:**
```json
{
  "tweets": [
    "First tweet in thread",
    "Second tweet in thread",
    "Final tweet in thread"
  ],
  "media_per_tweet": [
    ["media_id_1"],
    [],
    ["media_id_2", "media_id_3"]
  ]
}
```

#### GET /api/integrations/twitter/analytics/{tweet_id}
Get analytics for a specific tweet.

**Response:**
```json
{
  "tweet_id": "1234567890",
  "impressions": 1500,
  "retweets": 25,
  "likes": 150,
  "replies": 8,
  "engagement_rate": 12.2,
  "url_clicks": 45,
  "profile_clicks": 12
}
```

#### POST /api/integrations/twitter/upload-media
Upload media for tweets.

**Request:** Multipart form data with media file

**Response:**
```json
{
  "media_id": "media_123",
  "size": 1024000,
  "media_type": "image/jpeg"
}
```

### Usage Examples

#### Basic Tweet
```python
from backend.integrations.twitter_client import twitter_client

# Post a simple tweet
tweet = await twitter_client.post_tweet(
    access_token="user_token",
    text="Hello from AI Social Media Agent! 🤖 #AI #SocialMedia"
)

print(f"Tweet posted: {tweet.id}")
```

#### Tweet with Media
```python
# Upload media first
media_id = await twitter_client.upload_media(
    access_token="user_token",
    media_data=image_bytes,
    media_type="image/jpeg",
    alt_text="AI generated social media post"
)

# Post tweet with media
tweet = await twitter_client.post_tweet(
    access_token="user_token",
    text="Check out this AI-generated content!",
    media_ids=[media_id]
)
```

#### Create Thread
```python
# Create a thread
thread = await twitter_client.post_thread(
    access_token="user_token",
    tweets=[
        "🧵 Thread about AI in social media (1/3)",
        "AI is revolutionizing how we create and manage social media content... (2/3)",
        "The future of social media is AI-powered automation! (3/3)"
    ]
)

print(f"Thread created with {thread.total_tweets} tweets")
```

---

##  Integration

### Setup Instructions

1. **Create  App**
   ```bash
   # Visit https://www..com/developers/
   # Create a new app
   # Request necessary permissions: w_member_social, r_liteprofile, r_emailaddress
   ```

2. **Configure Environment Variables**
   ```bash
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_REDIRECT_URI=https://your-app.com/callback/
   ```

3. **OAuth 2.0 Setup**
   ```python
   oauth_manager.setup__oauth(
       client_id="your_client_id",
       client_secret="your_client_secret",
       redirect_uri="https://your-app.com/callback/"
   )
   ```

### API Endpoints

#### POST /api/integrations//post
Create a  post.

**Request Body:**
```json
{
  "text": "Professional update from AI Social Media Agent",
  "visibility": "PUBLIC",
  "media_assets": ["optional_media_urn"],
  "article_url": "https://example.com/article",
  "author_type": "person"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "urn:li:share:123456",
  "visibility": "PUBLIC",
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### POST /api/integrations//article
Create a  article.

**Request Body:**
```json
{
  "title": "The Future of AI in Social Media",
  "content": "<h1>Article content in HTML format</h1><p>Full article text...</p>",
  "visibility": "PUBLIC",
  "tags": ["AI", "SocialMedia", "Technology"]
}
```

#### GET /api/integrations//analytics/{post_id}
Get analytics for a  post.

**Response:**
```json
{
  "post_id": "urn:li:share:123456",
  "impressions": 2500,
  "clicks": 180,
  "reactions": 45,
  "comments": 12,
  "shares": 8,
  "engagement_rate": 9.6,
  "click_through_rate": 7.2
}
```

### Usage Examples

#### Professional Post
```python
from backend.integrations._client import _client

# Create professional post
post = await _client.create_post(
    access_token="user_token",
    text="Excited to share our latest AI breakthrough in social media automation! 🚀",
    visibility="PUBLIC"
)

print(f" post created: {post.id}")
```

#### Company Page Post
```python
# Post to company page
company_post = await _client.create_post(
    access_token="page_token",
    text="Company update: New AI features now available",
    visibility="PUBLIC",
    author_type="organization",
    author_id="company_page_id"
)
```

---

## Instagram Integration

### Setup Instructions

1. **Facebook App Setup**
   ```bash
   # Visit https://developers.facebook.com/
   # Create a Facebook app
   # Add Instagram Basic Display product
   # Configure Instagram Business Account
   ```

2. **Configure Environment Variables**
   ```bash
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   INSTAGRAM_CLIENT_ID=your_instagram_client_id
   INSTAGRAM_CLIENT_SECRET=your_instagram_client_secret
   ```

3. **Business Account Requirements**
   - Instagram Business Account
   - Connected Facebook Page
   - Proper permissions and verification

### API Endpoints

#### POST /api/integrations/instagram/post
Create an Instagram post.

**Request Body:**
```json
{
  "caption": "Amazing AI-generated content! #AI #Instagram #SocialMedia",
  "media_urls": ["https://example.com/image.jpg"],
  "media_type": "IMAGE",
  "location_id": "optional_location_id",
  "user_tags": [
    {
      "user_id": "instagram_user_id",
      "x": 0.5,
      "y": 0.3
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "instagram_post_id": "17841234567890123",
  "permalink": "https://www.instagram.com/p/ABC123/",
  "media_type": "IMAGE"
}
```

#### POST /api/integrations/instagram/reel
Create an Instagram Reel.

**Request Body:**
```json
{
  "caption": "Check out this AI-powered reel! #Reels #AI",
  "video_url": "https://example.com/video.mp4",
  "cover_url": "https://example.com/cover.jpg",
  "location_id": "optional_location_id"
}
```

#### GET /api/integrations/instagram/insights/{media_id}
Get insights for Instagram media.

**Response:**
```json
{
  "media_id": "17841234567890123",
  "impressions": 3500,
  "reach": 2800,
  "engagement": 280,
  "saves": 45,
  "shares": 12,
  "likes": 220,
  "comments": 18,
  "profile_visits": 25
}
```

### Usage Examples

#### Single Image Post
```python
from backend.integrations.instagram_client import instagram_client

# Post single image
media = await instagram_client.post_image(
    access_token="page_token",
    ig_user_id="instagram_business_id",
    image_url="https://example.com/ai-generated-image.jpg",
    caption="AI-generated artwork! #AI #Art #Creative"
)

print(f"Instagram post created: {media.permalink}")
```

#### Carousel Post
```python
# Create carousel post
carousel = await instagram_client.post_carousel(
    access_token="page_token",
    ig_user_id="instagram_business_id",
    media_items=[
        {"type": "image", "url": "https://example.com/image1.jpg"},
        {"type": "image", "url": "https://example.com/image2.jpg"},
        {"type": "video", "url": "https://example.com/video.mp4"}
    ],
    caption="AI content carousel! Swipe to see more → #AI #Carousel"
)
```

---

## Facebook Integration

### Setup Instructions

1. **Facebook App Configuration**
   ```bash
   # Create Facebook App at https://developers.facebook.com/
   # Add required products: Facebook Login, Pages API
   # Configure app permissions and domains
   ```

2. **Environment Variables**
   ```bash
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   FACEBOOK_REDIRECT_URI=https://your-app.com/callback/facebook
   ```

3. **Page Management Setup**
   - Facebook Page required for posting
   - Page access tokens needed
   - Proper page roles and permissions

### API Endpoints

#### POST /api/integrations/facebook/post
Create a Facebook post.

**Request Body:**
```json
{
  "message": "Exciting AI developments in social media! 🚀",
  "link": "https://example.com/article",
  "media_urls": ["https://example.com/image.jpg"],
  "scheduled_publish_time": "2025-01-01T18:00:00Z",
  "targeting": {
    "age_min": 18,
    "age_max": 65,
    "interests": ["Technology", "AI"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "facebook_post_id": "123456789_987654321",
  "post_url": "https://www.facebook.com/page/posts/123456789_987654321",
  "scheduled": false
}
```

#### POST /api/integrations/facebook/event
Create a Facebook event.

**Request Body:**
```json
{
  "name": "AI in Social Media Workshop",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-01T16:00:00Z",
  "description": "Learn about AI-powered social media automation",
  "location": "Virtual Event",
  "is_online": true,
  "cover_photo_url": "https://example.com/event-cover.jpg"
}
```

#### GET /api/integrations/facebook/insights/{post_id}
Get Facebook post insights.

**Response:**
```json
{
  "post_id": "123456789_987654321",
  "impressions": 4500,
  "reach": 3200,
  "engagement": 350,
  "reactions": 180,
  "comments": 45,
  "shares": 28,
  "clicks": 97,
  "video_views": 0
}
```

### Usage Examples

#### Text Post
```python
from backend.integrations.facebook_client import facebook_client

# Create text post
post = await facebook_client.create_text_post(
    page_access_token="page_token",
    page_id="facebook_page_id",
    message="AI is transforming social media management! 🤖 #AI #SocialMedia"
)

print(f"Facebook post created: {post.id}")
```

#### Photo Post
```python
# Create photo post
photo_post = await facebook_client.create_photo_post(
    page_access_token="page_token",
    page_id="facebook_page_id",
    photo_url="https://example.com/ai-image.jpg",
    caption="AI-generated visual content for social media!"
)
```

---

## Performance Optimization

### Caching
All integrations use intelligent caching to reduce API calls and improve performance.

```python
from backend.integrations.performance_optimizer import performance_optimizer

# Get performance statistics
stats = performance_optimizer.get_comprehensive_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']}%")
```

### Rate Limiting
Automatic rate limiting prevents API quota exhaustion.

```python
# Check rate limit status
rate_stats = performance_optimizer.rate_limiter.get_stats()
for platform, stats in rate_stats.items():
    print(f"{platform}: {stats['utilization']}% of rate limit used")
```

### Connection Pooling
HTTP connection pooling optimizes network performance.

```python
# Get connection pool stats
conn_stats = performance_optimizer.connection_pool.get_stats()
print(f"Active connection pools: {conn_stats['active_pools']}")
```

---

## Error Handling

### Automatic Retry Logic
All integrations include sophisticated error handling with automatic retry.

```python
from backend.integrations.integration_error_handler import integration_error_handler

# Get error summary
error_summary = integration_error_handler.get_error_summary(
    platform="twitter",
    hours=24
)

print(f"Error rate: {error_summary['total_errors']} errors in 24h")
print(f"Recovery rate: {error_summary['recovery_rate']}%")
```

### Circuit Breaker Pattern
Circuit breakers prevent cascade failures.

```python
# Check circuit breaker status
health = integration_error_handler.get_health_status()
for platform, status in health["circuit_breakers"].items():
    print(f"{platform} circuit breaker: {status['state']}")
```

---

## Workflow Orchestration

### Automated Workflows
The platform supports automated content workflows.

```python
from backend.services.workflow_orchestration import workflow_orchestrator

# Execute daily content workflow
execution = await workflow_orchestrator.execute_workflow(
    db=db_session,
    workflow_id="daily_content"
)

print(f"Workflow status: {execution.status}")
print(f"Steps completed: {len(execution.steps)}")
```

### Available Workflows
- **daily_content** - Automated daily content generation
- **trending_response** - Rapid response to trending topics
- **goal_driven** - Content aligned with business goals

---

## Testing

### Integration Tests
Comprehensive test suite for all platforms.

```bash
# Run integration tests
pytest backend/tests/integration/test_live_platform_integration.py -v

# Run with live API credentials (optional)
pytest backend/tests/integration/test_live_platform_integration.py -m integration -v
```

### Mock Testing
All integrations support mock testing for development.

```python
from unittest.mock import patch
from backend.integrations.twitter_client import twitter_client

# Mock Twitter API response
with patch.object(twitter_client, '_make_request') as mock_request:
    mock_request.return_value = {"id": "123", "text": "test"}
    
    tweet = await twitter_client.post_tweet(
        access_token="mock_token",
        text="Test tweet"
    )
    
    assert tweet.id == "123"
```

---

## Security Considerations

### Token Management
- Store tokens securely using encryption
- Implement token refresh mechanisms
- Use environment variables for sensitive data
- Regular token rotation

### API Security
- HTTPS only for all communications
- Request signing where supported
- Rate limiting and abuse prevention
- Input validation and sanitization

### Data Privacy
- GDPR compliance for user data
- Secure data storage and transmission
- User consent management
- Data retention policies

---

## Monitoring and Analytics

### Performance Metrics
Monitor integration performance with built-in metrics.

```python
# Get comprehensive performance stats
perf_stats = performance_optimizer.get_comprehensive_stats()

metrics = {
    "cache_hit_rate": perf_stats["cache"]["hit_rate"],
    "average_response_time": perf_stats["performance"]["average_response_time"],
    "total_requests": perf_stats["performance"]["requests_total"],
    "error_rate": perf_stats["performance"]["requests_rate_limited"]
}
```

### Health Checks
Regular health checks ensure system reliability.

```python
# Perform health check
health_status = await performance_optimizer.health_check()

if health_status["overall"] != "healthy":
    # Alert administrators
    send_alert(f"Integration health degraded: {health_status}")
```

---

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API credentials
   - Check token expiration
   - Confirm app permissions

2. **Rate Limiting**
   - Monitor API usage
   - Implement proper delays
   - Use caching effectively

3. **Content Validation**
   - Check content length limits
   - Validate media formats
   - Ensure proper encoding

### Debug Logging
Enable debug logging for troubleshooting.

```python
import logging

# Enable debug logging
logging.getLogger("backend.integrations").setLevel(logging.DEBUG)
```

### Support Resources
- Platform developer documentation
- Community forums and support
- Integration error logs and monitoring
- Performance analytics and optimization guides

---

## API Reference Summary

| Platform | Base URL | API Version | Rate Limits |
|----------|----------|-------------|-------------|
| Twitter | https://api.twitter.com/2 | v2 | 300 req/15min |
|  | https://api..com/v2 | v2 | 100 req/hour |
| Instagram | https://graph.facebook.com/v18.0 | v18.0 | 25 posts/hour |
| Facebook | https://graph.facebook.com/v18.0 | v18.0 | 600 req/10min |

---

## Integration Checklist

### Pre-deployment
- [ ] API credentials configured
- [ ] OAuth flows tested
- [ ] Rate limits configured
- [ ] Error handling implemented
- [ ] Caching optimized
- [ ] Security measures in place

### Post-deployment
- [ ] Performance monitoring active
- [ ] Error tracking enabled
- [ ] Health checks running
- [ ] Analytics collection working
- [ ] User feedback collection
- [ ] Regular maintenance scheduled

---

## TikTok Integration

### Setup Instructions

1. **TikTok for Developers Account**
   ```bash
   # Visit https://developers.tiktok.com/
   # Apply for developer access
   # Create a new app with required permissions
   # Get approval for production usage
   ```

2. **Configure Environment Variables**
   ```bash
   TIKTOK_CLIENT_ID=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   TIKTOK_REDIRECT_URI=https://your-app.com/callback/tiktok
   ```

3. **OAuth 2.0 Setup**
   ```python
   oauth_manager.setup_tiktok_oauth(
       client_id="your_client_id",
       client_secret="your_client_secret",
       redirect_uri="https://your-app.com/callback/tiktok",
       scopes=["user.info.basic", "video.publish", "video.list"]
   )
   ```

### API Endpoints

#### POST /api/integrations/tiktok/video
Upload a video to TikTok.

**Request Body:**
```json
{
  "video_url": "https://example.com/awesome_video.mp4",
  "description": "Amazing AI-generated content! 🤖 #AI #TikTok #Automation #ContentCreation",
  "privacy_level": "PUBLIC_TO_EVERYONE",
  "disable_duet": false,
  "disable_stitch": false,
  "disable_comment": false,
  "brand_content_toggle": true,
  "auto_add_music": true
}
```

**Response:**
```json
{
  "success": true,
  "publish_id": "v09044g40000123456789012345",
  "content_id": 12347,
  "platform": "tiktok",
  "estimated_processing_time": "5-10 minutes"
}
```

#### GET /api/integrations/tiktok/user/info
Get TikTok user profile information.

**Response:**
```json
{
  "user_info": {
    "open_id": "user_12345",
    "display_name": "AI Content Creator",
    "avatar_url": "https://example.com/avatar.jpg",
    "follower_count": 15000,
    "following_count": 500,
    "likes_count": 125000,
    "video_count": 85,
    "is_verified": false,
    "bio_description": "Creating amazing AI-powered content daily!"
  }
}
```

#### GET /api/integrations/tiktok/videos
Get user's TikTok videos with pagination.

**Query Parameters:**
- `max_count` (integer): Maximum videos to return (1-100, default: 20)
- `cursor` (string): Pagination cursor for next page

**Response:**
```json
{
  "videos": [
    {
      "id": "v09044g40000123456789012345",
      "title": "AI Content Creation Magic",
      "description": "Watch how AI creates amazing content!",
      "duration": 30,
      "cover_image_url": "https://example.com/cover.jpg",
      "share_url": "https://www.tiktok.com/@user/video/123",
      "create_time": "2025-07-25T10:30:00Z",
      "likes_count": 1500,
      "view_count": 25000,
      "share_count": 250,
      "comment_count": 180
    }
  ],
  "cursor": "cursor_for_next_page",
  "has_more": true,
  "total": 85
}
```

#### GET /api/integrations/tiktok/analytics/{video_id}
Get comprehensive analytics for a TikTok video.

**Response:**
```json
{
  "analytics": {
    "video_id": "v09044g40000123456789012345",
    "view_count": 25000,
    "like_count": 1500,
    "comment_count": 180,
    "share_count": 250,
    "profile_view": 450,
    "reach": 22000,
    "play_time_sum": 450000,
    "average_watch_time": 18.0,
    "completion_rate": 0.65,
    "engagement_rate": 8.4,
    "traffic_sources": {
      "for_you_page": 75,
      "following_feed": 15,
      "search": 5,
      "profile": 3,
      "others": 2
    },
    "audience_demographics": {
      "gender": {"male": 45, "female": 55},
      "age": {"18-24": 40, "25-34": 35, "35-44": 25},
      "top_territories": ["US", "GB", "CA", "AU"]
    },
    "date_range_begin": "2025-07-18T00:00:00Z",
    "date_range_end": "2025-07-25T00:00:00Z"
  }
}
```

#### GET /api/integrations/tiktok/hashtags/trending
Get trending TikTok hashtags for content optimization.

**Query Parameters:**
- `keywords` (array): Search keywords (1-10 items)
- `period` (integer): Analysis period in days (1-120, default: 7)
- `region_code` (string): Country code (default: US)

**Response:**
```json
{
  "hashtags": [
    {
      "hashtag_id": "hashtag_12345",
      "hashtag_name": "aiautomation",
      "view_count": 1500000,
      "publish_count": 25000,
      "is_commerce": false,
      "description": "AI automation and technology content",
      "trend_score": 85.5,
      "growth_rate": 15.2
    }
  ],
  "period_days": 7,
  "region_code": "US",
  "total": 50
}
```

### Usage Examples

#### Basic Video Upload
```python
from backend.integrations.tiktok_client import tiktok_client

# Upload video to TikTok
video_upload = await tiktok_client.upload_video(
    access_token="user_token",
    video_url="https://example.com/ai-generated-video.mp4",
    description="🤖 AI-generated content is the future! #AI #TikTok #Innovation",
    privacy_level="PUBLIC_TO_EVERYONE"
)

print(f"TikTok video uploaded: {video_upload.publish_id}")
```

#### Get Video Analytics
```python
# Get detailed analytics
analytics = await tiktok_client.get_video_analytics(
    access_token="user_token",
    video_ids=["v09044g40000123456789012345"]
)

print(f"Video engagement rate: {analytics[0].engagement_rate}%")
```

---

## Research Automation Integration

### API Endpoints

#### POST /api/integrations/research/execute
Execute automated research across multiple platforms.

**Request Body:**
```json
{
  "keywords": ["AI", "automation", "social media marketing"],
  "platforms": ["twitter", "instagram", "tiktok", "reddit"],
  "time_range": "24h",
  "location": "US",
  "max_results": 500,
  "include_sentiment": true,
  "include_engagement": true,
  "filters": {
    "min_engagement": 10,
    "verified_accounts_only": false,
    "exclude_keywords": ["spam", "fake"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Research pipeline started",
  "research_id": "research_12345",
  "query": {
    "keywords": ["AI", "automation", "social media marketing"],
    "platforms": ["twitter", "instagram", "tiktok", "reddit"],
    "time_range": "24h",
    "max_results": 500
  },
  "estimated_completion": "2-5 minutes"
}
```

#### GET /api/integrations/research/results
Get research results with comprehensive filtering.

**Query Parameters:**
- `keywords` (array): Filter by keywords
- `limit` (integer): Results limit (1-500, default: 50)
- `platform` (string): Filter by specific platform
- `min_sentiment` (float): Minimum sentiment score filter
- `sort_by` (string): Sort by `created_at`, `engagement`, `sentiment`

**Response:**
```json
{
  "results": [
    {
      "id": 12345,
      "source": "twitter",
      "content": "AI-powered social media automation is revolutionizing digital marketing!",
      "keywords": ["AI", "automation", "social media marketing"],
      "sentiment": 0.85,
      "engagement_metrics": {
        "likes": 150,
        "shares": 25,
        "comments": 18,
        "engagement_rate": 12.8
      },
      "author": {
        "username": "@marketingpro",
        "follower_count": 15000,
        "verified": true
      },
      "metadata": {
        "language": "en",
        "country": "US",
        "platform_url": "https://twitter.com/status/123456789"
      },
      "created_at": "2025-07-25T14:30:00Z"
    }
  ],
  "total": 250,
  "summary": {
    "avg_sentiment": 0.72,
    "total_engagement": 15000,
    "top_keywords": ["AI", "automation", "efficiency", "marketing"],
    "platform_distribution": {
      "twitter": 120,
      "instagram": 80,
      "tiktok": 35,
      "reddit": 15
    }
  }
}
```

---

## Content Generation Integration

### API Endpoints

#### POST /api/integrations/content/generate
Generate AI-optimized content for specific platforms.

**Request Body:**
```json
{
  "topic": "AI-powered social media automation platform for businesses",
  "platform": "twitter",
  "content_type": "post",
  "tone": "professional",
  "target_audience": "business owners and marketing professionals",
  "include_hashtags": true,
  "include_cta": true,
  "brand_voice": {
    "style": "innovative but approachable",
    "key_messages": ["efficiency", "automation", "growth"],
    "avoid_terms": ["cheap", "basic"]
  },
  "constraints": {
    "max_length": 280,
    "include_emojis": true,
    "mention_competitors": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "content": "🚀 Transform your social media strategy with AI-powered automation! Our platform helps businesses scale their online presence effortlessly, generating engaging content that converts. Ready to 10x your social media ROI? #AIAutomation #SocialMediaMarketing #BusinessGrowth",
  "hashtags": ["#AIAutomation", "#SocialMediaMarketing", "#BusinessGrowth"],
  "engagement_prediction": 8.5,
  "content_id": 12348,
  "generation_details": {
    "model": "openai-gpt-5",
    "confidence_score": 0.92,
    "optimization_factors": [
      "platform_best_practices",
      "audience_targeting",
      "trend_analysis",
      "engagement_optimization"
    ]
  },
  "performance_forecast": {
    "estimated_reach": 2500,
    "estimated_engagement": 200,
    "virality_score": 7.2,
    "best_posting_time": "2025-07-26T09:00:00Z"
  }
}
```

---

## Workflow Orchestration Integration

### API Endpoints

#### POST /api/integrations/workflow/trigger
Execute complex automated workflows.

**Request Body:**
```json
{
  "workflow_type": "daily_content",
  "parameters": {
    "platforms": ["twitter", "instagram", ""],
    "content_count": 5,
    "topics": ["AI", "automation", "social media trends"],
    "posting_schedule": {
      "twitter": ["09:00", "14:00", "18:00"],
      "instagram": ["12:00", "17:00"],
      "": ["08:00", "16:00"]
    },
    "engagement_goals": {
      "min_likes_per_post": 50,
      "target_reach": 5000,
      "engagement_rate_target": 3.5
    }
  },
  "schedule_for": "2025-07-26T08:00:00Z"
}
```

**Available Workflow Types:**
- `daily_content`: Generate and publish daily content
- `research_analysis`: Comprehensive market research
- `engagement_optimization`: Optimize posting times and content
- `trend_monitoring`: Monitor and respond to trending topics
- `competitor_analysis`: Analyze competitor strategies
- `audience_growth`: Focused audience growth campaigns

**Response:**
```json
{
  "success": true,
  "message": "Workflow 'daily_content' triggered successfully",
  "workflow_id": "workflow_12345",
  "workflow_type": "daily_content",
  "parameters": {
    "platforms": ["twitter", "instagram", ""],
    "content_count": 5,
    "estimated_duration": "2-3 hours"
  },
  "scheduled_for": "2025-07-26T08:00:00Z"
}
```

#### GET /api/integrations/workflow/status/{workflow_id}
Monitor workflow execution progress.

**Response:**
```json
{
  "status": {
    "workflow_id": "workflow_12345",
    "status": "in_progress",
    "progress": 65,
    "started_at": "2025-07-26T08:00:00Z",
    "estimated_completion": "2025-07-26T09:30:00Z",
    "current_step": "content_generation",
    "completed_steps": [
      "research_analysis",
      "topic_identification",
      "audience_analysis"
    ],
    "remaining_steps": [
      "content_optimization",
      "post_scheduling",
      "performance_tracking"
    ],
    "results": {
      "research_data_points": 150,
      "content_generated": 3,
      "posts_scheduled": 2,
      "engagement_predictions": {
        "twitter": 8.2,
        "instagram": 7.8,
        "": 9.1
      }
    }
  }
}
```

---

## Metrics Collection Integration

### API Endpoints

#### GET /api/integrations/metrics/collection
Monitor metrics collection status across all platforms.

**Response:**
```json
{
  "collection_status": {
    "last_update": "2025-07-25T15:30:00Z",
    "platforms": {
      "twitter": {
        "status": "active",
        "last_collection": "2025-07-25T15:25:00Z",
        "metrics_collected": 250,
        "rate_limit_status": "healthy",
        "next_collection": "2025-07-25T16:00:00Z"
      },
      "instagram": {
        "status": "active", 
        "last_collection": "2025-07-25T15:20:00Z",
        "metrics_collected": 180,
        "rate_limit_status": "healthy"
      },
      "facebook": {
        "status": "rate_limited",
        "last_collection": "2025-07-25T13:30:00Z",
        "metrics_collected": 95,
        "rate_limit_status": "limited_until_16:00"
      },
      "tiktok": {
        "status": "active",
        "last_collection": "2025-07-25T15:15:00Z", 
        "metrics_collected": 320,
        "rate_limit_status": "healthy"
      }
    },
    "total_metrics": 1250,
    "collection_rate": "95.2%",
    "errors_24h": 3,
    "average_collection_time": "2.3s"
  },
  "health_score": 92.5
}
```

---

## Enhanced Error Handling

### Error Response Format
All API endpoints return standardized error responses:

```json
{
  "error": {
    "code": "PLATFORM_AUTH_ERROR",
    "message": "Platform account not connected",
    "details": "User has not completed OAuth flow for this platform",
    "platform": "instagram",
    "timestamp": "2025-07-25T15:30:00Z",
    "request_id": "req_12345",
    "retry_after": 300,
    "documentation_url": "https://docs.aisocialmedia.com/errors/platform-auth"
  }
}
```

### Error Codes Reference

| Code | HTTP Status | Description | Action Required |
|------|-------------|-------------|-----------------|
| `PLATFORM_NOT_CONNECTED` | 401 | Social media account not linked | Complete OAuth flow |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded | Wait and retry |
| `INVALID_MEDIA_URL` | 400 | Media URL is invalid | Provide valid media URL |
| `CONTENT_TOO_LONG` | 400 | Content exceeds platform limits | Shorten content |
| `WORKFLOW_NOT_FOUND` | 404 | Workflow ID not found | Use valid workflow ID |
| `GENERATION_FAILED` | 500 | AI content generation failed | Retry with different parameters |
| `PLATFORM_API_ERROR` | 502 | External platform API error | Check platform status |
| `AUTHENTICATION_EXPIRED` | 401 | Authentication token expired | Refresh authentication |
| `INSUFFICIENT_PERMISSIONS` | 403 | Missing required permissions | Grant required permissions |
| `QUOTA_EXCEEDED` | 429 | Daily/monthly quota exceeded | Wait for quota reset |

---

## Advanced Features

### Webhook Support
Real-time notifications for workflow completion, post publication, and analytics updates.

**Webhook Registration:**
```http
POST /api/webhooks/register
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/integration",
  "events": [
    "workflow.completed",
    "post.published",
    "metrics.collected",
    "error.occurred"
  ],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload Example:**
```json
{
  "event": "workflow.completed",
  "data": {
    "workflow_id": "workflow_12345",
    "status": "completed",
    "results": {
      "content_generated": 5,
      "posts_published": 5,
      "total_reach": 12500,
      "total_engagement": 850
    }
  },
  "timestamp": "2025-07-25T16:00:00Z",
  "signature": "sha256=webhook_signature"
}
```

### Rate Limiting Information
All responses include rate limiting headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1643723400
X-RateLimit-Scope: user
```

### Batch Operations
Process multiple operations efficiently:

```http
POST /api/integrations/batch
Content-Type: application/json

{
  "operations": [
    {
      "type": "instagram_post",
      "data": { "caption": "Post 1", "media_urls": ["url1"] }
    },
    {
      "type": "twitter_post", 
      "data": { "text": "Tweet 1" }
    }
  ]
}
```

---

*Last Updated: July 25, 2025*  
*Integration Specialist: Agent #3*  
*Status: Production Ready with Enhanced Features* ✅  
*API Version: 2.0*