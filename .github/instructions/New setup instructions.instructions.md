# CryptoBinChecker Bot Project Setup Instructions for VS Code and Copilot

This file consolidates all instructions, file contexts, and code for setting up the CryptoBinChecker Telegram bot (@BINSearchCCGBot). It aligns with your Cloudflare (`cryptobinchecker.cc`) and Google Cloud Platform (GCP) setup using Cloud Run for hosting, Cloud SQL for the BIN database, GCP Memorystore for Redis, Telegram webhooks, and all features from the prototype (including `/bulk` and `/export`). API keys are managed via `.env` for local testing and GCP Secret Manager for production. The privacy page is hosted on Cloudflare Pages.

Follow these instructions in VS Code. Use Copilot to assist with code completion, debugging, and questions. If Copilot needs clarification, refer to the questions in the original setup.

## Prerequisites
- **VS Code**: Installed with Python extension (`ms-python.python`).
- **GCP Account**: Project created (e.g., `cryptobinchecker`) with billing enabled and APIs for Cloud Run, Cloud SQL, Cloud Storage, Secret Manager, Memorystore.
- **Cloudflare Account**: `cryptobinchecker.cc` added with DNS configured.
- **Docker**: Installed for containerized deployment.
- **API Keys**: In `.env` for local testing; migrate to Secret Manager for production.
- **Database**: `merged_bin_data.csv` ready for Cloud SQL migration.
- **Adobe Tools**: For designing `card_template.png`, `promo.png`, and landing page.

## Project Structure
Create a folder `cryptobinchecker` in VS Code. Add the following files with the provided content:

### 1. requirements.txt
python-telegram-bot==20.7
pandas==2.2.2
redis==5.0.8
aiohttp==3.10.5
python-dotenv==1.0.1
google-cloud-storage==2.18.2
google-cloud-secret-manager==2.20.2
psycopg2-binary==2.9.9
flask==3.0.3
gunicorn==23.0.0
sendgrid==6.11.0
pillow==10.4.0
text### 2. .env (Local Testing Only - Delete Before Deployment)
TELEGRAM_TOKEN=your-telegram-token
ETHERSCAN_API_KEY=your-etherscan-key
COINGECKO_API_KEY=your-coingecko-key
NOWPAYMENTS_API_KEY=your-nowpayments-key
SENDGRID_API_KEY=your-sendgrid-key
GCP_PROJECT_ID=your-gcp-project-id
REDIS_HOST=your-memorystore-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-memorystore-redis-password
SQL_HOST=your-cloud-sql-host
SQL_DATABASE=bin_database
SQL_USER=your-sql-user
SQL_PASSWORD=your-sql-password
text### 3. Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8443", "final_bot_no_citations:app"]
text### 4. privacy.html (Host on Cloudflare Pages)



    <title>Privacy Policy - CryptoBinChecker</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f0f0; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #6e8efb; }
    </style>


    
        Privacy Policy
        CryptoBinChecker (@BINSearchCCGBot) collects minimal user data (Telegram ID, usage stats) to provide test card generation and crypto wallet checking services. We do not store payment information. Data is stored securely on Google Cloud Platform and protected by Cloudflare.
        Contact: support@cryptobinchecker.cc
    


