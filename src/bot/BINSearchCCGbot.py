"""
Enhanced BIN Search & Crypto Wallet Bot for Telegram
Includes crypto balance checker functionality
"""

import logging
import asyncio
import random
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
from crypto_balance_checker import CryptoBalanceChecker
from web_api_client import api_client, cleanup_api_client

# Bot Configuration - Secure environment variable loading
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required but not set")

# Web API Configuration
WEB_API_BASE_URL = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
BOT_API_KEY = os.getenv("BOT_API_KEY", "")

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

# Global variables
user_sessions = {}

# Free tier settings
FREE_TIER_DAILY_LIMIT = 0
PREMIUM_TIER_DAILY_LIMIT = 5

async def test_api_connection():
    """Test connection to web API"""
    try:
        stats = await api_client.get_bin_stats()
        if stats:
            logger.info(f"API connection successful. Database has {stats.get('total_bins', 0)} BIN records")
            return True
    except Exception as e:
        logger.warning(f"API connection failed: {e}")
        logger.info("Bot will continue with limited functionality")
    return False

def get_user_session(user_id):
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'generations_today': 0,
            'total_cards_created': 0,
            'last_generation_date': None,
            'daily_crypto_checks': 0,
            'last_crypto_check_date': None
        }
    
    # Reset daily counters if new day
    today = datetime.now().date()
    session = user_sessions[user_id]
    
    if session['last_generation_date'] != today:
        session['generations_today'] = 0
        session['last_generation_date'] = today
    
    if session['last_crypto_check_date'] != today:
        session['daily_crypto_checks'] = 0
        session['last_crypto_check_date'] = today
        
    return session

