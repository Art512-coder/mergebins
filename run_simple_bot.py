"""
Simple BIN Search Bot - Integration Version
Focuses on directing users to the web platform
"""

import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Add project path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import authentication services
from src.services.api_auth import get_user_session, check_user_limits, record_user_activity

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User sessions for basic tracking
user_sessions = {}

def get_user_session(user_id):
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'generations_today': 0,
            'total_cards_created': 0,
        }
    return user_sessions[user_id]

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    username = update.effective_user.username or ""
    
    # Simple session management for now
    session = get_user_session(user_id)
    
    logger.info(f"User {user_id} ({user_name}) started the bot")
    
    # Default to free user for now
    status = "🆓 Free User"
    
    welcome_message = f"""Welcome {user_name}! 🚀

🌐 **ADVANCED BIN SEARCH & CARD GENERATOR**
*Status: {status}*
⚠️ Limited Mode

**🎯 NEW WEB FEATURES:**
• 🔍 Search 458K+ BIN database
• 💳 Generate realistic test cards
• 🌍 AVS support (7 countries)
• 📊 Real-time analytics
• 💎 Premium subscriptions ($9.99/month)
• 🔄 Export functionality

**📱 TELEGRAM FEATURES:**
• /binlookup - Quick BIN search
• /help - Command reference
• /premium - Upgrade information

**🚀 ENHANCED EXPERIENCE:**
Use our web platform for full features:
• Unlimited card generation
• Advanced filtering
• Bulk operations
• Export to CSV/JSON

**📊 YOUR STATS:**
• Total Cards: {session['total_generations']} generated
• Daily Limit: {limits.get('used_today', 0)}/{limits.get('daily_limit', 5)}
• Premium: {'Yes' if session['is_premium'] else 'No'}

⚠️ **All cards are for ETHICAL TESTING ONLY!**
Never use for real transactions."""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Open Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")],
        [InlineKeyboardButton("💎 Upgrade to Premium", callback_data="show_premium")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """🤖 **BIN SEARCH BOT COMMANDS**

**BASIC COMMANDS:**
• /start - Main menu and platform access
• /binlookup 413567 - Quick BIN lookup
• /help - This help message
• /premium - Upgrade information

**🌐 WEB PLATFORM FEATURES:**
• Advanced BIN search with filters
• Card generation with AVS data
• Bulk operations (up to 1000 cards)
• Export to multiple formats
• Real-time statistics
• Premium subscriptions

**💎 PREMIUM BENEFITS:**
• Unlimited daily generations
• AVS support (US, IT, GB, CA, AU, DE, FR)
• Bulk generation
• Priority support
• Export functionality

**🔗 ACCESS:**
Web Platform: https://5e336a94.bin-search-pro.pages.dev
Telegram: @Cryptobinchecker_ccbot

**⚠️ IMPORTANT:**
All generated cards are for TESTING ONLY!
Never attempt real transactions."""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Open Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")],
        [InlineKeyboardButton("ℹ️ Help & Commands", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def binlookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple BIN lookup with web platform redirect"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Please provide a BIN number.\n\n"
            "Usage: /binlookup 413567\n"
            "Example: /binlookup 411111\n\n"
            "🌐 For advanced search, use our web platform:"
        )
        return
    
    bin_number = context.args[0].strip()
    
    # Log activity
    logger.info(f"User {user_id} requested BIN lookup: {bin_number}")
    
    if not bin_number.isdigit() or len(bin_number) < 4:
        await update.message.reply_text(
            "⚠️ Invalid BIN format. Please provide at least 4 digits.\n\n"
            "Example: /binlookup 413567"
        )
        return
    
    # For now, direct users to web platform for actual lookup
    response_text = f"""🔍 **BIN Lookup: {bin_number}**

For detailed BIN information, please use our web platform:

🌐 **Features on Web Platform:**
• Complete BIN details
• 458K+ database records
• Advanced search filters
• Real-time results
• Export functionality

The web platform provides comprehensive BIN analysis with all the features you need!"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔍 Lookup {bin_number} on Web", 
                            url=f"https://5e336a94.bin-search-pro.pages.dev/?bin={bin_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')

async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium upgrade information"""
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    first_name = update.effective_user.first_name or "User"
    
    # Get current user session
    session = get_user_session(user_id)
    
    # Log activity
    logger.info(f"User {user_id} viewed premium info")
    
    # For now, assume all users are free users
    if False:  # session.get('is_premium', False):
        premium_text = f"""💎 **PREMIUM ACTIVE**

✅ You already have Premium access!

**🚀 YOUR BENEFITS:**
• Unlimited daily card generations
• AVS support (7 countries)
• Bulk generation (up to 1000 cards)
• Export functionality (JSON, CSV, TXT)
• Advanced search filters
• Priority support
• No rate limits

**📊 SUBSCRIPTION INFO:**
• Status: Active Premium User
• Total Generated: {session['total_generations']} cards
{'• Expires: ' + session['subscription_expires'] if session['subscription_expires'] else '• Plan: Active'}

🌐 **Access your premium features on our web platform!**"""
    else:
        premium_text = """💎 **PREMIUM UPGRADE**

**🚀 PREMIUM BENEFITS:**
• Unlimited daily card generations
• AVS support (7 countries)
• Bulk generation (up to 1000 cards)
• Export functionality (JSON, CSV, TXT)
• Advanced search filters
• Priority support
• No rate limits

**💰 PRICING:**
• Monthly: $9.99
• Yearly: $99.99 (Save 17%)

**💳 PAYMENT METHODS:**
• Bitcoin (BTC)
• Ethereum (ETH)
• Litecoin (LTC)
• USDT/USDC
• And more cryptocurrencies

**🎯 HOW TO UPGRADE:**
1. Visit our web platform
2. Click "Upgrade to Premium"
3. Choose cryptocurrency
4. Complete payment
5. Instant activation!

Premium features activate immediately after payment confirmation."""
    
    keyboard = [
        [InlineKeyboardButton("💎 Upgrade on Web Platform", 
                            url="https://5e336a94.bin-search-pro.pages.dev/subscription")],
        [InlineKeyboardButton("💰 View Pricing", callback_data="pricing_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(premium_text, reply_markup=reply_markup, parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "show_premium":
        await premium_handler(update, context)
    elif query.data == "show_help":
        await help_handler(update, context)
    elif query.data == "pricing_info":
        await query.edit_message_text(
            "💰 **PREMIUM PRICING**\n\n"
            "Monthly Plan: $9.99\n"
            "Yearly Plan: $99.99 (17% savings)\n\n"
            "🌐 Visit the web platform to complete your upgrade with cryptocurrency payments.",
            parse_mode='Markdown'
        )

def main():
    """Main function to run the bot"""
    logger.info("Starting BIN Search Bot - Integration Version")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("binlookup", binlookup_handler))
    application.add_handler(CommandHandler("premium", premium_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()