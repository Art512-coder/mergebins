"""
Crypto Balance Checker Module for BINSearchCCGBot
Standalone feature that checks wallet balances for major cryptocurrencies
Author: Expert Integration Team
Version: 1.0
"""

import requests
import re
import redis
import os
import json
import logging
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# API Configuration
BLOCKCHAIN_API_URL = "https://blockchain.info"
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', 'YourEtherscanAPIKey')
ETHERSCAN_API_URL = "https://api.etherscan.io/api"
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')
NOWPAYMENTS_CHECKOUT_URL = "https://nowpayments.io/payment"

# Address validation patterns
ADDRESS_PATTERNS = {
    'BTC': r'^(1|3|bc1)[a-zA-Z0-9]{25,62}$',
    'ETH': r'^0x[a-fA-F0-9]{40}$',
    'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'  # Future expansion
}

# Supported chains and their display info
SUPPORTED_CHAINS = {
    'BTC': {
        'name': 'Bitcoin',
        'symbol': 'BTC',
        'emoji': '₿',
        'explorer_url': 'https://blockchain.com/btc/address/',
        'decimals': 8,
        'coingecko_id': 'bitcoin'
    },
    'ETH': {
        'name': 'Ethereum',
        'symbol': 'ETH',
        'emoji': '⟠',
        'explorer_url': 'https://etherscan.io/address/',
        'decimals': 18,
        'coingecko_id': 'ethereum'
    }
}

