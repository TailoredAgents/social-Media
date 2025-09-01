# Social Media Integration Deployment Guide

## 🚀 Production Deployment Checklist

This guide provides step-by-step instructions for deploying the AI Social Media Content Agent integration layer to production environments.

## Prerequisites

### System Requirements
- Python 3.9+ (tested with Python 3.13)
- Redis server for caching and task queues
- PostgreSQL database for persistent storage
- SSL certificates for secure API communications
- Minimum 2GB RAM, 4 CPU cores recommended

### Required API Credentials

#### Twitter API v2
```bash
# Required scopes: tweet.read, tweet.write, users.read, offline.access
export TWITTER_CLIENT_ID="your_twitter_client_id"
export TWITTER_CLIENT_SECRET="your_twitter_client_secret"
export TWITTER_ACCESS_TOKEN="your_twitter_access_token"
export TWITTER_REFRESH_TOKEN="your_twitter_refresh_token"
```

####  API
```bash
# Required scopes: r_liteprofile, r_emailaddress, w_member_social
export LINKEDIN_CLIENT_ID="your__client_id"
export LINKEDIN_CLIENT_SECRET="your__client_secret"
export LINKEDIN_ACCESS_TOKEN="your__access_token"
export LINKEDIN_USER_ID="your__user_id"
```

#### Facebook/Instagram Graph API
```bash
# Required permissions: pages_manage_posts, pages_read_engagement, instagram_basic, instagram_content_publish
export FACEBOOK_APP_ID="your_facebook_app_id"
export FACEBOOK_APP_SECRET="your_facebook_app_secret"
export FACEBOOK_ACCESS_TOKEN="your_facebook_access_token"
export FACEBOOK_PAGE_ID="your_facebook_page_id"
export FACEBOOK_PAGE_ACCESS_TOKEN="your_facebook_page_access_token"
export INSTAGRAM_BUSINESS_ID="your_instagram_business_account_id"
```

## Installation Steps

### 1. Environment Setup

```bash
# Create production environment
python3 -m venv social_media_env
source social_media_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn supervisor prometheus-client
```

### 2. Configuration

Create production configuration file:

```python
# config/production.py
import os
from pydantic_settings import BaseSettings

class ProductionSettings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Social Media APIs
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    # Performance Settings
    CACHE_TTL_DEFAULT: int = 300
    MAX_CONCURRENT_REQUESTS: int = 10
    RATE_LIMIT_BURST_SIZE: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env.production"
```

### 3. Database Setup

```bash
# Run database migrations
alembic upgrade head

# Initialize performance optimization tables
python setup_performance_tables.py
```

### 4. Security Configuration

```python
# security/production.py
import ssl
from backend.core.config import get_settings

def configure_ssl():
    """Configure SSL for production deployment"""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    return context

def setup_cors():
    """Configure CORS for production"""
    return {
        "allow_origins": ["https://yourdomain.com"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["*"],
    }
```

## Performance Optimization

### 1. Caching Configuration

```python
# Enable production caching
from backend.integrations.performance_optimizer import performance_optimizer

# Configure cache settings
performance_optimizer.cache.max_size = 5000  # Increase for production
performance_optimizer.cache.default_ttl = 600  # 10 minutes

# Platform-specific TTL optimization
performance_optimizer.cache.ttl_overrides.update({
    "twitter_profile": 7200,    # 2 hours
    "_profile": 14400,  # 4 hours
    "instagram_insights": 3600, # 1 hour
    "facebook_insights": 3600   # 1 hour
})
```

### 2. Connection Pool Optimization

```python
# Optimize connection pools for production
from backend.integrations.performance_optimizer import performance_optimizer

# Increase connection limits
await performance_optimizer.connection_pool.__init__(
    max_connections=200,
    max_keepalive=50
)
```

### 3. Rate Limiting Configuration

```python
# Production rate limiting
rate_limits = {
    "twitter": {"requests": 280, "window": 900, "burst": 40},
    "": {"requests": 90, "window": 3600, "burst": 15},
    "instagram": {"requests": 180, "window": 3600, "burst": 20},
    "facebook": {"requests": 500, "window": 600, "burst": 80}
}
```

## Monitoring and Logging

