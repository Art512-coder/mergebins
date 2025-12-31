#!/usr/bin/env python3
"""
Production Monitoring and Health Check Service
Comprehensive monitoring for BIN Search Bot and API services
"""

import asyncio
import aiohttp
import json
import logging
import os
import psutil
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Comprehensive production monitoring system"""
    
    def __init__(self):
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        self.bot_health_url = "http://localhost:8001/health"
        self.telegram_api_url = "https://api.telegram.org"
        
        # Monitoring configuration
        self.check_interval = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))  # 1 minute
        self.alert_cooldown = int(os.getenv("ALERT_COOLDOWN_MINUTES", "15"))  # 15 minutes
        self.max_response_time = float(os.getenv("MAX_RESPONSE_TIME_SECONDS", "5.0"))  # 5 seconds
        
        # Database for monitoring data
        self.monitor_db_path = Path(__file__).parent.parent.parent / "data" / "monitoring.db"
        self._init_monitor_db()
        
        # Alert configuration
        self.email_alerts = os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true"
        self.webhook_alerts = os.getenv("ENABLE_WEBHOOK_ALERTS", "false").lower() == "true"
        self.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        
        # Service status cache
        self.service_status: Dict[str, Dict] = {}
        self.last_alerts: Dict[str, datetime] = {}
        
    def _init_monitor_db(self):
        """Initialize monitoring database"""
        self.monitor_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.monitor_db_path)
        cursor = conn.cursor()
        
        # Service health history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                details TEXT,
                timestamp TEXT,
                INDEX(service_name, timestamp)
            )
        """)
        
        # System metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_sent INTEGER,
                network_recv INTEGER,
                timestamp TEXT
            )
        """)
        
        # Alerts log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT,
                alert_type TEXT,
                message TEXT,
                severity TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TEXT,
                resolved_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Monitoring database initialized at {self.monitor_db_path}")
    
    async def check_web_api_health(self) -> Tuple[str, float, Dict]:
        """Check web API health"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return "healthy", response_time, data
                        except:
                            # API returned HTML instead of JSON
                            return "degraded", response_time, {"error": "API returning HTML instead of JSON"}
                    else:
                        return "unhealthy", response_time, {"status_code": response.status}
                        
        except asyncio.TimeoutError:
            response_time = asyncio.get_event_loop().time() - start_time
            return "timeout", response_time, {"error": "Request timeout"}
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            return "error", response_time, {"error": str(e)}
    
    async def check_bot_health(self) -> Tuple[str, float, Dict]:
        """Check Telegram bot health"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.bot_health_url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return "healthy", response_time, data
                    else:
                        return "unhealthy", response_time, {"status_code": response.status}
                        
        except aiohttp.ClientConnectorError:
            response_time = asyncio.get_event_loop().time() - start_time
            return "offline", response_time, {"error": "Bot service not responding"}
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            return "error", response_time, {"error": str(e)}
    
    async def check_telegram_api(self) -> Tuple[str, float, Dict]:
        """Check Telegram API connectivity"""
        start_time = asyncio.get_event_loop().time()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            return "error", 0.0, {"error": "No bot token configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.telegram_api_url}/bot{bot_token}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return "healthy", response_time, {"bot_info": data.get("result", {})}
                        else:
                            return "unhealthy", response_time, {"error": data.get("description")}
                    else:
                        return "unhealthy", response_time, {"status_code": response.status}
                        
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            return "error", response_time, {"error": str(e)}
    
    def check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "network_sent_mb": network.bytes_sent / (1024**2),
                "network_recv_mb": network.bytes_recv / (1024**2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {}
    
    def check_service_status(self, service_name: str) -> Dict:
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_active = result.returncode == 0
            status = result.stdout.strip()
            
            # Get detailed status
            detail_result = subprocess.run(
                ["systemctl", "status", service_name, "--no-pager", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "active": is_active,
                "status": status,
                "details": detail_result.stdout,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "active": False,
                "status": "error",
                "details": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def save_health_check(self, service_name: str, status: str, response_time: float, details: Dict):
        """Save health check result to database"""
        conn = sqlite3.connect(self.monitor_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO service_health (service_name, status, response_time, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            service_name, status, response_time, 
            json.dumps(details), datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def save_system_metrics(self, metrics: Dict):
        """Save system metrics to database"""
        if not metrics:
            return
            
        conn = sqlite3.connect(self.monitor_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_metrics 
            (cpu_percent, memory_percent, disk_percent, network_sent, network_recv, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            metrics.get("cpu_percent", 0),
            metrics.get("memory_percent", 0),
            metrics.get("disk_percent", 0),
            metrics.get("network_sent_mb", 0),
            metrics.get("network_recv_mb", 0),
            metrics.get("timestamp")
        ))
        
        conn.commit()
        conn.close()
    
    async def send_alert(self, service_name: str, alert_type: str, message: str, severity: str = "warning"):
        """Send alert via configured channels"""
        # Check cooldown
        alert_key = f"{service_name}_{alert_type}"
        last_alert = self.last_alerts.get(alert_key)
        
        if last_alert and (datetime.utcnow() - last_alert).total_seconds() < (self.alert_cooldown * 60):
            return  # Still in cooldown
        
        self.last_alerts[alert_key] = datetime.utcnow()
        
        # Log alert
        conn = sqlite3.connect(self.monitor_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (service_name, alert_type, message, severity, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, alert_type, message, severity, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        
        logger.warning(f"ALERT [{severity.upper()}] {service_name}: {message}")
        
        # Send webhook alert
        if self.webhook_alerts and self.alert_webhook_url:
            await self._send_webhook_alert(service_name, alert_type, message, severity)
    
    async def _send_webhook_alert(self, service_name: str, alert_type: str, message: str, severity: str):
        """Send webhook alert"""
        try:
            payload = {
                "service": service_name,
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.alert_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for {service_name}")
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Webhook alert error: {e}")
    
    async def run_health_checks(self):
        """Run all health checks"""
        timestamp = datetime.utcnow().isoformat()
        
        # Check Web API
        api_status, api_time, api_details = await self.check_web_api_health()
        self.save_health_check("web_api", api_status, api_time, api_details)
        
        if api_status == "unhealthy" or api_time > self.max_response_time:
            await self.send_alert("web_api", "health_check", 
                                f"Web API is {api_status} (response time: {api_time:.2f}s)", "critical")
        
        # Check Bot Health
        bot_status, bot_time, bot_details = await self.check_bot_health()
        self.save_health_check("telegram_bot", bot_status, bot_time, bot_details)
        
        if bot_status == "offline":
            await self.send_alert("telegram_bot", "health_check", 
                                "Telegram bot is offline", "critical")
        elif bot_status == "unhealthy":
            await self.send_alert("telegram_bot", "health_check", 
                                f"Telegram bot is unhealthy: {bot_details}", "warning")
        
        # Check Telegram API
        tg_status, tg_time, tg_details = await self.check_telegram_api()
        self.save_health_check("telegram_api", tg_status, tg_time, tg_details)
        
        if tg_status != "healthy":
            await self.send_alert("telegram_api", "connectivity", 
                                f"Telegram API connectivity issue: {tg_details}", "warning")
        
        # Check System Resources
        system_metrics = self.check_system_resources()
        if system_metrics:
            self.save_system_metrics(system_metrics)
            
            # Check for resource alerts
            if system_metrics.get("cpu_percent", 0) > 90:
                await self.send_alert("system", "cpu", 
                                    f"High CPU usage: {system_metrics['cpu_percent']:.1f}%", "warning")
            
            if system_metrics.get("memory_percent", 0) > 90:
                await self.send_alert("system", "memory", 
                                    f"High memory usage: {system_metrics['memory_percent']:.1f}%", "warning")
            
            if system_metrics.get("disk_percent", 0) > 85:
                await self.send_alert("system", "disk", 
                                    f"High disk usage: {system_metrics['disk_percent']:.1f}%", "warning")
        
        # Check Service Status
        service_status = self.check_service_status("binsearch-bot")
        if not service_status.get("active", False):
            await self.send_alert("binsearch-bot", "service", 
                                "Bot service is not active", "critical")
        
        # Update service status cache
        self.service_status = {
            "web_api": {"status": api_status, "response_time": api_time, "details": api_details},
            "telegram_bot": {"status": bot_status, "response_time": bot_time, "details": bot_details},
            "telegram_api": {"status": tg_status, "response_time": tg_time, "details": tg_details},
            "system": system_metrics,
            "service": service_status,
            "last_check": timestamp
        }
        
        logger.info(f"Health checks completed - API: {api_status}, Bot: {bot_status}, System: OK")
    
    def get_health_summary(self) -> Dict:
        """Get current health summary"""
        return {
            "overall_status": self._calculate_overall_status(),
            "services": self.service_status,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system status"""
        if not self.service_status:
            return "unknown"
        
        critical_services = ["web_api", "telegram_bot"]
        
        for service in critical_services:
            service_data = self.service_status.get(service, {})
            status = service_data.get("status", "unknown")
            
            if status in ["offline", "error", "unhealthy"]:
                return "critical"
            elif status in ["degraded", "timeout"]:
                return "degraded"
        
        return "healthy"
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        logger.info("🔍 Starting production monitoring service")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Alert cooldown: {self.alert_cooldown} minutes")
        
        while True:
            try:
                await self.run_health_checks()
                
                # Clean up old data (older than 30 days)
                cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
                conn = sqlite3.connect(self.monitor_db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM service_health WHERE timestamp < ?", (cutoff_date,))
                cursor.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_date,))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await self.send_alert("monitor", "error", f"Monitoring service error: {e}", "warning")
            
            await asyncio.sleep(self.check_interval)

# CLI interface
async def main():
    """Main monitoring service entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BIN Search Bot Production Monitor")
    parser.add_argument("--check", action="store_true", help="Run single health check")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--daemon", action="store_true", help="Run as monitoring daemon")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('monitoring.log'),
            logging.StreamHandler()
        ]
    )
    
    monitor = ProductionMonitor()
    
    if args.check:
        print("Running health check...")
        await monitor.run_health_checks()
        summary = monitor.get_health_summary()
        print(json.dumps(summary, indent=2))
        
    elif args.status:
        summary = monitor.get_health_summary()
        print(json.dumps(summary, indent=2))
        
    elif args.daemon:
        print("Starting monitoring daemon...")
        await monitor.start_monitoring()
        
    else:
        # Default: single check
        await monitor.run_health_checks()
        summary = monitor.get_health_summary()
        print(f"Overall Status: {summary['overall_status'].upper()}")

if __name__ == "__main__":
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    asyncio.run(main())