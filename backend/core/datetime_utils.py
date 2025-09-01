"""
Utility functions for handling datetime operations with timezone awareness.
Replaces deprecated datetime.utcnow() usage.
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time using timezone-aware datetime.
    
    Replaces deprecated datetime.utcnow() with datetime.now(timezone.utc).
    
    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """
    Get current UTC time as ISO string.
    
    Returns:
        Current UTC datetime as ISO format string
    """
    return utc_now().isoformat()


def utc_timestamp() -> int:
    """
    Get current UTC timestamp.
    
    Returns:
        Current UTC timestamp as integer
    """
    return int(utc_now().timestamp())