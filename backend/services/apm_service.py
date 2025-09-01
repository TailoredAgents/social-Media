"""
Application Performance Monitoring (APM) Service
Comprehensive monitoring, metrics collection, and alerting system
"""
import asyncio
import logging
import time
import psutil
import tracemalloc
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import sys
import gc

from backend.services.redis_cache import redis_cache
from backend.db.database_optimized import db_optimizer

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class SystemMetric:
    """System performance metric"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    active_connections: int
    request_count: int
    response_time_avg: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class ApplicationMetric:
    """Application-specific metric"""
    timestamp: datetime
    active_users: int
    total_requests: int
    cache_hit_ratio: float
    database_pool_usage: float
    celery_tasks_pending: int
    celery_tasks_active: int
    memory_leaks_detected: int
    gc_collections: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class PerformanceAlert:
    """Performance alert"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        if data['resolved_at']:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

class APMService:
    """
    Application Performance Monitoring service
    """
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_interval = 30  # seconds
        self.metrics_retention_hours = 24
        
        # Metrics storage
        self.system_metrics = deque(maxlen=2880)  # 24h at 30s intervals
        self.app_metrics = deque(maxlen=2880)
        self.alerts = deque(maxlen=1000)
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': {'warning': 70.0, 'critical': 90.0},
            'memory_percent': {'warning': 80.0, 'critical': 95.0},
            'disk_usage_percent': {'warning': 85.0, 'critical': 95.0},
            'response_time_avg': {'warning': 1000.0, 'critical': 3000.0},  # ms
            'error_rate': {'warning': 5.0, 'critical': 15.0},  # percentage
            'cache_hit_ratio': {'warning': 70.0, 'critical': 50.0},  # minimum acceptable
            'database_pool_usage': {'warning': 80.0, 'critical': 95.0}
        }
        
        # Alert tracking
        self.active_alerts = {}
        self.alert_cooldown = 300  # 5 minutes between same alerts
        self.last_alert_times = defaultdict(float)
        
        # Performance tracking
        self.request_metrics = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
        
        # Memory tracking
        self.memory_tracking_enabled = False
        self.memory_snapshots = []
        
    async def start_monitoring(self):
        """Start the APM monitoring service"""
        if self.is_monitoring:
            logger.warning("APM monitoring already running")
            return
        
        self.is_monitoring = True
        logger.info("Starting APM monitoring service")
        
        # Start memory tracking
        self._start_memory_tracking()
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the APM monitoring service"""
        self.is_monitoring = False
        self._stop_memory_tracking()
        logger.info("APM monitoring service stopped")
    
    def _start_memory_tracking(self):
        """Start memory tracking for leak detection"""
        try:
            tracemalloc.start()
            self.memory_tracking_enabled = True
            logger.info("Memory tracking enabled")
        except Exception as e:
            logger.warning(f"Failed to start memory tracking: {e}")
    
    def _stop_memory_tracking(self):
        """Stop memory tracking"""
        if self.memory_tracking_enabled:
            tracemalloc.stop()
            self.memory_tracking_enabled = False
            logger.info("Memory tracking disabled")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metric = await self._collect_system_metrics()
                self.system_metrics.append(system_metric)
                
                # Collect application metrics
                app_metric = await self._collect_application_metrics()
                self.app_metrics.append(app_metric)
                
                # Check for alerts
                await self._check_performance_alerts(system_metric, app_metric)
                
                # Store metrics in cache
                await self._store_metrics_in_cache(system_metric, app_metric)
                
                # Cleanup old data
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> SystemMetric:
        """Collect system-level performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Connection metrics
            connections = psutil.net_connections()
            active_connections = len([conn for conn in connections if conn.status == 'ESTABLISHED'])
            
            # Calculate request metrics
            recent_metrics = list(self.request_metrics)[-100:]  # Last 100 requests
            
            if recent_metrics:
                avg_response_time = sum(m['response_time'] for m in recent_metrics) / len(recent_metrics)
                error_count = sum(1 for m in recent_metrics if m['status_code'] >= 400)
                error_rate = (error_count / len(recent_metrics)) * 100
            else:
                avg_response_time = 0.0
                error_rate = 0.0
            
            return SystemMetric(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                active_connections=active_connections,
                request_count=len(recent_metrics),
                response_time_avg=avg_response_time,
                error_rate=error_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default metric
            return SystemMetric(
                timestamp=datetime.utcnow(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_io={},
                active_connections=0,
                request_count=0,
                response_time_avg=0.0,
                error_rate=0.0
            )
    
    async def _collect_application_metrics(self) -> ApplicationMetric:
        """Collect application-specific metrics"""
        try:
            # Get cache metrics
            cache_stats = await redis_cache.get_cache_stats()
            cache_hit_ratio = cache_stats.get('hit_ratio', 0.0)
            
            # Get database metrics
            db_stats = db_optimizer.get_stats()
            db_pool_usage = 0.0
            if db_stats.get('peak_connections', 0) > 0:
                db_pool_usage = (db_stats.get('active_connections', 0) / db_stats.get('peak_connections', 1)) * 100
            
            # Memory leak detection
            memory_leaks = 0
            if self.memory_tracking_enabled:
                current_snapshot = tracemalloc.take_snapshot()
                if len(self.memory_snapshots) > 0:
                    # Compare with previous snapshot
                    top_stats = current_snapshot.compare_to(self.memory_snapshots[-1], 'lineno')
                    memory_leaks = len([stat for stat in top_stats[:10] if stat.size_diff > 1024 * 1024])  # >1MB growth
                
                # Keep only last 5 snapshots
                self.memory_snapshots.append(current_snapshot)
                if len(self.memory_snapshots) > 5:
                    self.memory_snapshots.pop(0)
            
            # Garbage collection stats
            gc_stats = gc.get_stats()
            gc_collections = sum(stat['collections'] for stat in gc_stats)
            
            return ApplicationMetric(
                timestamp=datetime.utcnow(),
                active_users=0,  # Would need to implement session tracking
                total_requests=self.total_requests,
                cache_hit_ratio=cache_hit_ratio,
                database_pool_usage=db_pool_usage,
                celery_tasks_pending=0,  # Would need Celery integration
                celery_tasks_active=0,
                memory_leaks_detected=memory_leaks,
                gc_collections=gc_collections
            )
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return ApplicationMetric(
                timestamp=datetime.utcnow(),
                active_users=0,
                total_requests=0,
                cache_hit_ratio=0.0,
                database_pool_usage=0.0,
                celery_tasks_pending=0,
                celery_tasks_active=0,
                memory_leaks_detected=0,
                gc_collections=0
            )
    
    async def _check_performance_alerts(self, system_metric: SystemMetric, app_metric: ApplicationMetric):
        """Check for performance alerts based on thresholds"""
        current_time = time.time()
        
        # System metric alerts
        system_checks = [
            ('cpu_percent', system_metric.cpu_percent, 'CPU usage'),
            ('memory_percent', system_metric.memory_percent, 'Memory usage'),
            ('disk_usage_percent', system_metric.disk_usage_percent, 'Disk usage'),
            ('response_time_avg', system_metric.response_time_avg, 'Average response time'),
            ('error_rate', system_metric.error_rate, 'Error rate')
        ]
        
        for metric_name, value, description in system_checks:
            await self._check_threshold_alert(metric_name, value, description, current_time)
        
        # Application metric alerts
        app_checks = [
            ('cache_hit_ratio', app_metric.cache_hit_ratio, 'Cache hit ratio'),
            ('database_pool_usage', app_metric.database_pool_usage, 'Database pool usage')
        ]
        
        for metric_name, value, description in app_checks:
            if metric_name == 'cache_hit_ratio':
                # For cache hit ratio, lower is worse
                await self._check_threshold_alert_reverse(metric_name, value, description, current_time)
            else:
                await self._check_threshold_alert(metric_name, value, description, current_time)
        
        # Memory leak alerts
        if app_metric.memory_leaks_detected > 0:
            await self._create_alert(
                f"memory_leaks_{current_time}",
                AlertSeverity.WARNING,
                'memory_leaks',
                app_metric.memory_leaks_detected,
                0,
                f"Memory leaks detected: {app_metric.memory_leaks_detected} objects growing >1MB"
            )
    
    async def _check_threshold_alert(self, metric_name: str, value: float, description: str, current_time: float):
        """Check if metric exceeds thresholds and create alerts"""
        thresholds = self.thresholds.get(metric_name, {})
        
        # Check critical threshold
        if 'critical' in thresholds and value >= thresholds['critical']:
            if current_time - self.last_alert_times[f"{metric_name}_critical"] > self.alert_cooldown:
                await self._create_alert(
                    f"{metric_name}_critical_{current_time}",
                    AlertSeverity.CRITICAL,
                    metric_name,
                    value,
                    thresholds['critical'],
                    f"CRITICAL: {description} is {value:.2f}% (threshold: {thresholds['critical']}%)"
                )
                self.last_alert_times[f"{metric_name}_critical"] = current_time
        
        # Check warning threshold
        elif 'warning' in thresholds and value >= thresholds['warning']:
            if current_time - self.last_alert_times[f"{metric_name}_warning"] > self.alert_cooldown:
                await self._create_alert(
                    f"{metric_name}_warning_{current_time}",
                    AlertSeverity.WARNING,
                    metric_name,
                    value,
                    thresholds['warning'],
                    f"WARNING: {description} is {value:.2f}% (threshold: {thresholds['warning']}%)"
                )
                self.last_alert_times[f"{metric_name}_warning"] = current_time
    
    async def _check_threshold_alert_reverse(self, metric_name: str, value: float, description: str, current_time: float):
        """Check if metric falls below thresholds (for metrics where lower is worse)"""
        thresholds = self.thresholds.get(metric_name, {})
        
        # Check critical threshold (lower is worse)
        if 'critical' in thresholds and value <= thresholds['critical']:
            if current_time - self.last_alert_times[f"{metric_name}_critical"] > self.alert_cooldown:
                await self._create_alert(
                    f"{metric_name}_critical_{current_time}",
                    AlertSeverity.CRITICAL,
                    metric_name,
                    value,
                    thresholds['critical'],
                    f"CRITICAL: {description} is {value:.2f}% (minimum: {thresholds['critical']}%)"
                )
                self.last_alert_times[f"{metric_name}_critical"] = current_time
        
        # Check warning threshold
        elif 'warning' in thresholds and value <= thresholds['warning']:
            if current_time - self.last_alert_times[f"{metric_name}_warning"] > self.alert_cooldown:
                await self._create_alert(
                    f"{metric_name}_warning_{current_time}",
                    AlertSeverity.WARNING,
                    metric_name,
                    value,
                    thresholds['warning'],
                    f"WARNING: {description} is {value:.2f}% (minimum: {thresholds['warning']}%)"
                )
                self.last_alert_times[f"{metric_name}_warning"] = current_time
    
    async def _create_alert(
        self,
        alert_id: str,
        severity: AlertSeverity,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        message: str,
        context: Dict[str, Any] = None
    ):
        """Create a performance alert"""
        alert = PerformanceAlert(
            id=alert_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            context=context or {}
        )
        
        self.alerts.append(alert)
        self.active_alerts[alert_id] = alert
        
        # Log alert
        log_level = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }
        log_level[severity](f"APM Alert: {message}")
        
        # Store alert in cache
        try:
            await redis_cache.set(
                'system',
                'apm_alert',
                alert.to_dict(),
                resource_id=alert_id,
                ttl=86400  # Keep for 24 hours
            )
        except Exception as e:
            logger.warning(f"Failed to cache alert: {e}")
    
    async def _store_metrics_in_cache(self, system_metric: SystemMetric, app_metric: ApplicationMetric):
        """Store metrics in cache for persistence and external access"""
        try:
            timestamp = int(time.time())
            
            # Store current metrics
            await redis_cache.set(
                'system',
                'apm_metrics',
                {
                    'system': system_metric.to_dict(),
                    'application': app_metric.to_dict()
                },
                resource_id=f"current",
                ttl=3600  # 1 hour
            )
            
            # Store historical data
            await redis_cache.set(
                'system',
                'apm_history',
                {
                    'system': system_metric.to_dict(),
                    'application': app_metric.to_dict()
                },
                resource_id=f"history_{timestamp}",
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            logger.warning(f"Failed to store metrics in cache: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
        
        # Clean up old metrics (deques automatically handle max length)
        # Clean up resolved alerts older than retention period
        self.alerts = deque([
            alert for alert in self.alerts 
            if alert.timestamp >= cutoff_time or not alert.resolved
        ], maxlen=1000)
    
    def record_request(self, method: str, path: str, status_code: int, response_time: float):
        """Record a request for metrics tracking"""
        self.total_requests += 1
        
        if status_code >= 400:
            self.error_count += 1
        
        request_metric = {
            'timestamp': datetime.utcnow(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time': response_time
        }
        
        self.request_metrics.append(request_metric)
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            if not self.system_metrics or not self.app_metrics:
                return {'error': 'No metrics available yet'}
            
            latest_system = self.system_metrics[-1]
            latest_app = self.app_metrics[-1]
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system': latest_system.to_dict(),
                'application': latest_app.to_dict(),
                'active_alerts': len(self.active_alerts),
                'total_requests': self.total_requests,
                'error_count': self.error_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {'error': str(e)}
    
    async def get_metrics_history(self, hours: int = 1) -> Dict[str, Any]:
        """Get historical metrics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics by time
            system_history = [
                m.to_dict() for m in self.system_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            app_history = [
                m.to_dict() for m in self.app_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            return {
                'period_hours': hours,
                'data_points': len(system_history),
                'system_metrics': system_history,
                'application_metrics': app_history
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return {'error': str(e)}
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                logger.info(f"Resolved alert: {alert_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and health status"""
        try:
            if not self.system_metrics:
                return {'status': 'no_data'}
            
            latest_system = self.system_metrics[-1]
            latest_app = self.app_metrics[-1]
            
            # Calculate health score
            health_factors = [
                (100 - latest_system.cpu_percent) * 0.2,
                (100 - latest_system.memory_percent) * 0.2,
                (100 - latest_system.disk_usage_percent) * 0.1,
                min(latest_system.response_time_avg / 10, 100) * 0.2,  # Response time factor
                (100 - latest_system.error_rate) * 0.2,
                latest_app.cache_hit_ratio * 0.1
            ]
            
            health_score = sum(health_factors)
            
            # Determine status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 75:
                status = "good"
            elif health_score >= 60:
                status = "fair"
            elif health_score >= 40:
                status = "poor"
            else:
                status = "critical"
            
            return {
                'status': status,
                'health_score': round(health_score, 2),
                'active_alerts': len(self.active_alerts),
                'critical_alerts': len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]),
                'current_metrics': {
                    'cpu_usage': latest_system.cpu_percent,
                    'memory_usage': latest_system.memory_percent,
                    'response_time': latest_system.response_time_avg,
                    'error_rate': latest_system.error_rate,
                    'cache_hit_ratio': latest_app.cache_hit_ratio
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}

# Global APM service instance
apm_service = APMService()

# Middleware integration function
def create_apm_middleware():
    """Create APM middleware for FastAPI integration"""
    
    async def apm_middleware(request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            apm_service.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time=response_time
            )
            
            return response
            
        except Exception as e:
            # Record error
            response_time = (time.time() - start_time) * 1000
            apm_service.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=500,
                response_time=response_time
            )
            raise e
    
    return apm_middleware

class PrometheusMetrics:
    """
    Prometheus-compatible metrics exporter
    Exports APM metrics in Prometheus format
    """
    
    def __init__(self, apm_service: APMService):
        self.apm = apm_service
    
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics format"""
        lines = []
        
        # Add help and type declarations
        lines.extend([
            "# HELP apm_cpu_usage_percent Current CPU usage percentage",
            "# TYPE apm_cpu_usage_percent gauge",
            "# HELP apm_memory_usage_percent Current memory usage percentage",
            "# TYPE apm_memory_usage_percent gauge",
            "# HELP apm_disk_usage_percent Current disk usage percentage", 
            "# TYPE apm_disk_usage_percent gauge",
            "# HELP apm_response_time_avg_ms Average response time in milliseconds",
            "# TYPE apm_response_time_avg_ms gauge",
            "# HELP apm_error_rate_percent Error rate percentage",
            "# TYPE apm_error_rate_percent gauge",
            "# HELP apm_total_requests_total Total number of requests processed",
            "# TYPE apm_total_requests_total counter",
            "# HELP apm_cache_hit_ratio Cache hit ratio as a percentage",
            "# TYPE apm_cache_hit_ratio gauge",
            "# HELP apm_database_pool_usage_percent Database pool usage percentage",
            "# TYPE apm_database_pool_usage_percent gauge",
            "# HELP apm_active_alerts_total Number of currently active alerts",
            "# TYPE apm_active_alerts_total gauge",
            "# HELP apm_memory_leaks_detected_total Number of memory leaks detected",
            "# TYPE apm_memory_leaks_detected_total gauge",
            ""
        ])
        
        try:
            # Get current metrics
            if self.apm.system_metrics and self.apm.app_metrics:
                latest_system = self.apm.system_metrics[-1]
                latest_app = self.apm.app_metrics[-1]
                timestamp = int(latest_system.timestamp.timestamp() * 1000)
                
                # System metrics
                lines.extend([
                    f"apm_cpu_usage_percent {latest_system.cpu_percent} {timestamp}",
                    f"apm_memory_usage_percent {latest_system.memory_percent} {timestamp}",
                    f"apm_disk_usage_percent {latest_system.disk_usage_percent} {timestamp}",
                    f"apm_response_time_avg_ms {latest_system.response_time_avg} {timestamp}",
                    f"apm_error_rate_percent {latest_system.error_rate} {timestamp}",
                    f"apm_total_requests_total {latest_system.request_count} {timestamp}",
                    ""
                ])
                
                # Application metrics
                lines.extend([
                    f"apm_cache_hit_ratio {latest_app.cache_hit_ratio} {timestamp}",
                    f"apm_database_pool_usage_percent {latest_app.database_pool_usage} {timestamp}",
                    f"apm_memory_leaks_detected_total {latest_app.memory_leaks_detected} {timestamp}",
                    ""
                ])
                
                # Alert metrics
                critical_alerts = len([a for a in self.apm.active_alerts.values() if a.severity == AlertSeverity.CRITICAL])
                warning_alerts = len([a for a in self.apm.active_alerts.values() if a.severity == AlertSeverity.WARNING])
                
                lines.extend([
                    f"apm_active_alerts_total{{severity=\"critical\"}} {critical_alerts} {timestamp}",
                    f"apm_active_alerts_total{{severity=\"warning\"}} {warning_alerts} {timestamp}",
                    f"apm_active_alerts_total{{severity=\"all\"}} {len(self.apm.active_alerts)} {timestamp}",
                    ""
                ])
                
                # Network metrics
                if latest_system.network_io:
                    lines.extend([
                        f"apm_network_bytes_sent_total {latest_system.network_io.get('bytes_sent', 0)} {timestamp}",
                        f"apm_network_bytes_recv_total {latest_system.network_io.get('bytes_recv', 0)} {timestamp}",
                        ""
                    ])
                
                # Connection metrics
                lines.append(f"apm_active_connections {latest_system.active_connections} {timestamp}")
                
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            lines.append(f"# ERROR: Failed to generate metrics: {e}")
        
        return "\n".join(lines)

# Global Prometheus metrics instance
prometheus_metrics = PrometheusMetrics(apm_service)