async def is_user_premium(telegram_id: int) -> bool:
    """Check if user has premium status via API"""
    try:
        user_session = await api_client.get_or_create_user(telegram_id)
        return user_session.premium_status if user_session else False
    except Exception as e:
        logger.error(f"Premium status check failed: {e}")
        return False

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    username = update.effective_user.username or ""
    
    # Get user session from API
    user_session = await api_client.get_or_create_user(user_id, username, user_name)
    local_session = get_user_session(user_id)
    
    is_premium = user_session.premium_status if user_session else False
    status = "Premium User" if is_premium else "Free User"
    
    daily_gens = user_session.daily_generations if user_session else local_session['generations_today']
    total_gens = user_session.total_generations if user_session else local_session['total_cards_created']
    
    welcome_message = f"""Welcome {user_name}! 

🚀 ADVANCED BIN SEARCH & CRYPTO WALLET BOT (v2.0)
Status: {status}
💾 Connected to 458K+ BIN database

FREE FEATURES:
- /binlookup <number> - Search 458K+ BIN database
- /binsearch <criteria> - Advanced search options
- /generate <bin> - Create enhanced test card (5/day limit)
- /walletbalance <chain> <address> - Check crypto wallet balance
- /statistics - Database information

PREMIUM FEATURES:
- /generate_with_avs <bin> <country> - Generate with postal codes
- /bulk <bin> <count> - Generate up to 1000 cards
- /export <bin> <count> <format> - Download files
- Unlimited daily generations
- Priority support access

NEW ENHANCEMENTS:
- Production-like BIN validation (blocks test BINs)
- Enhanced digit patterns (weighted 0-5, no repeats)
- Dynamic card lengths per brand/type
- AVS support (7 countries: US, IT, GB, CA, AU, DE, FR)
- Improved expiry/CVV algorithms
- Crypto wallet balance checker with real-time USD values

YOUR STATS:
- Daily generations: {daily_gens}/5 (Free) or unlimited (Premium)
- Total cards created: {total_gens}
- Daily crypto checks: {local_session['daily_crypto_checks']}/3 (Free) or unlimited (Premium)

🌐 Web Platform: https://5e336a94.bin-search-pro.pages.dev
UPGRADE: /premium
HELP: /help

WARNING: All cards are for ETHICAL TESTING ONLY!
Never use for real transactions."""
    
    if not is_premium:
        keyboard = [
            [InlineKeyboardButton("🎆 Upgrade to Premium", callback_data="show_premium")],
            [InlineKeyboardButton("🌐 Open Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton("🌐 Open Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def binlookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BIN lookup command handler"""
    if not context.args:
        await update.message.reply_text(
            "Please provide a BIN number.\n\n"
            "Usage: /binlookup 413567\n"
            "Example: /binlookup 411111"
        )
        return
    
    # Check if API is available
    try:
        await api_client.get_bin_stats()  # Quick health check
    except:
        await update.message.reply_text(
            "⚠️ BIN lookup service temporarily unavailable.\n\n"
            "🌐 Please use our web platform:\n"
            "https://5e336a94.bin-search-pro.pages.dev\n\n"
            "Or try again later."
        )
        return
    
    bin_number = context.args[0].strip()
    
    # Validate BIN format
    if not bin_number.isdigit() or len(bin_number) < 4:
        await update.message.reply_text(
            "⚠️ Invalid BIN format. Please provide at least 4 digits.\n\n"
            "Example: /binlookup 413567"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text("🔍 Searching BIN database...")
    
    try:
        # Look up BIN via API
        bin_data = await api_client.lookup_bin(bin_number)
        
        if bin_data:
            result_text = f"""💳 BIN LOOKUP RESULTS

🔢 BIN: {bin_data.bin_number}
🏦 Brand: {bin_data.brand or 'Unknown'}
🌍 Country: {bin_data.country or 'Unknown'} ({bin_data.country_code or 'N/A'})
🏦 Bank: {bin_data.bank_name or 'Unknown'}
💳 Type: {bin_data.card_type or 'Unknown'}
⭐ Level: {bin_data.card_level or 'Unknown'}

📊 Database: 458K+ BIN records
⚠️ For testing purposes only!"""
            
            # Add web platform button
            keyboard = [
                [InlineKeyboardButton("🌐 Open Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await loading_msg.edit_text(result_text, reply_markup=reply_markup)
        else:
            await loading_msg.edit_text(
                f"❌ BIN {bin_number} not found in database.\n\n"
                "📊 Database contains 458K+ BIN records\n"
                "Try a different BIN number or use /binsearch for advanced search."
            )
    except Exception as e:
        logger.error(f"BIN lookup error: {e}")
        await loading_msg.edit_text(
            "⚠️ Database temporarily unavailable. Please try again later.\n\n"
            "If the issue persists, contact support."
        )

async def binsearch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BIN search command handler"""
    if not context.args:
        await update.message.reply_text(
            "🔍 BIN SEARCH HELP\n\n"
            "Search the 458K+ BIN database with filters:\n\n"
            "Usage Examples:\n"
            "\u2022 /binsearch brand=VISA\n"
            "\u2022 /binsearch country=USA\n"
            "\u2022 /binsearch issuer=Chase\n"
            "\u2022 /binsearch type=CREDIT\n\n"
            "Available Filters:\n"
            "\u2022 brand (VISA, MASTERCARD, AMEX, etc.)\n"
            "\u2022 country (USA, UK, Canada, etc.)\n"
            "\u2022 issuer (bank name)\n"
            "\u2022 type (CREDIT, DEBIT, PREPAID)\n\n"
            "Results limited to top 10 matches."
        )
        return
    
    # Parse search filters
    filters = {}
    search_query = ' '.join(context.args)
    
    try:
        for param in context.args:
            if '=' in param:
                key, value = param.split('=', 1)
                filters[key.lower()] = value.upper()
    except:
        await update.message.reply_text(
            "⚠️ Invalid search format.\n\n"
            "Use: /binsearch brand=VISA or /binsearch country=USA"
        )
        return
    
    if not filters:
        await update.message.reply_text(
            "⚠️ No valid filters provided.\n\n"
            "Example: /binsearch brand=VISA"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text("🔍 Searching database...")
    
    try:
        # Search BINs via API
        results = await api_client.search_bins(**filters)
        
        if results:
            result_text = f"🔍 SEARCH RESULTS ({len(results)} found)\n\n"
            
            for i, bin_data in enumerate(results[:10]):  # Limit to 10 results
                result_text += f"{i+1}. {bin_data.bin_number} - {bin_data.brand} ({bin_data.country})\n"
            
            if len(results) > 10:
                result_text += f"\n... and {len(results) - 10} more results\n"
            
            result_text += "\n🌐 Use web platform for advanced search and full results."
            
            # Add web platform button
            keyboard = [
                [InlineKeyboardButton("🌐 Advanced Search", url="https://5e336a94.bin-search-pro.pages.dev")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await loading_msg.edit_text(result_text, reply_markup=reply_markup)
        else:
            await loading_msg.edit_text(
                f"❌ No results found for: {search_query}\n\n"
                "Try different search criteria or check spelling."
            )
    except Exception as e:
        logger.error(f"BIN search error: {e}")
        await loading_msg.edit_text(
            "⚠️ Search temporarily unavailable. Please try again later."
        )

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Card generation handler"""
    user_id = update.effective_user.id
    
    # Check if user has reached daily limit
    is_premium = await is_user_premium(user_id)
    user_session = await api_client.get_or_create_user(user_id)
    
    if not is_premium and user_session and user_session.daily_generations >= 5:
        keyboard = [
            [InlineKeyboardButton("🎆 Upgrade to Premium", callback_data="show_premium")],
            [InlineKeyboardButton("🌐 Use Web Platform", url="https://5e336a94.bin-search-pro.pages.dev")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ Daily limit reached (5 cards for free users).\n\n"
            "🎆 Upgrade to Premium for unlimited generation\n"
            "🌐 Or use our web platform",
            reply_markup=reply_markup
        )
        return
    
    bin_number = ""
    if context.args:
        bin_number = context.args[0].strip()
    
    # Show loading message
    loading_msg = await update.message.reply_text("🎲 Generating card...")
    
    try:
        # Generate card via API
        result = await api_client.generate_cards(bin_number=bin_number, count=1)
        
        if result.get("success") and result.get("cards"):
            card = result["cards"][0]
            
            card_text = f"""💳 GENERATED CARD

🔢 Number: `{card.get('number', 'N/A')}`
📅 Expiry: {card.get('expiry', 'N/A')}
🔐 CVV: {card.get('cvv', 'N/A')}
🏦 Brand: {card.get('brand', 'N/A')}
🌍 Country: {card.get('country', 'N/A')}

⚠️ FOR TESTING ONLY - Not real account!"""
            
            # Update usage
            await api_client.update_user_usage(user_id, 1)
            
            await loading_msg.edit_text(card_text, parse_mode='Markdown')
        else:
            error_msg = result.get("error", "Generation failed")
            await loading_msg.edit_text(f"⚠️ Error: {error_msg}")
    except Exception as e:
        logger.error(f"Card generation error: {e}")
        await loading_msg.edit_text("⚠️ Generation service temporarily unavailable.")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """BIN SEARCH & CRYPTO WALLET BOT

*FREE COMMANDS:*
/start - Main menu and status
/binlookup 413567 - Look up BIN details
/binsearch brand=VISA - Search database
/generate 413567 - Create single test card
/walletbalance BTC <address> - Check crypto wallet balance
/statistics - Database statistics

*PREMIUM COMMANDS:*
/generate_with_avs 413567 US - Generate with postal code (AVS)
/bulk 413567 25 - Generate multiple cards
/export 413567 50 json - Export to file
/premium - Upgrade information

*CRYPTO WALLET CHECKER:*
Supported: BTC, ETH
Free: 3 checks per day
Premium: Unlimited checks
Real-time USD values
Explorer links included

*SEARCH EXAMPLES:*
/binsearch brand=VISA
/binsearch country=USA  
/binsearch issuer=Chase
/binsearch type=CREDIT

*WALLET EXAMPLES:*
/walletbalance BTC [bitcoin_address]
/walletbalance ETH [ethereum_address]

*AVS SUPPORTED COUNTRIES:*
US, IT, GB, CA, AU, DE, FR (expanding regularly)

*IMPORTANT NOTES:*
- All generated cards are TEST CARDS only
- Enhanced algorithms prevent test BIN detection
- Valid format but NOT real accounts
- For development and testing purposes
- Never attempt real transactions
- Wallet checker uses public blockchain data only

Need more help? Contact support."""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistics command using API"""
    loading_msg = await update.message.reply_text("📈 Loading statistics...")
    
    try:
        stats = await api_client.get_bin_stats()
        
        if stats:
            stats_text = f"""📈 DATABASE STATISTICS

💾 Total BINs: {stats.get('total_bins', 0):,}
🌍 Countries: {stats.get('total_countries', 0):,}
🏦 Brands: {stats.get('total_brands', 0):,}
🏯 Banks: {stats.get('total_banks', 0):,}

TOP BRANDS:"""
            
            top_brands = stats.get('top_brands', {})
            for brand, count in list(top_brands.items())[:5]:
                stats_text += f"\n\u2022 {brand}: {count:,} BINs"
            
            stats_text += "\n\nTOP COUNTRIES:"
            top_countries = stats.get('top_countries', {})
            for country, count in list(top_countries.items())[:5]:
                stats_text += f"\n\u2022 {country}: {count:,} BINs"
            
            stats_text += "\n\n🌐 Full analytics available on web platform"
            
            keyboard = [
                [InlineKeyboardButton("🌐 View Full Analytics", url="https://5e336a94.bin-search-pro.pages.dev")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await loading_msg.edit_text(stats_text, reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("⚠️ Statistics temporarily unavailable.")
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await loading_msg.edit_text("⚠️ Statistics service temporarily unavailable.")

async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium upgrade information"""
    premium_text = """PREMIUM UPGRADE

PREMIUM BENEFITS:
- Unlimited daily card generations
- AVS (Address Verification System) support
- Bulk generation (up to 1000 cards)
- Export functionality (JSON, CSV, TXT)
- Unlimited crypto wallet checks
- Priority support
- No rate limits

PRICING:
Monthly: $9.99
Yearly: $99.99 (Save 17%)

To upgrade, contact: @support_bot

PAYMENT METHODS:
- Bitcoin (BTC)
- Ethereum (ETH)
- Litecoin (LTC)
- PayPal
- Credit Card

Premium features activate immediately after payment confirmation."""
    
    keyboard = [
        [InlineKeyboardButton("Contact Support", url="https://t.me/support_bot")],
        [InlineKeyboardButton("Payment Info", callback_data="payment_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(premium_text, reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_premium":
        await premium_handler(update, context)
    elif query.data == "payment_info":
        await query.edit_message_text("For payment information and premium upgrade, please contact @support_bot")

def main():
    """Main function to run the bot"""
    
    async def setup_and_run():
        # Test API connection
        api_connected = await test_api_connection()
        if not api_connected:
            logger.warning("API connection failed. Bot will run with limited functionality.")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Initialize crypto balance checker
        crypto_checker = CryptoBalanceChecker()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("binlookup", binlookup_handler))
        application.add_handler(CommandHandler("binsearch", binsearch_handler))
        application.add_handler(CommandHandler("generate", generate_handler))
        application.add_handler(CommandHandler("statistics", statistics_handler))
        application.add_handler(CommandHandler("premium", premium_handler))
        application.add_handler(CommandHandler("walletbalance", crypto_checker.handle_wallet_balance))
        application.add_handler(CallbackQueryHandler(callback_handler))
        
        try:
            # Start the bot
            logger.info("Starting bot with web API integration...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await cleanup_api_client()
    
    # Run the setup
    asyncio.run(setup_and_run())

if __name__ == '__main__':
    main()