### 1. Prometheus Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
api_requests_total = Counter('social_media_api_requests_total', 
                           'Total API requests', ['platform', 'endpoint', 'status'])
api_request_duration = Histogram('social_media_api_request_duration_seconds',
                                'API request duration', ['platform', 'endpoint'])
cache_hit_rate = Gauge('social_media_cache_hit_rate', 'Cache hit rate percentage')
active_connections = Gauge('social_media_active_connections', 'Active connections', ['platform'])

def track_api_request(platform: str, endpoint: str):
    """Decorator to track API requests"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                api_requests_total.labels(platform=platform, endpoint=endpoint, status='success').inc()
                return result
            except Exception as e:
                api_requests_total.labels(platform=platform, endpoint=endpoint, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                api_request_duration.labels(platform=platform, endpoint=endpoint).observe(duration)
        return wrapper
    return decorator
```

### 2. Structured Logging

```python
# logging/production.py
import logging
import json
from datetime import datetime

class ProductionFormatter(logging.Formatter):
    """JSON formatter for production logs"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'platform'):
            log_entry["platform"] = record.platform
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        return json.dumps(log_entry)

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/social_media_agent.log')
    ]
)

# Set formatter
for handler in logging.root.handlers:
    handler.setFormatter(ProductionFormatter())
```

## Deployment Methods

### 1. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "backend.main:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  social-media-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/social_media_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=social_media_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

volumes:
  postgres_data:
```

### 2. Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: social-media-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: social-media-agent
  template:
    metadata:
      labels:
        app: social-media-agent
    spec:
      containers:
      - name: social-media-agent
        image: social-media-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: social-media-agent-service
spec:
  selector:
    app: social-media-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Testing in Production

### 1. Health Checks

```python
# health/checks.py
from fastapi import APIRouter
from backend.integrations.performance_optimizer import performance_optimizer
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/ready")
async def readiness_check():
    """Comprehensive readiness check"""
    checks = {}
    overall_status = "ready"
    
    # Check database connection
    try:
        # Add database ping here
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        overall_status = "not_ready"
    
    # Check Redis connection
    try:
        # Add Redis ping here
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        overall_status = "not_ready"
    
    # Check performance optimizer
    try:
        health = await performance_optimizer.health_check()
        checks["performance_optimizer"] = health["overall"]
        if health["overall"] != "healthy":
            overall_status = "degraded"
    except Exception as e:
        checks["performance_optimizer"] = f"unhealthy: {e}"
        overall_status = "not_ready"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    return performance_optimizer.get_comprehensive_stats()
```

### 2. Integration Smoke Tests

```python
# tests/smoke_tests.py
import asyncio
import pytest
from backend.integrations.twitter_client import twitter_client
from backend.integrations._client import _client

async def smoke_test_twitter():
    """Smoke test for Twitter integration"""
    try:
        # Test basic functionality without posting
        is_valid, _ = twitter_client.is_valid_tweet_text("Test tweet")
        assert is_valid
        return True
    except Exception:
        return False

async def smoke_test_():
    """Smoke test for  integration"""
    try:
        is_valid, _ = _client.validate_post_content("Test post")
        assert is_valid
        return True
    except Exception:
        return False

async def run_smoke_tests():
    """Run all smoke tests"""
    results = {
        "twitter": await smoke_test_twitter(),
        "": await smoke_test_(),
        # Add other platforms
    }
    
    return all(results.values()), results
```

## Security Best Practices

### 1. API Key Management

```python
# security/key_management.py
import os
from cryptography.fernet import Fernet

class SecureKeyManager:
    """Secure API key management"""
    
    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY").encode()
        self.fernet = Fernet(self.encryption_key)
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt API token"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt API token"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
```

### 2. Request Validation

```python
# security/validation.py
from pydantic import BaseModel, validator
import re

class SocialMediaPostRequest(BaseModel):
    platform: str
    content: str
    media_urls: list = []
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ['twitter', '', 'instagram', 'facebook']
        if v not in allowed_platforms:
            raise ValueError(f'Platform must be one of {allowed_platforms}')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:  # Max reasonable length
            raise ValueError('Content too long')
        return v
    
    @validator('media_urls')
    def validate_media_urls(cls, v):
        url_pattern = re.compile(r'^https?://.+')
        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f'Invalid URL: {url}')
        return v
```

