# Performance Optimization Guide

**Created by:** [Tailored Agents](https://tailoredagents.com) - AI Development Specialists

This guide covers performance optimization strategies, monitoring, and troubleshooting for the AI Social Media Content Agent.

## 📊 Performance Overview

### Performance Targets

| Metric | Target | Monitoring |
|--------|--------|------------|
| API Response Time | < 200ms | 95th percentile |
| Database Query Time | < 50ms | Average |
| Memory Usage | < 1GB | Peak |
| CPU Utilization | < 70% | Average |
| Cache Hit Rate | > 80% | Redis metrics |
| Error Rate | < 1% | Application logs |

### Architecture Performance Profile

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Stack                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  CDN  │  Load Balancer             │
│  - Bundle size: ~2MB  │       │  - Response: <10ms         │
│  - First load: <3s    │       │  - Health checks           │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI)                                     │
│  - Async processing   │  Rate limiting  │  Compression     │
│  - Response: <200ms   │  100 req/min    │  gzip enabled    │
├─────────────────────────────────────────────────────────────┤
│  Background Workers (Celery)                               │
│  - Task queue         │  Content gen    │  Social posting  │
│  - Processing: <30s   │  AI workflows   │  Analytics       │
├─────────────────────────────────────────────────────────────┤
│  Caching Layer (Redis)                                     │
│  - Memory: 256MB      │  TTL: 300s      │  Hit rate: >80%  │
│  - Connections: 100   │  Persistence    │  Clustering      │
├─────────────────────────────────────────────────────────────┤
│  Database (PostgreSQL)                                     │
│  - Connections: 20    │  Query: <50ms   │  Indexes: 15+    │
│  - Pool size: 100     │  VACUUM daily   │  Partitioning    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Backend Performance

### FastAPI Optimization

#### 1. Async Programming
```python
# Optimize database queries with async
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@app.get("/api/content/{content_id}")
async def get_content(
    content_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    # Use async queries for better concurrency
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    return result.scalar_one_or_none()
```

#### 2. Response Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Initialize caching
FastAPICache.init(RedisBackend(), prefix="fastapi-cache")

@app.get("/api/analytics/summary")
@cache(expire=300)  # Cache for 5 minutes
async def get_analytics_summary():
    # Expensive computation cached
    return await compute_analytics_summary()
```

#### 3. Database Connection Pooling
```python
# database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Base number of connections
    max_overflow=30,        # Additional connections allowed
    pool_timeout=30,        # Timeout for getting connection
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Validate connections
    echo=False,             # Disable SQL logging in production
)
```

#### 4. Request Optimization
```python
# middleware.py
import time
from fastapi import Request

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Add performance headers
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response
```

### Database Optimizations

#### 1. Index Strategy
```sql
-- Performance indexes for common queries
CREATE INDEX CONCURRENTLY idx_content_created_at_desc 
ON content (created_at DESC);

CREATE INDEX CONCURRENTLY idx_content_platform_status 
ON content (platform, status) 
WHERE status IN ('published', 'scheduled');

CREATE INDEX CONCURRENTLY idx_users_email_lower 
ON users (LOWER(email));

CREATE INDEX CONCURRENTLY idx_analytics_date_range 
ON analytics (created_at) 
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_content_user_platform_date 
ON content (user_id, platform, created_at DESC);

-- Partial indexes for filtered queries
CREATE INDEX CONCURRENTLY idx_content_active 
ON content (id, created_at) 
WHERE status = 'active';
```

#### 2. Query Optimization
```python
# Use select_related for foreign keys
from sqlalchemy.orm import selectinload, joinedload

# Efficient eager loading
async def get_user_with_content(user_id: int):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.content),
            joinedload(User.preferences)
        )
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# Batch queries instead of N+1
async def get_content_with_analytics(content_ids: List[int]):
    # Single query instead of multiple
    result = await db.execute(
        select(Content, Analytics)
        .join(Analytics, Content.id == Analytics.content_id)
        .where(Content.id.in_(content_ids))
    )
    return result.all()
