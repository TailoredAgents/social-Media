# Platform Integration Validation Setup

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists

This guide provides instructions for setting up platform integration validation with real API credentials.

## 🔐 Test Credentials Setup

### Prerequisites

1. Create test/developer accounts on each platform
2. Set up API applications for each platform
3. Obtain necessary API keys and access tokens
4. Configure environment variables

### Platform-Specific Setup

#### 1. Twitter API v2 Setup

```bash
# Required environment variables
export TWITTER_TEST_ACCESS_TOKEN="your_twitter_access_token"
export TWITTER_API_KEY="your_twitter_api_key"
export TWITTER_API_SECRET="your_twitter_api_secret"
export TWITTER_ACCESS_TOKEN="your_twitter_access_token"
export TWITTER_ACCESS_TOKEN_SECRET="your_twitter_access_token_secret"
```

**Steps:**
1. Create Twitter Developer Account: https://developer.twitter.com/
2. Create a new App in the Developer Portal
3. Generate API Keys and Access Tokens
4. Enable Read/Write permissions
5. Note: v2 API requires Essential access level (free)

#### 2. Instagram Basic Display API Setup

```bash
# Required environment variables
export INSTAGRAM_TEST_ACCESS_TOKEN="your_instagram_access_token"
export INSTAGRAM_APP_ID="your_instagram_app_id"
export INSTAGRAM_APP_SECRET="your_instagram_app_secret"
```

**Steps:**
1. Create Facebook Developer Account: https://developers.facebook.com/
2. Create a new App with Instagram Basic Display product
3. Add Instagram test users
4. Generate User Access Tokens for test users
5. Note: Production requires App Review for instagram_content_publish

#### 3.  API Setup

```bash
# Required environment variables
export LINKEDIN_TEST_ACCESS_TOKEN="your__access_token"
export LINKEDIN_CLIENT_ID="your__client_id"
export LINKEDIN_CLIENT_SECRET="your__client_secret"
```

**Steps:**
1. Create  Developer Account: https://developer..com/
2. Create a new App
3. Request access to Marketing Developer Platform
4. Add required products: Share on , Marketing Developer Platform
5. Generate Access Tokens for test  company page

#### 4. Facebook Pages API Setup

```bash
# Required environment variables
export FACEBOOK_TEST_ACCESS_TOKEN="your_facebook_page_access_token"
export FACEBOOK_APP_ID="your_facebook_app_id"
export FACEBOOK_APP_SECRET="your_facebook_app_secret"
```

**Steps:**
1. Use same Facebook Developer Account as Instagram
2. Create a test Facebook Page
3. Generate Page Access Token with pages_manage_posts permission
4. Add Facebook Login and Pages API products to your app

## 🚀 Running the Validation

### Basic Validation

```bash
# Run full platform validation
python -m backend.scripts.validate_platform_integrations
```

### Platform-Specific Validation

```bash
# Validate only Twitter
VALIDATE_PLATFORMS="twitter" python -m backend.scripts.validate_platform_integrations

# Validate multiple specific platforms
VALIDATE_PLATFORMS="twitter,instagram," python -m backend.scripts.validate_platform_integrations
```

### Development Mode (Mock APIs)

```bash
# Run validation with mock APIs (no real API calls)
VALIDATION_MODE="mock" python -m backend.scripts.validate_platform_integrations
```

## 📊 Validation Tests

The validation script performs these tests for each platform:

### 1. Authentication & Profile Tests
- ✅ OAuth token validation
- ✅ User profile retrieval
- ✅ API connectivity check
- ✅ Rate limit compliance

### 2. Content Operations Tests
- ✅ Content posting (with cleanup)
- ✅ Media upload (if supported)
- ✅ Content formatting validation
- ✅ Character/content limits

### 3. Analytics & Metrics Tests
- ✅ Post analytics retrieval
- ✅ Engagement metrics access
- ✅ Performance data validation

### 4. Error Handling Tests
- ✅ Invalid token handling
- ✅ Rate limit error handling
- ✅ Network error resilience
- ✅ API error response parsing

### 5. Performance Tests
- ✅ Response time measurement
- ✅ Throughput validation
- ✅ Timeout handling

## 📋 Expected Results

### Success Criteria

✅ **Twitter Integration**
- Profile fetch: < 500ms
- Content posting: < 1000ms
- Rate limiting enforced correctly
- Error handling working

✅ **Instagram Integration**
- Media upload: < 3000ms
- Content posting: < 2000ms
- Hashtag support working
- Story posting (if configured)

✅ ** Integration**
- Business profile access
- Company page posting
- Professional content formatting
- Analytics access

✅ **Facebook Integration**
- Page management access
- Content posting with media
- Audience targeting (basic)
- Insights access

- Business account access

### Performance Benchmarks

- **API Response Times**: < 1000ms average
- **Media Upload**: < 5000ms for images, < 30000ms for videos
- **Rate Limiting**: Properly enforced and handled
- **Error Recovery**: < 3 retry attempts with exponential backoff

## 🔧 Troubleshooting

### Common Issues

**1. Authentication Failures**
```
Error: "Invalid or expired access token"
Solution: Regenerate access tokens and update environment variables
```

**2. Permission Errors**
```
Error: "Insufficient permissions for this operation"
Solution: Review app permissions and request additional scopes
```

**3. Rate Limiting**
```
Error: "Rate limit exceeded"
Solution: Implement exponential backoff (already handled in clients)
```

**4. Network Timeouts**
```
Error: "Request timeout"
Solution: Check network connectivity and increase timeout values
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL="DEBUG"
python -m backend.scripts.validate_platform_integrations
```

### Manual Testing

```bash
# Test individual platform components
python -c "
import asyncio
from backend.integrations.twitter_client import twitter_client

async def test():
    token = 'your_token_here'
    profile = await twitter_client.get_user_profile(token)
    print(f'Profile: {profile}')

asyncio.run(test())
"
```

## 📈 Monitoring Integration

### Production Monitoring Setup

1. **Health Checks**: Add platform validation to monitoring endpoints
2. **Alerting**: Set up alerts for API failures
3. **Metrics**: Track API response times and success rates
4. **Logging**: Monitor API quota usage and rate limiting

### Automated Validation

```bash
# Add to CI/CD pipeline
- name: Validate Platform Integrations
  run: |
    export TWITTER_TEST_ACCESS_TOKEN=${{ secrets.TWITTER_TEST_TOKEN }}
    export INSTAGRAM_TEST_ACCESS_TOKEN=${{ secrets.INSTAGRAM_TEST_TOKEN }}
    # ... other tokens
    python -m backend.scripts.validate_platform_integrations
```

## 🔒 Security Considerations

1. **Token Storage**: Use secure environment variables
2. **Test Isolation**: Use dedicated test accounts
3. **Rate Limiting**: Respect platform API limits
4. **Cleanup**: Always clean up test content
5. **Monitoring**: Monitor for unusual API activity

## 📞 Support

For platform-specific API issues:

- **Twitter**: https://twittercommunity.com/
- **Instagram**: https://developers.facebook.com/support/
- ****: https://docs.microsoft.com/en-us//
- **Facebook**: https://developers.facebook.com/support/

For integration issues, check the validation logs and performance metrics generated by the validation script.