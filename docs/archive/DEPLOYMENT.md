# AI Social Media Content Agent - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AI Social Media Content Agent to production using Docker containers.

## Architecture

The production deployment consists of:
- **Backend API**: FastAPI application with authentication and content management
- **PostgreSQL**: Primary database for user data and content
- **Redis**: Caching and session storage
- **Celery**: Background task processing (worker + beat scheduler)
- **Nginx**: Reverse proxy and load balancer
- **Optional**: Prometheus + Grafana for monitoring

## Prerequisites

### System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 4GB RAM, 20GB storage
- SSL certificate for HTTPS (recommended)

### Required API Keys
1. **OpenAI API Key**: For AI content generation
2. **Auth0 Configuration**: For user authentication
3. **Social Media APIs**:
   - Twitter API v2 credentials
   -  API credentials
   - Instagram Basic Display API
   - Facebook Graph API

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AI\ social\ media\ content\ agent
```

### 2. Environment Configuration

```bash
# Copy production environment template
cp .env.production .env

# Edit with your actual values
nano .env
```

**Critical Environment Variables:**
```bash
# Security (REQUIRED)
JWT_SECRET_KEY=your_very_secure_jwt_secret_key_at_least_32_characters
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password

# Auth0 (REQUIRED)
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret

# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-your_openai_api_key

# Social Media APIs (Configure as needed)
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
# ... other social media credentials
```

### 3. Deploy

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec app python -c "from backend.db.init_db import init_db; init_db()"

# Verify database setup
docker-compose exec postgres psql -U aisocial -d aisocial_db -c "\\dt"
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx directory
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/private.key

# Update nginx configuration for HTTPS
# (See nginx/nginx.conf example below)
```

## Production Configuration

### Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/private.key;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://backend/api/health;
        }
    }
}
```

### Database Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U aisocial aisocial_db > "$BACKUP_DIR/backup_$DATE.sql"
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

## Monitoring Setup

### Enable Monitoring Stack

```bash
# Start with monitoring services
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3001
# Login: admin / [GRAFANA_PASSWORD from .env]

# Access Prometheus
open http://localhost:9090
```

### Custom Metrics

The application exports metrics at `/metrics` endpoint:
- Request duration and count
- Database query performance  
- Background task status
- Memory and CPU usage

## Security Considerations

### Network Security
- All services run in isolated Docker network
- Only necessary ports exposed to host
- Rate limiting enabled on API endpoints
- Input sanitization and validation

### Data Security
- Passwords hashed with bcrypt
- JWT tokens for stateless authentication
- SQL injection prevention with parameterized queries
- CSRF protection enabled

### Updates and Patches
```bash
# Update application
git pull origin main
docker-compose build app
docker-compose up -d app

# Update system packages
docker-compose pull
docker-compose up -d
```

## Scaling

### Horizontal Scaling

```bash
# Scale API servers
docker-compose up -d --scale app=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=4
```

### Load Balancer Configuration

Update nginx upstream block:
```nginx
upstream backend {
    server app_1:8000;
    server app_2:8000;
    server app_3:8000;
}
```

## Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait for healthy status, then run migrations
```

**Celery Tasks Not Running:**
```bash
# Check worker status
docker-compose exec celery-worker celery -A backend.tasks.celery_app inspect active

# Restart workers
docker-compose restart celery-worker celery-beat
```

**Memory Issues:**
```bash
# Monitor resource usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Logs and Debugging

```bash
# Application logs
docker-compose logs -f app

# Database logs  
docker-compose logs -f postgres

# All services
docker-compose logs -f

# Enter container for debugging
docker-compose exec app bash
```

## Performance Tuning

### Database Optimization
```sql
-- Create indexes for better query performance
-- (Already included in migrations)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_content_user_id ON content(user_id);
```

### Application Tuning
```yaml
# docker-compose.yml optimizations
services:
  app:
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

## Maintenance

### Regular Tasks
1. **Daily**: Check logs and system health
2. **Weekly**: Review security updates
3. **Monthly**: Database maintenance and cleanup
4. **Quarterly**: Security audit and dependency updates

### Health Monitoring
```bash
# Setup health check alerts
curl -X POST "your-monitoring-webhook" \
  -d '{"text": "AI Social Media Agent health check failed"}'
```

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Ensure all required API keys are configured
4. Check network connectivity and firewall settings

**Production Checklist:**
- [ ] All environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations completed
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security hardening applied
- [ ] Performance testing completed