```

#### 3. Connection Management
```python
# connection_manager.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Use connection pooling monitoring
async def monitor_db_pool():
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }
```

### Caching Strategy

#### 1. Multi-Level Caching
```python
# cache_manager.py
import redis
from functools import wraps
import pickle
from typing import Any, Optional

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(REDIS_URL)
        self.local_cache = {}  # In-memory cache
        
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache keys"""
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        # Try local cache first (fastest)
        if key in self.local_cache:
            return self.local_cache[key]
        
        # Try Redis cache
        try:
            data = await self.redis_client.get(key)
            if data:
                value = pickle.loads(data)
                # Store in local cache for next time
                self.local_cache[key] = value
                return value
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        # Store in both caches
        self.local_cache[key] = value
        try:
            await self.redis_client.setex(
                key, ttl, pickle.dumps(value)
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

# Usage decorator
def cached(prefix: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = cache_manager.cache_key(prefix, *args, **kwargs)
            
            # Try cache first
            result = await cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Application usage
@cached("user_profile", ttl=600)
async def get_user_profile(user_id: int):
    return await fetch_user_profile_from_db(user_id)
```

#### 2. Cache Invalidation
```python
# cache_invalidation.py
class CacheInvalidator:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        
    async def invalidate_user_cache(self, user_id: int):
        """Invalidate all user-related cache entries"""
        patterns = [
            f"user_profile:{user_id}",
            f"user_content:{user_id}:*",
            f"user_analytics:{user_id}:*",
        ]
        
        for pattern in patterns:
            keys = await self.cache.redis_client.keys(pattern)
            if keys:
                await self.cache.redis_client.delete(*keys)
    
    async def invalidate_content_cache(self, content_id: int):
        """Invalidate content-related cache entries"""
        patterns = [
            f"content:{content_id}",
            f"content_analytics:{content_id}",
            "content_list:*",  # Invalidate all content lists
        ]
        
        for pattern in patterns:
            keys = await self.cache.redis_client.keys(pattern)
            if keys:
                await self.cache.redis_client.delete(*keys)
```

### Background Task Optimization

#### 1. Celery Configuration
```python
# celery_config.py
from celery import Celery

# Optimized Celery configuration
celery_app = Celery("social_media_agent")

celery_app.conf.update(
    # Broker settings
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    
    # Performance settings
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Optimization settings
    task_compression='gzip',
    result_compression='gzip',
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle'],
    
    # Task routing
    task_routes={
        'content_generation.*': {'queue': 'content'},
        'social_posting.*': {'queue': 'posting'},
        'analytics.*': {'queue': 'analytics'},
    },
    
    # Result settings
    result_expires=3600,
    task_result_expires=3600,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
)
```

#### 2. Task Optimization
```python
# optimized_tasks.py
from celery import group, chord
from typing import List

@celery_app.task(bind=True, max_retries=3)
async def process_content_batch(self, content_ids: List[int]):
    """Process multiple content items efficiently"""
    try:
        # Batch database queries
        contents = await batch_fetch_content(content_ids)
        
        # Process in parallel using group
        job = group(
            process_single_content.s(content.id)
            for content in contents
        )
        
        result = job.apply_async()
        return result.get()
        
    except Exception as exc:
        # Exponential backoff retry
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task
async def generate_content_analytics(content_ids: List[int]):
    """Generate analytics for multiple content items"""
    # Use chord for map-reduce pattern
    callback = aggregate_analytics.s()
    job = chord(
        (analyze_single_content.s(content_id) 
         for content_id in content_ids),
        callback
    )
    
    return job.apply_async()
```

## 🎨 Frontend Performance

### React Optimization

#### 1. Code Splitting
```jsx
// App.jsx - Route-based code splitting
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Content = lazy(() => import('./pages/Content'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/content" element={<Content />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

#### 2. Component Optimization
```jsx
// OptimizedComponent.jsx
import React, { memo, useMemo, useCallback } from 'react';

const ExpensiveComponent = memo(({ 
  data, 
  onUpdate, 
  filters 
}) => {
  // Memoize expensive calculations
  const processedData = useMemo(() => {
    return data.filter(item => 
      filters.every(filter => filter(item))
    ).sort((a, b) => b.priority - a.priority);
  }, [data, filters]);

  // Memoize callbacks to prevent child re-renders
  const handleUpdate = useCallback((id, changes) => {
    onUpdate(id, changes);
  }, [onUpdate]);

  return (
    <div>
      {processedData.map(item => (
        <ItemComponent
          key={item.id}
          item={item}
          onUpdate={handleUpdate}
        />
      ))}
    </div>
  );
});

// Custom hook for optimized data fetching
function useOptimizedData(endpoint, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    let cancelled = false;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(endpoint);
        const result = await response.json();
        
        if (!cancelled) {
          setData(result);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Fetch error:', error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchData();
    
    return () => {
      cancelled = true;
    };
  }, dependencies);
  
  return { data, loading };
}
```

#### 3. Bundle Optimization
```js
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@emotion/react'],
          charts: ['chart.js', 'react-chartjs-2'],
          
          // Route-based chunks
          dashboard: ['./src/pages/Dashboard'],
          analytics: ['./src/pages/Analytics'],
          content: ['./src/pages/Content'],
        },
      },
    },
    // Optimization settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    cssCodeSplit: true,
    sourcemap: false, // Disable in production
  },
  
  // Development optimizations
  server: {
    hmr: {
      overlay: false,
    },
  },
});
```

### State Management Optimization

#### 1. TanStack Query Configuration
```jsx
// queryClient.js
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Optimize for performance
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (error?.status === 404) return false;
        return failureCount < 3;
      },
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // Background refetch settings
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
      refetchOnMount: 'always',
    },
    mutations: {
      retry: 2,
      retryDelay: 1000,
    },
  },
});

// Prefetch critical data
export const prefetchCriticalData = async () => {
  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: ['user', 'profile'],
      queryFn: fetchUserProfile,
    }),
    queryClient.prefetchQuery({
      queryKey: ['content', 'recent'],
      queryFn: fetchRecentContent,
    }),
  ]);
};
```

#### 2. Optimized Hooks
```jsx
// hooks/useOptimizedContent.js
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';

export function useOptimizedContent(filters = {}) {
  const queryClient = useQueryClient();
  
  // Create stable query key
  const queryKey = useMemo(() => [
    'content',
    'list',
    filters
  ], [filters]);
  
  const {
    data,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey,
    queryFn: ({ queryKey }) => fetchContent(queryKey[2]),
    select: (data) => {
      // Transform data efficiently
      return data?.items?.map(item => ({
        ...item,
        formattedDate: new Date(item.created_at).toLocaleDateString(),
        statusColor: getStatusColor(item.status),
      })) || [];
    },
    // Performance optimizations
    keepPreviousData: true,
    structuralSharing: true,
  });
  
  // Optimistic updates
  const updateContentOptimistically = useCallback((contentId, updates) => {
    queryClient.setQueryData(queryKey, (oldData) => {
      if (!oldData) return oldData;
      
      return {
        ...oldData,
        items: oldData.items.map(item =>
          item.id === contentId ? { ...item, ...updates } : item
        ),
      };
    });
  }, [queryClient, queryKey]);
  
  return {
    content: data,
    isLoading,
    error,
    refetch,
    updateContentOptimistically,
  };
}
```

## 📊 Monitoring and Profiling

### Performance Monitoring

#### 1. Application Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total app requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'app_active_connections',
    'Active database connections'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Decorators for automatic metrics
def track_performance(endpoint_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                REQUEST_COUNT.labels(
                    method='GET', 
                    endpoint=endpoint_name, 
                    status='success'
                ).inc()
                return result
                
            except Exception as e:
                REQUEST_COUNT.labels(
                    method='GET', 
                    endpoint=endpoint_name, 
                    status='error'
                ).inc()
                raise
                
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(
                    method='GET', 
                    endpoint=endpoint_name
                ).observe(duration)
                
        return wrapper
    return decorator

# Usage
@app.get("/api/content")
@track_performance("get_content")
async def get_content():
    return await fetch_content()
```

#### 2. Database Performance Monitoring
```python
# db_monitoring.py
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    
    # Log slow queries
    if total > 0.1:  # 100ms threshold
        logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}")
    
    # Update metrics
    query_type = statement.split()[0].lower()
    DB_QUERY_DURATION.labels(query_type=query_type).observe(total)

# Connection pool monitoring
def monitor_connection_pool():
    pool = engine.pool
    ACTIVE_CONNECTIONS.set(pool.checkedout())
    
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
```

#### 3. Custom Performance Profiler
```python
# profiler.py
import cProfile
import pstats
from functools import wraps
import time
from typing import Dict, List
import threading
from collections import defaultdict

class PerformanceProfiler:
    def __init__(self):
        self.profiles = defaultdict(list)
        self.active_requests = {}
        self.lock = threading.Lock()
    
    def profile_function(self, func_name: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                thread_id = threading.get_ident()
                
                # Start profiling
                profiler = cProfile.Profile()
                profiler.enable()
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable()
                    duration = time.time() - start_time
                    
                    # Store profile data
                    with self.lock:
                        self.profiles[func_name].append({
                            'duration': duration,
                            'timestamp': time.time(),
                            'thread_id': thread_id,
                            'profile': profiler
                        })
                        
                        # Keep only recent profiles
                        if len(self.profiles[func_name]) > 100:
                            self.profiles[func_name] = self.profiles[func_name][-50:]
            
            return wrapper
        return decorator
    
    def get_performance_report(self, func_name: str = None) -> Dict:
        with self.lock:
            if func_name:
                profiles = self.profiles.get(func_name, [])
            else:
                profiles = []
                for func_profiles in self.profiles.values():
                    profiles.extend(func_profiles)
            
            if not profiles:
                return {"error": "No profiles found"}
            
            durations = [p['duration'] for p in profiles]
            
            return {
                "count": len(profiles),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": sorted(durations)[int(len(durations) * 0.95)],
                "recent_profiles": profiles[-10:]
            }

# Global profiler instance
profiler = PerformanceProfiler()

# Usage
@profiler.profile_function("content_generation")
async def generate_content(prompt: str):
    return await ai_service.generate_content(prompt)
```

### Load Testing

#### 1. Locust Load Test
```python
# locustfile.py
from locust import HttpUser, task, between
import random
import json

class SocialMediaUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "testpassword"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/dashboard", headers=self.headers)
    
    @task(2)
    def view_content(self):
        self.client.get("/api/content", headers=self.headers)
    
    @task(1)
    def create_content(self):
        content_data = {
            "title": f"Test Content {random.randint(1, 1000)}",
            "content": "This is test content for load testing",
            "platform": random.choice(["twitter", "", "facebook"])
        }
        
        self.client.post(
            "/api/content",
            headers=self.headers,
            json=content_data
        )
    
    @task(1)
    def view_analytics(self):
        self.client.get("/api/analytics/summary", headers=self.headers)
    
    def view_user_profile(self):
        self.client.get("/api/users/me", headers=self.headers)
```

#### 2. Performance Test Suite
```python
# performance_tests.py
import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics

class PerformanceTestSuite:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    async def run_concurrent_requests(
        self, 
        endpoint: str, 
        num_requests: int = 100,
        concurrency: int = 10
    ) -> Dict:
        """Run concurrent requests and measure performance"""
        
        async def make_request(session: aiohttp.ClientSession) -> float:
            start_time = time.time()
            try:
                async with session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers
                ) as response:
                    await response.text()
                    return time.time() - start_time
            except Exception as e:
                print(f"Request failed: {e}")
                return -1
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(session: aiohttp.ClientSession) -> float:
            async with semaphore:
                return await make_request(session)
        
        # Run tests
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            tasks = [
                bounded_request(session) 
                for _ in range(num_requests)
            ]
            
            response_times = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Filter out failed requests
        valid_times = [t for t in response_times if t > 0]
        
        if not valid_times:
            return {"error": "All requests failed"}
        
        return {
            "endpoint": endpoint,
            "total_requests": num_requests,
            "successful_requests": len(valid_times),
            "failed_requests": num_requests - len(valid_times),
            "total_time": total_time,
            "requests_per_second": len(valid_times) / total_time,
            "avg_response_time": statistics.mean(valid_times),
            "median_response_time": statistics.median(valid_times),
            "p95_response_time": sorted(valid_times)[int(len(valid_times) * 0.95)],
            "min_response_time": min(valid_times),
            "max_response_time": max(valid_times),
        }
    
    async def run_full_performance_suite(self) -> Dict:
        """Run complete performance test suite"""
        
        test_endpoints = [
            "/api/health",
            "/api/users/me",
            "/api/content",
            "/api/analytics/summary",
            "/api/dashboard",
        ]
        
        results = {}
        
        for endpoint in test_endpoints:
            print(f"Testing {endpoint}...")
            results[endpoint] = await self.run_concurrent_requests(
                endpoint, 
                num_requests=50,
                concurrency=10
            )
        
        return results

# Usage
async def main():
    test_suite = PerformanceTestSuite(
        base_url="http://localhost:8000",
        auth_token="your-test-token"
    )
    
    results = await test_suite.run_full_performance_suite()
    
    for endpoint, metrics in results.items():
        print(f"\n{endpoint}:")
        print(f"  RPS: {metrics.get('requests_per_second', 0):.2f}")
        print(f"  Avg Response: {metrics.get('avg_response_time', 0):.3f}s")
        print(f"  P95 Response: {metrics.get('p95_response_time', 0):.3f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Performance Troubleshooting

### Common Performance Issues

#### 1. Database Performance Issues
```sql
-- Identify slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes and bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
    pg_stat_get_live_tuples(tablename::regclass) as live_tuples,
    pg_stat_get_dead_tuples(tablename::regclass) as dead_tuples
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- Check index usage
SELECT 
    indexrelname as index_name,
    relname as table_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

#### 2. Memory Issues
```python
# memory_monitor.py
import psutil
import gc
import tracemalloc
from typing import Dict

class MemoryMonitor:
    def __init__(self):
        tracemalloc.start()
        self.baseline = None
    
    def get_memory_stats(self) -> Dict:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        current, peak = tracemalloc.get_traced_memory()
        
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent(),
            "tracemalloc_current": current / 1024 / 1024,  # MB
            "tracemalloc_peak": peak / 1024 / 1024,  # MB
            "gc_stats": {
                "collections": gc.get_stats(),
                "objects": len(gc.get_objects())
            }
        }
    
    def take_snapshot(self) -> tracemalloc.Snapshot:
        return tracemalloc.take_snapshot()
    
    def compare_snapshots(
        self, 
        snapshot1: tracemalloc.Snapshot, 
        snapshot2: tracemalloc.Snapshot
    ):
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print("Top 10 memory growth:")
        for stat in top_stats[:10]:
            print(stat)
    
    def check_memory_leaks(self):
        if self.baseline is None:
            self.baseline = self.take_snapshot()
            return
        
        current = self.take_snapshot()
        self.compare_snapshots(self.baseline, current)

# Usage in middleware
memory_monitor = MemoryMonitor()

@app.middleware("http")
async def memory_monitoring_middleware(request: Request, call_next):
    # Check memory before request
    memory_before = memory_monitor.get_memory_stats()
    
    response = await call_next(request)
    
    # Check memory after request
    memory_after = memory_monitor.get_memory_stats()
    
    # Log if memory increased significantly
    memory_diff = memory_after["rss"] - memory_before["rss"]
    if memory_diff > 10:  # More than 10MB increase
        logger.warning(f"High memory usage in {request.url}: +{memory_diff:.2f}MB")
    
    return response
```

#### 3. Performance Debugging Tools
```python
# debug_tools.py
import cProfile
import pstats
import io
from functools import wraps
import time
import sys

def profile_slow_functions(threshold: float = 1.0):
    """Decorator to profile functions that take longer than threshold"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Start profiling
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                profiler.disable()
                duration = time.time() - start_time
                
                if duration > threshold:
                    # Generate profile report
                    s = io.StringIO()
                    ps = pstats.Stats(profiler, stream=s)
                    ps.sort_stats('cumulative')
                    ps.print_stats(20)  # Top 20 functions
                    
                    logger.warning(
                        f"Slow function {func.__name__} took {duration:.2f}s:\n{s.getvalue()}"
                    )
        
        return wrapper
    return decorator

