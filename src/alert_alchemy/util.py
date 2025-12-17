"""Utility functions for Alert Alchemy."""

import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID.
        
    Returns:
        A unique ID string.
    """
    short_uuid = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}-{short_uuid}"
    return short_uuid


def format_timestamp(iso_timestamp: str) -> str:
    """Format an ISO timestamp for display.
    
    Args:
        iso_timestamp: ISO format timestamp string.
        
    Returns:
        Human-readable timestamp.
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_timestamp


def format_duration(start_iso: str, end_iso: str | None = None) -> str:
    """Format duration between two timestamps.
    
    Args:
        start_iso: Start timestamp in ISO format.
        end_iso: End timestamp in ISO format (defaults to now).
        
    Returns:
        Human-readable duration string.
    """
    try:
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso) if end_iso else datetime.now()
        delta = end - start
        
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except (ValueError, TypeError):
        return "unknown"


def clamp(value: int | float, min_val: int | float, max_val: int | float) -> int | float:
    """Clamp a value between min and max.
    
    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        Clamped value.
    """
    return max(min_val, min(max_val, value))
