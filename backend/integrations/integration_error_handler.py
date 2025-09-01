"""
Enhanced Error Handling for Social Media Integrations
Provides comprehensive error recovery, retry logic, and graceful degradation
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import httpx

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of integration errors"""
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    API_ERROR = "api_error"
    CONTENT_VALIDATION = "content_validation"
    QUOTA_EXCEEDED = "quota_exceeded"
    TEMPORARY_FAILURE = "temporary_failure"
    PERMANENT_FAILURE = "permanent_failure"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Retry immediately
    MEDIUM = "medium"     # Retry with delay
    HIGH = "high"         # Retry with exponential backoff
    CRITICAL = "critical" # Manual intervention required

@dataclass
class ErrorContext:
    """Context information for errors"""
    platform: str
    operation: str
    error_type: ErrorType
    severity: ErrorSeverity
    original_error: Exception
    retry_count: int
    user_id: Optional[str] = None
    content_id: Optional[str] = None
    timestamp: datetime = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.additional_info is None:
            self.additional_info = {}

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: str = "exponential"  # linear, exponential, fixed

class IntegrationErrorHandler:
    """
    Comprehensive error handling system for social media integrations
    
    Features:
    - Platform-specific error classification
    - Intelligent retry strategies
    - Circuit breaker pattern
    - Error aggregation and reporting
    - Graceful degradation
    - Recovery mechanisms
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_history: List[ErrorContext] = []
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.error_stats = {
            "total_errors": 0,
            "errors_by_platform": {},
            "errors_by_type": {},
            "recovery_rate": 0.0,
            "last_reset": datetime.utcnow()
        }
        
        # Initialize default retry configurations
        self._setup_default_retry_configs()
        
        # Initialize circuit breakers
        self._setup_circuit_breakers()
        
        logger.info("Integration error handler initialized")
    
    def _setup_default_retry_configs(self):
        """Setup default retry configurations for different scenarios"""
        
        # Rate limiting - aggressive retry with exponential backoff
        self.retry_configs["rate_limit"] = RetryConfig(
            max_retries=5,
            base_delay=5.0,
            max_delay=300.0,
            exponential_base=2.0,
            backoff_strategy="exponential"
        )
        
        # Network errors - moderate retry
        self.retry_configs["network"] = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=1.5,
            backoff_strategy="exponential"
        )
        
        # API errors - conservative retry
        self.retry_configs["api_error"] = RetryConfig(
            max_retries=2,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            backoff_strategy="linear"
        )
        
        # Authentication errors - minimal retry
        self.retry_configs["authentication"] = RetryConfig(
            max_retries=1,
            base_delay=0.5,
            max_delay=5.0,
            backoff_strategy="fixed"
        )
        
        # Content validation - no retry
        self.retry_configs["content_validation"] = RetryConfig(
            max_retries=0,
            base_delay=0.0,
            max_delay=0.0,
            backoff_strategy="fixed"
        )
    
    def _setup_circuit_breakers(self):
        """Setup circuit breakers for each platform"""
        
        platforms = ["twitter", "linkedin", "instagram", "facebook"]
        
        for platform in platforms:
            self.circuit_breakers[platform] = {
                "state": "closed",  # closed, open, half-open
                "failure_count": 0,
                "failure_threshold": 5,
                "recovery_timeout": 300,  # 5 minutes
                "last_failure": None,
                "success_count": 0,
                "success_threshold": 3  # for half-open to closed transition
            }
    
    def classify_error(self, platform: str, error: Exception, operation: str = "") -> Tuple[ErrorType, ErrorSeverity]:
        """
        Classify error type and severity based on error message and platform
        
        Args:
            platform: Social media platform
            error: Exception that occurred
            operation: Operation that was being performed
            
        Returns:
            Tuple of (error_type, severity)
        """
        error_msg = str(error).lower()
        
        # Rate limiting errors
        if any(keyword in error_msg for keyword in ["rate limit", "too many requests", "429"]):
            return ErrorType.RATE_LIMIT, ErrorSeverity.HIGH
        
        # Authentication errors
        if any(keyword in error_msg for keyword in ["unauthorized", "invalid token", "expired", "401", "403"]):
            return ErrorType.AUTHENTICATION, ErrorSeverity.CRITICAL
        
        # Network errors
        if any(keyword in error_msg for keyword in ["timeout", "connection", "network", "dns", "unreachable"]):
            return ErrorType.NETWORK, ErrorSeverity.MEDIUM
        
        # Quota errors
        if any(keyword in error_msg for keyword in ["quota", "limit exceeded", "usage limit"]):
            return ErrorType.QUOTA_EXCEEDED, ErrorSeverity.HIGH
        
        # Content validation errors
        if any(keyword in error_msg for keyword in ["invalid content", "content too long", "validation failed"]):
            return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
        
        # Platform-specific error classification
        if platform == "twitter":
            if "tweet not found" in error_msg or "user not found" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
            if "duplicate" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
        
        elif platform == "linkedin":
            if "member not found" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
            if "access denied" in error_msg:
                return ErrorType.AUTHENTICATION, ErrorSeverity.CRITICAL
        
        elif platform == "instagram":
            if "media not found" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
            if "invalid media" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
        
        elif platform == "facebook":
            if "post not found" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
            if "page not found" in error_msg:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
        
        # HTTP status code classification
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            
            if status_code == 429:
                return ErrorType.RATE_LIMIT, ErrorSeverity.HIGH
            elif status_code in [401, 403]:
                return ErrorType.AUTHENTICATION, ErrorSeverity.CRITICAL
            elif status_code in [400, 422]:
                return ErrorType.CONTENT_VALIDATION, ErrorSeverity.LOW
            elif status_code in [500, 502, 503, 504]:
                return ErrorType.TEMPORARY_FAILURE, ErrorSeverity.MEDIUM
            elif status_code >= 400:
                return ErrorType.API_ERROR, ErrorSeverity.MEDIUM
        
        # Default classification
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def should_retry(self, error_context: ErrorContext) -> bool:
        """
        Determine if an operation should be retried based on error context
        
        Args:
            error_context: Error context information
            
        Returns:
            True if should retry, False otherwise
        """
        # Check circuit breaker
        if not self._is_circuit_closed(error_context.platform):
            logger.warning(f"Circuit breaker open for {error_context.platform}, not retrying")
            return False
        
        # Check retry count
        retry_config = self.retry_configs.get(
            error_context.error_type.value,
            self.retry_configs["api_error"]
        )
        
        if error_context.retry_count >= retry_config.max_retries:
            logger.info(f"Max retries ({retry_config.max_retries}) exceeded for {error_context.platform} {error_context.operation}")
            return False
        
        # Don't retry certain error types
        if error_context.error_type in [ErrorType.CONTENT_VALIDATION, ErrorType.AUTHENTICATION]:
            if error_context.retry_count > 0:  # Allow one retry for auth errors
                return False
        
        # Don't retry permanent failures
        if error_context.error_type == ErrorType.PERMANENT_FAILURE:
            return False
        
        return True
    
    def calculate_retry_delay(self, error_context: ErrorContext) -> float:
        """
        Calculate delay before retry based on error context and retry strategy
        
        Args:
            error_context: Error context information
            
        Returns:
            Delay in seconds
        """
        retry_config = self.retry_configs.get(
            error_context.error_type.value,
            self.retry_configs["api_error"]
        )
        
        if retry_config.backoff_strategy == "fixed":
            delay = retry_config.base_delay
        
        elif retry_config.backoff_strategy == "linear":
            delay = retry_config.base_delay * (error_context.retry_count + 1)
        
        elif retry_config.backoff_strategy == "exponential":
            delay = retry_config.base_delay * (retry_config.exponential_base ** error_context.retry_count)
        
        else:
            delay = retry_config.base_delay
        
        # Cap delay at maximum
        delay = min(delay, retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if retry_config.jitter:
            import random
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter
        
        return delay
    
    def _is_circuit_closed(self, platform: str) -> bool:
        """Check if circuit breaker is closed (allowing requests)"""
        
        if platform not in self.circuit_breakers:
            return True
        
        circuit = self.circuit_breakers[platform]
        
        if circuit["state"] == "closed":
            return True
        
        elif circuit["state"] == "open":
            # Check if recovery timeout has passed
            if circuit["last_failure"]:
                time_since_failure = (datetime.utcnow() - circuit["last_failure"]).total_seconds()
                if time_since_failure >= circuit["recovery_timeout"]:
                    # Move to half-open state
                    circuit["state"] = "half-open"
                    circuit["success_count"] = 0
                    logger.info(f"Circuit breaker for {platform} moved to half-open state")
                    return True
            return False
        
        elif circuit["state"] == "half-open":
            return True
        
        return False
    
    def record_success(self, platform: str, operation: str):
        """Record successful operation for circuit breaker management"""
        
        if platform not in self.circuit_breakers:
            return
        
        circuit = self.circuit_breakers[platform]
        
        if circuit["state"] == "half-open":
            circuit["success_count"] += 1
            
            if circuit["success_count"] >= circuit["success_threshold"]:
                # Move back to closed state
                circuit["state"] = "closed"
                circuit["failure_count"] = 0
                circuit["success_count"] = 0
                logger.info(f"Circuit breaker for {platform} closed after successful recovery")
        
        elif circuit["state"] == "closed":
            # Reset failure count on success
            circuit["failure_count"] = max(0, circuit["failure_count"] - 1)
    
    def record_failure(self, error_context: ErrorContext):
        """Record failure for circuit breaker and error tracking"""
        
        platform = error_context.platform
        
        # Update circuit breaker
        if platform in self.circuit_breakers:
            circuit = self.circuit_breakers[platform]
            circuit["failure_count"] += 1
            circuit["last_failure"] = datetime.utcnow()
            
            # Check if should open circuit
            if (circuit["state"] == "closed" and 
                circuit["failure_count"] >= circuit["failure_threshold"]):
                circuit["state"] = "open"
                logger.warning(f"Circuit breaker for {platform} opened due to {circuit['failure_count']} failures")
            
            elif circuit["state"] == "half-open":
                # Move back to open state
                circuit["state"] = "open"
                circuit["success_count"] = 0
                logger.warning(f"Circuit breaker for {platform} reopened after failure in half-open state")
        
        # Record error in history
        self.error_history.append(error_context)
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        # Update statistics
        self._update_error_stats(error_context)
    
    def _update_error_stats(self, error_context: ErrorContext):
        """Update error statistics"""
        
        self.error_stats["total_errors"] += 1
        
        # By platform
        platform = error_context.platform
        if platform not in self.error_stats["errors_by_platform"]:
            self.error_stats["errors_by_platform"][platform] = 0
        self.error_stats["errors_by_platform"][platform] += 1
        
        # By type
        error_type = error_context.error_type.value
        if error_type not in self.error_stats["errors_by_type"]:
            self.error_stats["errors_by_type"][error_type] = 0
        self.error_stats["errors_by_type"][error_type] += 1
    
    async def handle_error_with_retry(
        self,
        platform: str,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with comprehensive error handling and retry logic
        
        Args:
            platform: Social media platform
            operation: Operation being performed
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        retry_count = 0
        last_error = None
        
        while True:
            try:
                # Check circuit breaker
                if not self._is_circuit_closed(platform):
                    raise Exception(f"Circuit breaker open for {platform}")
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record success
                self.record_success(platform, operation)
                
                return result
            
            except Exception as error:
                last_error = error
                
                # Classify error
                error_type, severity = self.classify_error(platform, error, operation)
                
                # Create error context
                error_context = ErrorContext(
                    platform=platform,
                    operation=operation,
                    error_type=error_type,
                    severity=severity,
                    original_error=error,
                    retry_count=retry_count,
                    additional_info={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                # Record failure
                self.record_failure(error_context)
                
                # Check if should retry
                if not self.should_retry(error_context):
                    logger.error(f"Not retrying {platform} {operation} after {retry_count} attempts: {error}")
                    raise error
                
                # Calculate delay
                delay = self.calculate_retry_delay(error_context)
                
                logger.warning(f"Retrying {platform} {operation} in {delay:.1f}s (attempt {retry_count + 1}): {error}")
                
                # Wait before retry
                await asyncio.sleep(delay)
                
                retry_count += 1
        
        # This should never be reached, but just in case
        if last_error:
            raise last_error
        else:
            raise Exception(f"Unknown error in {platform} {operation}")
    
    def get_error_summary(self, platform: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the specified time period
        
        Args:
            platform: Specific platform to analyze (optional)
            hours: Number of hours to look back
            
        Returns:
            Error summary statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter errors by time and platform
        relevant_errors = [
            error for error in self.error_history
            if error.timestamp >= cutoff_time and (not platform or error.platform == platform)
        ]
        
        if not relevant_errors:
            return {
                "total_errors": 0,
                "time_period_hours": hours,
                "platform": platform,
                "error_types": {},
                "severity_distribution": {},
                "most_common_operations": {},
                "recovery_rate": 100.0
            }
        
        # Calculate statistics
        error_types = {}
        severity_dist = {}
        operations = {}
        
        for error in relevant_errors:
            # Error types
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Severity distribution
            severity = error.severity.value
            severity_dist[severity] = severity_dist.get(severity, 0) + 1
            
            # Operations
            operation = error.operation
            operations[operation] = operations.get(operation, 0) + 1
        
        # Calculate recovery rate (successful retries)
        total_retries = sum(1 for error in relevant_errors if error.retry_count > 0)
        successful_retries = total_retries  # Simplified calculation
        recovery_rate = (successful_retries / len(relevant_errors) * 100) if relevant_errors else 100.0
        
        return {
            "total_errors": len(relevant_errors),
            "time_period_hours": hours,
            "platform": platform,
            "error_types": dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)),
            "severity_distribution": severity_dist,
            "most_common_operations": dict(sorted(operations.items(), key=lambda x: x[1], reverse=True)[:5]),
            "recovery_rate": round(recovery_rate, 2),
            "circuit_breaker_status": self.circuit_breakers.get(platform, {}).get("state", "closed") if platform else None
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of integrations"""
        
        health_status = {
            "overall_health": "healthy",
            "circuit_breakers": {},
            "error_rates": {},
            "last_24h_summary": {},
            "recommendations": []
        }
        
        # Check circuit breakers
        for platform, circuit in self.circuit_breakers.items():
            health_status["circuit_breakers"][platform] = {
                "state": circuit["state"],
                "failure_count": circuit["failure_count"],
                "last_failure": circuit["last_failure"].isoformat() if circuit["last_failure"] else None
            }
            
            if circuit["state"] != "closed":
                health_status["overall_health"] = "degraded"
                health_status["recommendations"].append(f"Check {platform} integration - circuit breaker {circuit['state']}")
        
        # Get 24-hour error summary
        summary_24h = self.get_error_summary(hours=24)
        health_status["last_24h_summary"] = summary_24h
        
        if summary_24h["total_errors"] > 100:
            health_status["overall_health"] = "degraded"
            health_status["recommendations"].append("High error rate in last 24 hours - investigate most common error types")
        
        return health_status
    
    def reset_circuit_breaker(self, platform: str):
        """Manually reset circuit breaker for a platform"""
        
        if platform in self.circuit_breakers:
            self.circuit_breakers[platform].update({
                "state": "closed",
                "failure_count": 0,
                "success_count": 0,
                "last_failure": None
            })
            logger.info(f"Circuit breaker for {platform} manually reset")
    
    def clear_error_history(self, platform: Optional[str] = None):
        """Clear error history for all platforms or specific platform"""
        
        if platform:
            self.error_history = [
                error for error in self.error_history
                if error.platform != platform
            ]
            logger.info(f"Cleared error history for {platform}")
        else:
            self.error_history.clear()
            logger.info("Cleared all error history")
        
        # Reset statistics
        self.error_stats = {
            "total_errors": 0,
            "errors_by_platform": {},
            "errors_by_type": {},
            "recovery_rate": 0.0,
            "last_reset": datetime.utcnow()
        }


# Global error handler instance
integration_error_handler = IntegrationErrorHandler()


# Decorator for automatic error handling
def handle_integration_errors(platform: str, operation: str):
    """
    Decorator for automatic error handling and retry logic
    
    Args:
        platform: Social media platform
        operation: Operation name
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await integration_error_handler.handle_error_with_retry(
                platform=platform,
                operation=operation,
                func=func,
                *args,
                **kwargs
            )
        return wrapper
    return decorator