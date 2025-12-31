"""
Security Middleware for FastAPI
Intercepts all requests and applies security analysis
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import json
from typing import Callable

from app.services.security_service import security_service
from app.database import get_db
from app.models import User
from app.utils.security import get_user_from_token

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware that applies security analysis to all requests"""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", "/health", 
            "/favicon.ico", "/static/", "/.well-known/"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)
        
        # Skip security checks for certain paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Get user context if available
            user = None
            try:
                authorization = request.headers.get("authorization")
                if authorization and authorization.startswith("Bearer "):
                    token = authorization.split(" ")[1]
                    user = await get_user_from_token(token)
            except Exception:
                pass  # User not authenticated, continue with anonymous analysis
            
            # Perform security analysis
            risk_analysis = await security_service.analyze_request_risk(request, user)
            
            # Log security event
            await security_service.log_security_event(
                event_type="REQUEST_ANALYSIS",
                risk_analysis=risk_analysis,
                user_id=user.id if user else None
            )
            
            # Increment request counters
            await security_service.increment_ip_requests(risk_analysis["client_ip"])
            
            # Block high-risk requests
            if await security_service.should_block_request(risk_analysis):
                await self._log_blocked_request(request, risk_analysis, user)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Request blocked due to security policy",
                        "risk_level": risk_analysis["risk_level"],
                        "message": "Your request has been identified as high-risk. Please contact support if you believe this is an error."
                    }
                )
            
            # Add challenge for medium-risk requests
            if risk_analysis["requires_verification"] and not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Authentication required",
                        "message": "Please authenticate to access this resource.",
                        "risk_level": risk_analysis["risk_level"]
                    }
                )
            
            # Add security headers to request
            request.state.security_analysis = risk_analysis
            request.state.risk_score = risk_analysis["risk_score"]
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers to response
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY" 
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Risk-Score"] = str(risk_analysis["risk_score"])
            
            # Log processing time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log security middleware errors
            await security_service.log_security_event(
                event_type="MIDDLEWARE_ERROR",
                risk_analysis={"error": str(e), "risk_score": 0, "client_ip": request.client.host},
                user_id=user.id if user else None
            )
            
            # Continue processing even if security analysis fails
            return await call_next(request)
    
    async def _log_blocked_request(self, request: Request, risk_analysis: dict, user: User = None):
        """Log details of blocked requests for analysis"""
        blocked_request_data = {
            "timestamp": time.time(),
            "ip": risk_analysis["client_ip"],
            "user_agent": risk_analysis.get("user_agent", ""),
            "path": request.url.path,
            "method": request.method,
            "risk_score": risk_analysis["risk_score"],
            "risk_factors": risk_analysis["risk_factors"],
            "user_id": user.id if user else None,
            "headers": dict(request.headers)
        }
        
        # Store blocked request data
        await security_service.log_security_event(
            event_type="REQUEST_BLOCKED",
            risk_analysis=blocked_request_data,
            user_id=user.id if user else None
        )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Additional rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {
            "/api/bins/lookup": {"requests": 60, "window": 60},  # 60 requests per minute for BIN lookup
            "/api/generate": {"requests": 10, "window": 60},  # 10 per minute for card generation  
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 login attempts per 5 minutes
            "/api/auth/register": {"requests": 3, "window": 3600},  # 3 registrations per hour
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this endpoint has specific rate limits
        endpoint_limit = None
        for path, limit in self.rate_limits.items():
            if request.url.path.startswith(path):
                endpoint_limit = limit
                break
        
        if endpoint_limit:
            client_ip = self._get_client_ip(request)
            rate_key = f"rate_limit:{request.url.path}:{client_ip}"
            
            # Check current request count
            current_requests = await security_service.redis.get(rate_key)
            current_requests = int(current_requests) if current_requests else 0
            
            if current_requests >= endpoint_limit["requests"]:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {endpoint_limit['requests']} per {endpoint_limit['window']} seconds"
                    }
                )
            
            # Increment counter
            await security_service.redis.incr(rate_key)
            await security_service.redis.expire(rate_key, endpoint_limit["window"])
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host