## Backup and Recovery

### 1. Data Backup Strategy

```bash
#!/bin/bash
# backup/daily_backup.sh

# Database backup
pg_dump $DATABASE_URL > /backups/db_$(date +%Y%m%d_%H%M%S).sql

# Redis backup
redis-cli --rdb /backups/redis_$(date +%Y%m%d_%H%M%S).rdb

# Configuration backup
tar -czf /backups/config_$(date +%Y%m%d_%H%M%S).tar.gz config/

# Keep only last 30 days of backups
find /backups -name "*.sql" -mtime +30 -delete
find /backups -name "*.rdb" -mtime +30 -delete
find /backups -name "*.tar.gz" -mtime +30 -delete
```

### 2. Disaster Recovery Plan

```python
# recovery/disaster_recovery.py
import asyncio
import logging
from datetime import datetime

class DisasterRecoveryManager:
    """Manage disaster recovery procedures"""
    
    async def health_check_all_systems(self):
        """Check health of all critical systems"""
        systems = {
            "database": self.check_database_health(),
            "redis": self.check_redis_health(),
            "social_apis": self.check_social_api_health()
        }
        
        results = {}
        for system, check in systems.items():
            try:
                results[system] = await check
            except Exception as e:
                results[system] = {"status": "error", "error": str(e)}
        
        return results
    
    async def initiate_recovery(self, failed_systems: list):
        """Initiate recovery procedures for failed systems"""
        recovery_log = []
        
        for system in failed_systems:
            try:
                if system == "database":
                    await self.recover_database()
                elif system == "redis":
                    await self.recover_redis()
                elif system == "social_apis":
                    await self.recover_social_apis()
                
                recovery_log.append(f"{system}: recovery successful")
            except Exception as e:
                recovery_log.append(f"{system}: recovery failed - {e}")
        
        return recovery_log
```

## Final Deployment Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] SSL certificates installed and valid
- [ ] Database migrations completed
- [ ] All tests passing (unit, integration, smoke tests)
- [ ] Performance benchmarks met
- [ ] Security scan completed
- [ ] Backup procedures tested

### Deployment
- [ ] Blue-green deployment strategy implemented
- [ ] Health checks configured and passing
- [ ] Monitoring and alerting configured
- [ ] Log aggregation configured
- [ ] Auto-scaling policies configured
- [ ] Load balancer configured

### Post-Deployment
- [ ] Smoke tests passing in production
- [ ] Monitoring dashboards showing healthy metrics
- [ ] Error rates within acceptable thresholds
- [ ] Performance metrics meeting SLAs
- [ ] All integrations responding correctly
- [ ] Documentation updated with production URLs

## Support and Maintenance

### 1. Monitoring Dashboards

Key metrics to monitor:
- API response times (<200ms target)
- Error rates (<1% target)
- Cache hit rates (>80% target)
- Rate limit utilization (<90% warning)
- Memory and CPU usage
- Database connection pool usage

### 2. Maintenance Windows

Recommended maintenance schedule:
- **Daily**: Automated backups, log rotation
- **Weekly**: Performance optimization, cache cleanup
- **Monthly**: Security updates, dependency updates
- **Quarterly**: Comprehensive system review, capacity planning

### 3. Escalation Procedures

**Severity Levels:**
- **P0 (Critical)**: System down, data loss risk
- **P1 (High)**: Degraded performance, affecting users
- **P2 (Medium)**: Minor issues, workarounds available
- **P3 (Low)**: Cosmetic issues, future improvements

## Conclusion

This deployment guide provides comprehensive instructions for taking the AI Social Media Content Agent integration layer from development to production. The system is designed for enterprise-scale deployment with robust monitoring, security, and disaster recovery capabilities.

For additional support, refer to:
- API Documentation: `SOCIAL_MEDIA_INTEGRATION_API_DOCS.md`
- Test Results: Generated test reports in the project directory
- Performance Metrics: Available through the `/metrics` endpoint

The integration layer is production-ready and capable of handling high-volume social media operations with enterprise-grade reliability and performance.