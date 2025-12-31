#!/usr/bin/env python3
"""
Health Check Endpoint for BIN Search Bot
Provides health status for load balancers and monitoring systems
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from aiohttp import web, ClientSession
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class HealthCheckServer:
    """HTTP server providing health check endpoints"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        
    async def health_check(self, request):
        """Basic health check endpoint"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        health_data = {
            "status": "healthy",
            "service": "bin-search-bot",
            "version": "1.0.0",
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.utcnow().isoformat(),
            "bot_info": {
                "name": "BIN Search Bot",
                "users": "458000+",
                "features": ["BIN lookup", "Card generation", "Premium features"]
            }
        }
        
        return web.json_response(health_data)
    
    async def ready_check(self, request):
        """Readiness check - validates all dependencies"""
        checks = {
            "bot_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "web_api": await self._check_web_api(),
            "database": self._check_database(),
        }
        
        all_ready = all(checks.values())
        status_code = 200 if all_ready else 503
        
        response_data = {
            "status": "ready" if all_ready else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return web.json_response(response_data, status=status_code)
    
    async def live_check(self, request):
        """Liveness check - basic service responsiveness"""
        return web.json_response({
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def metrics(self, request):
        """Prometheus-style metrics endpoint"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        metrics_text = f"""# HELP bot_uptime_seconds Total uptime of the bot
# TYPE bot_uptime_seconds counter
bot_uptime_seconds {uptime_seconds}

# HELP bot_status Bot status (1 = healthy, 0 = unhealthy)  
# TYPE bot_status gauge
bot_status 1

# HELP bot_info Bot information
# TYPE bot_info gauge
bot_info{{name="BIN Search Bot",version="1.0.0"}} 1
"""
        
        return web.Response(text=metrics_text, content_type="text/plain")
    
    async def _check_web_api(self) -> bool:
        """Check if web API is accessible"""
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/health",
                    timeout=5
                ) as response:
                    return response.status in [200, 404]  # 404 is acceptable for health endpoint
        except:
            return False
    
    def _check_database(self) -> bool:
        """Check if local database files exist"""
        data_dir = Path(__file__).parent.parent / "data"
        return (data_dir / "merged_bin_data.csv").exists()
    
    async def create_app(self):
        """Create the web application"""
        app = web.Application()
        
        # Health check routes
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/ready', self.ready_check)
        app.router.add_get('/live', self.live_check)
        app.router.add_get('/metrics', self.metrics)
        
        # CORS headers for monitoring tools
        async def add_cors_headers(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        app.middlewares.append(add_cors_headers)
        
        return app

async def start_health_server():
    """Start the health check server"""
    port = int(os.getenv("HEALTH_CHECK_PORT", "8001"))
    
    health_server = HealthCheckServer()
    app = await health_server.create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🏥 Health check server started on port {port}")
    logger.info(f"Health endpoints available:")
    logger.info(f"  - http://localhost:{port}/health")
    logger.info(f"  - http://localhost:{port}/ready") 
    logger.info(f"  - http://localhost:{port}/live")
    logger.info(f"  - http://localhost:{port}/metrics")
    
    return runner

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        runner = await start_health_server()
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except KeyboardInterrupt:
            logger.info("Shutting down health check server...")
        finally:
            await runner.cleanup()
    
    asyncio.run(main())