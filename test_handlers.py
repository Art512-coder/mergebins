#!/usr/bin/env python3
"""
Simple Bot Test - Verify Commands Work
Quick test to check if bot handlers are working
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_handlers():
    """Test that all handlers are properly imported and callable"""
    print("=== Bot Handler Test ===")
    
    try:
        # Test imports
        print("[1/5] Testing imports...")
        from run_simple_bot import (
            start_handler, 
            help_handler, 
            binlookup_handler, 
            premium_handler,
            callback_handler
        )
        print("✓ All handlers imported successfully")
        
        # Test bot token
        print("[2/5] Testing bot token...")
        from dotenv import load_dotenv
        load_dotenv()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            print(f"✓ Bot token loaded: {bot_token[:10]}...")
        else:
            print("✗ Bot token not found")
            return False
        
        # Test telegram library
        print("[3/5] Testing Telegram library...")
        from telegram.ext import Application
        app = Application.builder().token(bot_token).build()
        print("✓ Telegram application created")
        
        # Test handler registration
        print("[4/5] Testing handler registration...")
        from telegram.ext import CommandHandler, CallbackQueryHandler
        
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("binlookup", binlookup_handler))
        app.add_handler(CommandHandler("premium", premium_handler))
        app.add_handler(CallbackQueryHandler(callback_handler))
        print("✓ All handlers registered")
        
        # Test bot initialization
        print("[5/5] Testing bot initialization...")
        await app.initialize()
        me = await app.bot.get_me()
        print(f"✓ Bot initialized: @{me.username}")
        
        await app.shutdown()
        
        print()
        print("🎉 All tests passed!")
        print("The bot should now respond to /start command on Telegram")
        print(f"Bot username: @{me.username}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_handlers())
    if success:
        print("\n✅ Bot is ready to use!")
        print("Go to Telegram and message @Cryptobinchecker_ccbot")
        print("Send /start to test the bot")
    else:
        print("\n❌ Bot has issues - check the errors above")
        sys.exit(1)