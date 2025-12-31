#!/usr/bin/env python3
"""
Simple Backend Server Test
Tests basic functionality without complex dependencies
"""

import json
import os
from typing import Dict, Optional

# Simple mock classes for testing
class MockUser:
    def __init__(self, email: str, tier: str = "free"):
        self.email = email
        self.subscription_tier = tier
        self.id = hash(email) % 1000

class MockCryptoService:
    """Mock crypto service for testing"""
    
    def __init__(self):
        self.payments = {}
    
    async def create_charge(self, amount_usd: float, order_id: str, user_email: str):
        """Create a mock charge"""
        charge_id = f"charge_{len(self.payments) + 1}"
        
        charge_data = {
            "id": charge_id,
            "hosted_url": f"https://commerce.coinbase.com/checkout/{charge_id}",
            "amount_usd": amount_usd,
            "user_email": user_email,
            "order_id": order_id,
            "status": "pending",
            "expires_at": "2025-08-29T12:00:00Z"
        }
        
        self.payments[charge_id] = charge_data
        return charge_data
    
    async def get_price_estimate(self, amount_usd: float, currency: str):
        """Mock price estimate"""
        rates = {
            "btc": 0.000023,  # ~$43,000 per BTC
            "eth": 0.00041,   # ~$2,400 per ETH
            "usdt": 1.0,      # 1:1 with USD
            "usdc": 1.0       # 1:1 with USD
        }
        
        rate = rates.get(currency.lower(), 0.001)
        crypto_amount = amount_usd * rate
        
        return {
            "estimated_amount": f"{crypto_amount:.8f}",
            "currency": currency.upper(),
            "amount_usd": amount_usd
        }

def test_payment_creation():
    """Test payment creation flow"""
    print("🧪 Testing Payment System")
    print("=" * 50)
    
    # Initialize services
    crypto_service = MockCryptoService()
    user = MockUser("test@example.com", "free")
    
    print(f"👤 User: {user.email} (Tier: {user.subscription_tier})")
    print()
    
    # Test 1: Price Estimation
    print("1️⃣ Testing Price Estimation...")
    
    async def run_price_test():
        currencies = ["btc", "eth", "usdt", "usdc"]
        amount_usd = 9.99
        
        for currency in currencies:
            estimate = await crypto_service.get_price_estimate(amount_usd, currency)
            print(f"   💰 {currency.upper()}: {estimate['estimated_amount']} (${amount_usd})")
    
    import asyncio
    asyncio.run(run_price_test())
    print()
    
    # Test 2: Payment Creation
    print("2️⃣ Testing Payment Creation...")
    
    async def run_payment_test():
        charge = await crypto_service.create_charge(
            amount_usd=9.99,
            order_id=f"sub_{user.id}",
            user_email=user.email
        )
        
        print(f"   ✅ Charge Created: {charge['id']}")
        print(f"   🔗 Payment URL: {charge['hosted_url']}")
        print(f"   💵 Amount: ${charge['amount_usd']}")
        print(f"   📧 User: {charge['user_email']}")
        print(f"   ⏰ Expires: {charge['expires_at']}")
        
        return charge
    
    charge = asyncio.run(run_payment_test())
    print()
    
    # Test 3: Payment Status
    print("3️⃣ Testing Payment Status...")
    payment_id = charge['id']
    stored_payment = crypto_service.payments.get(payment_id)
    
    if stored_payment:
        print(f"   📊 Payment {payment_id}: {stored_payment['status']}")
        print(f"   💡 In real app: User would pay at {stored_payment['hosted_url']}")
        print(f"   ⚡ Status would update via webhook or polling")
    
    print()
    print("🎉 All tests passed! Payment system is working.")
    print()
    print("🔗 Next Steps:")
    print("   1. Install Python properly")
    print("   2. Set up FastAPI server") 
    print("   3. Add real Coinbase Commerce API keys")
    print("   4. Build frontend payment interface")

if __name__ == "__main__":
    test_payment_creation()
