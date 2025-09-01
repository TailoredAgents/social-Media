# API Integration Guide

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists

Complete guide for integrating with the AI Social Media Content Agent APIs.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Reference](#api-reference)
- [Integration Examples](#integration-examples)
- [SDKs and Libraries](#sdks-and-libraries)
- [Webhooks](#webhooks)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Getting Started

### Base URL

```
Production: https://api.aisocialmediaagent.com
Staging: https://staging-api.aisocialmediaagent.com
Development: http://localhost:8000
```

### API Versioning

The API uses path-based versioning:
```
/api/v1/endpoint
```

Current version: `v1`

### Content Types

All API endpoints accept and return JSON:
```
Content-Type: application/json
Accept: application/json
```

## Authentication

### OAuth 2.0 with Auth0

The API uses OAuth 2.0 authorization code flow via Auth0.

#### 1. Authorization

Redirect users to the authorization endpoint:

```
GET https://your-tenant.auth0.com/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  scope=openid profile email&
  audience=https://api.aisocialmediaagent.com
```

#### 2. Token Exchange

Exchange authorization code for access token:

```bash
curl -X POST https://your-tenant.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "code": "AUTHORIZATION_CODE",
    "redirect_uri": "YOUR_REDIRECT_URI"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "v1.MjAxNjEwMjUtMDAtMDA...",
  "scope": "openid profile email"
}
```

#### 3. API Requests

Include the access token in the Authorization header:

```bash
curl -X GET https://api.aisocialmediaagent.com/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API Key Authentication (Server-to-Server)

For server-to-server integrations, use API keys:

```bash
curl -X GET https://api.aisocialmediaagent.com/api/v1/content \
  -H "X-API-Key: YOUR_API_KEY"
```

## API Reference

### User Management

#### Get Current User
```
GET /api/v1/users/me
```

Response:
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "subscription": {
    "plan": "pro",
    "expires_at": "2024-12-15T10:30:00Z"
  }
}
```

#### Update User Profile
```
PUT /api/v1/users/me
```

Request:
```json
{
  "name": "John Smith",
  "bio": "Content creator and social media manager",
  "timezone": "America/New_York"
}
```

### Content Management

#### List Content
```
GET /api/v1/content?platform=twitter&status=published&limit=20&offset=0
```

Query Parameters:
- `platform`: Filter by social media platform (twitter, instagram, facebook)
- `status`: Filter by status (draft, scheduled, published, failed)
- `limit`: Number of items to return (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)
- `search`: Search in content text
- `date_from`: Filter from date (ISO 8601)
- `date_to`: Filter to date (ISO 8601)

Response:
```json
{
  "items": [
    {
      "id": 456,
      "title": "My awesome post",
      "content": "This is the content of my post...",
      "platform": "twitter",
      "status": "published",
      "scheduled_at": "2024-01-20T15:00:00Z",
      "published_at": "2024-01-20T15:00:00Z",
      "created_at": "2024-01-20T14:30:00Z",
      "updated_at": "2024-01-20T15:00:00Z",
      "analytics": {
        "views": 1250,
        "likes": 45,
        "shares": 12,
        "comments": 8
      }
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

#### Create Content
```
POST /api/v1/content
```

Request:
```json
{
  "title": "New Social Media Post",
  "content": "Check out our latest product update! 🚀",
  "platform": "twitter",
  "scheduled_at": "2024-01-25T10:00:00Z",
  "tags": ["product", "update", "announcement"],
  "media": [
    {
      "type": "image",
      "url": "https://example.com/image.jpg",
      "alt_text": "Product screenshot"
    }
  ]
}
```

Response:
```json
{
  "id": 789,
  "title": "New Social Media Post",
  "content": "Check out our latest product update! 🚀",
  "platform": "twitter",
  "status": "scheduled",
  "scheduled_at": "2024-01-25T10:00:00Z",
  "created_at": "2024-01-20T16:45:00Z",
  "updated_at": "2024-01-20T16:45:00Z"
}
```

#### Update Content
```
PUT /api/v1/content/{content_id}
```

#### Delete Content
```
DELETE /api/v1/content/{content_id}
```

### AI Content Generation

#### Generate Content
```
POST /api/v1/ai/generate
```

Request:
```json
{
  "prompt": "Create a tweet about sustainable technology",
  "platform": "twitter",
  "tone": "professional",
  "hashtags": true,
  "max_length": 280,
  "language": "en"
}
```

Response:
```json
{
  "generated_content": "🌱 Sustainable technology is shaping our future! From solar panels to electric vehicles, innovation is driving us toward a cleaner planet. What sustainable tech are you most excited about? #CleanTech #Sustainability #Innovation #GreenFuture",
  "metadata": {
    "character_count": 234,
    "hashtag_count": 4,
    "estimated_engagement": "high",
    "tone_analysis": "professional, optimistic"
  }
}
```

#### Content Suggestions
```
GET /api/v1/ai/suggestions?topic=technology&platform=instagram
```

### Analytics

#### Get Analytics Summary
```
GET /api/v1/analytics/summary?period=last_30_days
```

Response:
```json
{
  "period": "last_30_days",
  "total_posts": 45,
  "total_views": 12500,
  "total_engagements": 890,
  "engagement_rate": 7.12,
  "by_platform": {
    "twitter": {
      "posts": 20,
      "views": 6800,
      "engagements": 485
    },
    "instagram": {
      "posts": 15,
      "views": 3200,
      "engagements": 245
    },
    "facebook": {
      "posts": 10,
      "views": 2500,
      "engagements": 160
    }
  },
  "top_performing_posts": [
    {
      "id": 123,
      "title": "AI Revolution in Marketing",
      "platform": "instagram",
      "views": 450,
      "engagements": 67
    }
  ]
}
```

#### Detailed Analytics
```
GET /api/v1/analytics/detailed?content_id=123
```

### Social Media Integration

#### List Connected Accounts
```
GET /api/v1/integrations/accounts
```

Response:
```json
{
  "accounts": [
    {
      "id": "twitter_123",
      "platform": "twitter",
      "username": "@johndoe",
      "display_name": "John Doe",
      "connected_at": "2024-01-15T10:30:00Z",
      "status": "active",
      "permissions": ["read", "write"],
      "rate_limit": {
        "remaining": 245,
        "reset_at": "2024-01-20T17:00:00Z"
      }
    }
  ]
}
```

#### Connect Social Account
```
POST /api/v1/integrations/connect
```

Request:
```json
{
  "platform": "twitter",
  "oauth_token": "oauth_token_from_platform",
  "oauth_verifier": "oauth_verifier_from_platform"
}
```

### Workflows

#### List Workflows
```
GET /api/v1/workflows
```

#### Create Workflow
```
POST /api/v1/workflows
```

Request:
```json
{
  "name": "Daily Twitter Posts",
  "description": "Automatically post daily content to Twitter",
  "schedule": "0 9 * * *",
  "platforms": ["twitter"],
  "content_rules": {
    "topics": ["technology", "AI", "innovation"],
    "tone": "professional",
    "include_hashtags": true,
    "max_posts_per_day": 3
  },
  "enabled": true
}
```

## Integration Examples

### JavaScript/Node.js

```javascript
class SocialMediaAgentAPI {
  constructor(accessToken, baseURL = 'https://api.aisocialmediaagent.com') {
    this.accessToken = accessToken;
    this.baseURL = baseURL;
  }

  async request(method, endpoint, data = null) {
    const url = `${this.baseURL}/api/v1${endpoint}`;
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      },
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API Error: ${error.message}`);
    }

    return await response.json();
  }

  // Content methods
  async getContent(filters = {}) {
    const params = new URLSearchParams(filters);
    return await this.request('GET', `/content?${params}`);
  }

  async createContent(contentData) {
    return await this.request('POST', '/content', contentData);
  }

  async updateContent(contentId, updates) {
    return await this.request('PUT', `/content/${contentId}`, updates);
  }

  async deleteContent(contentId) {
    return await this.request('DELETE', `/content/${contentId}`);
  }

  // AI generation
  async generateContent(prompt, options = {}) {
    return await this.request('POST', '/ai/generate', {
      prompt,
      ...options
    });
  }

  // Analytics
  async getAnalytics(period = 'last_30_days') {
    return await this.request('GET', `/analytics/summary?period=${period}`);
  }
}

// Usage example
const api = new SocialMediaAgentAPI('your_access_token');

async function createAndSchedulePost() {
  try {
    // Generate content with AI
    const generated = await api.generateContent(
      'Create a post about the benefits of remote work',
      {
        platform: 'instagram',
        tone: 'professional',
        hashtags: true
      }
    );

    // Create scheduled post
    const post = await api.createContent({
      title: 'Remote Work Benefits',
      content: generated.generated_content,
      platform: 'instagram',
      scheduled_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // Tomorrow
    });

    console.log('Post scheduled successfully:', post);
  } catch (error) {
    console.error('Error:', error.message);
  }
}
```

### Python

```python
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SocialMediaAgentAPI:
    def __init__(self, access_token: str, base_url: str = "https://api.aisocialmediaagent.com"):
        self.access_token = access_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}/api/v1{endpoint}"
        
        response = self.session.request(method, url, json=data)
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            raise Exception(f"API Error {response.status_code}: {error_data.get('message', 'Unknown error')}")
        
        return response.json()
    
    # Content methods
    def get_content(self, **filters) -> Dict:
        params = "&".join([f"{k}={v}" for k, v in filters.items()])
        endpoint = f"/content?{params}" if params else "/content"
        return self._request("GET", endpoint)
    
    def create_content(self, content_data: Dict) -> Dict:
        return self._request("POST", "/content", content_data)
    
    def update_content(self, content_id: int, updates: Dict) -> Dict:
        return self._request("PUT", f"/content/{content_id}", updates)
    
    def delete_content(self, content_id: int) -> Dict:
        return self._request("DELETE", f"/content/{content_id}")
    
    # AI methods
    def generate_content(self, prompt: str, **options) -> Dict:
        return self._request("POST", "/ai/generate", {
            "prompt": prompt,
            **options
        })
    
    # Analytics methods
    def get_analytics(self, period: str = "last_30_days") -> Dict:
        return self._request("GET", f"/analytics/summary?period={period}")
    
    def get_detailed_analytics(self, content_id: int) -> Dict:
        return self._request("GET", f"/analytics/detailed?content_id={content_id}")
    
    # Workflow methods
    def create_workflow(self, workflow_data: Dict) -> Dict:
        return self._request("POST", "/workflows", workflow_data)
    
    def get_workflows(self) -> Dict:
        return self._request("GET", "/workflows")

# Usage example
def main():
    api = SocialMediaAgentAPI("your_access_token")
    
    try:
        # Generate content
        generated = api.generate_content(
            "Write a Twitter thread about AI ethics",
            platform="twitter",
            tone="thoughtful",
            hashtags=True
        )
        
        # Create multiple posts for a thread
        posts = []
        thread_content = generated["generated_content"].split("\n\n")
        
        for i, content in enumerate(thread_content):
            post_data = {
                "title": f"AI Ethics Thread {i+1}",
                "content": content,
                "platform": "twitter",
                "scheduled_at": (datetime.now() + timedelta(minutes=i*5)).isoformat()
            }
            
            post = api.create_content(post_data)
            posts.append(post)
        
        print(f"Created {len(posts)} posts for thread")
        
        # Get analytics
        analytics = api.get_analytics("last_7_days")
        print(f"Engagement rate: {analytics['engagement_rate']:.2%}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

### PHP

```php
<?php

class SocialMediaAgentAPI {
    private $accessToken;
    private $baseURL;
    
    public function __construct($accessToken, $baseURL = 'https://api.aisocialmediaagent.com') {
        $this->accessToken = $accessToken;
        $this->baseURL = $baseURL;
    }
    
    private function request($method, $endpoint, $data = null) {
        $url = $this->baseURL . '/api/v1' . $endpoint;
        
        $headers = [
            'Authorization: Bearer ' . $this->accessToken,
            'Content-Type: application/json'
        ];
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_CUSTOMREQUEST => $method
        ]);
        
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode >= 400) {
            $error = json_decode($response, true);
            throw new Exception("API Error {$httpCode}: " . ($error['message'] ?? 'Unknown error'));
        }
        
        return json_decode($response, true);
    }
    
    // Content methods
    public function getContent($filters = []) {
        $params = http_build_query($filters);
        $endpoint = '/content' . ($params ? '?' . $params : '');
        return $this->request('GET', $endpoint);
    }
    
    public function createContent($contentData) {
        return $this->request('POST', '/content', $contentData);
    }
    
    // AI methods
    public function generateContent($prompt, $options = []) {
        return $this->request('POST', '/ai/generate', array_merge([
            'prompt' => $prompt
        ], $options));
    }
}

// Usage example
try {
    $api = new SocialMediaAgentAPI('your_access_token');
    
    // Generate and create content
    $generated = $api->generateContent(
        'Create a Facebook post about healthy eating',
        [
            'platform' => 'facebook',
            'tone' => 'friendly',
            'hashtags' => true
        ]
    );
    
    $post = $api->createContent([
        'title' => 'Healthy Eating Tips',
        'content' => $generated['generated_content'],
        'platform' => 'facebook',
        'scheduled_at' => date('c', strtotime('+2 hours'))
    ]);
    
    echo "Post created with ID: " . $post['id'] . "\n";
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## Webhooks

### Setting Up Webhooks

Configure webhooks to receive real-time notifications about events:

```
POST /api/v1/webhooks
```

Request:
```json
{
  "url": "https://your-app.com/webhooks/social-media-agent",
  "events": [
    "content.published",
    "content.failed",
    "analytics.updated",
    "workflow.completed"
  ],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### Content Published
```json
{
  "event": "content.published",
  "timestamp": "2024-01-20T15:00:00Z",
  "data": {
    "content_id": 123,
    "platform": "twitter",
    "status": "published",
    "published_at": "2024-01-20T15:00:00Z"
  }
}
```

#### Analytics Updated
```json
{
  "event": "analytics.updated",
  "timestamp": "2024-01-20T16:00:00Z",
  "data": {
    "content_id": 123,
    "platform": "twitter",
    "analytics": {
      "views": 150,
      "likes": 12,
      "shares": 3
    }
  }
}
```

### Webhook Verification

Verify webhook authenticity using HMAC signature:

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expectedSignature, 'hex')
  );
}

// Express.js example
app.post('/webhooks/social-media-agent', (req, res) => {
  const signature = req.headers['x-signature'];
  const payload = JSON.stringify(req.body);
  
  if (!verifyWebhook(payload, signature, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Unauthorized');
  }
  
  // Process webhook
  const { event, data } = req.body;
  console.log(`Received ${event}:`, data);
  
  res.status(200).send('OK');
});
```

## Rate Limiting

### Limits

| Plan | Requests per minute | Burst limit |
|------|-------------------|-------------|
| Free | 60 | 100 |
| Pro | 300 | 500 |
| Enterprise | 1000 | 2000 |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1642694400
```

### Handling Rate Limits

```javascript
async function apiRequestWithRetry(apiCall, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await apiCall();
      return response;
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers['retry-after'] || Math.pow(2, attempt);
        console.log(`Rate limited. Retrying after ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Content is required",
    "details": {
      "field": "content",
      "constraint": "required"
    }
  },
  "request_id": "req_1234567890"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

### Error Handling Best Practices

```python
import time
import random

class APIClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.max_retries = 3
        self.base_delay = 1
    
    def request_with_retry(self, method, endpoint, data=None):
        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_request(method, endpoint, data)
                return response
                
            except requests.exceptions.RequestException as e:
                if e.response is None:
                    # Network error - retry with exponential backoff
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                        continue
                    raise
                
                status_code = e.response.status_code
                
                if status_code == 429:
                    # Rate limited - respect Retry-After header
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    if attempt < self.max_retries:
                        time.sleep(retry_after)
                        continue
                
                elif status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                        continue
                
                # Don't retry for client errors (4xx except 429)
                raise
        
        raise Exception(f"Max retries exceeded for {method} {endpoint}")
```

## Best Practices

### 1. Authentication Management

```javascript
class TokenManager {
  constructor(clientId, clientSecret) {
    this.clientId = clientId;
    this.clientSecret = clientSecret;
    this.accessToken = null;
    this.refreshToken = null;
    this.expiresAt = null;
  }

  async getValidToken() {
    if (this.accessToken && this.expiresAt > Date.now()) {
      return this.accessToken;
    }

    if (this.refreshToken) {
      await this.refreshAccessToken();
      return this.accessToken;
    }

    throw new Error('No valid token available. Please re-authenticate.');
  }

  async refreshAccessToken() {
    const response = await fetch('https://your-tenant.auth0.com/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_type: 'refresh_token',
        client_id: this.clientId,
        client_secret: this.clientSecret,
        refresh_token: this.refreshToken
      })
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    this.expiresAt = Date.now() + (data.expires_in * 1000);
    
    if (data.refresh_token) {
      this.refreshToken = data.refresh_token;
    }
  }
}
```

### 2. Request Optimization

- **Batch requests** when possible
- **Use pagination** for large datasets
- **Cache responses** where appropriate
- **Implement request deduplication**

### 3. Error Recovery

```python
class RobustAPIClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.retry_config = {
            'max_attempts': 3,
            'backoff_factor': 2,
            'jitter': True
        }
    
    async def make_request(self, method, endpoint, data=None):
        if self.circuit_breaker.is_open():
            raise Exception("Circuit breaker is open")
        
        try:
            response = await self._execute_request(method, endpoint, data)
            self.circuit_breaker.record_success()
            return response
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
    
    async def _execute_request(self, method, endpoint, data):
        for attempt in range(self.retry_config['max_attempts']):
            try:
                # Make actual request
                return await self._http_request(method, endpoint, data)
                
            except (NetworkError, ServerError) as e:
                if attempt == self.retry_config['max_attempts'] - 1:
                    raise
                
                # Calculate backoff delay
                delay = self.retry_config['backoff_factor'] ** attempt
                if self.retry_config['jitter']:
                    delay += random.uniform(0, 1)
                
                await asyncio.sleep(delay)
```

### 4. Data Validation

Always validate data before sending to the API:

```javascript
const contentSchema = {
  title: { required: true, maxLength: 200 },
  content: { required: true, maxLength: 10000 },
  platform: { required: true, enum: ['twitter', 'instagram', 'facebook'] },
  scheduled_at: { type: 'datetime', future: true }
};

function validateContent(data) {
  const errors = [];
  
  for (const [field, rules] of Object.entries(contentSchema)) {
    const value = data[field];
    
    if (rules.required && !value) {
      errors.push(`${field} is required`);
      continue;
    }
    
    if (value && rules.maxLength && value.length > rules.maxLength) {
      errors.push(`${field} exceeds maximum length of ${rules.maxLength}`);
    }
    
    if (value && rules.enum && !rules.enum.includes(value)) {
      errors.push(`${field} must be one of: ${rules.enum.join(', ')}`);
    }
  }
  
  return errors;
}
```

### 5. Monitoring and Logging

```python
import logging
import time
from functools import wraps

def log_api_calls(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logging.info(f"API call successful: {func.__name__} took {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"API call failed: {func.__name__} took {duration:.2f}s, error: {e}")
            raise
    
    return wrapper

class APIMetrics:
    def __init__(self):
        self.call_count = 0
        self.error_count = 0
        self.total_duration = 0
    
    def record_call(self, duration, success=True):
        self.call_count += 1
        self.total_duration += duration
        if not success:
            self.error_count += 1
    
    @property
    def average_duration(self):
        return self.total_duration / self.call_count if self.call_count > 0 else 0
    
    @property
    def error_rate(self):
        return self.error_count / self.call_count if self.call_count > 0 else 0
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, AsyncMock
from api_client import SocialMediaAgentAPI

class TestSocialMediaAgentAPI:
    @pytest.fixture
    def api_client(self):
        return SocialMediaAgentAPI("test_token")
    
    @pytest.fixture
    def mock_session(self, api_client):
        mock = Mock()
        api_client.session = mock
        return mock
    
    def test_create_content_success(self, api_client, mock_session):
        # Arrange
        content_data = {
            "title": "Test Post",
            "content": "This is a test",
            "platform": "twitter"
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": 123, **content_data}
        mock_session.request.return_value = mock_response
        
        # Act
        result = api_client.create_content(content_data)
        
        # Assert
        assert result["id"] == 123
        assert result["title"] == "Test Post"
        mock_session.request.assert_called_once_with(
            "POST", 
            "https://api.aisocialmediaagent.com/api/v1/content",
            json=content_data
        )
    
    def test_api_error_handling(self, api_client, mock_session):
        # Arrange
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Validation error"}
        mock_session.request.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            api_client.create_content({"invalid": "data"})
        
        assert "API Error 400" in str(exc_info.value)
```

### Integration Testing

```python
@pytest.mark.integration
class TestAPIIntegration:
    def setup_method(self):
        self.api = SocialMediaAgentAPI(
            access_token=os.getenv("TEST_ACCESS_TOKEN"),
            base_url=os.getenv("TEST_API_URL", "http://localhost:8000")
        )
    
    async def test_full_content_workflow(self):
        # Create content
        content_data = {
            "title": "Integration Test Post",
            "content": "This is an integration test",
            "platform": "twitter"
        }
        
        created_content = await self.api.create_content(content_data)
        assert created_content["id"] is not None
        
        # Update content
        updates = {"title": "Updated Test Post"}
        updated_content = await self.api.update_content(
            created_content["id"], 
            updates
        )
        assert updated_content["title"] == "Updated Test Post"
        
        # Get content
        retrieved_content = await self.api.get_content(
            id=created_content["id"]
        )
        assert retrieved_content["title"] == "Updated Test Post"
        
        # Delete content
        await self.api.delete_content(created_content["id"])
        
        # Verify deletion
        with pytest.raises(Exception) as exc_info:
            await self.api.get_content(id=created_content["id"])
        assert "404" in str(exc_info.value)
```

---

This API Integration Guide provides comprehensive examples and best practices for integrating with the AI Social Media Content Agent. For additional support, please refer to our [Support Documentation](../README.md#support) or contact our developer support team.