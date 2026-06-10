"""Helper utilities"""
from datetime import datetime

def format_timestamp(timestamp):
    """Format timestamp"""
    if isinstance(timestamp, datetime):
        return timestamp.isoformat()
    if timestamp is None:
        return ""
    return str(timestamp)
