"""
CryptoBinChecker.cc Enhanced FastAPI Application
Main application entry point with all routes and middleware
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from .routes import bins, crypto, health, payments, webhooks

# Create FastAPI application
app = FastAPI(
    title="CryptoBinChecker.cc API",
    description="Enhanced BIN checker and cryptocurrency wallet balance API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "cryptobinchecker-api", "version": "2.0"}

# Include route modules
app.include_router(bins.router, prefix="/api/v1/bin", tags=["BIN Checker"])
app.include_router(crypto.router, prefix="/api/v1/crypto", tags=["Crypto Wallet"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(payments.router, prefix="/api/v1/payment", tags=["Payments"])
app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CryptoBinChecker.cc Enhanced API",
        "version": "2.0",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
