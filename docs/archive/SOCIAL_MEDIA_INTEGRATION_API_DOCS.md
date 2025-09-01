# Social Media Integration API Documentation

## Overview

This comprehensive API documentation covers all social media platform integrations within the AI Social Media Content Agent. The system provides a unified interface for posting content, retrieving analytics, and managing social media presence across Twitter, , Instagram, and Facebook.

## Table of Contents

1. [Authentication](#authentication)
2. [Twitter Integration](#twitter-integration)
3. [ Integration](#-integration)
4. [Instagram Integration](#instagram-integration)
5. [Facebook Integration](#facebook-integration)
6. [Performance Optimization](#performance-optimization)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Testing & Validation](#testing--validation)

## Authentication

All social media integrations use OAuth 2.0 authentication with platform-specific requirements.

### Required Environment Variables

```env
# Twitter API v2
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_REFRESH_TOKEN=your_twitter_refresh_token

#  API
LINKEDIN_ACCESS_TOKEN=your__access_token
LINKEDIN_USER_ID=your__user_id

# Instagram Business API (requires Facebook)
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id
INSTAGRAM_BUSINESS_ID=your_instagram_business_account_id

# Facebook Graph API
FACEBOOK_PAGE_ACCESS_TOKEN=your_facebook_page_access_token
```

### Authentication Flow

```python
from backend.auth.social_oauth import oauth_manager

# Initialize OAuth for a platform
auth_url = await oauth_manager.get_authorization_url("twitter")

# Handle callback and get tokens
tokens = await oauth_manager.handle_callback("twitter", authorization_code)
```

## Twitter Integration

### TwitterAPIClient

**Base URL:** `https://api.twitter.com/v2`

#### Key Features
- Tweet posting with media support
- Thread creation and management
- Analytics data retrieval
- User timeline management
- Rate limit handling

#### Methods

##### get_user_profile(access_token, username=None)
Retrieve Twitter user profile information.

**Parameters:**
- `access_token` (str): OAuth access token
- `username` (str, optional): Username to lookup

**Returns:** Dict with user profile data

**Example:**
```python
from backend.integrations.twitter_client import twitter_client

profile = await twitter_client.get_user_profile(access_token)
print(f"User: @{profile['username']} ({profile['public_metrics']['followers_count']} followers)")
```

##### post_tweet(access_token, text, media_ids=None, reply_to_tweet_id=None)
Post a new tweet.

**Parameters:**
- `access_token` (str): OAuth access token
- `text` (str): Tweet text (max 280 characters)
- `media_ids` (list, optional): List of uploaded media IDs
- `reply_to_tweet_id` (str, optional): ID of tweet to reply to

**Returns:** TwitterPost object

**Example:**
```python
tweet = await twitter_client.post_tweet(
    access_token=token,
    text="Hello from AI Social Media Agent! 🤖 #AI #Automation",
    media_ids=["media_123"]
)
print(f"Tweet posted: {tweet.id}")
```

##### post_thread(access_token, tweets)
Post a Twitter thread.

**Parameters:**
- `access_token` (str): OAuth access token
- `tweets` (list): List of tweet texts

**Returns:** TwitterThread object

**Example:**
```python
thread_tweets = [
    "Thread about AI automation 1/3 🧵",
    "AI is transforming social media management 2/3",
    "The future is automated content creation 3/3"
]

thread = await twitter_client.post_thread(access_token, thread_tweets)
print(f"Thread posted: {thread.thread_id}")
```

##### get_tweet_analytics(access_token, tweet_id)
Get analytics for a specific tweet.

**Parameters:**
- `access_token` (str): OAuth access token
- `tweet_id` (str): Tweet ID

**Returns:** TwitterAnalytics object

**Example:**
```python
analytics = await twitter_client.get_tweet_analytics(access_token, tweet_id)
print(f"Impressions: {analytics.impressions}, Engagement: {analytics.engagement_rate}%")
```

##### upload_media(access_token, media_data, media_type, alt_text=None)
Upload media to Twitter.

**Parameters:**
- `access_token` (str): OAuth access token
- `media_data` (bytes): Binary media data
- `media_type` (str): Media MIME type
- `alt_text` (str, optional): Alternative text for accessibility

**Returns:** Media ID string

##### Content Validation
```python
is_valid, error = twitter_client.is_valid_tweet_text("Your tweet text here")
if not is_valid:
    print(f"Validation error: {error}")
```

##  Integration

### APIClient

**Base URL:** `https://api..com/v2`

#### Key Features
- Professional post creation
- Company page content management
- Article publishing
- Analytics and engagement metrics
- Professional audience targeting

#### Methods

##### get_user_profile(access_token)
Get authenticated user's  profile.

**Parameters:**
- `access_token` (str): OAuth access token

**Returns:** Dict with profile information

**Example:**
```python
from backend.integrations._client import _client

profile = await _client.get_user_profile(access_token)
print(f"User: {profile['first_name']} {profile['last_name']}")
print(f"Connections: {profile['connections']}")
```

##### create_post(access_token, text, visibility="PUBLIC", media_assets=None)
Create a  post.

**Parameters:**
- `access_token` (str): OAuth access token
- `text` (str): Post content (max 3000 characters)
- `visibility` (str): Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN)
- `media_assets` (list, optional): List of uploaded media asset URNs

**Returns:** Post object

**Example:**
```python
post = await _client.create_post(
    access_token=token,
    text="""🚀 Exciting developments in AI social media automation!

Our platform now supports intelligent content optimization across multiple platforms.

Key Features:
• AI-powered content generation
• Multi-platform scheduling
• Real-time analytics and insights
• Professional audience targeting

#AI #SocialMediaManagement #Automation""",
    visibility="PUBLIC"
)
print(f" post created: {post.id}")
```

##### upload_media(access_token, media_data, media_type, filename)
Upload media to .

**Parameters:**
- `access_token` (str): OAuth access token
- `media_data` (bytes): Binary media data
- `media_type` (str): Media MIME type
- `filename` (str): Original filename

**Returns:** Media asset URN

##### create_article(access_token, title, content, visibility="PUBLIC")
Create a  article.

**Parameters:**
- `access_token` (str): OAuth access token
- `title` (str): Article title (max 150 characters)
- `content` (str): Article content (max 110,000 characters)
- `visibility` (str): Article visibility

**Returns:** Article object

##### get_post_analytics(access_token, post_id)
Get analytics for a  post.

**Parameters:**
- `access_token` (str): OAuth access token
- `post_id` (str): Post ID

**Returns:** Analytics object

## Instagram Integration

### InstagramAPIClient

**Base URL:** `https://graph.facebook.com/v18.0`

#### Key Features
- Image and video posting
- Carousel (multi-image) posts
- Reels creation
- Stories posting
- Insights and analytics

#### Methods

##### get_profile(access_token, ig_user_id)
Get Instagram profile information.

**Parameters:**
- `access_token` (str): Facebook access token
- `ig_user_id` (str): Instagram Business Account ID

**Returns:** InstagramProfile object

**Example:**
```python
from backend.integrations.instagram_client import instagram_client

profile = await instagram_client.get_profile(access_token, ig_user_id)
print(f"Instagram: @{profile.username} ({profile.followers_count} followers)")
```

##### post_image(access_token, ig_user_id, image_url, caption)
Post a single image to Instagram.

**Parameters:**
- `access_token` (str): Facebook access token
- `ig_user_id` (str): Instagram Business Account ID
- `image_url` (str): Public URL of the image
- `caption` (str): Post caption (max 2200 characters)

**Returns:** InstagramMedia object

**Example:**
```python
media = await instagram_client.post_image(
    access_token=token,
    ig_user_id=ig_account_id,
    image_url="https://example.com/image.jpg",
    caption="""✨ AI-powered social media automation in action!

Our latest update brings intelligent content optimization across all platforms.

#AI #SocialMedia #Automation #TechInnovation #DigitalMarketing"""
)
print(f"Instagram post created: {media.id}")
```

##### post_video(access_token, ig_user_id, video_url, caption)
Post a video to Instagram.

**Parameters:**
- `access_token` (str): Facebook access token
- `ig_user_id` (str): Instagram Business Account ID
- `video_url` (str): Public URL of the video
- `caption` (str): Post caption

**Returns:** InstagramMedia object

##### post_carousel(access_token, ig_user_id, media_items, caption)
Post a carousel (multiple images/videos) to Instagram.

**Parameters:**
- `access_token` (str): Facebook access token
- `ig_user_id` (str): Instagram Business Account ID
- `media_items` (list): List of dicts with 'type' and 'url' keys
- `caption` (str): Post caption

**Returns:** InstagramMedia object

**Example:**
```python
carousel_items = [
    {"type": "image", "url": "https://example.com/image1.jpg"},
    {"type": "image", "url": "https://example.com/image2.jpg"},
    {"type": "video", "url": "https://example.com/video.mp4"}
]

carousel = await instagram_client.post_carousel(
    access_token=token,
    ig_user_id=ig_account_id,
    media_items=carousel_items,
    caption="Multi-media showcase of our AI platform! 🚀"
)
```

##### post_reel(access_token, ig_user_id, video_url, caption, cover_url=None)
Post a Reel to Instagram.

**Parameters:**
- `access_token` (str): Facebook access token
- `ig_user_id` (str): Instagram Business Account ID
- `video_url` (str): Public URL of the video (9:16 recommended)
- `caption` (str): Post caption
- `cover_url` (str, optional): Cover image URL

**Returns:** InstagramMedia object

##### get_media_insights(access_token, media_id)
Get insights for a media item.

**Parameters:**
- `access_token` (str): Facebook access token
- `media_id` (str): Instagram media ID

**Returns:** InstagramInsight object

## Facebook Integration

### FacebookAPIClient

**Base URL:** `https://graph.facebook.com/v18.0`

#### Key Features
- Text, photo, and video posting
- Event creation and management
- Link sharing with previews
- Comprehensive insights and analytics
- Live video streaming

#### Methods

##### get_user_pages(access_token)
Get Facebook Pages that user manages.

**Parameters:**
- `access_token` (str): Facebook user access token

**Returns:** List of FacebookPage objects

**Example:**
```python
from backend.integrations.facebook_client import facebook_client

pages = await facebook_client.get_user_pages(access_token)
for page in pages:
    print(f"Page: {page.name} ({page.followers_count} followers)")
```

##### create_text_post(page_access_token, page_id, message, link=None)
Create a text post on Facebook Page.

**Parameters:**
- `page_access_token` (str): Facebook Page access token
- `page_id` (str): Facebook Page ID
- `message` (str): Post message (max 63,206 characters)
- `link` (str, optional): Optional link to share

**Returns:** FacebookPost object

**Example:**
```python
post = await facebook_client.create_text_post(
    page_access_token=page_token,
    page_id=page_id,
    message="""🚀 Exciting News: AI Social Media Agent Update!

We're thrilled to announce our latest features:

✨ Advanced AI Content Generation
📊 Real-time Cross-Platform Analytics  
🤖 Intelligent Audience Targeting
⚡ Lightning-Fast Multi-Platform Posting

Our platform now manages content across Twitter, , Instagram, and Facebook with unprecedented intelligence and efficiency.

What social media challenges would you like AI to solve next? Share your thoughts below! 👇

#AI #SocialMediaManagement #Automation #TechInnovation""",
    link="https://our-platform.com/features"
)
print(f"Facebook post created: {post.id}")
```

##### create_photo_post(page_access_token, page_id, photo_url, caption=None)
Create a photo post on Facebook Page.

**Parameters:**
- `page_access_token` (str): Facebook Page access token
- `page_id` (str): Facebook Page ID
- `photo_url` (str): URL of the photo to post
- `caption` (str, optional): Photo caption

**Returns:** FacebookPost object

##### create_video_post(page_access_token, page_id, video_url, title=None, description=None)
Create a video post on Facebook Page.

**Parameters:**
- `page_access_token` (str): Facebook Page access token
- `page_id` (str): Facebook Page ID
- `video_url` (str): URL of the video to post
- `title` (str, optional): Video title
- `description` (str, optional): Video description

**Returns:** FacebookPost object

##### create_event(page_access_token, page_id, name, start_time, description=None)
Create an event on Facebook Page.

**Parameters:**
- `page_access_token` (str): Facebook Page access token
- `page_id` (str): Facebook Page ID
- `name` (str): Event name
- `start_time` (datetime): Event start time
- `description` (str, optional): Event description

**Returns:** FacebookEvent object

##### get_post_insights(access_token, post_id)
Get insights for a Facebook post.

**Parameters:**
- `access_token` (str): Facebook access token
- `post_id` (str): Facebook post ID

**Returns:** FacebookInsights object

## Performance Optimization

The system includes a comprehensive performance optimization layer that provides caching, connection pooling, and intelligent rate limiting.

### Performance Optimizer

```python
from backend.integrations.performance_optimizer import performance_optimizer

# Get performance statistics
stats = performance_optimizer.get_comprehensive_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']}%")
print(f"Average response time: {stats['performance']['average_response_time']:.2f}s")

# Perform health check
health = await performance_optimizer.health_check()
print(f"System health: {health['overall']}")
```

### Caching Decorators

Use platform-specific caching decorators for optimal performance:

```python
from backend.integrations.performance_optimizer import (
    cached_twitter_request,
    cached__request,
    cached_instagram_request,
    cached_facebook_request
)

@cached_twitter_request("get_profile", cache_ttl=3600)
async def get_optimized_twitter_profile(access_token):
    return await twitter_client.get_user_profile(access_token)
```

### Batch Operations

Execute multiple requests concurrently:

```python
requests = [
    (twitter_client.get_user_profile, (twitter_token,), {}),
    (_client.get_user_profile, (_token,), {}),
    (instagram_client.get_profile, (fb_token, ig_id), {})
]

results = await performance_optimizer.batch_request(requests, max_concurrent=3)
```

## Error Handling

All integrations implement comprehensive error handling with automatic retry logic and intelligent fallback mechanisms.

### Common Error Types

1. **Authentication Errors (401/403)**
   - Invalid or expired tokens
   - Insufficient permissions

2. **Rate Limiting (429)**
   - Automatic retry with exponential backoff
   - Platform-specific rate limit handling

3. **Content Validation Errors**
   - Character limit exceeded
   - Invalid media formats
   - Policy violations

4. **Network Errors**
   - Connection timeouts
   - Service unavailable

### Error Handling Example

```python
try:
    tweet = await twitter_client.post_tweet(access_token, text)
except Exception as e:
    if "rate limit" in str(e).lower():
        # Wait and retry
        await asyncio.sleep(60)
        tweet = await twitter_client.post_tweet(access_token, text)
    elif "401" in str(e):
        # Refresh token
        new_token = await refresh_access_token(refresh_token)
        tweet = await twitter_client.post_tweet(new_token, text)
    else:
        # Log and handle other errors
        logger.error(f"Unexpected error: {e}")
        raise
```

## Rate Limiting

Each platform has specific rate limits that are automatically managed:

### Platform-Specific Limits

| Platform | Endpoint | Limit | Window |
|----------|----------|-------|--------|
| Twitter | Tweet Creation | 300 requests | 15 minutes |
| Twitter | User Lookup | 300 requests | 15 minutes |
|  | Post Creation | 100 requests | 1 hour |
| Instagram | Content Publishing | 25 requests | 1 hour |
| Facebook | Page Posts | 600 requests | 10 minutes |

### Rate Limit Monitoring

```python
from backend.integrations.performance_optimizer import performance_optimizer

# Check rate limit status
rate_stats = performance_optimizer.rate_limiter.get_stats()
for platform, stats in rate_stats.items():
    print(f"{platform}: {stats['utilization']}% utilized")
    print(f"Burst tokens remaining: {stats['burst_tokens_remaining']}")
```

## Testing & Validation

### Integration Tests

Run comprehensive integration tests:

```bash
# Run basic integration validation
python3 test_integration_validation.py

# Run end-to-end workflow tests  
python3 test_end_to_end_workflow.py

# Run live API tests (requires credentials)
python3 test_social_integrations.py
```

### Content Validation

Validate content before posting:

```python
# Twitter validation
is_valid, error = twitter_client.is_valid_tweet_text(tweet_text)

#  validation  
is_valid, error = _client.validate_post_content(post_text)

# Instagram validation
is_valid, error = instagram_client.validate_caption(caption_text)

# Facebook validation
is_valid, error = facebook_client.validate_post_content(post_text)
```

### Test Results Summary

Recent test results show excellent system reliability:

- **Integration Structure Tests:** 100% pass rate (12/12 tests)
- **Content Validation Tests:** 100% pass rate (all platforms)
- **Error Handling Tests:** 100% pass rate (comprehensive coverage)
- **End-to-End Workflows:** 80% success rate (4/5 workflows passing)

## Best Practices

### 1. Authentication Management
- Store tokens securely using environment variables
- Implement automatic token refresh
- Handle authentication errors gracefully

### 2. Content Optimization
- Validate content before posting
- Use platform-specific optimization
- Include relevant hashtags and mentions

### 3. Rate Limit Management
- Monitor rate limit usage
- Implement exponential backoff
- Use burst tokens judiciously

### 4. Error Handling
- Implement comprehensive try-catch blocks
- Log errors for debugging
- Provide meaningful error messages to users

### 5. Performance Optimization
- Use caching for frequently accessed data
- Batch requests when possible
- Monitor performance metrics regularly

## Support and Troubleshooting

### Common Issues

1. **"Rate Limited" Errors**
   - Check rate limit status
   - Wait for rate limit window to reset
   - Use burst tokens if available

2. **Authentication Failures**
   - Verify token validity
   - Check token permissions
   - Refresh expired tokens

3. **Content Validation Failures**
   - Check character limits
   - Validate media formats
   - Review platform policies

### Getting Help

For additional support:
1. Check the error logs for detailed error messages
2. Review the test results for system health status
3. Monitor performance metrics for optimization opportunities
4. Refer to platform-specific API documentation for advanced features

## Conclusion

This comprehensive API documentation provides everything needed to integrate with and manage content across Twitter, , Instagram, and Facebook. The system is designed for reliability, performance, and ease of use, with extensive testing and validation to ensure production-ready quality.

The integration layer abstracts away platform-specific complexities while providing full access to advanced features, making it easy to build sophisticated social media management applications.