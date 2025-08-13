# BIN Search Credit Card Generator Bot 🤖�

An advanced Telegram bot for BIN (Bank Identification Number) lookup and ethical credit card test generation, featuring a comprehensive database of 458,000+ BIN records with enhanced security algorithms.

## 🌟 Features

### 🆓 Free Features
- **BIN Lookup** - Search 458K+ BIN database instantly
- **Advanced Search** - Filter by brand, country, issuer, type
- **Test Card Generation** - 5 enhanced cards daily with CVV/expiry
- **Database Statistics** - Comprehensive BIN analytics

### 💎 Premium Features  
- **Unlimited Generation** - No daily limits
- **AVS Support** - Generate cards with postal codes (7 countries)
- **Bulk Generation** - Create up to 1000 cards at once
- **Export Capabilities** - JSON/CSV/XML formats
- **Enhanced Algorithms** - Production-like validation

## 🛡️ Security Enhancements v2.0

### Enhanced BIN Validation
- ✅ **Test BIN Blocking** - Prevents sandbox BINs (411111, 555555, etc.)
- ✅ **Database Validation** - Ensures production-like BINs only
- ✅ **Dynamic Length** - Correct card lengths per brand/type

### Advanced Generation Algorithm
- ✅ **Weighted Digits** - Natural 0-5 distribution patterns
- ✅ **Pattern Filtering** - No 3 identical/consecutive digits
- ✅ **Enhanced CVV** - Seeded generation with SHA256
- ✅ **Smart Expiry** - 1-2 years prepaid, 3-5 years regular

### AVS (Address Verification) Support
- ✅ **7 Countries** - US, IT, GB, CA, AU, DE, FR
- ✅ **Realistic Postal Codes** - Major cities per country
- ✅ **Premium Feature** - Enhanced testing capabilities

## 📁 Project Structure

```
Merge BINs/
├── BINSearchCCGbot.py              # Main enhanced Telegram bot
├── merged_bin_data.csv             # 458K+ BIN database
├── requirements_clean.txt          # Python dependencies
├── merge_bin_databases.py          # Database merge utility
├── ENHANCEMENT_IMPLEMENTATION_SUMMARY.md  # Technical details
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_clean.txt
```

### 2. Configure Bot Token
Edit `BINSearchCCGbot.py` and replace:
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"
```

### 3. Run the Bot
```bash
python BINSearchCCGbot.py
```

## 💬 Bot Commands

### Free Commands
```
/start                    - Welcome message and features
/help                     - Complete command reference
/binlookup 413567        - Look up BIN details
/binsearch brand=VISA    - Search database
/generate 413567         - Create enhanced test card
/statistics              - Database overview
```

### Premium Commands
```
/generate_with_avs 413567 US  - Generate with postal code
/bulk 413567 25              - Generate multiple cards
/export 413567 50 json       - Export to file
/premium                     - Upgrade information
```

## 🔍 Search Examples

```
/binsearch brand=VISA           # Find all Visa cards
/binsearch country=USA          # US-issued cards
/binsearch issuer=Chase         # Chase Bank cards
/binsearch type=CREDIT          # Credit cards only
/binsearch brand=VISA country=USA  # Combined search
```

## 🌍 AVS Supported Countries

| Country | Code | Example Cities |
|---------|------|----------------|
| 🇺🇸 United States | US | NYC, LA, Chicago, SF, Miami |
| 🇮🇹 Italy | IT | Rome, Milan, Naples, Bologna |
| 🇬🇧 United Kingdom | GB | London, Manchester, Birmingham |
| 🇨🇦 Canada | CA | Toronto, Vancouver, Calgary |
| 🇦🇺 Australia | AU | Sydney, Melbourne, Brisbane |
| 🇩🇪 Germany | DE | Berlin, Hamburg, Munich |
| 🇫🇷 France | FR | Paris, Lyon, Marseille |

## 🔬 Technical Specifications

### Enhanced Algorithm Features
- **Luhn Validation** - All cards pass checksum verification
- **Realistic Patterns** - Weighted digit distribution (0-5 favored)
- **Security Filters** - Prevents unrealistic number sequences
- **Brand Compliance** - Correct lengths per card type

### Database Coverage
- **458,051 BIN Records** - Comprehensive global coverage
- **Real-time Validation** - Production BIN verification
- **Multiple Brands** - Visa, Mastercard, Amex, Discover, JCB, etc.
- **Global Reach** - 200+ countries and territories

## ⚠️ Important Disclaimer

**FOR ETHICAL TESTING ONLY**

All generated cards are for:
- ✅ Software development testing
- ✅ Payment gateway sandbox testing  
- ✅ Educational purposes
- ✅ Security research

**NEVER use for:**
- ❌ Real transactions
- ❌ Fraud or illegal activities
- ❌ Unauthorized testing
- ❌ Production environments

## 🏆 Competitive Advantages

| Feature | Our Bot | Competitors |
|---------|---------|-------------|
| **BIN Database** | 458K+ records | Limited |
| **Generation Quality** | Enhanced algorithms | Basic |
| **AVS Support** | 7 countries | None |
| **Export Formats** | JSON/CSV/XML | None |
| **Pricing** | $9.99/month | $29+/month |
| **Daily Limits** | 5 free, unlimited premium | Paid only |

## 📈 Upgrade to Premium

**Only $9.99/month** for:
- 🚀 Unlimited daily generations
- 🌍 AVS support (7 countries)
- 📊 Bulk generation (1000+ cards)
- 💾 Export capabilities
- ⚡ Priority support
- 🔄 API access (coming soon)

## 🔧 Advanced Usage

### Database Merging
```bash
python merge_bin_databases.py
```
Merges multiple BIN CSV files into a single deduplicated database.

### Custom BIN Validation
The bot automatically validates BINs against the database and blocks known test prefixes for realistic generation.

## 📞 Support

- **Bot Username**: @BINSearchCCGBot
- **Issues**: Create GitHub issue
- **Premium Support**: Included with subscription

---

**Made with ❤️ for ethical testing and development**

### 2. Interactive Tool
```bash
# Launch interactive menu
python bin_lookup.py

