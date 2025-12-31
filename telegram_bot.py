#!/usr/bin/env python3
"""
Independent Telegram Bot for BIN Checker
Connects to unified API backend for cross-platform user management
Enhanced with real crypto payment processing
"""
import os
import logging
import requests
import json
import asyncio
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
from telegram_payment_integration import TelegramPaymentManager

# Enhanced error handling for Telegram bot
try:
    from enhanced_monitoring import error_tracker, setup_enhanced_logging
    setup_enhanced_logging()
    monitoring_enabled = True
    print("✅ Enhanced monitoring initialized for Telegram bot")
except ImportError as e:
    print(f"⚠️ Enhanced monitoring not available: {e}")
    monitoring_enabled = False
    error_tracker = None

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = 'https://cryptobinchecker-cc.arturovillanueva1994.workers.dev/api/v1'

# Initialize payment manager
payment_manager = TelegramPaymentManager()

# Store pending payments (in production, use Redis or database)
pending_payments = {}

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with user authentication"""
    try:
        user = update.effective_user
        
        # Authenticate user with unified API
        auth_data = {
            'telegram_id': user.id,
            'username': user.username or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or ''
        }
        
        response = requests.post(f'{API_BASE_URL}/users/telegram-auth', 
                                json=auth_data, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()['user']
            is_premium = user_info.get('is_premium', False)
            
            welcome_msg = f"""🔍 **BIN Checker Bot** 🔍

👋 Welcome {user.first_name}!
🆔 User ID: {user_info['id']}
💳 Premium Status: {'✅ Active' if is_premium else '❌ Free'}

**Available Commands:**
🔍 `/check <BIN>` - Check BIN information
💳 `/generate <BIN>` - Generate test cards
📊 `/stats` - View database statistics
👤 `/profile` - View your profile
💎 `/premium` - Upgrade to premium

