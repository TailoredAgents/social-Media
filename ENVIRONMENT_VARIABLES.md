# Environment Variables Documentation

**AI Social Media Content Agent - Backend Configuration**  
**Last Updated:** July 25, 2025  
**Version:** 1.0.0

This document provides comprehensive documentation for all environment variables used in the AI Social Media Content Agent backend system.

---

## 📋 Quick Setup Guide

1. Copy `.env.example` to `.env`
2. Fill in your API keys and credentials
3. Configure database connection
4. Set up social media platform credentials
5. Configure authentication (Auth0 or local JWT)

---

## 🔧 Environment Variables Reference

### **🌍 Application Environment**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Application environment (`development`, `staging`, `production`) |
| `DEBUG` | No | `true` | Enable debug mode (affects logging and error handling) |
| `PORT` | No | `8000` | Server port number |
| `HOST` | No | `0.0.0.0` | Server host address |

**Example:**
```bash
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
```

---

### **🤖 AI Services Configuration**

#### **OpenAI API (Required)**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | OpenAI API key for embeddings and content generation |

#### **Search API (Optional)**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERPER_API_KEY` | No | - | Serper API key for web search functionality |

#### **Image Generation API (Optional)**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `XAI_API_KEY` | No | - | xAI API key for Grok-2 image generation |

**Example:**
```bash
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
SERPER_API_KEY=your-serper-api-key-here
XAI_API_KEY=xai-your-xai-api-key-here
```

**Setup Instructions:**

**OpenAI API:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set billing limits and monitor usage
4. Add key to environment variables