# Or lookup directly
python bin_lookup.py 411111
```

## 🤖 Telegram Bot Integration

### Setup
1. Install required packages:
```bash
pip install python-telegram-bot pandas
```

2. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram

3. Get your bot token and replace `YOUR_BOT_TOKEN` in `telegram_bin_bot.py`

4. Run the bot:
```bash
python telegram_bin_bot.py
```

### Bot Commands
- `/binlist 411111` - Look up specific BIN
- `/binsearch brand=VISA` - Search by criteria
- `/binsearch country=USA type=CREDIT` - Multiple criteria
- `/stats` - Database statistics
- `/help` - Show help

### Integration Functions
```python
from telegram_bot_integration import handle_binlist_command, handle_binsearch_command

# BIN lookup
response = handle_binlist_command("411111")

# Search
search_params = {"brand": "VISA", "type": "CREDIT"}
response = handle_binsearch_command(search_params)
```

## 📊 Database Details

### Statistics
- **Total BINs:** 458,051
- **Brands:** 74 (MAESTRO, VISA, MASTERCARD, etc.)
- **Countries:** 423
- **Issuers:** 19,412

### Data Structure
```csv
bin,brand,type,category,issuer,country,bank_phone,bank_url
411111,VISA,CREDIT,,JPMORGAN CHASE BANK N.A.,United States,1-800-432-3117,www.chase.com
```

### Supported Search Parameters
- **`brand`** - Card brand (VISA, MASTERCARD, AMERICAN EXPRESS, etc.)
- **`country`** - Country name
- **`issuer`** - Bank or issuer name
- **`type`** - Card type (CREDIT, DEBIT)

## 🔧 Merging New Databases

To merge additional BIN databases:

1. Place CSV files in the directory
2. Update filenames in `merge_bin_databases.py`
3. Run the merge:
```bash
python merge_bin_databases.py
```

### Supported Input Formats
The merger handles different CSV column formats:
- Format 1: `bin,brand,type,category,issuer,alpha_2,alpha_3,country,latitude,longitude,bank_phone,bank_url`
- Format 2: `BIN,Brand,Type,Category,Issuer,IssuerPhone,IssuerUrl,isoCode2,isoCode3,CountryName`

## 📱 Usage Examples

### Command Line
```bash
# Quick lookups
python quick_bin_lookup.py 411111
python quick_bin_lookup.py 4111

# Search examples
python quick_bin_lookup.py search brand=VISA
python quick_bin_lookup.py search country=Canada
python quick_bin_lookup.py search issuer=Chase
python quick_bin_lookup.py search brand=MASTERCARD type=DEBIT
```

### Python Integration
```python
from telegram_bot_integration import lookup_bin, search_bins_by_criteria

# BIN lookup
bin_info = lookup_bin("411111")
if bin_info:
    print(f"Brand: {bin_info['brand']}")
    print(f"Issuer: {bin_info['issuer']}")

# Search
results = search_bins_by_criteria(brand="VISA", country="USA", limit=5)
for result in results:
    print(f"{result['bin']} - {result['issuer']}")
```

## 🛠️ Requirements

### Minimal (quick_bin_lookup.py)
- Python 3.6+
- No external dependencies

### Full Features
- Python 3.7+
- pandas
- python-telegram-bot (for bot integration)

### Installation
```bash
pip install pandas python-telegram-bot
```

## 📝 Sample Output

### BIN Lookup
```
🔍 BIN Information

🔢 BIN: 411111
💳 Brand: VISA
📋 Type: CREDIT
🏷️ Category: N/A
🏦 Issuer: JPMORGAN CHASE BANK, N.A.
🌍 Country: United States
📞 Phone: 1-800-432-3117
🌐 Website: www.chase.com
```

### Search Results
```
🔍 Search Results for: brand=VISA, country=USA
Found 5 result(s)

1. 400000 - VISA CREDIT
   🏦 INTL HDQTRS-CENTER OWNED
   🌍 UNITED STATES

2. 400001 - VISA CREDIT
   🏦 INTL HDQTRS-CENTER OWNED
   🌍 UNITED STATES
```

## 🔒 Security Notes

- This tool is for educational and legitimate business purposes only
- BIN information is publicly available data used for payment processing
- Always comply with applicable laws and regulations
- Never store or transmit sensitive payment card data

## 📈 Performance

- **Database Load Time:** ~2-3 seconds
- **Lookup Speed:** < 1ms (in-memory)
- **Memory Usage:** ~50MB (loaded database)
- **File Size:** 27.6MB (CSV database)

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is for educational purposes. Please ensure compliance with applicable laws and terms of service when using BIN data.