**Quick Actions:**"""
            
            keyboard = [
                [InlineKeyboardButton("📊 Database Stats", callback_data="stats")],
                [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
                [InlineKeyboardButton("💎 Premium Info", callback_data="premium")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_msg, 
                                          parse_mode='Markdown', 
                                          reply_markup=reply_markup)
        else:
            await update.message.reply_text("⚠️ Authentication failed. Please try again later.")
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable.")

async def check_bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check BIN information"""
    try:
        if not context.args:
            await update.message.reply_text("📝 Usage: `/check <BIN>`\nExample: `/check 424242`", parse_mode='Markdown')
            return
        
        bin_number = context.args[0].strip()
        
        if not bin_number.isdigit() or len(bin_number) < 6:
            await update.message.reply_text("❌ Please provide a valid BIN (at least 6 digits)")
            return
        
        # Query unified API
        response = requests.get(f'{API_BASE_URL}/bins/lookup/{bin_number}', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                bin_info = data['bin_data']
                result_msg = f"""🔍 **BIN Information**

🏦 **BIN:** `{bin_info['bin']}`
💳 **Brand:** {bin_info['brand']}
🌍 **Country:** {bin_info['country']}
🏛️ **Bank:** {bin_info['bank_name']}
📋 **Type:** {bin_info['type']}
⭐ **Level:** {bin_info['level']}

*Data from unified database*"""
                
                await update.message.reply_text(result_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ {data['error']}")
        else:
            await update.message.reply_text("❌ BIN not found in database")
            
    except Exception as e:
        logger.error(f"Error in check_bin: {e}")
        await update.message.reply_text("❌ Service error. Please try again.")

async def generate_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate test cards using unified API"""
    try:
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text("📝 Usage: `/generate <BIN> [count]`\nExample: `/generate 424242 3`", parse_mode='Markdown')
            return
        
        bin_number = context.args[0].strip()
        count = int(context.args[1]) if len(context.args) > 1 else 1
        
        if not bin_number.isdigit() or len(bin_number) < 6:
            await update.message.reply_text("❌ Please provide a valid BIN (at least 6 digits)")
            return
        
        if count > 10:
            await update.message.reply_text("❌ Maximum 10 cards per request")
            return
        
        # Generate cards via unified API
        gen_data = {
            'bin': bin_number,
            'count': count,
            'telegram_id': user.id
        }
        
        response = requests.post(f'{API_BASE_URL}/cards/generate', 
                               json=gen_data, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                cards = data['cards']
                bin_info = data['bin_info']
                
                result_msg = f"""💳 **Generated Cards**

🏦 **BIN Info:**
• Brand: {bin_info['brand']}
• Type: {bin_info['type']}
• Bank: {bin_info['issuer']}

🔢 **Cards:**"""
                
                for i, card in enumerate(cards, 1):
                    result_msg += f"""
`{i}.` `{card['number']}`
`{card['expiry_month']}/{card['expiry_year']} | {card['cvv']}`"""
                
                result_msg += "\n\n⚠️ *For testing purposes only*"
                
                await update.message.reply_text(result_msg, parse_mode='Markdown')
                
                # Track usage
                requests.post(f'{API_BASE_URL}/users/update-usage',
                            json={'telegram_id': user.id, 'generations_used': count})
            else:
                await update.message.reply_text(f"❌ {data.get('error', 'Generation failed')}")
        else:
            await update.message.reply_text("❌ Card generation service unavailable")
            
    except ValueError:
        await update.message.reply_text("❌ Count must be a number")
    except Exception as e:
        logger.error(f"Error in generate_cards: {e}")
        await update.message.reply_text("❌ Service error. Please try again.")

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get database statistics"""
    try:
        response = requests.get(f'{API_BASE_URL}/bins/stats', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                stats = data['stats']
                stats_msg = f"""📊 **Database Statistics**

📈 **Total Records:** {stats['total_records']:,}
🏦 **Brands:** {stats['brands']}
🌍 **Countries:** {stats['countries']}

*Unified cross-platform database*"""
                
                await update.message.reply_text(stats_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Failed to retrieve statistics")
        else:
            await update.message.reply_text("❌ Statistics service unavailable")
            
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        await update.message.reply_text("❌ Service error. Please try again.")

async def get_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user profile information"""
    try:
        user = update.effective_user
        
        auth_data = {
            'telegram_id': user.id,
            'username': user.username or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or ''
        }
        
        response = requests.post(f'{API_BASE_URL}/users/telegram-auth', 
                               json=auth_data, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()['user']
            
            profile_msg = f"""👤 **Your Profile**

🆔 **User ID:** {user_info['id']}
📱 **Telegram ID:** {user_info['telegram_id']}
💎 **Premium Status:** {'✅ Active' if user_info.get('is_premium', False) else '❌ Free'}
📊 **Daily Generations:** {user_info.get('daily_generations', 0)}
📈 **Total Generations:** {user_info.get('total_generations', 0)}

*Cross-platform account linked*"""
            
            await update.message.reply_text(profile_msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to retrieve profile")
            
    except Exception as e:
        logger.error(f"Error in get_profile: {e}")
        await update.message.reply_text("❌ Service error. Please try again.")

async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium information with payment options"""
    premium_msg = """💎 **Premium Membership**

✨ **Premium Benefits:**
• 🚀 Unlimited card generation
• ⚡ Priority API access
• 🔄 Cross-platform sync with web
• 📊 Advanced analytics
• 🛡️ Premium support

💰 **Pricing:** $9.99/month

🪙 **Payment Methods:**
Choose your preferred cryptocurrency:"""
    
    # Create cryptocurrency selection keyboard
    currencies = payment_manager.get_supported_currencies()
    keyboard = []
    
    # Add crypto buttons in rows of 3
    for i in range(0, len(currencies), 3):
        row = []
        for currency in currencies[i:i+3]:
            emoji = {
                'btc': '₿', 'eth': '⟠', 'ltc': 'Ł', 
                'usdt': '₮', 'bch': '⟢', 'doge': 'Ð'
            }.get(currency, '🪙')
            row.append(InlineKeyboardButton(
                f"{emoji} {currency.upper()}", 
                callback_data=f"pay_{currency}"
            ))
        keyboard.append(row)
    
    # Add alternative options
    keyboard.extend([
        [InlineKeyboardButton("🌐 Web Portal", url="https://cryptobinchecker.cc")],
        [InlineKeyboardButton("💬 Support", callback_data="support")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(premium_msg, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, currency: str):
    """Handle cryptocurrency payment selection"""
    query = update.callback_query
    user = query.from_user
    
    await query.answer("Creating payment...")
    
    try:
        # Create payment
        payment = await payment_manager.create_payment_for_user(user.id, currency)
        
        if payment:
            payment_id = payment.get('payment_id')
            payment_url = payment.get('payment_url')
            crypto_amount = payment.get('crypto_amount', 'TBD')
            
            # Store payment for status tracking
            pending_payments[payment_id] = {
                'user_id': user.id,
                'currency': currency,
                'created_at': datetime.utcnow(),
                'status': 'pending'
            }
            
            payment_msg = f"""💳 **Payment Created**

**Amount:** {crypto_amount} {currency.upper()}
**Payment ID:** `{payment_id}`

⏱️ **Expires:** 1 hour from now
🔗 **Payment Link:** [Click to Pay]({payment_url})

**Instructions:**
1. Click the payment link above
2. Send the exact amount to the provided address
3. Payment will be confirmed automatically
4. Premium access activates immediately

**Need Help?** Contact support if you have issues."""
            
            keyboard = [
                [InlineKeyboardButton("🔗 Pay Now", url=payment_url)],
                [InlineKeyboardButton("🔄 Check Status", callback_data=f"status_{payment_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                payment_msg, 
                parse_mode='Markdown', 
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            # Schedule status check
            context.job_queue.run_once(
                check_payment_status_job,
                when=300,  # Check after 5 minutes
                data={'payment_id': payment_id, 'user_id': user.id},
                name=f"payment_check_{payment_id}"
            )
            
        else:
            await query.edit_message_text(
                "❌ **Payment Creation Failed**\n\nPlease try again or contact support.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error creating crypto payment: {e}")
        await query.edit_message_text(
            "❌ **Error**\n\nFailed to create payment. Please try again later.",
            parse_mode='Markdown'
        )

async def check_payment_status_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check payment status"""
    job_data = context.job.data
    payment_id = job_data['payment_id']
    user_id = job_data['user_id']
    
    try:
        status = await payment_manager.check_payment_status(payment_id)
        
        if status and status.get('status') in ['completed', 'finished']:
            # Payment successful
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 **Payment Confirmed!**\n\nYour premium membership is now active!\nEnjoy unlimited access to all features.",
                parse_mode='Markdown'
            )
            
            # Remove from pending payments
            if payment_id in pending_payments:
                del pending_payments[payment_id]
                
        elif status and status.get('status') in ['expired', 'failed']:
            # Payment failed
            await context.bot.send_message(
                chat_id=user_id,
                text="⏰ **Payment Expired**\n\nYour payment has expired. Please create a new payment to upgrade to premium.",
                parse_mode='Markdown'
            )
            
            # Remove from pending payments
            if payment_id in pending_payments:
                del pending_payments[payment_id]
        else:
            # Still pending, check again later
            context.job_queue.run_once(
                check_payment_status_job,
                when=600,  # Check again in 10 minutes
                data=job_data,
                name=f"payment_check_{payment_id}_retry"
            )
            
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")

async def handle_payment_status_check(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Handle manual payment status check"""
    query = update.callback_query
    
    await query.answer("Checking payment status...")
    
    try:
        status = await payment_manager.check_payment_status(payment_id)
        
        if status:
            payment_status = status.get('status', 'unknown')
            
            if payment_status in ['completed', 'finished']:
                await query.edit_message_text(
                    "🎉 **Payment Confirmed!**\n\nYour premium membership is now active!\nEnjoy unlimited access to all features.",
                    parse_mode='Markdown'
                )
            elif payment_status in ['expired', 'failed']:
                await query.edit_message_text(
                    "❌ **Payment Failed**\n\nYour payment has expired or failed. Please create a new payment.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"⏳ **Payment Status:** {payment_status.title()}\n\nPlease wait for confirmation. You'll be notified when the payment is processed.",
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text(
                "❌ **Status Check Failed**\n\nUnable to check payment status. Please try again.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        await query.edit_message_text(
            "❌ **Error**\n\nFailed to check payment status. Please try again.",
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        await get_stats(query, context)
    elif query.data == "profile":
        await get_profile(query, context)
    elif query.data == "premium":
        await premium_info(query, context)
    elif query.data == "support":
        await query.edit_message_text("📧 **Support:** Contact us at support@cryptobinchecker.cc")
    elif query.data.startswith("pay_"):
        # Handle crypto payment selection
        currency = query.data.replace("pay_", "")
        await handle_crypto_payment(update, context, currency)
    elif query.data.startswith("status_"):
        # Handle payment status check
        payment_id = query.data.replace("status_", "")
        await handle_payment_status_check(update, context, payment_id)
    elif query.data == "cancel_payment":
        await query.edit_message_text(
            "❌ **Payment Cancelled**\n\nYou can create a new payment anytime using `/premium`",
            parse_mode='Markdown'
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages"""
    text = update.message.text
    
    # Check if it looks like a BIN
    if text.isdigit() and len(text) >= 6:
        context.args = [text]
        await check_bin(update, context)
    else:
        help_msg = """❓ **Help**

**Commands:**
🔍 `/check <BIN>` - Check BIN info
💳 `/generate <BIN>` - Generate cards
📊 `/stats` - Database statistics
👤 `/profile` - Your profile
💎 `/premium` - Premium info

**Quick tip:** Send a BIN number directly!
Example: `424242`"""
        
        await update.message.reply_text(help_msg, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    if monitoring_enabled and error_tracker and isinstance(update, Update):
        error_tracker.log_telegram_error(update, context, context.error)
    
    logger.error(f'Update {update} caused error {context.error}', exc_info=context.error)
    
    # Try to send error message to user if possible
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ An error occurred. Please try again later or contact support if the problem persists."
            )
        except Exception:
            pass  # Ignore if we can't send the error message

def main():
    """Start the bot"""
    logger.info(f"Starting Telegram Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add handlers with error wrapping
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_bin))
    application.add_handler(CommandHandler("generate", generate_cards))
    application.add_handler(CommandHandler("stats", get_stats))
    application.add_handler(CommandHandler("profile", get_profile))
    application.add_handler(CommandHandler("premium", premium_info))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("✅ Bot handlers configured")
    
    # Start the bot with retry logic
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("🚀 Starting polling...")
            application.run_polling(drop_pending_updates=True)
            break  # If successful, break the loop
        except Exception as e:
            retry_count += 1
            logger.error(f"Bot startup failed (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count >= max_retries:
                logger.critical("❌ Bot failed to start after maximum retries")
                raise
            
            # Wait before retrying
            import time
            time.sleep(5)

if __name__ == '__main__':
    main()