# Autonomous Scheduling System

## Overview

The autonomous scheduling system provides fully automated daily content generation, posting, and performance monitoring using Celery beat schedules.

## Architecture

### Components

1. **Autonomous Scheduler** (`backend/tasks/autonomous_scheduler.py`)
   - Core logic for autonomous content workflows
   - User configuration management
   - Research and content generation coordination

2. **Celery Beat Configuration** (`backend/tasks/celery_app.py`)
   - Production scheduling with multiple queues
   - Daily, weekly, and periodic task definitions
   - Queue-based task distribution

3. **Database Models** (`backend/db/models.py`)
   - `enable_autonomous_mode` field for user opt-in
   - `timezone` field for scheduling personalization
   - Enhanced `UserSetting` model

## Scheduled Tasks

### 🕕 Daily Tasks

#### `autonomous_daily_content_generation` 
- **Schedule**: Daily at 6 AM UTC
- **Queue**: `autonomous`
- **Function**: Generates and schedules content for users with autonomous mode enabled
- **Process**:
  1. Find users with `enable_autonomous_mode = True`
  2. Execute research for trending topics
  3. Generate platform-specific content
  4. Schedule content based on user's preferred posting times
  5. Create `WorkflowExecution` records for tracking

#### `autonomous_metrics_collection`
- **Schedule**: Daily at 2 AM UTC  
- **Queue**: `metrics`
- **Function**: Collects engagement metrics for published content
- **Process**:
  1. Find content published in the last 24 hours
  2. Simulate metrics collection (views, likes, shares, comments)
  3. Update content records with engagement data
  4. Calculate engagement rates and performance indicators

### 📅 Weekly Tasks

#### `autonomous_weekly_report`
- **Schedule**: Weekly on Sundays at 8 AM UTC
- **Queue**: `reports` 
- **Function**: Generates comprehensive performance reports
- **Process**:
  1. Analyze past week's workflow executions
  2. Calculate success rates and content performance
  3. Generate recommendations for optimization
  4. Store insights in memory system for future reference

### ⏰ Periodic Tasks

#### `autonomous_content_posting`
- **Schedule**: Every 15 minutes
- **Queue**: `posting`
- **Function**: Processes and posts scheduled content
- **Process**:
  1. Find content scheduled for posting (within 1-hour window)
  2. Execute platform-specific posting logic
  3. Mark content as published with external post IDs
  4. Handle posting failures and retries

## User Configuration

### Database Fields

```sql
-- Added to user_settings table
enable_autonomous_mode BOOLEAN DEFAULT FALSE
timezone VARCHAR DEFAULT 'UTC'
```

### User Settings Structure

```python
{
    'user_id': 123,
    'email': 'user@example.com',
    'timezone': 'America/New_York',
    'preferred_platforms': ['twitter', ''],
    'content_frequency': 3,  # posts per week
    'posting_times': {
        'twitter': '09:00',
        '': '10:00'
    },
    'brand_voice': 'professional',
    'creativity_level': 0.7
}
```

## Deployment

### Docker Compose Setup

```yaml
# docker-compose.celery.yml
services:
  celery-worker:
    command: celery -A backend.tasks.celery_app worker --loglevel=info --queues=autonomous,reports,metrics,posting,legacy
    
  celery-beat:
    command: celery -A backend.tasks.celery_app beat --loglevel=info --schedule=/app/celerybeat-schedule
    
  celery-flower:
    command: celery -A backend.tasks.celery_app flower --port=5555
```

### Environment Variables

```bash
# Required for autonomous operation
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host:5432/db
```

## Queue Architecture

### Queue Types

1. **`autonomous`** - Daily content generation tasks
2. **`reports`** - Weekly and monthly reporting
3. **`metrics`** - Performance data collection
4. **`posting`** - Real-time content publishing
5. **`legacy`** - Backward compatibility tasks

### Worker Configuration

