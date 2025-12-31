#!/usr/bin/env python3
"""
Windows Production Bot Launcher
Simplified launcher for Windows development/testing
"""

import asyncio
import logging
import os
import sys
import signal
import gc
from datetime import datetime
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for Windows"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "bot.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting BIN Search Bot on Windows")
    return logger

def install_dependencies():
    """Install required dependencies if missing"""
    required_packages = [
        'python-telegram-bot',
        'aiohttp',
        'python-dotenv',
        'requests',
        'PyJWT'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def load_environment():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"[OK] Loaded environment from {env_file}")
    else:
        print("[WARNING] No .env file found")

async def start_health_server():
    """Start simple health server for Windows"""
    from aiohttp import web
    
    async def health_handler(request):
        return web.json_response({
            "status": "healthy",
            "bot": "Crypto BIN Checker Bot",
            "username": "@Cryptobinchecker_ccbot",
            "timestamp": datetime.now().isoformat(),
            "platform": "Windows"
        })
    
    app = web.Application()
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8001)
    await site.start()
    
    print("[HEALTH] Server started at http://localhost:8001/health")
    return runner

async def main():
    """Main bot launcher"""
    logger = setup_logging()
    health_runner = None
    app = None
    
    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(cleanup_and_exit())
    
    async def cleanup_and_exit():
        nonlocal health_runner, app
        try:
            if app:
                logger.info("Stopping Telegram bot...")
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            if health_runner:
                logger.info("Stopping health server...")
                await health_runner.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            # Force garbage collection
            gc.collect()
            logger.info("Cleanup complete")
            os._exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Load environment
        load_environment()
        
        # Check bot token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("[ERROR] TELEGRAM_BOT_TOKEN not found in environment")
            return
        
        logger.info(f"[OK] Bot token loaded: {bot_token[:10]}...")
        
        # Start health server
        health_runner = await start_health_server()
        
        # Import bot components directly
        from telegram.ext import Application
        import run_simple_bot
        
        logger.info("[BOT] Starting Telegram bot...")
        logger.info("[BOT] Username: @Cryptobinchecker_ccbot")
        logger.info("[WEB] Platform: https://5e336a94.bin-search-pro.pages.dev")
        
        # Create and configure bot application with connection pooling
        app = Application.builder().token(bot_token).concurrent_updates(True).build()
        
        # Add handlers from run_simple_bot
        from telegram.ext import CommandHandler, CallbackQueryHandler
        
        # Import handlers
        from run_simple_bot import (
            start_handler, 
            help_handler, 
            binlookup_handler, 
            premium_handler,
            callback_handler
        )
        
        # Add all handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("binlookup", binlookup_handler))
        app.add_handler(CommandHandler("premium", premium_handler))
        app.add_handler(CallbackQueryHandler(callback_handler))
        
        # Start the bot with error handling
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
        logger.info("[OK] Bot started successfully!")
        logger.info("[INFO] Try messaging @Cryptobinchecker_ccbot on Telegram")
        logger.info("[INFO] Press Ctrl+C to stop the bot")
        
        # Keep running with periodic cleanup
        loop_count = 0
        try:
            while True:
                await asyncio.sleep(1)
                loop_count += 1
                
                # Periodic garbage collection every 5 minutes
                if loop_count % 300 == 0:
                    gc.collect()
                    logger.debug("Performed garbage collection")
                    
        except KeyboardInterrupt:
            logger.info("⚡ Keyboard interrupt received, stopping bot...")
            await cleanup_and_exit()
        
    except KeyboardInterrupt:
        logger.info("[STOP] Bot stopped by user")
        await cleanup_and_exit()
    except Exception as e:
        logger.error(f"[ERROR] Bot error: {e}", exc_info=True)
        await cleanup_and_exit()
    finally:
        logger.info("[SHUTDOWN] Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())