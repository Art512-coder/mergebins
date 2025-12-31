#!/usr/bin/env python3
"""
Production Bot Launcher with Integrated Health Monitoring
Enhanced version of run_simple_bot.py with health checks and monitoring
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import health server
from src.health_server import start_health_server

class ProductionBotLauncher:
    """Production bot launcher with health monitoring"""
    
    def __init__(self):
        self.health_runner = None
        self.bot_task = None
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        
    async def start_health_monitoring(self):
        """Start health check server"""
        try:
            self.health_runner = await start_health_server()
            logger.info("✅ Health monitoring server started")
        except Exception as e:
            logger.error(f"❌ Failed to start health monitoring: {e}")
            raise
    
    async def start_telegram_bot(self):
        """Start the Telegram bot"""
        try:
            # Import bot components
            from run_simple_bot import create_application, setup_handlers
            
            # Create application
            app = create_application()
            setup_handlers(app)
            
            # Start bot
            logger.info("🤖 Starting Telegram bot...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            logger.info("✅ Telegram bot started successfully")
            
            # Keep bot running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Bot startup failed: {e}")
            raise
        finally:
            try:
                if 'app' in locals():
                    await app.updater.stop()
                    await app.stop()
                    await app.shutdown()
                    logger.info("🛑 Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.health_runner:
                await self.health_runner.cleanup()
                logger.info("🧹 Health monitoring stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def run(self):
        """Main production run method"""
        try:
            # Start health monitoring
            await self.start_health_monitoring()
            
            # Start Telegram bot
            await self.start_telegram_bot()
            
        except KeyboardInterrupt:
            logger.info("⚡ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"💥 Fatal error: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()

# Setup production logging
def setup_production_logging():
    """Configure logging for production environment"""
    
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = log_dir / "production_bot.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - PID:%(process)d - %(message)s'
    )
    
    # Setup handlers
    handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    
    # Console handler for systemd journal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - PID:%(process)d - %(message)s'
    )
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Log startup information
    logger.info("=" * 60)
    logger.info("🚀 BIN Search Bot - Production Mode")
    logger.info("=" * 60)
    logger.info(f"📍 Working Directory: {Path.cwd()}")
    logger.info(f"🐍 Python Version: {sys.version}")
    logger.info(f"📝 Log Level: {log_level}")
    logger.info(f"📄 Log File: {log_file}")
    logger.info(f"🔢 Process ID: {os.getpid()}")
    logger.info(f"👤 User: {os.getenv('USER', 'unknown')}")
    logger.info(f"⏰ Start Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    return logger

async def main():
    """Main entry point for production bot"""
    # Setup logging
    global logger
    logger = setup_production_logging()
    
    try:
        # Validate environment
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set")
            sys.exit(1)
        
        logger.info("✅ Environment validation passed")
        
        # Start production launcher
        launcher = ProductionBotLauncher()
        await launcher.run()
        
    except Exception as e:
        logger.error(f"💥 Production launcher failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("👋 Production bot shutdown complete")

if __name__ == "__main__":
    # Ensure we have required dependencies
    try:
        import telegram
        import aiohttp
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot", "aiohttp"])
        import telegram
        import aiohttp
    
    # Run the production bot
    asyncio.run(main())