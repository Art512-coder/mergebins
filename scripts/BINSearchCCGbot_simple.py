"""
Enhanced BIN Search & Crypto Wallet Bot for Telegram
Includes crypto balance checker functionality
"""

import logging
import pandas as pd
import random
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from crypto_balance_checker import CryptoBalanceChecker

# Bot Configuration
BOT_TOKEN = "7444150670:AAFDgL5_Wt7-HeTT3lT1EmbFYIzZ7wA9UHE"
BIN_FILE_PATH = "merged_bin_data.csv"

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
df = None
user_sessions = {}

# Free tier settings
FREE_TIER_DAILY_LIMIT = 0
PREMIUM_TIER_DAILY_LIMIT = 5

def load_bin_data():
    """Load BIN data from CSV file"""
    global df
    try:
        df = pd.read_csv(BIN_FILE_PATH)
        logger.info(f"Loaded {len(df)} BIN records")
        return True
    except Exception as e:
        logger.error(f"Error loading BIN data: {e}")
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

def is_user_premium(user_id):
    """Check if user has premium status"""
    # For now, return False for all users
    # This would be connected to payment system in production
    return False

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    session = get_user_session(user_id)
    
    status = "Premium User" if is_user_premium(user_id) else "Free User"
    
    welcome_message = f"""Welcome {user_name}! 

ADVANCED BIN SEARCH & CRYPTO WALLET BOT (Enhanced v2.0)
Status: {status}

FREE FEATURES:
- /binlookup <number> - Search 450000+ BIN database
- /binsearch <criteria> - Advanced search options
- /generate <bin> - Create enhanced test card (daily limit varies)
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
- Daily generations: {session['generations_today']}/5 (Free) or unlimited (Premium)
- Total cards created: {session['total_cards_created']}
- Daily crypto checks: {session['daily_crypto_checks']}/3 (Free) or unlimited (Premium)

UPGRADE: /premium
HELP: /help

WARNING: All cards are for ETHICAL TESTING ONLY!
Never use for real transactions."""
    
    if not is_user_premium(user_id):
        keyboard = [[InlineKeyboardButton("Upgrade to Premium", callback_data="show_premium")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_message)

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
    """Statistics command"""
    if df is not None:
        total_bins = len(df)
        brands = df['brand'].value_counts().head(5).to_dict()
        countries = df['country'].value_counts().head(5).to_dict()
        
        stats_text = f"""📊 DATABASE STATISTICS

Total BINs: {total_bins:,}

TOP BRANDS:
"""
        for brand, count in brands.items():
            stats_text += f"• {brand}: {count:,} BINs\n"
        
        stats_text += "\nTOP COUNTRIES:\n"
        for country, count in countries.items():
            stats_text += f"• {country}: {count:,} BINs\n"
        
        await update.message.reply_text(stats_text)
    else:
        await update.message.reply_text("Database not loaded. Please try again later.")

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
    # Load BIN data
    if not load_bin_data():
        logger.error("Failed to load BIN data. Exiting.")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize crypto balance checker
    crypto_checker = CryptoBalanceChecker()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("statistics", statistics_handler))
    application.add_handler(CommandHandler("premium", premium_handler))
    application.add_handler(CommandHandler("walletbalance", crypto_checker.handle_wallet_balance))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
