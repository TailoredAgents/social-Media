"""
Comprehensive logging and monitoring configuration
"""
import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_data["duration"] = record.duration
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        
        return json.dumps(log_data, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add application context
        record.service = "aisocial-backend"
        record.version = "1.0.0"
        record.environment = os.getenv("ENVIRONMENT", "development")
        
        return True

def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    max_size: str = "100MB",
    backup_count: int = 5
) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        log_file: Path to log file (None for stdout only)
        max_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    
    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Setup formatters
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Setup context filter
    context_filter = ContextFilter()
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max_size
        size_map = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        size_value = int(max_size[:-2])
        size_unit = max_size[-2:]
        max_bytes = size_value * size_map.get(size_unit, 1024**2)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)
    
    # Add monitoring handler for production error tracking
    if os.getenv("ENVIRONMENT", "development") == "production":
        monitoring_handler = MonitoringLogHandler()
        monitoring_handler.setLevel(logging.ERROR)  # Only ERROR and above
        root_logger.addHandler(monitoring_handler)
    
    # Setup specific loggers
    setup_application_loggers(level)
    
    # Log startup message
    logging.info(
        "Logging system initialized",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "log_file": log_file,
            "handlers": len(root_logger.handlers)
        }
    )

def setup_application_loggers(level: int) -> None:
    """Setup application-specific loggers with appropriate levels"""
    
    # FastAPI and Uvicorn loggers
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("fastapi").setLevel(level)
    
    # SQLAlchemy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # Redis logger
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    # Celery loggers
    logging.getLogger("celery").setLevel(level)
    logging.getLogger("celery.worker").setLevel(level)
    logging.getLogger("celery.task").setLevel(level)
    
    # OpenAI logger
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # Application loggers
    logging.getLogger("backend").setLevel(level)
    logging.getLogger("backend.api").setLevel(level)
    logging.getLogger("backend.services").setLevel(level)
    logging.getLogger("backend.tasks").setLevel(level)

class RequestLoggingContextManager:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str, user_id: Optional[int] = None, endpoint: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.endpoint = endpoint
        self.start_time = datetime.utcnow()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            logging.info(
                "Request completed successfully",
                extra={
                    "request_id": self.request_id,
                    "user_id": self.user_id,
                    "endpoint": self.endpoint,
                    "duration": duration,
                    "status": "success"
                }
            )
        else:
            logging.error(
                "Request failed with exception",
                extra={
                    "request_id": self.request_id,
                    "user_id": self.user_id,
                    "endpoint": self.endpoint,
                    "duration": duration,
                    "status": "error",
                    "exception_type": exc_type.__name__ if exc_type else None
                },
                exc_info=True
            )

def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: Optional[int] = None,
    request_id: Optional[str] = None
) -> None:
    """Log API request details"""
    
    level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
    
    logging.log(
        level,
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id,
            "request_id": request_id,
            "type": "api_request"
        }
    )

def log_database_query(
    query_type: str,
    table: str,
    duration: float,
    rows_affected: Optional[int] = None
) -> None:
    """Log database query performance"""
    
    logging.debug(
        f"Database {query_type} on {table}",
        extra={
            "query_type": query_type,
            "table": table,
            "duration": duration,
            "rows_affected": rows_affected,
            "type": "database_query"
        }
    )

def log_background_task(
    task_name: str,
    task_id: str,
    status: str,
    duration: Optional[float] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Log background task execution"""
    
    level = logging.INFO if status == "success" else logging.ERROR
    
    logging.log(
        level,
        f"Background task {task_name} {status}",
        extra={
            "task_name": task_name,
            "task_id": task_id,
            "status": status,
            "duration": duration,
            "result": result,
            "error": error,
            "type": "background_task"
        }
    )

def log_external_api_call(
    service: str,
    endpoint: str,
    method: str,
    status_code: Optional[int],
    duration: float,
    error: Optional[str] = None
) -> None:
    """Log external API calls"""
    
    level = logging.INFO if status_code and 200 <= status_code < 400 else logging.WARNING
    
    logging.log(
        level,
        f"External API call to {service}",
        extra={
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration": duration,
            "error": error,
            "type": "external_api_call"
        }
    )

def log_security_event(
    event_type: str,
    user_id: Optional[int],
    ip_address: Optional[str],
    details: Dict[str, Any]
) -> None:
    """Log security-related events"""
    
    logging.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "type": "security_event"
        }
    )

def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str,
    tags: Optional[Dict[str, str]] = None
) -> None:
    """Log performance metrics"""
    
    logging.info(
        f"Performance metric: {metric_name}",
        extra={
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": tags or {},
            "type": "performance_metric"
        }
    )

# Health check logging
def log_health_check(
    component: str,
    status: str,
    response_time: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """Log health check results"""
    
    level = logging.INFO if status == "healthy" else logging.ERROR
    
    logging.log(
        level,
        f"Health check: {component} is {status}",
        extra={
            "component": component,
            "status": status,
            "response_time": response_time,
            "error": error,
            "type": "health_check"
        }
    )

def _send_to_monitoring(log_record: Dict[str, Any]) -> None:
    """
    Send log records to external monitoring systems (Sentry, DataDog, etc.)
    
    This function integrates with monitoring services to provide centralized
    log aggregation and alerting for production deployments.
    """
    try:
        # Sentry integration for error tracking
        if log_record.get("level") in ["ERROR", "CRITICAL"] and log_record.get("exception"):
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(
                    Exception(log_record["message"]),
                    extra={
                        "logger": log_record.get("logger"),
                        "module": log_record.get("module"),
                        "function": log_record.get("function"),
                        "user_id": log_record.get("user_id"),
                        "request_id": log_record.get("request_id")
                    }
                )
            except ImportError:
                pass  # Sentry not configured
        
        # DataDog logs integration (example)
        try:
            import os
            if os.getenv("DATADOG_API_KEY"):
                # Would integrate with DataDog logs API here
                pass
        except ImportError:
            pass
        
        # Custom webhook integration
        webhook_url = os.getenv("LOG_MONITORING_WEBHOOK")
        if webhook_url and log_record.get("level") in ["ERROR", "CRITICAL"]:
            try:
                import requests
                requests.post(webhook_url, json=log_record, timeout=5)
            except Exception:
                pass  # Don't fail on monitoring errors
        
    except Exception:
        # Never let monitoring interfere with application logging
        pass

class MonitoringLogHandler(logging.Handler):
    """Custom log handler that sends critical logs to monitoring systems"""
    
    def emit(self, record: logging.LogRecord):
        """Send log record to monitoring systems"""
        try:
            # Convert LogRecord to dict
            log_data = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "thread": record.thread,
                "process": record.process
            }
            
            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.format(record)
            
            # Add extra fields
            for attr in ['user_id', 'request_id', 'duration', 'status_code', 'endpoint']:
                if hasattr(record, attr):
                    log_data[attr] = getattr(record, attr)
            
            # Send to monitoring if it's a critical log
            if record.levelno >= logging.ERROR:
                _send_to_monitoring(log_data)
                
        except Exception:
            # Never let monitoring interfere with logging
            pass