class CryptoBalanceChecker:
    """Main class for crypto balance checking functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BINSearchCCGBot/1.0 Crypto Balance Checker'
        })
    
    async def check_user_limits(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user has remaining balance checks for today
        Returns: (can_check, remaining_checks)
        """
        try:
            # Check if user is premium
            premium_key = f"premium:{user_id}"
            if redis_client.get(premium_key):
                return True, -1  # Unlimited for premium users
            
            # Check daily usage for free users
            usage_key = f"wallet_usage:{user_id}"
            current_usage = redis_client.get(usage_key)
            current_usage = int(current_usage) if current_usage else 0
            
            FREE_DAILY_LIMIT = 3
            remaining = FREE_DAILY_LIMIT - current_usage
            
            return remaining > 0, remaining
            
        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
            return True, 1  # Default to allow on error
    
    def increment_usage(self, user_id: int):
        """Increment user's daily usage counter"""
        try:
            usage_key = f"wallet_usage:{user_id}"
            current = redis_client.incr(usage_key)
            if current == 1:  # First usage today
                redis_client.expire(usage_key, 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
    
    def validate_address(self, chain: str, address: str) -> bool:
        """Validate cryptocurrency address format"""
        if chain not in ADDRESS_PATTERNS:
            return False
        return bool(re.match(ADDRESS_PATTERNS[chain], address))
    
    async def get_crypto_price(self, chain: str) -> Optional[float]:
        """Get current USD price for cryptocurrency"""
        try:
            # Check cache first
            cache_key = f"price:{chain.lower()}"
            cached_price = redis_client.get(cache_key)
            if cached_price:
                return float(cached_price)
            
            # Fetch from CoinGecko
            coin_id = SUPPORTED_CHAINS[chain]['coingecko_id']
            url = f"{COINGECKO_API_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = data[coin_id]['usd']
            
            # Cache for 5 minutes
            redis_client.setex(cache_key, 300, str(price))
            
            return float(price)
            
        except Exception as e:
            logger.error(f"Error fetching {chain} price: {e}")
            return None
    
    async def get_btc_balance(self, address: str) -> Optional[float]:
        """Get Bitcoin balance for address"""
        try:
            url = f"{BLOCKCHAIN_API_URL}/balance?active={address}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            # Balance is in satoshis, convert to BTC
            balance_satoshis = data[address]['final_balance']
            balance_btc = balance_satoshis / 1e8
            
            return balance_btc
            
        except Exception as e:
            logger.error(f"Error fetching BTC balance for {address}: {e}")
            return None
    
    async def get_eth_balance(self, address: str) -> Optional[float]:
        """Get Ethereum balance for address"""
        try:
            url = ETHERSCAN_API_URL
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': ETHERSCAN_API_KEY
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] != '1':
                raise Exception(f"Etherscan API error: {data.get('message', 'Unknown error')}")
            
            # Balance is in wei, convert to ETH
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 1e18
            
            return balance_eth
            
        except Exception as e:
            logger.error(f"Error fetching ETH balance for {address}: {e}")
            return None
    
    async def get_wallet_balance(self, chain: str, address: str) -> Optional[Dict]:
        """
        Get wallet balance with caching
        Returns: {balance: float, usd_value: float, price: float}
        """
        try:
            # Check cache first
            cache_key = f"wallet:{chain}:{address}"
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # Get current price
            price = await self.get_crypto_price(chain)
            if price is None:
                return None
            
            # Get balance based on chain
            if chain == 'BTC':
                balance = await self.get_btc_balance(address)
            elif chain == 'ETH':
                balance = await self.get_eth_balance(address)
            else:
                return None
            
            if balance is None:
                return None
            
            # Calculate USD value
            usd_value = balance * price
            
            result = {
                'balance': balance,
                'usd_value': usd_value,
                'price': price,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache for 5 minutes
            redis_client.setex(cache_key, 300, json.dumps(result))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return None
    
    async def handle_wallet_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /walletbalance command
        """
        return await walletbalance(update, context)

# Initialize checker instance
crypto_checker = CryptoBalanceChecker()

async def walletbalance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main command handler for /walletbalance
    Usage: /walletbalance <chain> <address>
    Example: /walletbalance BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
    """
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    try:
        # Parse arguments
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "🔍 *Crypto Balance Checker*\n\n"
                "Usage: `/walletbalance <chain> <address>`\n\n"
                "Supported chains:\n"
                "• `BTC` - Bitcoin\n"
                "• `ETH` - Ethereum\n\n"
                "Example:\n"
                "`/walletbalance BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`\n"
                "`/walletbalance ETH 0x690B9A9E9aa1C9dB991C28d09DAAd5BBA6f6Fb73`",
                parse_mode='Markdown'
            )
            return
        
        chain = context.args[0].upper()
        address = context.args[1]
        
        # Validate chain
        if chain not in SUPPORTED_CHAINS:
            await update.message.reply_text(
                f"❌ Unsupported chain: `{chain}`\n\n"
                f"Supported chains: {', '.join(SUPPORTED_CHAINS.keys())}",
                parse_mode='Markdown'
            )
            return
        
        # Validate address format
        if not crypto_checker.validate_address(chain, address):
            chain_info = SUPPORTED_CHAINS[chain]
            await update.message.reply_text(
                f"❌ Invalid {chain_info['name']} address format\n\n"
                f"Please check your {chain} address and try again.",
                parse_mode='Markdown'
            )
            return
        
        # Check user limits
        can_check, remaining = await crypto_checker.check_user_limits(user_id)
        
        if not can_check:
            # User exceeded free limit
            keyboard = [
                [InlineKeyboardButton("💳 Upgrade to Premium ($9.99/month)", url=f"{NOWPAYMENTS_CHECKOUT_URL}/premium")],
                [InlineKeyboardButton("💰 Pay $5 for One Check", url=f"{NOWPAYMENTS_CHECKOUT_URL}/single")],
                [InlineKeyboardButton("ℹ️ Learn More", callback_data="wallet_limits_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🚫 *Daily Limit Reached*\n\n"
                "You've used all 3 free balance checks today.\n\n"
                "Options:\n"
                "• Upgrade to Premium for unlimited checks\n"
                "• Pay $5 for an additional check\n"
                "• Wait until tomorrow for free checks to reset",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # Send "checking" message
        checking_msg = await update.message.reply_text(
            f"🔍 Checking {chain} wallet balance...\n"
            f"📍 Address: `{address[:10]}...{address[-6:]}`",
            parse_mode='Markdown'
        )
        
        # Get wallet balance
        wallet_data = await crypto_checker.get_wallet_balance(chain, address)
        
        if wallet_data is None:
            await checking_msg.edit_text(
                "❌ *Error Checking Balance*\n\n"
                "Unable to fetch wallet data. This could be due to:\n"
                "• Network connectivity issues\n"
                "• API service temporarily unavailable\n"
                "• Invalid address\n\n"
                "Please try again in a few moments.",
                parse_mode='Markdown'
            )
            return
        
        # Increment usage counter
        crypto_checker.increment_usage(user_id)
        
        # Format response
        chain_info = SUPPORTED_CHAINS[chain]
        balance = wallet_data['balance']
        usd_value = wallet_data['usd_value']
        price = wallet_data['price']
        
        # Format numbers nicely
        if balance >= 1:
            balance_str = f"{balance:,.6f}".rstrip('0').rstrip('.')
        else:
            balance_str = f"{balance:.8f}".rstrip('0').rstrip('.')
        
        if usd_value >= 1:
            usd_str = f"${usd_value:,.2f}"
        else:
            usd_str = f"${usd_value:.6f}".rstrip('0').rstrip('.')
        
        # Build response message
        response_text = (
            f"💰 *{chain_info['name']} Wallet Status*\n\n"
            f"📍 *Address*: `{address}`\n"
            f"{chain_info['emoji']} *Balance*: {balance_str} {chain}\n"
            f"💵 *USD Value*: {usd_str}\n"
            f"📈 *Current Price*: ${price:,.2f}\n\n"
        )
        
        # Add remaining checks info for free users
        if remaining > 0:
            response_text += f"ℹ️ Free checks remaining today: {remaining - 1}\n\n"
        elif remaining == 0:
            response_text += "ℹ️ This was your last free check today\n\n"
        
        response_text += (
            "🔒 *Privacy Notice*: Only public blockchain data is accessed. "
            "See our privacy policy for details."
        )
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton(f"🔍 View on Explorer", url=f"{chain_info['explorer_url']}{address}")],
            [InlineKeyboardButton("🔄 Check Another", callback_data="check_another"),
             InlineKeyboardButton("⭐ Go Premium", callback_data="wallet_upgrade_premium")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update message with results
        await checking_msg.edit_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Log successful check
        logger.info(f"Wallet balance check: User {username} ({user_id}) checked {chain} address {address[:10]}...")
        
    except Exception as e:
        logger.error(f"Error in walletbalance command: {e}")
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later.",
            parse_mode='Markdown'
        )

async def wallet_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks for wallet feature"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        await query.answer()
        
        if query.data == "check_another":
            await query.edit_message_text(
                "🔍 *Check Another Wallet*\n\n"
                "Use the command: `/walletbalance <chain> <address>`\n\n"
                "Supported chains: BTC, ETH\n\n"
                "Example:\n"
                "`/walletbalance BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`",
                parse_mode='Markdown'
            )
        
        elif query.data == "wallet_upgrade_premium":
            keyboard = [
                [InlineKeyboardButton("💳 Upgrade Now ($9.99/month)", url=f"{NOWPAYMENTS_CHECKOUT_URL}/premium")],
                [InlineKeyboardButton("ℹ️ Premium Benefits", callback_data="wallet_premium_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⭐ *Upgrade to Premium*\n\n"
                "Premium benefits:\n"
                "• Unlimited wallet balance checks\n"
                "• Unlimited BIN lookups\n"
                "• 5 card generations per day\n"
                "• Priority support\n"
                "• Advanced features\n\n"
                "Only $9.99/month",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif query.data == "wallet_premium_info":
            keyboard = [
                [InlineKeyboardButton("💳 Get Premium", url=f"{NOWPAYMENTS_CHECKOUT_URL}/premium")],
                [InlineKeyboardButton("🔙 Back", callback_data="wallet_upgrade_premium")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⭐ *Premium Features*\n\n"
                "🔓 *Unlimited Access*:\n"
                "• Wallet balance checks\n"
                "• BIN lookups\n"
                "• Advanced BIN data\n\n"
                "💳 *Card Generation*:\n"
                "• 5 cards per day\n"
                "• AVS data included\n"
                "• Bulk export (CSV/JSON)\n\n"
                "🚀 *Premium Support*:\n"
                "• Priority assistance\n"
                "• Early access to features\n"
                "• API access (coming soon)\n\n"
                "💰 *Flexible Payment*:\n"
                "• Crypto payments accepted\n"
                "• Monthly billing\n"
                "• Cancel anytime",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif query.data == "wallet_limits_info":
            keyboard = [
                [InlineKeyboardButton("💳 Upgrade to Premium", url=f"{NOWPAYMENTS_CHECKOUT_URL}/premium")],
                [InlineKeyboardButton("🔙 Back", callback_data="check_another")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "ℹ️ *Usage Limits*\n\n"
                "**Free Tier:**\n"
                "• 3 wallet checks per day\n"
                "• 3 BIN lookups per day\n"
                "• Basic features only\n\n"
                "**Premium Tier ($9.99/month):**\n"
                "• Unlimited wallet checks\n"
                "• Unlimited BIN lookups\n"
                "• 5 card generations per day\n"
                "• Advanced features\n\n"
                "Limits reset daily at midnight UTC.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Error in wallet button callback: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

def register_crypto_handlers(application):
    """Register crypto balance checker handlers with the bot application"""
    # Command handler
    application.add_handler(CommandHandler("walletbalance", walletbalance))
    
    # Callback query handler for wallet-specific callbacks
    application.add_handler(CallbackQueryHandler(
        wallet_button_callback, 
        pattern="^(check_another|wallet_upgrade_premium|wallet_premium_info|wallet_limits_info)$"
    ))
    
    logger.info("Crypto balance checker handlers registered successfully")

# Test functions for development
async def test_crypto_checker():
    """Test function for development - not used in production"""
    checker = CryptoBalanceChecker()
    
    # Test BTC balance
    btc_result = await checker.get_wallet_balance('BTC', '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa')
    print(f"BTC Test Result: {btc_result}")
    
    # Test ETH balance
    eth_result = await checker.get_wallet_balance('ETH', '0x690B9A9E9aa1C9dB991C28d09DAAd5BBA6f6Fb73')
    print(f"ETH Test Result: {eth_result}")

if __name__ == "__main__":
    # Run tests if executed directly
    import asyncio
    asyncio.run(test_crypto_checker())
