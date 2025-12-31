from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check environment for minimal mode
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "minimal":
    # Minimal setup
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional

    app = FastAPI(title="BIN Search API - Minimal")

    # Enable CORS for all origins (development only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    class UserRegister(BaseModel):
        username: str
        email: str
        password: str

    class UserResponse(BaseModel):
        id: int
        username: str
        email: str
        plan: str

    class AuthResponse(BaseModel):
        access_token: str
        token_type: str
        user: UserResponse

    @app.get("/")
    async def root():
        return {"message": "BIN Search API - Minimal Version for Testing"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "bin-search-api"}

    @app.post("/api/v1/auth/register", response_model=AuthResponse)
    async def register(user_data: UserRegister):
        # Mock registration for testing
        mock_user = UserResponse(
            id=1,
            username=user_data.username,
            email=user_data.email,
            plan="free"
        )
        return AuthResponse(
            access_token="mock_token",
            token_type="bearer",
            user=mock_user
        )

else:
    # Full setup
    # Add parent directory to path for enhanced_monitoring
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../..')

    from app.routes import bins, cards, crypto, webhooks, health, auth  # NEW: crypto, webhooks, auth
    from app.routes import health_enhanced  # Enhanced health monitoring
    from app.services.security_service import SecurityService
    from app.services.rate_limiter import rate_limiter

    # Initialize enhanced monitoring
    try:
        from enhanced_monitoring import error_tracker, handle_errors
        monitoring_enabled = True
        print("✅ Enhanced monitoring initialized")
    except ImportError as e:
        print(f"⚠️ Enhanced monitoring not available: {e}")
        monitoring_enabled = False
        error_tracker = None

    # Initialize security service
    security_service = SecurityService()

    app = FastAPI(
        title="Professional BIN Search & Card Testing API",
        description="Secure API with 458K+ BIN records, card generation, and crypto wallet checking",
        version="2.0.0"
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with enhanced error tracking"""
        if monitoring_enabled and error_tracker:
            error_tracker.log_api_error(request, exc)
        
        # Log the error
        logging.error(f"Global exception caught: {exc}", exc_info=True)
        
        # Return appropriate error response
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail}
            )
        
        # For unhandled exceptions, return generic error in production
        if os.getenv("DEBUG", "True").lower() == "true":
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc),
                    "type": exc.__class__.__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )

    # Security middleware - CRITICAL
    ALLOWED_ORIGINS = [
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
        if origin.strip()  # Remove empty strings
    ]
    
    # Add production domain if specified
    PRODUCTION_URL = os.getenv("PRODUCTION_URL")
    if PRODUCTION_URL:
        ALLOWED_ORIGINS.append(PRODUCTION_URL)
    
    # Development mode - more permissive CORS
    if os.getenv("DEBUG", "True").lower() == "true":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins in development
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
            max_age=3600,
        )
    else:
        # Production - restrictive CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "X-CSRF-Token"],
            max_age=3600,
        )
    
    # Add trusted host middleware for additional security
    ALLOWED_HOSTS = [
        host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    ]
    
    # Add production hosts if specified
    if os.getenv("PRODUCTION_DOMAIN"):
        ALLOWED_HOSTS.append(os.getenv("PRODUCTION_DOMAIN"))
    
    # Add testserver for testing
    ALLOWED_HOSTS.append("testserver")
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=ALLOWED_HOSTS
    )
    
    # CSRF Protection Middleware (disabled in development)
    @app.middleware("http")
    async def csrf_protection_middleware(request: Request, call_next):
        """
        CSRF protection for state-changing operations.
        """
        # Skip CSRF in development mode
        if os.getenv("DEBUG", "True").lower() == "true":
            response = await call_next(request)
            return response
        
        # Skip CSRF for GET, HEAD, OPTIONS, and API docs
        if request.method in ["GET", "HEAD", "OPTIONS"] or request.url.path in ["/docs", "/openapi.json", "/health"]:
            response = await call_next(request)
            return response
        
        # Skip CSRF for API endpoints with Bearer tokens (already secured)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            response = await call_next(request)
            return response
        
        # For other state-changing requests, check CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=403,
                content={"error": "CSRF token required", "code": "CSRF_TOKEN_MISSING"}
            )
        
        # Validate CSRF token (implement proper validation in production)
        # For now, just check it's not empty - implement proper CSRF validation
        response = await call_next(request)
        return response
    
    # CSRF Token Generation Endpoint
    @app.get("/api/csrf-token")
    async def get_csrf_token():
        """Generate CSRF token for client-side requests."""
        csrf_token = secrets.token_urlsafe(32)
        return {"csrf_token": csrf_token}
    
    # Include routers with security
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(bins.router, prefix="/api/v1/bins", tags=["BIN Lookup"])
    app.include_router(cards.router, prefix="/api", tags=["Card Generation"])
    app.include_router(crypto.router, prefix="/api/v1/crypto", tags=["Crypto Wallet"])  # NEW
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])  # NEW
    app.include_router(health.router, prefix="", tags=["Health"])
    app.include_router(health_enhanced.router, prefix="/api/v1", tags=["Enhanced Monitoring"])  # Enhanced health checks
    
    @app.get("/")
    async def root():
        return {
            "service": "Professional BIN Search & Card Testing API",
            "version": "2.0.0",
            "features": [
                "458,051+ BIN records (world's largest free database)",
                "Secure card generation with IP rate limiting",
                "Crypto wallet balance checking (Bitcoin, Ethereum)",
                "Advanced security & fraud detection",
                "Webhook payment processing",
                "Premium tier with advanced features"
            ],
            "security": [
                "Bot detection & IP risk analysis",
                "Rate limiting & abuse prevention", 
                "Webhook signature verification",
                "Real-time threat monitoring"
            ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