```bash
# Production worker command
celery -A backend.tasks.celery_app worker \
  --loglevel=info \
  --queues=autonomous,reports,metrics,posting,legacy \
  --concurrency=4 \
  --max-tasks-per-child=1000
```

## Monitoring

### Celery Flower Dashboard

- **URL**: `http://localhost:5555`
- **Features**:
  - Real-time task monitoring
  - Worker health status
  - Task success/failure rates
  - Queue depth monitoring
  - Task execution history

### Key Metrics

1. **Task Success Rate**: Should be >95%
2. **Queue Depth**: Should remain <100 pending tasks
3. **Worker Health**: All workers should be online
4. **Execution Time**: Tasks should complete within time limits

## Autonomous Workflow

### Daily Cycle (6 AM UTC)

```mermaid
graph TD
    A[Find Autonomous Users] --> B[Execute Research]
    B --> C[Generate Content Ideas]
    C --> D[Create Platform Content]
    D --> E[Schedule Posts]
    E --> F[Update Workflow Status]
    F --> G[Store Research in Memory]
```

### Content Posting (Every 15 minutes)

```mermaid
graph TD
    A[Query Scheduled Content] --> B{Content Ready?}
    B -->|Yes| C[Post to Platform]
    B -->|No| D[Wait for Next Cycle]
    C --> E[Mark as Published]
    E --> F[Store External Post ID]
    F --> G[Update Metrics]
```

## User Opt-in Process

### 1. Enable Autonomous Mode
```python
# Update user settings
user_setting.enable_autonomous_mode = True
user_setting.timezone = 'America/New_York'
user_setting.preferred_platforms = ['twitter', '']
user_setting.posting_times = {
    'twitter': '09:00',
    '': '17:00'
}
```

### 2. Content Frequency Configuration
- `content_frequency`: Posts per week (1-14)
- Platform-specific posting times
- Brand voice and creativity settings

### 3. Monitoring Setup
- Weekly email reports (optional)
- Real-time notifications for failures
- Performance dashboard access

## Error Handling

### Task Failures
- Automatic retry with exponential backoff
- Error logging to Sentry
- Workflow status updates
- User notifications for critical failures

### Content Posting Failures
- Platform-specific error handling
- Retry logic for temporary failures
- Fallback to manual review queue
- Detailed error reporting

## Security Considerations

### User Data Protection
- All content generated is user-scoped
- Platform tokens encrypted at rest
- Audit logs for all autonomous actions
- User control over autonomous features

### API Rate Limiting
- Respect platform rate limits
- Distributed task execution
- Intelligent retry mechanisms
- Load balancing across workers

## Migration Guide

### Database Migration
```bash
# Apply autonomous mode migration
alembic upgrade head
```

### Existing User Migration
```python
# Enable autonomous mode for existing users (optional)
UPDATE user_settings 
SET enable_autonomous_mode = false, 
    timezone = 'UTC' 
WHERE enable_autonomous_mode IS NULL;
```

## Performance Optimization

### Task Distribution
- Queue-specific workers for optimal performance
- Memory-efficient task processing
- Database connection pooling
- Resource cleanup after tasks

### Scaling Considerations
- Horizontal worker scaling
- Redis clustering for high availability
- Database read replicas for metrics collection
- CDN integration for media content

## Troubleshooting

### Common Issues

1. **Tasks Not Executing**
   - Check Celery beat is running
   - Verify Redis connectivity
   - Ensure workers are active

2. **Content Not Posting**
   - Validate platform API credentials
   - Check posting queue depth
   - Review error logs

3. **Memory Issues**
   - Monitor worker memory usage
   - Restart workers regularly
   - Optimize task payload sizes

### Debug Commands

```bash
# Check beat schedule
celery -A backend.tasks.celery_app inspect scheduled

# Monitor active tasks  
celery -A backend.tasks.celery_app inspect active

# View worker stats
celery -A backend.tasks.celery_app inspect stats
```