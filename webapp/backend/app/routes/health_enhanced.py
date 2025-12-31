"""
Enhanced Health Check Routes
Provides comprehensive system status and monitoring endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import psutil
import os
import json

from app.database import get_db, get_redis
from enhanced_monitoring import health_monitor, error_tracker

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str = "2.0.0"
    uptime: float
    services: Dict[str, Any]

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int

class ErrorSummary(BaseModel):
    last_24h: int
    last_hour: int
    critical_errors: List[str]

# Store startup time for uptime calculation
startup_time = datetime.now(timezone.utc)

@router.get("/health", response_model=HealthStatus)
async def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    Returns overall system status and service health
    """
    try:
        current_time = datetime.now(timezone.utc)
        uptime = (current_time - startup_time).total_seconds()
        
        # Check database health
        db_health = health_monitor.check_database_health(db)
        
        # Check Redis health (if available)
        redis_client = get_redis()
        redis_health = {"status": "not_configured"}
        if redis_client:
            try:
                redis_client.ping()
                redis_health = {"status": "healthy"}
            except Exception as e:
                redis_health = {"status": "unhealthy", "error": str(e)}
        
        # Check external services
        external_services = health_monitor.check_external_services()
        
        # Overall status determination
        critical_services = ['database']
        overall_status = "healthy"
        
        if db_health['status'] != 'healthy':
            overall_status = "unhealthy"
        elif any(service['status'] == 'unhealthy' for service in external_services.values()):
            overall_status = "degraded"
        
        services = {
            "database": db_health,
            "redis": redis_health,
            "external_services": external_services
        }
        
        return HealthStatus(
            status=overall_status,
            timestamp=current_time.isoformat(),
            uptime=uptime,
            services=services
        )
        
    except Exception as e:
        error_tracker.log_api_error(request, e)
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(request: Request, db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics and error summaries
    """
    try:
        # Get basic health status
        basic_health = await health_check(request, db)
        
        # System metrics
        system_metrics = SystemMetrics(
            cpu_usage=psutil.cpu_percent(interval=1),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            active_connections=len(psutil.net_connections())
        )
        
        # Database statistics
        try:
            bin_count = db.execute("SELECT COUNT(*) FROM bin_data").scalar()
            user_count = db.execute("SELECT COUNT(*) FROM users").scalar()
            subscription_count = db.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'").scalar()
            
            database_stats = {
                "bin_records": bin_count,
                "total_users": user_count,
                "active_subscriptions": subscription_count
            }
        except Exception as e:
            database_stats = {"error": str(e)}
        
        # API endpoint checks
        api_health = health_monitor.check_api_endpoints()
        
        # Error summary (mock - in production, read from logs/database)
        error_summary = ErrorSummary(
            last_24h=0,  # Would be calculated from error logs
            last_hour=0,  # Would be calculated from error logs
            critical_errors=[]  # Would be extracted from error logs
        )
        
        return {
            "basic_health": basic_health.dict(),
            "system_metrics": system_metrics.dict(),
            "database_stats": database_stats,
            "api_endpoints": api_health,
            "error_summary": error_summary.dict(),
            "environment": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
                "timezone": str(datetime.now(timezone.utc).astimezone().tzinfo)
            }
        }
        
    except Exception as e:
        error_tracker.log_api_error(request, e)
        raise HTTPException(status_code=500, detail="Detailed health check failed")

@router.get("/health/database")
async def database_health(db: Session = Depends(get_db)):
    """Specific database health check"""
    return health_monitor.check_database_health(db)

@router.get("/health/external-services")
async def external_services_health():
    """Check status of external service dependencies"""
    return health_monitor.check_external_services()

@router.post("/health/test-error")
async def test_error_handling(request: Request):
    """Test endpoint for error handling (development only)"""
    if os.getenv("DEBUG", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Test endpoints only available in debug mode")
    
    try:
        # Intentionally raise an error to test error handling
        raise ValueError("Test error for monitoring system")
    except Exception as e:
        error_tracker.log_api_error(request, e, context={"test": True})
        return {"message": "Error logged successfully", "error": str(e)}

@router.get("/health/logs")
async def get_recent_logs(lines: int = 100):
    """Get recent log entries (development only)"""
    if os.getenv("DEBUG", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Log endpoints only available in debug mode")
    
    try:
        log_files = ['logs/application.log', 'logs/errors.log']
        logs = {}
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_lines = f.readlines()
                    logs[log_file] = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        return logs
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        metrics = []
        
        # System metrics
        metrics.append(f"system_cpu_usage {psutil.cpu_percent()}")
        metrics.append(f"system_memory_usage {psutil.virtual_memory().percent}")
        metrics.append(f"system_disk_usage {psutil.disk_usage('/').percent}")
        
        # Application metrics (these would be tracked in a real application)
        metrics.append(f"api_requests_total 0")  # Would be tracked
        metrics.append(f"api_errors_total 0")    # Would be tracked
        metrics.append(f"payment_transactions_total 0")  # Would be tracked
        
        # Uptime
        uptime = (datetime.now(timezone.utc) - startup_time).total_seconds()
        metrics.append(f"application_uptime_seconds {uptime}")
        
        return {"metrics": "\\n".join(metrics)}
        
    except Exception as e:
        return {"error": str(e)}