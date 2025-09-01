"""
Advanced Error Recovery Service
Intelligent error handling, circuit breakers, and automatic recovery mechanisms
"""
import asyncio
import logging
import time
import random
from typing import Any, Dict, List, Optional, Callable, Type, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from functools import wraps
import traceback

from backend.services.redis_cache import redis_cache

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ESCALATION = "escalation"

@dataclass
class ErrorInfo:
    """Error information tracking"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'stack_trace': self.stack_trace,
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful
        }

@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    success_count: int = 0
    total_requests: int = 0
    
    def reset(self):
        """Reset circuit breaker state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"
        self.success_count = 0

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on: List[Type[Exception]] = field(default_factory=list)
    
class ErrorRecoveryService:
    """
    Advanced error recovery service with multiple recovery strategies
    """
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.circuit_breakers = {}
        self.recovery_handlers = {}
        self.fallback_handlers = {}
        self.error_patterns = defaultdict(list)
        
        # Configuration
        self.circuit_breaker_threshold = 5  # failures before opening
        self.circuit_breaker_timeout = 60  # seconds to keep circuit open
        self.error_analysis_window = 300  # 5 minutes
        
        # Register default error handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default error recovery handlers"""
        
        # Database connection errors
        self.register_recovery_handler(
            "DatabaseConnectionError",
            self._handle_database_connection_error
        )
        
        # API timeout errors
        self.register_recovery_handler(
            "TimeoutError",
            self._handle_timeout_error
        )
        
        # Rate limiting errors
        self.register_recovery_handler(
            "RateLimitError",
            self._handle_rate_limit_error
        )
        
        # Authentication errors
        self.register_recovery_handler(
            "AuthenticationError",
            self._handle_authentication_error
        )
        
        # Network errors
        self.register_recovery_handler(
            "NetworkError",
            self._handle_network_error
        )
    
    def register_recovery_handler(self, error_type: str, handler: Callable):
        """Register a recovery handler for specific error types"""
        if error_type not in self.recovery_handlers:
            self.recovery_handlers[error_type] = []
        self.recovery_handlers[error_type].append(handler)
        logger.info(f"Registered recovery handler for {error_type}")
    
    def register_fallback_handler(self, operation: str, handler: Callable):
        """Register a fallback handler for specific operations"""
        self.fallback_handlers[operation] = handler
        logger.info(f"Registered fallback handler for {operation}")
    
    async def record_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorInfo:
        """
        Record an error for analysis and recovery
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            severity: Error severity level
            
        Returns:
            ErrorInfo object with error details
        """
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            timestamp=datetime.utcnow(),
            context=context,
            stack_trace=traceback.format_exc()
        )
        
        # Store error in history
        self.error_history.append(error_info)
        
        # Update error patterns
        self.error_patterns[error_info.error_type].append(error_info)
        
        # Store in cache for persistence
        try:
            await redis_cache.set(
                "system",
                "error_log",
                error_info.to_dict(),
                resource_id=f"error_{int(time.time())}",
                ttl=86400  # Keep for 24 hours
            )
        except Exception as e:
            logger.warning(f"Failed to cache error info: {e}")
        
        logger.error(f"Recorded error: {error_info.error_type} - {error_info.error_message}")
        return error_info
    
    async def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """
        Attempt to recover from an error
        
        Args:
            error_info: Error information
            
        Returns:
            True if recovery was successful
        """
        error_info.recovery_attempted = True
        
        try:
            # Get recovery handlers for this error type
            handlers = self.recovery_handlers.get(error_info.error_type, [])
            
            for handler in handlers:
                try:
                    success = await handler(error_info)
                    if success:
                        error_info.recovery_successful = True
                        logger.info(f"Successfully recovered from {error_info.error_type}")
                        return True
                except Exception as e:
                    logger.warning(f"Recovery handler failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error during recovery attempt: {e}")
            return False
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreakerState:
        """Get or create circuit breaker for operation"""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreakerState()
        return self.circuit_breakers[operation]
    
    def circuit_breaker(
        self,
        operation: str,
        failure_threshold: int = None,
        timeout: int = None
    ):
        """
        Circuit breaker decorator
        
        Args:
            operation: Operation name
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to keep circuit open
        """
        threshold = failure_threshold or self.circuit_breaker_threshold
        cb_timeout = timeout or self.circuit_breaker_timeout
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cb_state = self.get_circuit_breaker(operation)
                
                # Check if circuit is open
                if cb_state.state == "open":
                    if (cb_state.last_failure_time and 
                        (datetime.utcnow() - cb_state.last_failure_time).seconds < cb_timeout):
                        
                        # Circuit is still open, try fallback
                        fallback = self.fallback_handlers.get(operation)
                        if fallback:
                            logger.info(f"Circuit breaker open for {operation}, using fallback")
                            return await fallback(*args, **kwargs)
                        else:
                            raise Exception(f"Circuit breaker open for {operation}, no fallback available")
                    else:
                        # Timeout expired, try half-open
                        cb_state.state = "half_open"
                        logger.info(f"Circuit breaker half-open for {operation}")
                
                try:
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Success - update circuit breaker
                    if cb_state.state == "half_open":
                        cb_state.state = "closed"
                        cb_state.failure_count = 0
                        logger.info(f"Circuit breaker closed for {operation} after successful call")
                    
                    cb_state.success_count += 1
                    cb_state.total_requests += 1
                    
                    return result
                    
                except Exception as e:
                    # Failure - update circuit breaker
                    cb_state.failure_count += 1
                    cb_state.total_requests += 1
                    cb_state.last_failure_time = datetime.utcnow()
                    
                    # Open circuit if threshold exceeded
                    if cb_state.failure_count >= threshold:
                        cb_state.state = "open"
                        logger.warning(f"Circuit breaker opened for {operation} after {cb_state.failure_count} failures")
                    
                    # Record error
                    await self.record_error(
                        e,
                        {
                            'operation': operation,
                            'circuit_breaker_state': cb_state.state,
                            'failure_count': cb_state.failure_count
                        }
                    )
                    
                    raise e
            
            return wrapper
        return decorator
    
    def retry_with_backoff(
        self,
        config: RetryConfig = None,
        operation: str = None
    ):
        """
        Retry decorator with exponential backoff
        
        Args:
            config: Retry configuration
            operation: Operation name for tracking
        """
        retry_config = config or RetryConfig()
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(retry_config.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                        
                    except Exception as e:
                        last_exception = e
                        
                        # Check if we should retry this exception type
                        if retry_config.retry_on and type(e) not in retry_config.retry_on:
                            raise e
                        
                        # Don't retry on last attempt
                        if attempt == retry_config.max_attempts - 1:
                            break
                        
                        # Calculate delay
                        delay = retry_config.base_delay
                        if retry_config.exponential_backoff:
                            delay *= (2 ** attempt)
                        
                        # Apply jitter
                        if retry_config.jitter:
                            delay *= (0.5 + random.random() * 0.5)
                        
                        # Respect max delay
                        delay = min(delay, retry_config.max_delay)
                        
                        logger.warning(f"Attempt {attempt + 1} failed for {operation or func.__name__}: {e}. Retrying in {delay:.2f}s")
                        
                        # Record retry attempt
                        await self.record_error(
                            e,
                            {
                                'operation': operation or func.__name__,
                                'attempt': attempt + 1,
                                'max_attempts': retry_config.max_attempts,
                                'delay': delay
                            },
                            ErrorSeverity.LOW
                        )
                        
                        await asyncio.sleep(delay)
                
                # All retries failed
                if last_exception:
                    await self.record_error(
                        last_exception,
                        {
                            'operation': operation or func.__name__,
                            'all_retries_failed': True,
                            'total_attempts': retry_config.max_attempts
                        },
                        ErrorSeverity.HIGH
                    )
                    raise last_exception
            
            return wrapper
        return decorator
    
    # Default error recovery handlers
    async def _handle_database_connection_error(self, error_info: ErrorInfo) -> bool:
        """Handle database connection errors"""
        try:
            logger.info("Attempting database connection recovery")
            
            # Wait a bit for connection to recover
            await asyncio.sleep(2)
            
            # Try to ping database
            from backend.db.database_optimized import get_db_connection
            with get_db_connection() as db:
                db.execute("SELECT 1")
            
            logger.info("Database connection recovered")
            return True
            
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False
    
    async def _handle_timeout_error(self, error_info: ErrorInfo) -> bool:
        """Handle timeout errors"""
        try:
            # Implement timeout recovery logic
            # For now, just log and suggest retry
            logger.info("Timeout error detected - suggesting retry with longer timeout")
            
            # Could implement adaptive timeout adjustment here
            return False  # Let retry mechanism handle it
            
        except Exception as e:
            logger.error(f"Timeout recovery failed: {e}")
            return False
    
    async def _handle_rate_limit_error(self, error_info: ErrorInfo) -> bool:
        """Handle rate limiting errors"""
        try:
            # Extract rate limit info from context
            context = error_info.context
            
            # Wait for rate limit reset
            reset_time = context.get('rate_limit_reset', 60)
            logger.info(f"Rate limit hit, waiting {reset_time} seconds")
            
            await asyncio.sleep(min(reset_time, 300))  # Max 5 minutes
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit recovery failed: {e}")
            return False
    
    async def _handle_authentication_error(self, error_info: ErrorInfo) -> bool:
        """Handle authentication errors"""
        try:
            logger.info("Authentication error detected - token refresh may be needed")
            
            # Could implement automatic token refresh here
            # For now, just log for manual intervention
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication recovery failed: {e}")
            return False
    
    async def _handle_network_error(self, error_info: ErrorInfo) -> bool:
        """Handle network errors"""
        try:
            logger.info("Network error detected - checking connectivity")
            
            # Simple connectivity check
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://httpbin.org/status/200', timeout=10) as response:
                    if response.status == 200:
                        logger.info("Network connectivity restored")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Network recovery failed: {e}")
            return False
    
    async def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze error patterns to identify recurring issues
        
        Returns:
            Error pattern analysis
        """
        try:
            analysis = {
                'total_errors': len(self.error_history),
                'error_types': {},
                'severity_distribution': defaultdict(int),
                'recent_errors': [],
                'top_error_contexts': defaultdict(int),
                'recovery_success_rate': 0.0
            }
            
            # Analyze recent errors (last 5 minutes)
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            recent_errors = [e for e in self.error_history if e.timestamp >= recent_time]
            
            analysis['recent_errors'] = [e.to_dict() for e in recent_errors]
            
            # Analyze error types and severity
            recovery_attempts = 0
            successful_recoveries = 0
            
            for error in self.error_history:
                error_type = error.error_type
                if error_type not in analysis['error_types']:
                    analysis['error_types'][error_type] = {
                        'count': 0,
                        'last_occurrence': None,
                        'recovery_rate': 0.0
                    }
                
                analysis['error_types'][error_type]['count'] += 1
                analysis['error_types'][error_type]['last_occurrence'] = error.timestamp.isoformat()
                
                analysis['severity_distribution'][error.severity.value] += 1
                
                # Track recovery statistics
                if error.recovery_attempted:
                    recovery_attempts += 1
                    if error.recovery_successful:
                        successful_recoveries += 1
                
                # Analyze error contexts
                for key, value in error.context.items():
                    context_key = f"{key}:{value}"
                    analysis['top_error_contexts'][context_key] += 1
            
            # Calculate recovery success rate
            if recovery_attempts > 0:
                analysis['recovery_success_rate'] = (successful_recoveries / recovery_attempts) * 100
            
            # Calculate recovery rates per error type
            for error_type, error_data in analysis['error_types'].items():
                type_errors = [e for e in self.error_history if e.error_type == error_type]
                type_recoveries = [e for e in type_errors if e.recovery_attempted]
                type_successes = [e for e in type_recoveries if e.recovery_successful]
                
                if type_recoveries:
                    error_data['recovery_rate'] = (len(type_successes) / len(type_recoveries)) * 100
            
            # Convert defaultdicts to regular dicts for JSON serialization
            analysis['severity_distribution'] = dict(analysis['severity_distribution'])
            analysis['top_error_contexts'] = dict(analysis['top_error_contexts'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")
            return {'error': str(e)}
    
    async def get_recovery_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for improving error recovery
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        try:
            analysis = await self.analyze_error_patterns()
            
            # Check for high-frequency errors
            for error_type, data in analysis.get('error_types', {}).items():
                if data['count'] > 10:  # Frequent error
                    if data['recovery_rate'] < 50:  # Low recovery rate
                        recommendations.append({
                            'type': 'improve_recovery',
                            'priority': 'high',
                            'description': f"Improve recovery for {error_type} (occurs {data['count']} times, {data['recovery_rate']:.1f}% recovery rate)",
                            'error_type': error_type
                        })
            
            # Check circuit breaker effectiveness
            for operation, cb_state in self.circuit_breakers.items():
                if cb_state.total_requests > 0:
                    failure_rate = (cb_state.failure_count / cb_state.total_requests) * 100
                    if failure_rate > 20:  # High failure rate
                        recommendations.append({
                            'type': 'circuit_breaker_tuning',
                            'priority': 'medium',
                            'description': f"High failure rate for {operation} ({failure_rate:.1f}%), consider adjusting circuit breaker settings",
                            'operation': operation
                        })
            
            # Check for missing fallback handlers
            open_circuits = [op for op, cb in self.circuit_breakers.items() if cb.state == "open"]
            for operation in open_circuits:
                if operation not in self.fallback_handlers:
                    recommendations.append({
                        'type': 'add_fallback',
                        'priority': 'high',
                        'description': f"Add fallback handler for {operation} (circuit breaker is open)",
                        'operation': operation
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def reset_circuit_breaker(self, operation: str) -> bool:
        """Reset circuit breaker for an operation"""
        try:
            if operation in self.circuit_breakers:
                self.circuit_breakers[operation].reset()
                logger.info(f"Reset circuit breaker for {operation}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to reset circuit breaker: {e}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health from error perspective"""
        try:
            recent_time = datetime.utcnow() - timedelta(minutes=30)
            recent_errors = [e for e in self.error_history if e.timestamp >= recent_time]
            
            # Calculate health score
            total_errors = len(recent_errors)
            critical_errors = len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
            
            # Health score (0-100, lower is worse)
            health_score = max(0, 100 - (total_errors * 2) - (critical_errors * 10))
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "degraded"
            elif health_score >= 50:
                status = "unhealthy"
            else:
                status = "critical"
            
            return {
                'status': status,
                'health_score': health_score,
                'recent_errors_count': total_errors,
                'critical_errors_count': critical_errors,
                'open_circuit_breakers': len([cb for cb in self.circuit_breakers.values() if cb.state == "open"]),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {'status': 'unknown', 'error': str(e)}

# Global error recovery service
error_recovery_service = ErrorRecoveryService()

# Convenience decorators
def with_circuit_breaker(operation: str, **kwargs):
    """Convenience decorator for circuit breaker"""
    return error_recovery_service.circuit_breaker(operation, **kwargs)

def with_retry(config: RetryConfig = None, operation: str = None):
    """Convenience decorator for retry with backoff"""
    return error_recovery_service.retry_with_backoff(config, operation)