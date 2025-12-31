#!/usr/bin/env python3
"""
NOWPayments API Test Script
Tests the connection and available currencies
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
BASE_URL = "https://api.nowpayments.io/v1"

async def test_nowpayments_api():
    """Test NOWPayments API connection and available currencies"""
    
    if not API_KEY:
        print("❌ NOWPAYMENTS_API_KEY not found in environment")
        return
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Test 1: API Status
        print("🔄 Testing API connection...")
        try:
            async with session.get(f"{BASE_URL}/status", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Status: {data.get('message', 'OK')}")
                else:
                    print(f"❌ API Status failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return
        
        # Test 2: Available Currencies
        print("\n🔄 Fetching available currencies...")
        try:
            async with session.get(f"{BASE_URL}/currencies", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    currencies = data.get("currencies", [])
                    print(f"✅ Found {len(currencies)} available currencies")
                    
                    # Show popular cryptocurrencies
                    popular = ["btc", "eth", "usdt", "usdc", "ltc", "xrp", "ada", "sol"]
                    available_popular = [c for c in currencies if c.lower() in popular]
                    print(f"💰 Popular cryptos available: {', '.join(available_popular[:10])}")
                    
                else:
                    print(f"❌ Currencies fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Error fetching currencies: {e}")
        
        # Test 3: Minimum Payment Amounts
        print("\n🔄 Getting minimum payment amounts...")
        try:
            async with session.get(f"{BASE_URL}/min-amount?currency_from=usd&currency_to=btc", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    min_amount = data.get("min_amount")
                    print(f"✅ Minimum BTC payment: {min_amount} USD")
                else:
                    print(f"❌ Min amount fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Error fetching min amounts: {e}")

if __name__ == "__main__":
    print("🚀 NOWPayments API Test Starting...")
    print(f"📊 Using API Key: {API_KEY[:8]}...{API_KEY[-4:] if API_KEY else 'Not Found'}")
    print("-" * 50)
    
    asyncio.run(test_nowpayments_api())
    
    print("\n" + "="*50)
    print("🎯 Next Steps:")
    print("1. Set up IPN secret in your dashboard")
    print("2. Configure webhook URL: https://yourdomain.com/webhook/nowpayments")
    print("3. Test payment creation in development")
    print("4. Switch to production API when ready")
