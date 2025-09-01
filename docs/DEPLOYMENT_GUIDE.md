# Deployment Guide - AI Social Media Content Agent

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists

This comprehensive guide covers deployment strategies, configurations, and best practices for the AI Social Media Content Agent in production environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Traditional Server Deployment](#traditional-server-deployment)
- [Cloud Platform Deployments](#cloud-platform-deployments)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Security Hardening](#security-hardening)
- [Monitoring and Observability](#monitoring-and-observability)
- [Backup and Recovery](#backup-and-recovery)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores, 2.4 GHz
- RAM: 4GB
- Storage: 20GB SSD
- Network: 1 Gbps

**Recommended Requirements:**
- CPU: 4 cores, 3.0 GHz
- RAM: 8GB
- Storage: 50GB SSD
- Network: 1 Gbps

### Software Dependencies

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+
- **Node.js**: 20.x+
- **PostgreSQL**: 15+
- **Redis**: 7+

### External Services

- **Auth0 Account**: For authentication
- **OpenAI API Key**: For AI content generation
- **Social Media API Keys**: X/Twitter, Instagram, Facebook
- **Domain Name**: For production deployment
- **SSL Certificate**: For HTTPS

## Deployment Options

### 1. Docker Deployment (Recommended)

Best for: Development, testing, and small-scale production

**Pros:**
- Easy setup and deployment
- Consistent environment
- Built-in orchestration with Docker Compose
- Simplified scaling

**Cons:**
- Single-host limitation
- Manual scaling

### 2. Kubernetes Deployment

Best for: Large-scale production, high availability

**Pros:**
- Auto-scaling capabilities
- High availability
- Rolling deployments
- Advanced orchestration

**Cons:**
- Complex setup
- Requires Kubernetes expertise

### 3. Traditional Server Deployment

Best for: Custom environments, legacy infrastructure

**Pros:**
- Full control over environment
- No containerization overhead
- Direct system access

**Cons:**
- Manual dependency management
- Environment inconsistency
- Complex scaling

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/ai-social-media-agent.git
cd ai-social-media-agent

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Production Docker Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/backend/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_social_media
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A backend.tasks.celery_app worker --loglevel=info
    environment:
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/backend/logs
    restart: unless-stopped

  beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A backend.tasks.celery_app beat --loglevel=info
    environment:
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/backend/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS Configuration
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }
}
```

## Kubernetes Deployment

### Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-social-media
  labels:
    name: ai-social-media
```

### PostgreSQL Deployment

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: ai-social-media
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "ai_social_media"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: ai-social-media
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Application Deployment

```yaml
# app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-social-media-app
  namespace: ai-social-media
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-social-media-app
  template:
    metadata:
      labels:
        app: ai-social-media-app
    spec:
      containers:
      - name: app
        image: your-registry/ai-social-media-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: app-service
  namespace: ai-social-media
spec:
  selector:
    app: ai-social-media-app
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-social-media-ingress
  namespace: ai-social-media
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: ai-social-media-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 8000
```

## Cloud Platform Deployments

### AWS Deployment

#### Using AWS ECS

1. **Create Task Definition**
2. **Setup ECS Cluster**
3. **Configure Load Balancer**
4. **Setup RDS for PostgreSQL**
5. **Configure ElastiCache for Redis**

#### Using AWS EKS

1. **Create EKS Cluster**
2. **Deploy using kubectl**
3. **Setup AWS Load Balancer Controller**
4. **Configure AWS RDS and ElastiCache**

### Google Cloud Platform

#### Using Google Cloud Run

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ai-social-media-app
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/execution-environment: gen2
    spec:
      containers:
      - image: gcr.io/your-project/ai-social-media-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Azure Deployment

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name ai-social-media --location eastus

# Create container instance
az container create \
  --resource-group ai-social-media \
  --name ai-social-media-app \
  --image your-registry/ai-social-media-agent:latest \
  --ports 8000 \
  --dns-name-label ai-social-media-unique \
  --environment-variables \
    ENVIRONMENT=production \
    DEBUG=false
```

## Database Setup

### PostgreSQL Configuration

#### Production Settings

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Database Initialization

```bash
# Create database and user
psql -U postgres -c "CREATE DATABASE ai_social_media;"
psql -U postgres -c "CREATE USER ai_app WITH PASSWORD 'secure_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ai_social_media TO ai_app;"

# Run migrations
alembic upgrade head

# Create indexes for performance
psql -U ai_app -d ai_social_media -f scripts/performance_indexes.sql
```

### Redis Configuration

#### Production Redis Settings

```conf
# redis-prod.conf
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300
daemonize yes
supervised no
pidfile "/var/run/redis/redis-server.pid"
loglevel notice
logfile "/var/log/redis/redis-server.log"
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename "dump.rdb"
dir "/var/lib/redis"
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

## Environment Configuration

### Production Environment Variables

```bash
# Core Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-at-least-32-chars
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_social_media
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password

# Security
HTTPS_REDIRECT=true
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true

# Performance
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
TIMEOUT=30
KEEPALIVE=2

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

## Security Hardening

### SSL/TLS Configuration

1. **Obtain SSL Certificate**
   ```bash
   # Using Let's Encrypt
   certbot certonly --webroot -w /var/www/html -d yourdomain.com
   ```

2. **Configure Strong SSL Settings**
   - Use TLS 1.2+ only
   - Strong cipher suites
   - HSTS headers
   - OCSP stapling

### Firewall Configuration

```bash
# UFW (Ubuntu)
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw deny 6379/tcp  # Redis (internal only)
ufw enable

# iptables rules
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 127.0.0.1 -j ACCEPT
iptables -P INPUT DROP
```

### Application Security

1. **Environment Variable Security**
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys regularly
   - Limit access permissions

2. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular security updates
   - Backup encryption

3. **API Security**
   - Rate limiting
   - Input validation
   - Output sanitization
   - Authentication and authorization

## Monitoring and Observability

### Application Monitoring

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-social-media-app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

#### Grafana Dashboards

Key metrics to monitor:
- Request rate and response time
- Error rate and types
- Database connection pool status
- Redis memory usage
- CPU and memory utilization
- Social media API rate limits

### Log Management

#### Structured Logging Configuration

```python
# logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "default": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/app.log",
            "maxBytes": 10485760,
            "backupCount": 5,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default", "file"],
    },
}
```

## Performance Optimization

### Application Performance

1. **Database Optimization**
   ```sql
   -- Add performance indexes
   CREATE INDEX CONCURRENTLY idx_content_created_at ON content (created_at DESC);
   CREATE INDEX CONCURRENTLY idx_users_email ON users (email);
   CREATE INDEX CONCURRENTLY idx_posts_platform_status ON posts (platform, status);
   ```

2. **Caching Strategy**
   ```python
   # Redis caching configuration
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://localhost:6379/1',
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

