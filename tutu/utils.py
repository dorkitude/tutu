from datetime import datetime
import pytz

PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

def format_relative_time(dt: datetime) -> str:
    """Convert a datetime to a relative time string like '5 minutes ago'"""
    if dt.tzinfo is None:
        # Assume it's in Pacific time if no timezone info
        dt = PACIFIC_TZ.localize(dt)
    
    # Get current time in Pacific timezone
    now = datetime.now(PACIFIC_TZ)
    
    # Calculate the time difference
    diff = now - dt
    
    # Total seconds difference
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:
        seconds = int(total_seconds)
        if seconds == 1:
            return "1 second ago"
        return f"{seconds} seconds ago"
    
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds / 60)
        if minutes == 1:
            return "1 minute ago"
        return f"{minutes} minutes ago"
    
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds / 3600)
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"
    
    else:  # Days
        days = int(total_seconds / 86400)
        if days == 1:
            return "1 day ago"
        return f"{days} days ago"