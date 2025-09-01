"""
System logs and error tracking API endpoints
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import asyncio
import json
from collections import deque
import logging
import traceback
import sys
import os
import uuid
from threading import Lock
from datetime import datetime, timezone
from backend.core.timezone_utils import now_in_est, format_lily_timestamp

router = APIRouter(
    prefix="/api/system",
    tags=["system"]
)

# In-memory error log storage (for free tier - no database required)
class ErrorLogStore:
    def __init__(self, max_size: int = 1000):
        self.errors = deque(maxlen=max_size)
        self.warnings = deque(maxlen=max_size)
        self.info = deque(maxlen=max_size)
        self.websocket_clients: List[WebSocket] = []
        self._lock = Lock()  # Thread-safe ID generation
        
    def add_error(self, error_data: Dict[str, Any]):
        """Add error to store and notify websocket clients"""
        with self._lock:
            error_data['timestamp'] = format_lily_timestamp()  # Use EST timezone
            error_data['timestamp_utc'] = datetime.now(timezone.utc).isoformat()  # Use timezone-aware UTC
            error_data['id'] = str(uuid.uuid4())  # Unique ID
            self.errors.appendleft(error_data)
        
        # Notify all connected WebSocket clients (only if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._notify_clients('error', error_data))
        except RuntimeError:
            # No event loop running (during startup) - skip notification
            pass
        
    def add_warning(self, warning_data: Dict[str, Any]):
        """Add warning to store"""
        with self._lock:
            warning_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            warning_data['id'] = str(uuid.uuid4())  # Unique ID
            self.warnings.appendleft(warning_data)
        
        # Notify all connected WebSocket clients (only if event loop is running)
        try:
            asyncio.create_task(self._notify_clients('warning', warning_data))
        except RuntimeError:
            # No event loop running (during startup) - skip notification
            pass
        
    def add_info(self, info_data: Dict[str, Any]):
        """Add info log to store"""
        with self._lock:
            info_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            info_data['id'] = str(uuid.uuid4())  # Unique ID
            self.info.appendleft(info_data)
        
    async def _notify_clients(self, log_type: str, data: Dict[str, Any]):
        """Notify all connected WebSocket clients"""
        if self.websocket_clients:
            message = json.dumps({
                'type': log_type,
                'data': data
            })
            
            # Remove disconnected clients
            active_clients = []
            for client in self.websocket_clients:
                try:
                    await client.send_text(message)
                    active_clients.append(client)
                except:
                    pass
            
            self.websocket_clients = active_clients
    
    def _parse_timestamp(self, log_entry: Dict[str, Any]) -> datetime:
        """Parse timestamp from log entry, handling both UTC and EST formats"""
        try:
            # Try UTC timestamp first (ISO format)
            if 'timestamp_utc' in log_entry:
                return datetime.fromisoformat(log_entry['timestamp_utc'].replace('Z', ''))
            
            # Fall back to parsing EST timestamp (remove timezone suffix)
            timestamp_str = log_entry.get('timestamp', '')
            if ' EST' in timestamp_str or ' EDT' in timestamp_str:
                # Remove timezone suffix and parse
                timestamp_str = timestamp_str.replace(' EST', '').replace(' EDT', '')
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Try direct ISO parsing
            return datetime.fromisoformat(timestamp_str)
            
        except (ValueError, KeyError):
            # Return a very old timestamp if parsing fails
            return datetime(1970, 1, 1)
    
    def get_errors(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict]:
        """Get recent errors"""
        errors = list(self.errors)[:limit]
        if severity:
            errors = [e for e in errors if e.get('severity') == severity]
        return errors
    
    def get_warnings(self, limit: int = 50) -> List[Dict]:
        """Get recent warnings"""
        return list(self.warnings)[:limit]
    
    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """Get all logs combined"""
        all_logs = []
        
        # Add errors
        for error in list(self.errors)[:limit//3]:
            error['log_type'] = 'error'
            all_logs.append(error)
            
        # Add warnings
        for warning in list(self.warnings)[:limit//3]:
            warning['log_type'] = 'warning'
            all_logs.append(warning)
            
        # Add info
        for info in list(self.info)[:limit//3]:
            info['log_type'] = 'info'
            all_logs.append(info)
            
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_logs[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Count errors by time period (use UTC timestamp for comparison)
        hour_errors = sum(1 for e in self.errors 
                         if self._parse_timestamp(e) > hour_ago)
        day_errors = sum(1 for e in self.errors 
                        if self._parse_timestamp(e) > day_ago)
        
        # Count by severity
        severity_counts = {}
        for error in self.errors:
            sev = error.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
        # Count by endpoint
        endpoint_counts = {}
        for error in self.errors:
            endpoint = error.get('endpoint', 'unknown')
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors_last_hour': hour_errors,
            'errors_last_day': day_errors,
            'severity_breakdown': severity_counts,
            'top_error_endpoints': dict(sorted(
                endpoint_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            'websocket_clients': len(self.websocket_clients)
        }

# Global error store instance
error_store = ErrorLogStore()

# Custom logging handler to capture all logs
class APILogHandler(logging.Handler):
    """Custom handler to capture logs to our error store"""
    
    def emit(self, record):
        log_data = {
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info else None
            }
        
        # Route to appropriate store
        if record.levelno >= logging.ERROR:
            log_data['severity'] = 'error' if record.levelno == logging.ERROR else 'critical'
            error_store.add_error(log_data)
        elif record.levelno >= logging.WARNING:
            error_store.add_warning(log_data)
        else:
            error_store.add_info(log_data)

# Add handler to root logger
api_handler = APILogHandler()
api_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(api_handler)

@router.get("/logs")
async def get_system_logs(
    log_type: Optional[str] = Query(None, description="Filter by log type: error, warning, info, all"),
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None, description="Filter errors by severity: error, critical")
):
    """Get system logs with optional filtering"""
    if log_type == "error":
        return {
            "logs": error_store.get_errors(limit, severity),
            "total": len(error_store.errors)
        }
    elif log_type == "warning":
        return {
            "logs": error_store.get_warnings(limit),
            "total": len(error_store.warnings)
        }
    elif log_type == "info":
        return {
            "logs": list(error_store.info)[:limit],
            "total": len(error_store.info)
        }
    else:
        return {
            "logs": error_store.get_all_logs(limit),
            "total": len(error_store.errors) + len(error_store.warnings) + len(error_store.info)
        }

@router.get("/logs/stats")
async def get_log_statistics():
    """Get error and log statistics"""
    return error_store.get_stats()

@router.post("/logs/error")
async def log_client_error(error_data: Dict[str, Any]):
    """Log errors from the frontend client"""
    error_data['source'] = 'frontend'
    error_data['severity'] = error_data.get('severity', 'error')
    error_store.add_error(error_data)
    return {"status": "logged", "id": error_data.get('id')}

@router.websocket("/logs/stream")
async def websocket_log_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()
    error_store.websocket_clients.append(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to log stream",
                "stats": error_store.get_stats()
            }
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for any message from client (ping/pong)
                data = await websocket.receive_text()
                
                # Echo back as pong (send as JSON to avoid parsing errors)
                if data == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": format_lily_timestamp()})
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Remove from clients list
        if websocket in error_store.websocket_clients:
            error_store.websocket_clients.remove(websocket)

@router.get("/logs/export")
async def export_logs(
    format: str = Query("json", description="Export format: json, csv"),
    log_type: str = Query("all", description="Log type to export")
):
    """Export logs for analysis"""
    if log_type == "error":
        logs = error_store.get_errors(limit=1000)
    elif log_type == "warning":
        logs = error_store.get_warnings(limit=1000)
    else:
        logs = error_store.get_all_logs(limit=1000)
    
    if format == "csv":
        # Simple CSV format
        import csv
        import io
        
        output = io.StringIO()
        if logs:
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=system_logs.csv"}
        )
    else:
        return {"logs": logs, "count": len(logs)}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system info"""
    import platform
    import psutil
    
    # Get memory info
    memory = psutil.virtual_memory()
    
    # Get CPU info
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "process_id": os.getpid(),
        },
        "resources": {
            "memory": {
                "total_mb": memory.total // (1024 * 1024),
                "available_mb": memory.available // (1024 * 1024),
                "used_percent": memory.percent
            },
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            }
        },
        "error_tracking": error_store.get_stats(),
        "environment": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "DEBUG": os.getenv("DEBUG", "false"),
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "has_database": bool(os.getenv("DATABASE_URL")),
            "has_redis": bool(os.getenv("REDIS_URL"))
        }
    }

# Function to manually log errors from other parts of the app
def log_api_error(
    endpoint: str,
    method: str,
    error: Exception,
    request_data: Optional[Dict] = None,
    user_id: Optional[int] = None
):
    """Helper function to log API errors"""
    error_data = {
        "endpoint": endpoint,
        "method": method,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "severity": "error",
        "request_data": request_data,
        "user_id": user_id
    }
    
    error_store.add_error(error_data)
    
# Export for use in other modules
__all__ = ["router", "error_store", "log_api_error"]