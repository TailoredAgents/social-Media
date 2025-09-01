"""
API Performance Monitoring and Response Compression
Real-time performance tracking with intelligent response optimization
"""
import gzip
import json
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from backend.services.redis_cache import redis_cache

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """API performance metric data"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    request_size: int
    response_size: int
    compressed_size: Optional[int]
    user_id: Optional[int]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class PerformanceMonitor:
    """
    Real-time API performance monitoring with compression analytics
    """
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics = deque(maxlen=max_metrics)
        self.endpoint_stats = defaultdict(lambda: {
            'total_requests': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'error_count': 0,
            'compression_ratio': 0.0,
            'last_updated': None
        })
        
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.slow_endpoint_threshold = 1000  # 1 second
        
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics.append(metric)
        
        # Update endpoint statistics
        stats = self.endpoint_stats[f"{metric.method} {metric.endpoint}"]
        stats['total_requests'] += 1
        stats['total_response_time'] += metric.response_time
        stats['avg_response_time'] = stats['total_response_time'] / stats['total_requests']
        stats['min_response_time'] = min(stats['min_response_time'], metric.response_time)
        stats['max_response_time'] = max(stats['max_response_time'], metric.response_time)
        stats['last_updated'] = datetime.utcnow()
        
        if metric.status_code >= 400:
            stats['error_count'] += 1
        
        # Calculate compression ratio if applicable
        if metric.compressed_size:
            compression_ratio = (1 - metric.compressed_size / metric.response_size) * 100
            # Running average of compression ratio
            current_ratio = stats.get('compression_ratio', 0)
            total_requests = stats['total_requests']
            stats['compression_ratio'] = (current_ratio * (total_requests - 1) + compression_ratio) / total_requests
        
        # Log slow endpoints
        if metric.response_time > self.slow_endpoint_threshold:
            logger.warning(f"Slow endpoint detected: {metric.method} {metric.endpoint} took {metric.response_time:.2f}ms")
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics for endpoints"""
        if endpoint:
            return dict(self.endpoint_stats.get(endpoint, {}))
        
        return {endpoint: dict(stats) for endpoint, stats in self.endpoint_stats.items()}
    
    def get_recent_metrics(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics from the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return [
            metric.to_dict() 
            for metric in self.metrics 
            if metric.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.metrics:
            return {"error": "No metrics available"}
        
        recent_metrics = self.get_recent_metrics(60)  # Last hour
        
        if not recent_metrics:
            return {"error": "No recent metrics available"}
        
        total_requests = len(recent_metrics)
        avg_response_time = sum(m['response_time'] for m in recent_metrics) / total_requests
        error_count = sum(1 for m in recent_metrics if m['status_code'] >= 400)
        error_rate = (error_count / total_requests) * 100
        
        # Find slowest endpoints
        endpoint_times = defaultdict(list)
        for metric in recent_metrics:
            key = f"{metric['method']} {metric['endpoint']}"
            endpoint_times[key].append(metric['response_time'])
        
        slowest_endpoints = []
        for endpoint, times in endpoint_times.items():
            avg_time = sum(times) / len(times)
            slowest_endpoints.append({
                'endpoint': endpoint,
                'avg_response_time': avg_time,
                'request_count': len(times)
            })
        
        slowest_endpoints.sort(key=lambda x: x['avg_response_time'], reverse=True)
        
        return {
            'total_requests_last_hour': total_requests,
            'avg_response_time': avg_response_time,
            'error_rate': error_rate,
            'error_count': error_count,
            'slowest_endpoints': slowest_endpoints[:10],
            'last_updated': datetime.utcnow().isoformat()
        }

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for intelligent response compression and performance monitoring
    """
    
    def __init__(self, app, compression_threshold: int = 1024, monitor: Optional[PerformanceMonitor] = None):
        super().__init__(app)
        self.compression_threshold = compression_threshold
        self.monitor = monitor or PerformanceMonitor()
        
        # Compressible content types
        self.compressible_types = {
            'application/json',
            'application/javascript',
            'text/html',
            'text/plain',
            'text/css',
            'text/xml',
            'application/xml'
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with compression and monitoring"""
        start_time = time.time()
        
        # Get request size
        request_size = 0
        if hasattr(request, 'body'):
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Extract user_id if available (from JWT or session)
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Get original response size
        response_body = b''
        compressed_size = None
        
        # Check if response should be compressed
        if (hasattr(response, 'body') and 
            self._should_compress(request, response) and
            hasattr(response, 'media_type') and
            response.media_type in self.compressible_types):
            
            try:
                # Get response body
                if hasattr(response, 'body'):
                    response_body = response.body
                elif hasattr(response, 'content'):
                    response_body = response.content
                
                original_size = len(response_body)
                
                # Compress if above threshold
                if original_size > self.compression_threshold:
                    compressed_body = gzip.compress(response_body)
                    compressed_size = len(compressed_body)
                    
                    # Create new response with compressed content
                    compressed_response = Response(
                        content=compressed_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                    
                    # Add compression headers
                    compressed_response.headers['Content-Encoding'] = 'gzip'
                    compressed_response.headers['Content-Length'] = str(compressed_size)
                    compressed_response.headers['X-Original-Size'] = str(original_size)
                    compressed_response.headers['X-Compression-Ratio'] = f"{((original_size - compressed_size) / original_size * 100):.1f}%"
                    
                    response = compressed_response
                    
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
                compressed_size = None
        
        response_size = len(response_body) if response_body else 0
        
        # Record performance metric
        metric = PerformanceMetric(
            endpoint=str(request.url.path),
            method=request.method,
            response_time=response_time,
            status_code=response.status_code,
            request_size=request_size,
            response_size=response_size,
            compressed_size=compressed_size,
            user_id=user_id,
            timestamp=datetime.utcnow()
        )
        
        self.monitor.record_metric(metric)
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
        response.headers['X-Request-ID'] = str(id(request))
        
        return response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Determine if response should be compressed"""
        # Check if client accepts gzip encoding
        accept_encoding = request.headers.get('accept-encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return False
        
        # Don't compress if already compressed
        content_encoding = response.headers.get('content-encoding')
        if content_encoding:
            return False
        
        # Check content type
        content_type = getattr(response, 'media_type', None)
        if content_type:
            return content_type.split(';')[0] in self.compressible_types
        
        return False

class PerformanceAPI:
    """
    API endpoints for performance monitoring
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    async def get_performance_metrics(
        self, 
        endpoint: Optional[str] = None,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            if endpoint:
                return {
                    'endpoint': endpoint,
                    'stats': self.monitor.get_endpoint_stats(endpoint),
                    'recent_metrics': [
                        m for m in self.monitor.get_recent_metrics(minutes)
                        if m['endpoint'] == endpoint
                    ]
                }
            else:
                return {
                    'summary': self.monitor.get_performance_summary(),
                    'endpoint_stats': self.monitor.get_endpoint_stats(),
                    'recent_metrics_count': len(self.monitor.get_recent_metrics(minutes))
                }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    async def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        try:
            recent_metrics = self.monitor.get_recent_metrics(60)
            
            compressed_responses = [m for m in recent_metrics if m.get('compressed_size')]
            
            if not compressed_responses:
                return {
                    'total_responses': len(recent_metrics),
                    'compressed_responses': 0,
                    'compression_rate': 0,
                    'avg_compression_ratio': 0
                }
            
            total_original_size = sum(m['response_size'] for m in compressed_responses)
            total_compressed_size = sum(m['compressed_size'] for m in compressed_responses)
            
            avg_compression_ratio = ((total_original_size - total_compressed_size) / total_original_size) * 100
            
            return {
                'total_responses': len(recent_metrics),
                'compressed_responses': len(compressed_responses),
                'compression_rate': (len(compressed_responses) / len(recent_metrics)) * 100,
                'avg_compression_ratio': avg_compression_ratio,
                'bytes_saved': total_original_size - total_compressed_size,
                'original_size': total_original_size,
                'compressed_size': total_compressed_size
            }
            
        except Exception as e:
            logger.error(f"Error getting compression stats: {e}")
            return {'error': str(e)}
    
    async def get_slow_endpoints(self, threshold: float = 1000) -> Dict[str, Any]:
        """Get endpoints that are performing slowly"""
        try:
            endpoint_stats = self.monitor.get_endpoint_stats()
            
            slow_endpoints = []
            for endpoint, stats in endpoint_stats.items():
                if stats['avg_response_time'] > threshold:
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'avg_response_time': stats['avg_response_time'],
                        'max_response_time': stats['max_response_time'],
                        'total_requests': stats['total_requests'],
                        'error_rate': (stats['error_count'] / stats['total_requests']) * 100
                    })
            
            slow_endpoints.sort(key=lambda x: x['avg_response_time'], reverse=True)
            
            return {
                'threshold_ms': threshold,
                'slow_endpoints': slow_endpoints,
                'total_slow_endpoints': len(slow_endpoints)
            }
            
        except Exception as e:
            logger.error(f"Error getting slow endpoints: {e}")
            return {'error': str(e)}
    
    async def clear_metrics(self) -> Dict[str, Any]:
        """Clear all performance metrics"""
        try:
            self.monitor.metrics.clear()
            self.monitor.endpoint_stats.clear()
            
            return {
                'status': 'success',
                'message': 'All performance metrics cleared',
                'cleared_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error clearing metrics: {e}")
            return {'error': str(e)}

# Global instances
performance_monitor = PerformanceMonitor()
performance_api = PerformanceAPI(performance_monitor)

# Middleware factory
def create_compression_middleware(app, compression_threshold: int = 1024):
    """Create compression middleware with monitoring"""
    return ResponseCompressionMiddleware(app, compression_threshold, performance_monitor)