**xAI API (for image generation):**
1. Visit [xAI Console](https://console.x.ai/)
2. Create a new API key
3. Monitor usage and billing
4. Add key to environment variables (image generation will be disabled without this)

---

### **🗄️ Database Configuration**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./socialmedia.db` | Primary database URL (SQLite for dev) |
| `POSTGRES_URL` | No | - | PostgreSQL URL for production |

**Development (SQLite):**
```bash
DATABASE_URL=sqlite:///./socialmedia.db
```

**Production (PostgreSQL):**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/socialmedia_db
# OR
POSTGRES_URL=postgresql://username:password@host:port/database
```

**Setup Instructions:**
- **Development:** SQLite is automatically created
- **Production:** Set up PostgreSQL instance and create database
- **Cloud:** Use connection strings from Render, Heroku, or AWS RDS

---

### **🔐 Authentication Configuration**

#### **JWT Token Settings**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | `your-secret-key-change-this` | JWT signing secret (change in production!) |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token expiration time |

#### **Auth0 Configuration (Recommended)**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH0_DOMAIN` | No | - | Auth0 domain (e.g., `your-app.auth0.com`) |
| `AUTH0_CLIENT_ID` | No | - | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | No | - | Auth0 application client secret |
| `AUTH0_AUDIENCE` | No | - | Auth0 API audience identifier |

**Example:**
```bash
SECRET_KEY=your-super-secure-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Auth0 (Optional but recommended)
AUTH0_DOMAIN=your-app.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_AUDIENCE=https://your-api.example.com
```

---

### **📊 Background Tasks & Caching**

#### **Redis Configuration**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `CELERY_BROKER_URL` | No | `redis://localhost:6379/0` | Celery message broker URL |
| `CELERY_RESULT_BACKEND` | No | `redis://localhost:6379/0` | Celery result storage URL |

**Example:**
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis Cloud (Production)
REDIS_URL=redis://username:password@host:port/0
```

---

### **📱 Social Media Platform APIs**

#### **Twitter/X API v2**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TWITTER_API_KEY` | No | - | Twitter API key (consumer key) |
| `TWITTER_API_SECRET` | No | - | Twitter API secret (consumer secret) |
| `TWITTER_ACCESS_TOKEN` | No | - | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | No | - | Twitter access token secret |
| `TWITTER_BEARER_TOKEN` | No | - | Twitter Bearer token (for API v2) |

#### **Facebook API (Additional)**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FACEBOOK_PAGE_TOKEN` | No | - | Facebook page-specific access token |
| `FACEBOOK_USER_TOKEN` | No | - | Facebook user access token |
| `FACEBOOK_WEBHOOK_SECRET` | No | - | Facebook webhook verification secret |

#### **Instagram Business API**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INSTAGRAM_APP_ID` | No | - | Instagram app ID (via Facebook) |
| `INSTAGRAM_APP_SECRET` | No | - | Instagram app secret |
| `INSTAGRAM_ACCESS_TOKEN` | No | - | Instagram access token |
| `INSTAGRAM_BUSINESS_ID` | No | - | Instagram business account ID |

#### **Facebook API**
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FACEBOOK_APP_ID` | No | - | Facebook application ID |
| `FACEBOOK_APP_SECRET` | No | - | Facebook application secret |
| `FACEBOOK_ACCESS_TOKEN` | No | - | Facebook access token |
| `FACEBOOK_PAGE_ID` | No | - | Facebook page ID |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | No | - | Facebook page access token |

**Example:**
```bash
# Twitter
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Additional Facebook Settings
FACEBOOK_PAGE_TOKEN=your_facebook_page_token
FACEBOOK_USER_TOKEN=your_facebook_user_token

# Instagram
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token

# Facebook
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
```

---

### **🔒 Security & CORS Configuration**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated list of allowed hosts |
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Comma-separated CORS origins |

**Example:**
```bash
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost:5173,https://your-frontend.com
```

---

## 🏗️ Environment-Specific Configurations

### **Development Environment**
```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite:///./socialmedia.db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### **Staging Environment**
```bash
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://username:password@staging-db:5432/socialmedia_staging
REDIS_URL=redis://staging-redis:6379/0
CORS_ORIGINS=https://staging-app.example.com
```

### **Production Environment**
```bash
ENVIRONMENT=production  
DEBUG=false
DATABASE_URL=postgresql://username:password@prod-db:5432/socialmedia_prod
REDIS_URL=redis://prod-redis:6379/0
CORS_ORIGINS=https://app.example.com
SECRET_KEY=super-secure-production-secret-key
```

---

## 🚀 Deployment Platform Configurations

### **Render.com**
```bash
# Render automatically sets PORT
PYTHON_VERSION=3.13.0
DATABASE_URL=postgresql://render-postgres-url
REDIS_URL=redis://render-redis-url
```

### **Heroku**
```bash
# Heroku automatically sets PORT and DATABASE_URL
REDIS_URL=redis://heroku-redis-url
```

### **Railway.app**
```bash
# Railway automatically sets PORT
DATABASE_URL=postgresql://railway-postgres-url
REDIS_URL=redis://railway-redis-url
```

### **Docker/Docker Compose**
```bash
DATABASE_URL=postgresql://postgres:password@db:5432/socialmedia
REDIS_URL=redis://redis:6379/0
```

---

## 🧪 Testing Environment Variables

The following variables are automatically set for testing (in `pytest.ini`):

```bash
ENVIRONMENT=testing
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=test_secret_key_123
OPENAI_API_KEY=test_openai_key
AUTH0_DOMAIN=test.auth0.com
AUTH0_CLIENT_ID=test_client_id
REDIS_URL=redis://localhost:6379/1
```

---

## ⚠️ Security Best Practices

### **1. Secret Key Management**
- **Never** commit actual secrets to version control
- Use different `SECRET_KEY` for each environment
- Generate secure random keys: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### **2. API Key Security**
- Rotate API keys regularly
- Set up billing alerts for AI services
- Use environment-specific keys when possible
- Monitor API usage for anomalies

### **3. Database Security**
- Use SSL connections in production
- Implement proper database access controls
- Regular database backups
- Monitor for suspicious queries

### **4. Production Checklist**
- [ ] All example values replaced with real credentials
- [ ] DEBUG set to false
- [ ] Secure SECRET_KEY generated
- [ ] Database SSL enabled
- [ ] CORS origins properly configured
- [ ] All API keys have proper rate limits
- [ ] Environment variables stored securely (not in code)

---

## 🔍 Validation & Troubleshooting

### **Environment Validation Endpoint**
Check configuration status at: `GET /api/health`

### **Common Issues**

1. **OpenAI API Errors**
   - Check API key validity
   - Verify billing account status
   - Monitor rate limits

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check network connectivity
   - Ensure database exists

3. **Redis Connection Problems**
   - Verify Redis server is running
   - Check REDIS_URL format
   - Test network connectivity

4. **Social Media API Issues**
   - Verify API credentials
   - Check application permissions
   - Monitor rate limits

### **Debug Commands**
```bash
# Test database connection
python -c "from backend.db.database import engine; engine.connect()"

# Test Redis connection  
python -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print(r.ping())"

# Validate environment
python -c "from backend.core.config import get_settings; print(get_settings().dict())"
```

---

## 📞 Support & Resources

### **Platform Documentation**
- [OpenAI API Docs](https://platform.openai.com/docs)
- [X/Twitter API v2 Docs](https://developer.x.com/en/docs/twitter-api)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- [Auth0 Documentation](https://auth0.com/docs)

### **Deployment Guides**
- [Render Deployment](https://render.com/docs)
- [Heroku Deployment](https://devcenter.heroku.com/)
- [Railway Deployment](https://docs.railway.app/)

**For additional support, check the project's GitHub issues or contact the development team.**

---

*Last updated: July 25, 2025 | Version 1.0.0*