def monitor_function_calls():
    """Monitor all function calls for debugging"""
    def trace_calls(frame, event, arg):
        if event == 'call':
            filename = frame.f_code.co_filename
            if 'backend' in filename:  # Only monitor our code
                func_name = frame.f_code.co_name
                print(f"Calling: {filename}:{func_name} at line {frame.f_lineno}")
        return trace_calls
    
    sys.settrace(trace_calls)

# Database query analyzer
class QueryAnalyzer:
    def __init__(self):
        self.queries = []
    
    def log_query(self, query: str, duration: float, params=None):
        self.queries.append({
            'query': query,
            'duration': duration,
            'params': params,
            'timestamp': time.time()
        })
    
    def get_slow_queries(self, threshold: float = 0.1):
        return [q for q in self.queries if q['duration'] > threshold]
    
    def get_query_stats(self):
        if not self.queries:
            return {}
        
        durations = [q['duration'] for q in self.queries]
        return {
            'total_queries': len(self.queries),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'slow_queries': len(self.get_slow_queries())
        }

query_analyzer = QueryAnalyzer()
```

## 🎯 Performance Best Practices

### Development Best Practices

1. **Profile Early and Often**
   - Use profiling tools during development
   - Set performance budgets
   - Monitor critical paths

2. **Database Best Practices**
   - Use appropriate indexes
   - Avoid N+1 queries
   - Use connection pooling
   - Regular VACUUM and ANALYZE

3. **Caching Strategy**
   - Cache at multiple levels
   - Use appropriate TTL values
   - Implement cache invalidation
   - Monitor cache hit rates

4. **Frontend Optimization**
   - Code splitting and lazy loading
   - Optimize bundle sizes
   - Use React.memo and useMemo
   - Implement virtual scrolling for long lists

### Production Monitoring

1. **Key Metrics to Monitor**
   - Response times (95th percentile)
   - Error rates
   - Throughput (requests per second)
   - Resource utilization (CPU, memory, disk)
   - Database performance
   - Cache hit rates

2. **Alerting Thresholds**
   - API response time > 500ms
   - Error rate > 5%
   - Memory usage > 80%
   - Database connections > 80% of pool
   - Cache hit rate < 70%

3. **Performance Testing**
   - Regular load testing
   - Stress testing for peak loads
   - Endurance testing for memory leaks
   - Spike testing for traffic bursts

---

This performance guide provides comprehensive strategies for optimizing the AI Social Media Content Agent. Regular monitoring and optimization based on these guidelines will ensure optimal performance in production environments.