3. **Connection Pooling**
   ```python
   # Database connection pooling
   DATABASE_POOL_SIZE = 20
   DATABASE_MAX_OVERFLOW = 30
   DATABASE_POOL_TIMEOUT = 30
   DATABASE_POOL_RECYCLE = 3600
   ```

### Infrastructure Performance

1. **Load Balancing**
   - Use nginx or HAProxy
   - Configure health checks
   - Session affinity if needed

2. **CDN Configuration**
   - Static asset caching
   - Global distribution
   - Compression

3. **Auto-scaling**
   ```yaml
   # Kubernetes HPA
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: ai-social-media-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: ai-social-media-app
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="ai_social_media"

# Create backup
pg_dump -h localhost -U ai_app -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://your-backup-bucket/database/
```

### Application Backup

```bash
#!/bin/bash
# app_backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /app/data /app/logs

# Backup configuration
cp /app/.env $BACKUP_DIR/env_backup_$DATE

# Clean old backups
find $BACKUP_DIR -name "app_data_*.tar.gz" -mtime +7 -delete
```

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop application
   docker-compose stop app worker beat
   
   # Restore database
   gunzip -c /backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U ai_app -d ai_social_media
   
   # Start application
   docker-compose start app worker beat
   ```

2. **Full System Recovery**
   ```bash
   # Restore from backup
   tar -xzf /backups/app_data_YYYYMMDD_HHMMSS.tar.gz -C /
   
   # Restore environment
   cp /backups/env_backup_YYYYMMDD_HHMMSS /app/.env
   
   # Restart services
   docker-compose restart
   ```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats
free -h
ps aux --sort=-%mem | head

# Solutions:
# - Increase memory limits
# - Optimize database queries
# - Implement pagination
# - Add memory monitoring
```

#### Database Connection Issues
```bash
# Check database status
pg_ctl status
docker-compose logs postgres

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Solutions:
# - Increase connection pool size
# - Check network connectivity
# - Verify credentials
# - Monitor slow queries
```

#### Performance Issues
```bash
# Check application metrics
curl localhost:8000/metrics

# Database performance
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# Solutions:
# - Add database indexes
# - Implement caching
# - Optimize queries
# - Scale horizontally
```

### Health Checks

```bash
# Application health
curl -f http://localhost:8000/health

# Database health
pg_isready -h localhost -p 5432

# Redis health
redis-cli ping

# Full system check
make health-check
```

### Log Analysis

```bash
# Application logs
docker-compose logs -f app

# Error logs
grep ERROR /app/logs/app.log | tail -50

# Performance logs
grep "slow query" /app/logs/app.log

# Access logs
tail -f /var/log/nginx/access.log
```

## Maintenance

### Regular Maintenance Tasks

1. **Daily**
   - Monitor system health
   - Check error logs
   - Verify backup completion

2. **Weekly**
   - Update security patches
   - Clean log files
   - Performance review

3. **Monthly**
   - Security audit
   - Dependency updates
   - Capacity planning

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL certificates valid
- [ ] Monitoring configured
- [ ] Backups tested
- [ ] Security settings verified
- [ ] Performance benchmarks met
- [ ] Health checks passing
- [ ] Documentation updated

---

For additional support or questions about deployment, please refer to our [Support Documentation](SUPPORT.md) or contact the development team.