import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
from functools import wraps

# Get logger
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Class to manage API rate limiting
    """
    
    def __init__(self, calls_per_minute: int = 1):
        """
        Initialize RateLimiter
        
        Parameters:
        - calls_per_minute: Maximum number of calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # Minimum interval between calls in seconds
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """
        Wait if needed to respect rate limits
        """
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        # If less than the minimum interval has passed, wait
        if elapsed < self.min_interval and self.last_call_time > 0:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: Waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        # Update last call time
        self.last_call_time = time.time()

def rate_limited(calls_per_minute: int = 1):
    """
    Decorator for rate-limited functions
    
    Parameters:
    - calls_per_minute: Maximum number of calls allowed per minute
    
    Returns:
    - Decorated function
    """
    # Create a rate limiter for this function
    limiter = RateLimiter(calls_per_minute)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Apply rate limiting
            limiter.wait_if_needed()
            
            # Call the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class ApiQuota:
    """
    Class to track and manage API quota usage
    """
    
    def __init__(self, name: str, total: int, reset_interval_days: int = 30):
        """
        Initialize ApiQuota
        
        Parameters:
        - name: Name of the API
        - total: Total quota available
        - reset_interval_days: Days after which the quota resets
        """
        self.name = name
        self.total = total
        self.used = 0
        self.reset_interval = timedelta(days=reset_interval_days)
        self.last_reset = datetime.now()
    
    def use(self, amount: int = 1) -> bool:
        """
        Use some of the quota
        
        Parameters:
        - amount: Amount of quota to use
        
        Returns:
        - Boolean indicating if the quota was available
        """
        # Check if we need to reset
        if datetime.now() - self.last_reset > self.reset_interval:
            self.reset()
        
        # Check if we have enough quota
        if self.used + amount > self.total:
            logger.warning(f"{self.name} API quota exceeded: {self.used}/{self.total}")
            return False
        
        # Use the quota
        self.used += amount
        logger.debug(f"Used {amount} {self.name} API credits, {self.used}/{self.total} total")
        return True
    
    def reset(self):
        """Reset the quota"""
        self.used = 0
        self.last_reset = datetime.now()
        logger.info(f"Reset {self.name} API quota")
    
    def remaining(self) -> int:
        """
        Get the remaining quota
        
        Returns:
        - Remaining quota
        """
        # Check if we need to reset
        if datetime.now() - self.last_reset > self.reset_interval:
            self.reset()
        
        return self.total - self.used
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current quota status
        
        Returns:
        - Dictionary with quota status
        """
        # Check if we need to reset
        if datetime.now() - self.last_reset > self.reset_interval:
            self.reset()
        
        return {
            "name": self.name,
            "total": self.total,
            "used": self.used,
            "remaining": self.total - self.used,
            "last_reset": self.last_reset.isoformat(),
            "next_reset": (self.last_reset + self.reset_interval).isoformat()
        }
