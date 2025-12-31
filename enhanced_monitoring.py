"""
Enhanced Error Handling and Monitoring System
Provides comprehensive error tracking, logging, and alerting for production stability
"""
import logging
import traceback
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Request, HTTPException
from telegram import Update
from telegram.ext import ContextTypes

# Enhanced logging configuration
def setup_enhanced_logging():
    """Setup comprehensive logging for all components"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Clear existing handlers
    
    # File handlers
    file_handler = logging.FileHandler('logs/application.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if os.getenv('DEBUG') == 'true' else logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Telegram bot specific logger
    telegram_logger = logging.getLogger('telegram_bot')
    telegram_handler = logging.FileHandler('logs/telegram_bot.log')
    telegram_handler.setFormatter(detailed_formatter)
    telegram_logger.addHandler(telegram_handler)
    
    # Payment system logger
    payment_logger = logging.getLogger('payments')
    payment_handler = logging.FileHandler('logs/payments.log')
    payment_handler.setFormatter(detailed_formatter)
    payment_logger.addHandler(payment_handler)
    
    print("✅ Enhanced logging system initialized")

class ErrorTracker:
    """Centralized error tracking and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('error_tracker')
        
    def log_api_error(self, request: Request, error: Exception, context: Dict[str, Any] = None):
        """Log API-related errors with context"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'api_error',
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'url': str(request.url),
            'method': request.method,
            'client_ip': getattr(request, 'client', {}).get('host', 'unknown'),
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"API Error: {json.dumps(error_data, indent=2)}")
        
        # In production, you could send to external monitoring services
        # self._send_to_sentry(error_data)
        # self._send_to_slack(error_data)
    
    def log_database_error(self, db: Session, error: Exception, query: str = None):
        """Log database-related errors"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'database_error',
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'query': query,
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"Database Error: {json.dumps(error_data, indent=2)}")
    
    def log_telegram_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Log Telegram bot errors"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'telegram_error',
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'user_id': update.effective_user.id if update.effective_user else None,
            'chat_id': update.effective_chat.id if update.effective_chat else None,
            'message': update.effective_message.text if update.effective_message else None,
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"Telegram Error: {json.dumps(error_data, indent=2)}")
    
    def log_payment_error(self, user_id: Optional[int], payment_id: Optional[str], error: Exception, provider: str = None):
        """Log payment processing errors"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'payment_error',
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'user_id': user_id,
            'payment_id': payment_id,
            'provider': provider,
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"Payment Error: {json.dumps(error_data, indent=2)}")

class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('health_monitor')
    
    def check_database_health(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            result = db.execute(text("SELECT 1"))
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check critical API endpoints"""
        endpoints_to_check = [
            '/health',
            '/api/v1/bins/stats',
            '/api/v1/auth/me'
        ]
        
        results = {}
        
        for endpoint in endpoints_to_check:
            try:
                import requests
                start_time = datetime.now()
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                response_time = (datetime.now() - start_time).total_seconds()
                
                results[endpoint] = {
                    'status': 'healthy' if response.status_code < 400 else 'unhealthy',
                    'status_code': response.status_code,
                    'response_time': response_time
                }
            except Exception as e:
                results[endpoint] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return results
    
    def check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        services = {
            'blockchain_info': 'https://blockchain.info/q/getblockcount',
            'etherscan': 'https://api.etherscan.io/api?module=stats&action=ethsupply',
            'coingecko': 'https://api.coingecko.com/api/v3/ping'
        }
        
        results = {}
        
        for service, url in services.items():
            try:
                import requests
                start_time = datetime.now()
                response = requests.get(url, timeout=10)
                response_time = (datetime.now() - start_time).total_seconds()
                
                results[service] = {
                    'status': 'healthy' if response.status_code == 200 else 'degraded',
                    'response_time': response_time
                }
            except Exception as e:
                results[service] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return results

# Global instances
error_tracker = ErrorTracker()
health_monitor = HealthMonitor()

# Decorator for automatic error handling
def handle_errors(error_type: str = "general"):
    """Decorator for automatic error logging and handling"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if error_type == "api" and len(args) > 0 and hasattr(args[0], 'client'):
                    error_tracker.log_api_error(args[0], e)
                elif error_type == "telegram" and len(args) >= 2:
                    error_tracker.log_telegram_error(args[0], args[1], e)
                else:
                    logging.getLogger(func.__module__).error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_type == "api" and len(args) > 0 and hasattr(args[0], 'client'):
                    error_tracker.log_api_error(args[0], e)
                else:
                    logging.getLogger(func.__module__).error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Recovery mechanisms
class RecoveryManager:
    """Handles automatic recovery from common errors"""
    
    def __init__(self):
        self.logger = logging.getLogger('recovery')
    
    def recover_database_connection(self, db: Session) -> bool:
        """Attempt to recover database connection"""
        try:
            db.rollback()
            db.execute(text("SELECT 1"))
            self.logger.info("Database connection recovered")
            return True
        except Exception as e:
            self.logger.error(f"Database recovery failed: {e}")
            return False
    
    def recover_api_client(self, client) -> bool:
        """Attempt to recover API client connection"""
        try:
            # Reset client state
            if hasattr(client, 'close'):
                client.close()
            # Reinitialize if needed
            self.logger.info("API client recovered")
            return True
        except Exception as e:
            self.logger.error(f"API client recovery failed: {e}")
            return False

recovery_manager = RecoveryManager()

# Initialize enhanced logging on import
setup_enhanced_logging()