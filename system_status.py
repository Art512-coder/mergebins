#!/usr/bin/env python3
"""
System Status Dashboard
Provides a comprehensive overview of system health and performance
"""
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

class StatusDashboard:
    """System status dashboard for monitoring all components"""
    
    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.telegram_status = "unknown"
        
    def check_web_api(self) -> Dict[str, Any]:
        """Check web API status"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health information"""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/health/detailed", timeout=15)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {"error": str(e)}
    
    def check_database_status(self) -> Dict[str, Any]:
        """Check database status"""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/health/database", timeout=10)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {"error": str(e)}
    
    def check_external_services(self) -> Dict[str, Any]:
        """Check external services status"""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/health/external-services", timeout=15)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            return {"error": str(e)}
    
    def check_telegram_bot(self) -> Dict[str, Any]:
        """Check if Telegram bot is running"""
        # This would need to be implemented based on your monitoring setup
        # For now, check if the process is running
        try:
            import psutil
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'telegram_bot.py' in ' '.join(process.info['cmdline'] or []):
                    return {"status": "running", "pid": process.info['pid']}
            return {"status": "not_running"}
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        print("🔍 Checking system status...")
        
        # Check all components
        web_api = self.check_web_api()
        detailed_health = self.check_detailed_health()
        database = self.check_database_status()
        external_services = self.check_external_services()
        telegram_bot = self.check_telegram_bot()
        
        # Calculate overall status
        critical_services_healthy = (
            web_api.get("status") == "healthy" and
            database.get("status") == "healthy"
        )
        
        overall_status = "healthy" if critical_services_healthy else "unhealthy"
        
        if overall_status == "healthy" and any(
            service.get("status") == "unhealthy" 
            for service in external_services.values()
        ):
            overall_status = "degraded"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "components": {
                "web_api": web_api,
                "database": database,
                "telegram_bot": telegram_bot,
                "external_services": external_services
            },
            "detailed_metrics": detailed_health
        }
    
    def print_status_report(self):
        """Print formatted status report to console"""
        report = self.generate_report()
        
        print("\\n" + "="*50)
        print("🏥 CRYPTOBINCHECKER SYSTEM STATUS")
        print("="*50)
        print(f"📅 Timestamp: {report['timestamp']}")
        print(f"🎯 Overall Status: {self.get_status_emoji(report['overall_status'])} {report['overall_status'].upper()}")
        
        print("\\n📊 COMPONENT STATUS:")
        print("-" * 30)
        
        components = report["components"]
        
        # Web API
        web_status = components["web_api"]
        print(f"🌐 Web API: {self.get_status_emoji(web_status.get('status', 'unknown'))} {web_status.get('status', 'unknown').upper()}")
        if "response_time" in web_status:
            print(f"   Response Time: {web_status['response_time']:.3f}s")
        
        # Database
        db_status = components["database"]
        print(f"🗄️  Database: {self.get_status_emoji(db_status.get('status', 'unknown'))} {db_status.get('status', 'unknown').upper()}")
        if "response_time" in db_status:
            print(f"   Response Time: {db_status['response_time']:.3f}s")
        
        # Telegram Bot
        tg_status = components["telegram_bot"]
        print(f"🤖 Telegram Bot: {self.get_status_emoji(tg_status.get('status', 'unknown'))} {tg_status.get('status', 'unknown').upper()}")
        if "pid" in tg_status:
            print(f"   Process ID: {tg_status['pid']}")
        
        # External Services
        ext_services = components["external_services"]
        if ext_services and not ext_services.get("error"):
            print("\\n🌍 EXTERNAL SERVICES:")
            for service, status in ext_services.items():
                service_status = status.get("status", "unknown")
                print(f"   {service}: {self.get_status_emoji(service_status)} {service_status.upper()}")
        
        # System Metrics
        detailed = report.get("detailed_metrics", {})
        if "system_metrics" in detailed:
            metrics = detailed["system_metrics"]
            print("\\n💻 SYSTEM METRICS:")
            print(f"   CPU Usage: {metrics.get('cpu_usage', 0):.1f}%")
            print(f"   Memory Usage: {metrics.get('memory_usage', 0):.1f}%")
            print(f"   Disk Usage: {metrics.get('disk_usage', 0):.1f}%")
        
        # Database Statistics
        if "database_stats" in detailed:
            db_stats = detailed["database_stats"]
            if not db_stats.get("error"):
                print("\\n📊 DATABASE STATISTICS:")
                print(f"   BIN Records: {db_stats.get('bin_records', 0):,}")
                print(f"   Total Users: {db_stats.get('total_users', 0):,}")
                print(f"   Active Subscriptions: {db_stats.get('active_subscriptions', 0):,}")
        
        print("\\n" + "="*50)
        
        # Health recommendations
        if report['overall_status'] != "healthy":
            print("⚠️  RECOMMENDATIONS:")
            if web_status.get("status") != "healthy":
                print("   - Check web API service and logs")
            if db_status.get("status") != "healthy":
                print("   - Check database connectivity")
            if tg_status.get("status") != "running":
                print("   - Restart Telegram bot service")
            print()
    
    def get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        emoji_map = {
            "healthy": "✅",
            "running": "✅", 
            "degraded": "⚠️",
            "unhealthy": "❌",
            "not_running": "❌",
            "unknown": "❓"
        }
        return emoji_map.get(status, "❓")

def main():
    """Main function"""
    dashboard = StatusDashboard()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Output JSON for programmatic use
        report = dashboard.generate_report()
        print(json.dumps(report, indent=2))
    else:
        # Output formatted report for human reading
        dashboard.print_status_report()

if __name__ == "__main__":
    main()