```
5. sql_init.sql (For Cloud SQL Initialization)
textCREATE DATABASE bin_database;
\c bin_database
CREATE TABLE bins (
    bin VARCHAR(8),
    brand VARCHAR(50),
    type VARCHAR(50),
    category VARCHAR(50),
    issuer VARCHAR(100),
    country VARCHAR(50),
    bank_phone VARCHAR(50),
    bank_url VARCHAR(100)
);
CREATE INDEX idx_bin ON bins(bin);
6. final_bot_no_citations.py (Main Bot Code)
text"""
CryptoBinChecker Bot for Telegram
Bot Username: @BINSearchCCGBot
"""

import logging
import pandas as pd
import random
import hashlib
import json
import os
import io
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from google.cloud import secretmanager
import redis
import aiohttp
from dotenv import load_dotenv
from collections import defaultdict
import re
import psycopg2
from PIL import Image, ImageDraw, ImageFont

# Load environment variables
load_dotenv()
def get_secret(secret_id):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {e}")
        return os.getenv(secret_id.upper())

# Configuration
TOKEN = get_secret('telegram-token')
ETHERSCAN_API_KEY = get_secret('etherscan-api-key')
COINGECKO_API_KEY = get_secret('coingecko-api-key')
NOWPAYMENTS_API_KEY = get_secret('nowpayments-api-key')
SENDGRID_API_KEY = get_secret('sendgrid-api-key')
REDIS_HOST = get_secret('redis-host')
REDIS_PORT = int(get_secret('redis-port') or 6379)
REDIS_PASSWORD = get_secret('redis-password')
SQL_HOST = get_secret('sql-host')
SQL_DATABASE = get_secret('sql-database')
SQL_USER = get_secret('sql-user')
SQL_PASSWORD = get_secret('sql-password')

# Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
except redis.RedisError as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load database from Cloud SQL
def load_database():
    try:
        conn = psycopg2.connect(
            host=SQL_HOST,
            database=SQL_DATABASE,
            user=SQL_USER,
            password=SQL_PASSWORD
        )
        return pd.read_sql_query("SELECT * FROM bins", conn)
    except Exception as e:
        logger.error(f"Database load failed: {e}")
        return None
bin_database = load_database()

# Rate limiting
rate_limits = {
    'etherscan': {'limit': 1, 'tokens': 1, 'last_refill': time.time()},
    'coingecko': {'limit': 0.16, 'tokens': 0.16, 'last_refill': time.time()},
    'blockchain': {'limit': 1, 'tokens': 1, 'last_refill': time.time()}
}
free_usage = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})

def check_rate_limit(api: str) -> bool:
    now = time.time()
    cache_key = f"rate_limit:{api}"
    if redis_client and redis_client.exists(cache_key):
        tokens, last_refill = redis_client.hmget(cache_key, 'tokens', 'last_refill')
        tokens = float(tokens or rate_limits[api]['tokens'])
        last_refill = float(last_refill or rate_limits[api]['last_refill'])
    else:
        tokens, last_refill = rate_limits[api]['tokens'], rate_limits[api]['last_refill']
    elapsed = now - last_refill
    tokens = min(rate_limits[api]['limit'], tokens + elapsed * rate_limits[api]['limit'])
    if redis_client:
        redis_client.hset(cache_key, mapping={'tokens': tokens, 'last_refill': now})
    rate_limits[api]['tokens'], rate_limits[api]['last_refill'] = tokens, now
    if tokens >= 1:
        rate_limits[api]['tokens'] -= 1
        if redis_client:
            redis_client.hset(cache_key, 'tokens', tokens)
        return True
    return False

# Known test BIN prefixes
test_bins = [
    '411111', '555555', '378282', '378734', '371449', '601111', '360000',
    '305693', '385200', '601100', '353011', '356600', '630495', '630490'
]

# AVS postal dataset
avs_data = {
    'US': ['10001', '90210', '60601', '94105', '33101'],
    'IT': ['00100', '20121', '80100', '40100', '50100'],
    'GB': ['SW1A 1AA', 'M1 1AA', 'B1 1AA', 'L1 1AA', 'CF1 1AA'],
    'CA': ['M5V 3A8', 'V6B 1A1', 'T2P 1A1', 'H3B 1A1', 'K1A 0A6'],
    'AU': ['2000', '3000', '4000', '5000', '6000'],
    'DE': ['10115', '20095', '80331', '50667', '01067'],
    'FR': ['75001', '69001', '13001', '31000', '59000']
}

def validate_bin(bin_input, bin_database):
    """Enhanced BIN validation with test BIN filtering and database checking"""
    bin_str = str(bin_input).strip()
    if not re.match(r'^\d{6,8}$', bin_str):
        return None, "Invalid BIN (must be 6-8 digits)."
    if any(bin_str.startswith(test) for test in test_bins):
        return None, "Test BIN blocked for realistic generation. Use a production-like BIN."
    if bin_database is not None:
        matches = bin_database[bin_database['bin'].astype(str).str.startswith(bin_str)]
        if matches.empty:
            return None, "BIN not found in 458k+ database. Use /binlookup or /binsearch first."
        info = matches.iloc[0].to_dict()
        return info, "Valid BIN."
    return None, "Database not available for validation."

def get_card_length(brand, card_type):
    """Get appropriate card length based on brand and type"""
    brand = (brand or "").upper()
    card_type = (card_type or "").upper()
    if "AMERICAN EXPRESS" in brand or "AMEX" in brand:
        return 15
    elif "DINERS" in brand:
        return random.choice([14, 16])
    elif "DISCOVER" in brand:
        return random.choice([16, 19])
    elif "PREPAID" in card_type:
        return 16
    return 16

def get_user_session(user_id):
    """Get or create user session data"""
    cache_key = f"user_session:{user_id}"
    if redis_client and redis_client.exists(cache_key):
        return json.loads(redis_client.get(cache_key))
    session = {'generations_today': 0, 'total_cards_created': 0, 'last_activity': None, 'premium_status': False}
    if redis_client:
        redis_client.setex(cache_key, 30*24*3600, json.dumps(session))
    return session

def is_user_premium(user_id):
    """Check premium status"""
    if redis_client:
        return redis_client.get(f"premium:{user_id}") == "active"
    return False

def can_generate_card(user_id):
    """Check if user can generate cards (rate limiting)"""
    session = get_user_session(user_id)
    today = datetime.now().date()
    if session['last_activity']:
        try:
            last_date = datetime.fromisoformat(session['last_activity']).date()
            if last_date != today:
                session['generations_today'] = 0
        except:
            session['generations_today'] = 0
    if not is_user_premium(user_id) and session['generations_today'] >= 5:
        return False
    return True

def record_generation(user_id):
    """Record a card generation"""
    session = get_user_session(user_id)
    session['generations_today'] += 1
    session['total_cards_created'] += 1
    session['last_activity'] = datetime.now().isoformat()
    if redis_client:
        redis_client.setex(f"user_session:{user_id}", 30*24*3600, json.dumps(session))

def validate_card_number(number):
    """Luhn algorithm validation"""
    digits = [int(d) for d in str(number)]
    checksum = 0
    for i in range(len(digits) - 2, -1, -2):
        doubled = digits[i] * 2
        if doubled > 9:
            doubled -= 9
        checksum += doubled
    for i in range(len(digits) - 1, -1, -2):
        checksum += digits[i]
    return checksum % 10 == 0

def luhn_checksum(card_number):
    """Alternative Luhn implementation"""
    return validate_card_number(card_number)

def create_card_number(bin_prefix, info=None):
    """Enhanced card generation with weighted digits and filters"""
    if info is None:
        info = {}
    if len(bin_prefix) < 6:
        bin_prefix = bin_prefix.ljust(6, '0')
    length = get_card_length(info.get('brand'), info.get('type'))
    remaining_length = length - len(bin_prefix) - 1
    digits = []
    used_digits = {str(i): 0 for i in range(10)}
    for _ in range(remaining_length):
        while True:
            candidate = random.choices(range(10), weights=[2, 2, 2, 2, 2, 2, 1, 1, 1, 1])[0]
            if used_digits[str(candidate)] < 2:
                digits.append(str(candidate))
                used_digits[str(candidate)] += 1
                break
    random.shuffle(digits)
    partial = str(bin_prefix) + ''.join(digits)
    max_attempts = 100
    attempts = 0
    while attempts < max_attempts:
        has_three_same = any(partial[i:i+3] == d*3 for d in '0123456789' for i in range(len(partial)-2))
        has_ascending = any(
            len(partial) > i+2 and
            int(partial[i+2]) - int(partial[i+1]) == 1 and
            int(partial[i+1]) - int(partial[i]) == 1
            for i in range(len(partial)-2)
        )
        has_descending = any(
            len(partial) > i+2 and
            int(partial[i]) - int(partial[i+1]) == 1 and
            int(partial[i+1]) - int(partial[i+2]) == 1
            for i in range(len(partial)-2)
        )
        if not (has_three_same or has_ascending or has_descending):
            break
        random.shuffle(digits)
        partial = str(bin_prefix) + ''.join(digits)
        attempts += 1
    for check_digit in range(10):
        full_number = partial + str(check_digit)
        if luhn_checksum(full_number):
            return full_number
    return None

def generate_cvv(card_number, expiry=None, seed=True):
    """Enhanced CVV generation"""
    length = 4 if card_number.startswith(('34', '37')) else 3
    if seed and expiry:
        hash_obj = hashlib.sha256(f"{card_number}{expiry}".encode())
        cvv = int(hash_obj.hexdigest(), 16) % (10 ** length)
        return f"{cvv:0{length}d}"
    return f"{random.randint(10**(length-1), 10**length - 1)}"

def generate_expiry(card_type=None):
    """Enhanced expiry generation"""
    card_type = (card_type or "").upper()
    if "PREPAID" in card_type:
        months = random.randint(12, 24)
    else:
        months = random.randint(36, 60)
    expiry_date = datetime.now() + timedelta(days=30 * months)
    return expiry_date.strftime("%m/%Y")

def format_card_display(number, cvv, expiry, info=None):
    """Create card image with Adobe-designed template"""
    try:
        img = Image.open('card_template.png')
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('arial.ttf', 24)
        draw.text((50, 50), number, fill='black', font=font)
        draw.text((50, 100), f"CVV: {cvv}", fill='black', font=font)
        draw.text((50, 150), f"Exp: {expiry}", fill='black', font=font)
        img_path = f"card_{number}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        # Fallback to ASCII
        return f"""
++++++++++++++++++++++++++++++++++++++++++++++++++++
+                                                  +
+          CryptoBinChecker Bot                    +
+                                                  +
+                                                  +
+                     {number}                   +
+                                                  +
+                                                  +
+          CVV  {cvv}                Exp {expiry}          +
+                                                  +
++++++++++++++++++++++++++++++++++++++++++++++++++++"""

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    session = get_user_session(user_id)
    status = "PREMIUM" if is_user_premium(user_id) else "FREE"
    welcome_message = f"""Welcome {user_name}!

CryptoBinChecker Bot (Enhanced v2.0)
Status: {status}

FREE FEATURES:
- /binlookup <number> - Search 458K+ BIN database
- /binsearch <criteria> - Advanced search options
- /generate <bin> - Create test card (5 daily limit)
- /statistics - Database information
- /walletbalance <chain> <address> - Check crypto wallet balance

PREMIUM FEATURES:
- /generate_with_avs <bin> <country> - Generate with postal codes
- /bulk <bin> <count> - Generate up to 1000 cards
- /export <bin> <count> <format> - Download files
- Unlimited daily generations
- Priority support access

NEW ENHANCEMENTS:
✅ Production-like BIN validation
✅ Enhanced digit patterns
✅ Dynamic card lengths
✅ AVS support (7 countries: US, IT, GB, CA, AU, DE, FR)
✅ Improved expiry/CVV algorithms

YOUR STATS:
- Daily generations: {session['generations_today']}/5 (Free) or unlimited (Premium)
- Total cards created: {session['total_cards_created']}

UPGRADE: /premium
HELP: /help
PRIVACY: https://cryptobinchecker.cc/privacy

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
    help_text = """COMMAND REFERENCE

FREE COMMANDS:
/start - Main menu and status
/binlookup 413567 - Look up BIN details
/binsearch brand=VISA - Search database
/generate 413567 - Create single test card
/statistics - Database statistics
/walletbalance eth 0x123... - Check crypto wallet balance
/checkwallet 0x123... eth - Check wallet with explorer links

PREMIUM COMMANDS:
/generate_with_avs 413567 US - Generate with postal code
/bulk 413567 25 - Generate multiple cards
/export 413567 50 json - Export to file
/premium - Upgrade information

SEARCH EXAMPLES:
/binsearch brand=VISA
/binsearch country=USA
/binsearch issuer=Chase
/binsearch type=CREDIT

AVS SUPPORTED COUNTRIES:
US, IT, GB, CA, AU, DE, FR

IMPORTANT NOTES:
- All generated cards are TEST CARDS only
- Valid format but NOT real accounts
- For development and testing purposes
- Never attempt real transactions

PRIVACY: https://cryptobinchecker.cc/privacy"""
    await update.message.reply_text(help_text)

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate single card"""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "Usage: /generate <bin>\nExample: /generate 413567\nTip: Use /binlookup 413567 first"
        )
        return
    if not can_generate_card(user_id):
        keyboard = [[InlineKeyboardButton("Upgrade to Premium", callback_data="show_premium")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "DAILY LIMIT REACHED (5 cards for free users)\nPREMIUM BENEFITS:\n- Unlimited generations\n- Bulk creation\n- Export capabilities\n- Priority support",
            reply_markup=reply_markup
        )
        return
    bin_input = context.args[0].strip()
    try:
        info, error_msg = validate_bin(bin_input, bin_database)
        if info is None:
            await update.message.reply_text(f"{error_msg}\nWARNING: FOR ETHICAL TESTING ONLY.")
            return
        card_number = create_card_number(bin_input, info)
        if not card_number:
            await update.message.reply_text("Error: Cannot generate valid card from this BIN")
            return
        expiry = generate_expiry(info.get('type'))
        cvv = generate_cvv(card_number, expiry, seed=True)
        bin_details = f"""
BIN INFORMATION:
Brand: {info.get('brand', 'Unknown')}
Type: {info.get('type', 'Unknown')}
Issuer: {info.get('issuer', 'Unknown')}
Country: {info.get('country', 'Unknown')}
Length: {len(card_number)} digits"""
        card_display = format_card_display(card_number, cvv, expiry, info)
        record_generation(user_id)
        session = get_user_session(user_id)
        response = f"""TEST CARD GENERATED

{bin_details}

Usage: {session['generations_today']}/5 daily
WARNING: FOR ETHICAL TESTING ONLY!

Want unlimited + AVS support? /premium"""
        if card_display.endswith('.png'):
            with open(card_display, 'rb') as img_file:
                await update.message.reply_photo(photo=img_file, caption=response, parse_mode='Markdown')
            os.remove(card_display)
        else:
            await update.message.reply_text(f"```{card_display}```{response}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Generation error: {e}")
        await update.message.reply_text("Generation failed. Please try again.")

async def binlookup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BIN lookup command"""
    if not context.args:
        await update.message.reply_text("Usage: /binlookup <bin>\nExample: /binlookup 413567")
        return
    if bin_database is None:
        await update.message.reply_text("Database not available")
        return
    bin_input = context.args[0].strip()
    results = bin_database[bin_database['bin'].astype(str).str.startswith(bin_input)]
    if results.empty:
        await update.message.reply_text(f"No data found for BIN: {bin_input}\nTry /binsearch")
        return
    info = results.iloc[0]
    response = f"""BIN LOOKUP RESULT - {bin_input}

COMPLETE DETAILS:
- BIN: {info['bin']}
- Brand: {info['brand']}
- Type: {info['type']}
- Category: {info.get('category', 'N/A')}
- Issuer: {info['issuer']}
- Country: {info['country']}
- Bank Phone: {info.get('bank_phone', 'N/A')}
- Bank URL: {info.get('bank_url', 'N/A')}

Found in our 458K+ BIN database!
Generate card: /generate {bin_input}
Search similar: /binsearch issuer={info['issuer'][:15]}"""
    await update.message.reply_text(response)

async def binsearch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BIN search command"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /binsearch <criteria>\nExamples:\n/binsearch brand=VISA\n/binsearch country=USA"
        )
        return
    if bin_database is None:
        await update.message.reply_text("Database not available")
        return
    search_term = ' '.join(context.args).strip()
    try:
        if '=' in search_term:
            field, value = search_term.split('=', 1)
            field = field.strip().lower()
            value = value.strip()
            if field in ['brand', 'country', 'issuer', 'type']:
                matches = bin_database[bin_database[field].str.contains(value, case=False, na=False)].head(10)
            else:
                await update.message.reply_text("Valid fields: brand, country, issuer, type")
                return
        else:
            mask = (bin_database['brand'].str.contains(search_term, case=False, na=False) |
                    bin_database['country'].str.contains(search_term, case=False, na=False) |
                    bin_database['issuer'].str.contains(search_term, case=False, na=False))
            matches = bin_database[mask].head(10)
        if matches.empty:
            await update.message.reply_text(f"No results found for: {search_term}")
            return
        response = f"SEARCH RESULTS - '{search_term}'\n\n"
        for _, row in matches.iterrows():
            response += f"{row['bin']} - {row['brand']} {row['type']}\n  {row['issuer']} ({row['country']})\n\n"
        response += f"Showing {len(matches)} results\nGenerate: /generate <bin>"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text("Search error. Please check format.")

async def statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Database statistics"""
    if bin_database is None:
        await update.message.reply_text("Database not available")
        return
    total_bins = len(bin_database)
    unique_brands = bin_database['brand'].nunique()
    unique_countries = bin_database['country'].nunique()
    unique_issuers = bin_database['issuer'].nunique()
    top_brands = bin_database['brand'].value_counts().head(5)
    top_countries = bin_database['country'].value_counts().head(5)
    response = f"""DATABASE STATISTICS

OVERVIEW:
- Total BIN Records: {total_bins:,}
- Unique Brands: {unique_brands:,}
- Unique Countries: {unique_countries:,}
- Unique Issuers: {unique_issuers:,}

TOP BRANDS:"""
    for brand, count in top_brands.items():
        response += f"\n- {brand}: {count:,} BINs"
    response += f"\n\nTOP COUNTRIES:"
    for country, count in top_countries.items():
        response += f"\n- {country}: {count:,} BINs"
    response += f"\n\nMost comprehensive BIN database on Telegram!"
    await update.message.reply_text(response)

async def generate_with_avs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate card with AVS support"""
    user_id = update.effective_user.id
    if not is_user_premium(user_id):
        keyboard = [[InlineKeyboardButton("Upgrade to Premium", callback_data="show_premium")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "AVS GENERATION (Premium Feature)\nGenerate cards with postal codes for address verification testing.\nUpgrade to access!",
            reply_markup=reply_markup
        )
        return
    if len(context.args) < 2:
        supported_countries = ', '.join(avs_data.keys())
        await update.message.reply_text(
            f"Usage: /generate_with_avs <bin> <country_code>\nExample: /generate_with_avs 413567 US\nSupported countries: {supported_countries}"
        )
        return
    bin_input = context.args[0].strip()
    country = context.args[1].upper()
    if country not in avs_data:
        supported_countries = ', '.join(avs_data.keys())
        await update.message.reply_text(f"Supported countries: {supported_countries}\nExpanding coverage regularly!")
        return
    try:
        info, error_msg = validate_bin(bin_input, bin_database)
        if info is None:
            await update.message.reply_text(f"{error_msg}\nWARNING: FOR ETHICAL TESTING ONLY.")
            return
        card_number = create_card_number(bin_input, info)
        if not card_number:
            await update.message.reply_text("Generation failed.")
            return
        expiry = generate_expiry(info.get('type'))
        cvv = generate_cvv(card_number, expiry, seed=True)
        postal = random.choice(avs_data[country])
        card_display = format_card_display(card_number, cvv, expiry, info)
        bin_details = f"""
BIN INFORMATION:
Brand: {info.get('brand', 'Unknown')}
Type: {info.get('type', 'Unknown')}
Issuer: {info.get('issuer', 'Unknown')}
Country: {info.get('country', 'Unknown')}

AVS DETAILS:
Postal Code: {postal}
Country: {country}"""
        response = f"""PREMIUM AVS CARD GENERATED

{bin_details}

WARNING: FOR ETHICAL TESTING ONLY!
Perfect for sandbox testing with address verification."""
        if card_display.endswith('.png'):
            with open(card_display, 'rb') as img_file:
                await update.message.reply_photo(photo=img_file, caption=response, parse_mode='Markdown')
            os.remove(card_display)
        else:
            await update.message.reply_text(f"```{card_display}```{response}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"AVS Generation error: {e}")
        await update.message.reply_text("AVS generation failed. Please try again.")

async def walletbalance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check crypto wallet balance"""
    user_id = str(update.effective_user.id)
    if time.time() - free_usage[user_id]['last_reset'] > 86400:
        free_usage[user_id] = {'count': 0, 'last_reset': time.time()}
    is_premium = is_user_premium(user_id)
    if not is_premium and free_usage[user_id]['count'] >= 3:
        await update.message.reply_text(
            "Free limit reached! Non-premium users pay $10/check. Use /premium for $9.99/month (unlimited $5/checks).",
            parse_mode='Markdown'
        )
        return
    if is_premium and free_usage[user_id]['count'] >= 3:
        await update.message.reply_text(
            "Premium: $5/check after 3 free daily checks. Use /premium to renew.",
            parse_mode='Markdown'
        )
        return
    free_usage[user_id]['count'] += 1
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /walletbalance <chain> <address> (e.g., eth 0x123... or btc 1ABC...)")
        return
    chain = context.args[0].strip().lower()
    address = context.args[1].strip()
    cache_key = f"balance:{chain}:{address}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                await update.message.reply_text(
                    f"{cached}\n*Disclaimer*: For informational use only (cached, valid for 5 min).\n*Privacy*: https://cryptobinchecker.cc/privacy",
                    parse_mode='Markdown'
                )
                return
        except redis.RedisError as e:
            logger.error(f"Redis get failed: {e}")
    async with aiohttp.ClientSession() as session:
        try:
            if chain == 'eth':
                if not check_rate_limit('etherscan'):
                    raise ValueError("Rate limit exceeded for Etherscan")
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                async with session.get(url, timeout=5) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data['status'] == "1":
                        balance_wei = int(data['result'])
                        balance = balance_wei / 10**18
                        coin_id = 'ethereum'
                    else:
                        raise ValueError("Invalid ETH address or API error")
            elif chain == 'btc':
                if not check_rate_limit('blockchain'):
                    raise ValueError("Rate limit exceeded for Blockchain.com")
                url = f"https://blockchain.info/balance?active={address}"
                async with session.get(url, timeout=5) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if address in data:
                        balance_sat = data[address]['final_balance']
                        balance = balance_sat / 10**8
                        coin_id = 'bitcoin'
                    else:
                        raise ValueError("Invalid BTC address or API error")
            elif chain == 'sol' and is_premium:
                if not check_rate_limit('solscan'):
                    raise ValueError("Rate limit exceeded for Solscan")
                url = f"https://public-api.solscan.io/account/{address}"
                async with session.get(url, headers={"accept": "application/json"}, timeout=5) as response:
                    data = await response.json()
                    if data.get("lamports") is not None:
                        balance = int(data["lamports"]) / 1e9
                        coin_id = 'solana'
                    else:
                        raise ValueError("Invalid SOL address or API error")
            else:
                await update.message.reply_text("Supported chains: eth, btc, sol (premium)")
                return
            if not check_rate_limit('coingecko'):
                raise ValueError("Rate limit exceeded for CoinGecko")
            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            headers = {"x-cg-demo-api-key": COINGECKO_API_KEY} if COINGECKO_API_KEY else {}
            async with session.get(price_url, headers=headers, timeout=5) as price_response:
                price_response.raise_for_status()
                price_data = await price_response.json()
                if coin_id not in price_data:
                    raise ValueError("CoinGecko price fetch failed")
                usd_price = price_data[coin_id]['usd']
                usd_value = balance * usd_price
                response_text = f"*{chain.upper()} Balance*: {balance:.4f} {chain.upper()} (${usd_value:.2f})"
                if redis_client:
                    try:
                        if redis_client.dbsize() > 9000:
                            redis_client.delete(redis_client.lrange('keys', -100, -1))
                        redis_client.lpush('keys', cache_key)
                        redis_client.setex(cache_key, 300, response_text)
                    except redis.RedisError as e:
                        logger.error(f"Redis set failed: {e}")
                await update.message.reply_text(
                    f"{response_text}\n*Disclaimer*: For informational use only.\n*Privacy*: https://cryptobinchecker.cc/privacy\n*Unlock Solana & alerts with /premium!*",
                    parse_mode='Markdown'
                )
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            await update.message.reply_text(f"Error: API request failed ({str(e)})")
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await update.message.reply_text("Error: Something went wrong.")

async def checkwallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check wallet balance with explorer links"""
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /checkwallet <address> [coin] (BTC/ETH/SOL)")
        return
    address = args[0]
    coin = args[1].upper() if len(args) > 1 else "ETH"
    user_id = str(update.effective_user.id)
    async with aiohttp.ClientSession() as session:
        try:
            if coin == "ETH":
                if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
                    await update.message.reply_text("❌ Invalid Ethereum address!")
                    return
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                async with session.get(url, timeout=5) as response:
                    resp = await response.json()
                    if resp.get("status") == "1":
                        balance = int(resp["result"]) / 1e18
                        reply = f"\U0001F4B0 <b>Ethereum Wallet</b>\n<b>Address:</b> <code>{address}</code>\n<b>Balance:</b> {balance:.6f} ETH"
                        keyboard = [[InlineKeyboardButton("View on Etherscan", url=f"https://etherscan.io/address/{address}")]]
                        await update.message.reply_text(reply, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
                    else:
                        await update.message.reply_text("⚠️ Error fetching ETH balance.")
            elif coin == "BTC":
                if not re.match(r'^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,39}$', address):
                    await update.message.reply_text("❌ Invalid Bitcoin address!")
                    return
                url = f"https://blockchain.info/balance?active={address}"
                async with session.get(url, timeout=5) as response:
                    data = await response.json()
                    if address in data:
                        balance = data[address]['final_balance'] / 1e8
                        reply = f"\U0001F4B0 <b>Bitcoin Wallet</b>\n<b>Address:</b> <code>{address}</code>\n<b>Balance:</b> {balance:.8f} BTC"
                        keyboard = [[InlineKeyboardButton("View on Blockchain.com", url=f"https://blockchain.info/address/{address}")]]
                        await update.message.reply_text(reply, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
                    else:
                        await update.message.reply_text("⚠️ Error fetching BTC balance.")
            elif coin == "SOL" and is_user_premium(user_id):
                if not (len(address) in [32, 44] and re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address)):
                    await update.message.reply_text("❌ Invalid Solana address!")
                    return
                url = f"https://public-api.solscan.io/account/{address}"
                headers = {"accept": "application/json"}
                async with session.get(url, headers=headers, timeout=5) as response:
                    resp = await response.json()
                    if resp.get("lamports") is not None:
                        balance = int(resp["lamports"]) / 1e9
                        reply = f"\U0001F4B0 <b>Solana Wallet</b>\n<b>Address:</b> <code>{address}</code>\n<b>Balance:</b> {balance:.6f} SOL"
                        keyboard = [[InlineKeyboardButton("View on Solscan", url=f"https://solscan.io/account/{address}")]]
                        await update.message.reply_text(reply, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
                    else:
                        await update.message.reply_text("⚠️ Error fetching SOL balance.")
            else:
                await update.message.reply_text("Unsupported coin or premium required. Use BTC, ETH, or SOL (premium).")
        except Exception as e:
            logger.error(f"Checkwallet error: {e}")
            await update.message.reply_text("Error: Something went wrong.")

async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium upgrade information"""
    user_id = str(update.effective_user.id)
    is_premium = is_user_premium(user_id)
    if is_premium:
        await update.message.reply_text(
            "You're already a Premium member! Enjoy unlimited checks & $5/check pricing.",
            parse_mode='Markdown'
        )
        return
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.nowpayments.io/v1/payment"
            payload = {
                "price_amount": 9.99,
                "price_currency": "usd",
                "pay_currency": "btc",
                "order_id": f"premium_{user_id}_{int(time.time())}",
                "order_description": "CryptoBinChecker Premium Subscription",
                "ipn_callback_url": "https://cryptobinchecker.cc/ipn",
                "success_url": "https://t.me/BINSearchCCGBot",
                "cancel_url": "https://t.me/BINSearchCCGBot"
            }
            headers = {"x-api-key": NOWPAYMENTS_API_KEY}
            async with session.post(url, json=payload, headers=headers, timeout=5) as response:
                response.raise_for_status()
                data = await response.json()
                payment_url = data.get("payment_url")
                if payment_url:
                    await update.message.reply_text(
                        f"Unlock Premium for $9.99/month! Pay with crypto:\n{payment_url}\n*Privacy*: https://cryptobinchecker.cc/privacy",
                        parse_mode='Markdown'
                    )
                else:
                    raise ValueError("Failed to generate payment link")
    except Exception as e:
        logger.error(f"NOWPayments error: {e}")
        await update.message.reply_text("Error: Payment link generation failed.")

async def bulk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate multiple cards"""
    user_id = str(update.effective_user.id)
    if not is_user_premium(user_id):
        await update.message.reply_text("Bulk generation is a Premium feature. Use /premium to upgrade.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /bulk <bin> <count>\nExample: /bulk 413567 25")
        return
    bin_input, count = context.args[0].strip(), int(context.args[1])
    if count > 1000:
        await update.message.reply_text("Maximum 1000 cards per request.")
        return
    info, error_msg = validate_bin(bin_input, bin_database)
    if info is None:
        await update.message.reply_text(error_msg)
        return
    cards = []
    for _ in range(count):
        card_number = create_card_number(bin_input, info)
        if card_number:
            expiry = generate_expiry(info.get('type'))
            cvv = generate_cvv(card_number, expiry)
            cards.append({'number': card_number, 'cvv': cvv, 'expiry': expiry})
    response = f"Generated {len(cards)} cards:\n" + "\n".join([f"{c['number']} | CVV: {c['cvv']} | Exp: {c['expiry']}" for c in cards])
    await update.message.reply_text(response, parse_mode='Markdown')

async def export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export cards to file"""
    user_id = str(update.effective_user.id)
    if not is_user_premium(user_id):
        await update.message.reply_text("Export is a Premium feature. Use /premium to upgrade.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /export <bin> <count> <format>\nExample: /export 413567 50 json")
        return
    bin_input, count, fmt = context.args[0].strip(), int(context.args[1]), context.args[2].lower()
    if fmt not in ['json', 'csv', 'xml']:
        await update.message.reply_text("Supported formats: json, csv, xml")
        return
    info, error_msg = validate_bin(bin_input, bin_database)
    if info is None:
        await update.message.reply_text(error_msg)
        return
    cards = []
    for _ in range(count):
        card_number = create_card_number(bin_input, info)
        if card_number:
            expiry = generate_expiry(info.get('type'))
            cvv = generate_cvv(card_number, expiry)
            cards.append({'number': card_number, 'cvv': cvv, 'expiry': expiry})
    if fmt == 'json':
        output = json.dumps(cards)
        filename = f'cards_{user_id}.json'
        with open(filename, 'w') as f:
            f.write(output)
        await update.message.reply_document(document=open(filename, 'rb'), filename='cards.json')
        os.remove(filename)
    elif fmt == 'csv':
        import csv
        filename = f'cards_{user_id}.csv'
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['number', 'cvv', 'expiry'])
            writer.writeheader()
            writer.writerows(cards)
        await update.message.reply_document(document=open(filename, 'rb'), filename='cards.csv')
        os.remove(filename)
    elif fmt == 'xml':
        from xml.etree.ElementTree import Element, tostring
        root = Element('cards')
        for card in cards:
            card_elem = Element('card')
            for key, value in card.items():
                elem = Element(key)
                elem.text = value
                card_elem.append(elem)
            root.append(card_elem)
        filename = f'cards_{user_id}.xml'
        with open(filename, 'wb') as f:
            f.write(tostring(root))
        await update.message.reply_document(document=open(filename, 'rb'), filename='cards.xml')
        os.remove(filename)

async def marketing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote bot features"""
    await update.message.reply_photo(
        photo='https://cryptobinchecker.cc/assets/promo.png',
        caption="Join CryptoBinChecker for test card generation and crypto wallet checks! Visit cryptobinchecker.cc for more."
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    if query.data == "show_premium":
        await premium_handler(update, context)
    elif query.data == "activate_premium":
        user_id = query.from_user.id
        await query.edit_message_text(
            text="PREMIUM ACTIVATED! (Demo Mode)\nYou now have:\n- Unlimited generations\n- Bulk creation\n- Export functionality\n- Priority support\nTry: /bulk 413567 25\nPrivacy: https://cryptobinchecker.cc/privacy"
        )
    elif query.data == "compare_features":
        comparison_text = """DETAILED FEATURE COMPARISON

OUR BOT vs COMPETITORS:
GENERATION FEATURES:
- Free: 5/day + Enhanced algorithms
- Premium: Unlimited + Bulk + AVS
- Competitors: Basic numbers only
DATABASE FEATURES:
- 458K+ BINs with validation
- Competitors: Limited data
SECURITY FEATURES:
- Test BIN blocking + Digit filters
- Competitors: Basic generation
EXPORT FEATURES:
- Premium: JSON/CSV/XML + AVS
- Competitors: None
AVS SUPPORT:
- Premium: 7 countries
- Competitors: Not available
PRICING:
- Premium: $9.99/month
- Competitors: $29+/month"""
        await query.edit_message_text(text=comparison_text)

async def error_handler(update, context):
    """Error handling"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    logger.info("Starting CryptoBinChecker Bot...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("generate", generate_handler))
    application.add_handler(CommandHandler("generate_with_avs", generate_with_avs_handler))
    application.add_handler(CommandHandler("binlookup", binlookup_handler))
    application.add_handler(CommandHandler("binsearch", binsearch_handler))
    application.add_handler(CommandHandler("statistics", statistics_handler))
    application.add_handler(CommandHandler("walletbalance", walletbalance_handler))
    application.add_handler(CommandHandler("checkwallet", checkwallet_handler))
    application.add_handler(CommandHandler("premium", premium_handler))
    application.add_handler(CommandHandler("bulk", bulk_handler))
    application.add_handler(CommandHandler("export", export_handler))
    application.add_handler(CommandHandler("marketing", marketing_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_error_handler(error_handler)
    webhook_url = "https://cryptobinchecker.cc/webhook"
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=webhook_url
    )
    logger.info("Bot is running with webhook!")

if __name__ == "__main__":
    main()