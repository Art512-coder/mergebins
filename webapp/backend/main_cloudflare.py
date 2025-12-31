from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.routes import bins, cards, crypto, webhooks, health  # NEW: crypto, webhooks
from app.services.security_service import SecurityService

# Initialize security service
security_service = SecurityService()

app = FastAPI(
    title="Professional BIN Search & Card Testing API",
    description="Secure API with 458K+ BIN records, card generation, and crypto wallet checking",
    version="2.0.0"
)

# Security middleware - CRITICAL
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """
    Global security middleware that analyzes every request.
    """
    start_time = time.time()
    
    # Skip security for health checks and docs
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    # Analyze request security
    security_analysis = await security_service.analyze_request_security(request)
    
    # Block high-risk requests
    if security_analysis['risk_level'] == 'HIGH':
        await security_service.log_security_event(
            request, 
            "REQUEST_BLOCKED", 
            security_analysis
        )
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied", "code": "SECURITY_BLOCK"}
        )
    
    # Add security headers to response
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Add security metadata to response headers (for debugging)
    if security_analysis['risk_level'] in ['MEDIUM', 'HIGH']:
        response.headers["X-Security-Risk"] = security_analysis['risk_level']
    
    # Log processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers with security
app.include_router(bins.router, prefix="/api/v1/bins", tags=["BIN Lookup"])
app.include_router(cards.router, prefix="/api/v1/cards", tags=["Card Generation"])
app.include_router(crypto.router, prefix="/api/v1/crypto", tags=["Crypto Wallet"])  # NEW
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])  # NEW
app.include_router(health.router, prefix="", tags=["Health"])

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
