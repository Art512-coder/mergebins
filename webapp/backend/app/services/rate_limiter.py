"""
Enhanced Rate Limiting Service for BIN Search Pro API
Implements sliding window rate limiting with Redis backend and memory fallback.
"""

import time
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

import redis
from fastapi import Request, HTTPException, status


class EnhancedRateLimiter:
    """
    Advanced rate limiter with sliding window, progressive penalties,
    and violation tracking.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        # Redis client setup
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                print("✅ Connected to Redis for rate limiting")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}. Using memory fallback.")
                self.redis_client = None
        
        # Memory fallback store
        self.memory_store: Dict[str, Any] = defaultdict(list)
        
        # Rate limit configurations (requests per window in seconds)
        self.rate_limits = {
            "default": {"requests": 60, "window": 60, "burst": 10},
            "bin_lookup": {"requests": 100, "window": 60, "burst": 15},
            "card_generation": {"requests": 20, "window": 60, "burst": 5},
            "crypto_check": {"requests": 30, "window": 60, "burst": 8},
            "auth": {"requests": 10, "window": 300, "burst": 3},  # 5 min window for auth
            "webhook": {"requests": 1000, "window": 60, "burst": 50},  # Higher for webhooks
            "premium": {"requests": 500, "window": 60, "burst": 50}  # Premium users
        }
        
        # Progressive penalty multipliers based on violation count
        self.penalty_multipliers = {
            1: 1.0,    # 1 minute
            2: 2.0,    # 2 minutes
            3: 4.0,    # 4 minutes
            4: 8.0,    # 8 minutes
            5: 16.0    # 16 minutes
        }
    
    def _get_client_identifier(self, request: Request, user_id: Optional[int] = None) -> str:
        """Generate unique identifier for rate limiting."""
        if user_id:
            return f"user:{user_id}"
        
        # Get IP address from various headers
        ip = (
            request.headers.get("cf-connecting-ip") or  # Cloudflare
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip") or
            request.client.host if request.client else "unknown"
        )
        
        # Include user agent hash for additional uniqueness
        user_agent = request.headers.get("user-agent", "")[:50]
        return f"ip:{ip}:ua:{hash(user_agent) % 10000}"
    
    def _get_rate_limit_key(self, identifier: str, action: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"rate_limit:{action}:{identifier}"
    
    def _get_violation_key(self, identifier: str) -> str:
        """Generate Redis key for violation tracking."""
        return f"violations:{identifier}"
    
    def _get_current_usage(self, key: str, window: int) -> Tuple[int, int]:
        """Get current usage count and window start time."""
        now = int(time.time())
        window_start = now - (now % window)
        
        if self.redis_client:
            try:
                # Use Redis sorted set for sliding window
                pipe = self.redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, now - window)
                
                # Count current entries
                pipe.zcard(key)
                
                # Set expiration
                pipe.expire(key, window)
                
                results = pipe.execute()
                current_count = results[1]
                
                return current_count, window_start
            except Exception as e:
                print(f"Redis error in _get_current_usage: {e}")
                return self._memory_get_usage(key, window)
        else:
            return self._memory_get_usage(key, window)
    
    def _memory_get_usage(self, key: str, window: int) -> Tuple[int, int]:
        """Fallback in-memory usage tracking."""
        now = int(time.time())
        window_start = now - (now % window)
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Clean old entries
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key] 
            if timestamp > now - window
        ]
        
        return len(self.memory_store[key]), window_start
    
    def _record_request(self, key: str, window: int) -> None:
        """Record a new request."""
        now = int(time.time())
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                # Add current timestamp to sorted set
                pipe.zadd(key, {str(now): now})
                # Set expiration
                pipe.expire(key, window)
                pipe.execute()
            except Exception as e:
                print(f"Redis error in _record_request: {e}")
                self._memory_record_request(key, now)
        else:
            self._memory_record_request(key, now)
    
    def _memory_record_request(self, key: str, timestamp: int) -> None:
        """Fallback in-memory request recording."""
        if key not in self.memory_store:
            self.memory_store[key] = []
        self.memory_store[key].append(timestamp)
    
    def _get_violation_count(self, identifier: str) -> int:
        """Get current violation count for progressive penalties."""
        violation_key = self._get_violation_key(identifier)
        
        if self.redis_client:
            try:
                count = self.redis_client.get(violation_key)
                return int(count) if count else 0
            except Exception:
                return 0
        else:
            return self.memory_store.get(violation_key, 0)
    
    def _record_violation(self, identifier: str) -> None:
        """Record a rate limit violation for progressive penalties."""
        violation_key = self._get_violation_key(identifier)
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(violation_key)
                pipe.expire(violation_key, 3600)  # Reset violations after 1 hour
                pipe.execute()
            except Exception:
                pass
        else:
            self.memory_store[violation_key] = self.memory_store.get(violation_key, 0) + 1
    
    def _calculate_penalty_delay(self, violation_count: int) -> int:
        """Calculate delay based on violation count."""
        multiplier = self.penalty_multipliers.get(
            min(violation_count, max(self.penalty_multipliers.keys())),
            16.0
        )
        return int(60 * multiplier)  # Base delay of 60 seconds
    
    async def check_rate_limit(
        self, 
        request: Request, 
        action: str, 
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        
        identifier = self._get_client_identifier(request, user_id)
        rate_limit_config = self.rate_limits.get(action, self.rate_limits["default"])
        
        key = self._get_rate_limit_key(identifier, action)
        window = rate_limit_config["window"]
        limit = rate_limit_config["requests"]
        burst = rate_limit_config["burst"]
        
        current_count, window_start = self._get_current_usage(key, window)
        
        # Check for burst limit (short-term spike protection)
        recent_requests = 0
        if self.redis_client:
            try:
                now = int(time.time())
                recent_requests = self.redis_client.zcount(key, now - 60, now)
            except Exception:
                recent_requests = 0
        
        # Check violations and calculate penalty
        violation_count = self._get_violation_count(identifier)
        penalty_delay = self._calculate_penalty_delay(violation_count)
        
        # Rate limit checks
        rate_limited = False
        reason = ""
        
        if current_count >= limit:
            rate_limited = True
            reason = f"Rate limit exceeded: {current_count}/{limit} requests per {window}s"
        elif recent_requests >= burst:
            rate_limited = True
            reason = f"Burst limit exceeded: {recent_requests}/{burst} requests per minute"
        
        if rate_limited:
            self._record_violation(identifier)
            
            # Log security event
            await self._log_rate_limit_violation(request, action, identifier, {
                "current_count": current_count,
                "limit": limit,
                "window": window,
                "violation_count": violation_count + 1,
                "penalty_delay": penalty_delay
            })
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "reason": reason,
                    "retry_after": penalty_delay,
                    "violation_count": violation_count + 1
                },
                headers={
                    "Retry-After": str(penalty_delay),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(max(0, limit - current_count)),
                    "X-RateLimit-Reset": str(window_start + window)
                }
            )
        
        # Record successful request
        self._record_request(key, window)
        
        return {
            "allowed": True,
            "current_count": current_count + 1,
            "limit": limit,
            "window": window,
            "remaining": max(0, limit - current_count - 1),
            "reset_time": window_start + window
        }
    
    async def _log_rate_limit_violation(
        self, 
        request: Request, 
        action: str, 
        identifier: str, 
        details: Dict[str, Any]
    ) -> None:
        """Log rate limit violations for security monitoring."""
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "rate_limit_violation",
                "action": action,
                "identifier": identifier,
                "ip_address": self._get_client_identifier(request).split(":")[1],
                "user_agent": request.headers.get("user-agent", "")[:200],
                "path": str(request.url.path),
                "method": request.method,
                "details": details
            }
            
            # Log to file or external service
            print(f"🚨 Rate Limit Violation: {json.dumps(log_data)}")
            
        except Exception as e:
            print(f"Error logging rate limit violation: {e}")


# Global rate limiter instance
rate_limiter = EnhancedRateLimiter()


# Decorator for easy rate limiting
def rate_limit(action: str):
    """Decorator for applying rate limits to endpoints."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Try to get user_id from request state if available
            user_id = getattr(request.state, 'user_id', None)
            
            # Check rate limit
            await rate_limiter.check_rate_limit(request, action, user_id)
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator