"""
IP-based rate limiting utilities for anonymous users
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import redis
import json
from app.database import get_redis

class IPRateLimit:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or get_redis()
        
    def check_ip_limit(self, ip_address: str, action: str, limit: int, window_hours: int = 24) -> tuple[bool, int]:
        """
        Check if an IP address has exceeded the rate limit for a specific action.
        
        Args:
            ip_address: The client IP address
            action: The action being rate limited (e.g., 'cc_generation')
            limit: Maximum allowed actions within the window
            window_hours: Time window in hours (default 24)
            
        Returns:
            tuple[bool, int]: (is_allowed, remaining_count)
        """
        try:
            key = f"ip_limit:{ip_address}:{action}"
            current_time = datetime.now(timezone.utc)
            
            # Get current usage data
            usage_data = self.redis_client.get(key)
            
            if not usage_data:
                # First time usage
                usage = {
                    'count': 0,
                    'reset_time': (current_time + timedelta(hours=window_hours)).isoformat()
                }
            else:
                usage = json.loads(usage_data)
                reset_time = datetime.fromisoformat(usage['reset_time'])
                
                # Check if window has expired
                if current_time >= reset_time:
                    usage = {
                        'count': 0,
                        'reset_time': (current_time + timedelta(hours=window_hours)).isoformat()
                    }
            
            # Check if limit exceeded
            if usage['count'] >= limit:
                return False, 0
            
            return True, limit - usage['count']
            
        except Exception as e:
            # If Redis fails, allow the request (fail open)
            print(f"Redis error in IP rate limiting: {e}")
            return True, limit
    
    def increment_ip_usage(self, ip_address: str, action: str, window_hours: int = 24):
        """
        Increment the usage count for an IP address and action.
        """
        try:
            key = f"ip_limit:{ip_address}:{action}"
            current_time = datetime.now(timezone.utc)
            
            # Get current usage data
            usage_data = self.redis_client.get(key)
            
            if not usage_data:
                # First time usage
                usage = {
                    'count': 1,
                    'reset_time': (current_time + timedelta(hours=window_hours)).isoformat()
                }
            else:
                usage = json.loads(usage_data)
                reset_time = datetime.fromisoformat(usage['reset_time'])
                
                # Check if window has expired
                if current_time >= reset_time:
                    usage = {
                        'count': 1,
                        'reset_time': (current_time + timedelta(hours=window_hours)).isoformat()
                    }
                else:
                    usage['count'] += 1
            
            # Store updated usage with expiration
            expire_seconds = int(window_hours * 3600)
            self.redis_client.setex(key, expire_seconds, json.dumps(usage))
            
        except Exception as e:
            # If Redis fails, continue silently
            print(f"Redis error in IP usage increment: {e}")
    
    def get_ip_usage_info(self, ip_address: str, action: str) -> Dict:
        """
        Get current usage information for an IP address.
        """
        try:
            key = f"ip_limit:{ip_address}:{action}"
            usage_data = self.redis_client.get(key)
            
            if not usage_data:
                return {
                    'count': 0,
                    'reset_time': None,
                    'remaining': None
                }
            
            usage = json.loads(usage_data)
            reset_time = datetime.fromisoformat(usage['reset_time'])
            current_time = datetime.now(timezone.utc)
            
            # Check if window has expired
            if current_time >= reset_time:
                return {
                    'count': 0,
                    'reset_time': None,
                    'remaining': None
                }
            
            return {
                'count': usage['count'],
                'reset_time': reset_time.isoformat(),
                'time_until_reset': str(reset_time - current_time)
            }
            
        except Exception as e:
            print(f"Redis error getting IP usage info: {e}")
            return {
                'count': 0,
                'reset_time': None,
                'remaining': None,
                'error': str(e)
            }

# Global instance
ip_rate_limiter = IPRateLimit()
