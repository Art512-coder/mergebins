#!/usr/bin/env python3
"""
Payment Flow End-to-End Testing Script
Tests cryptocurrency payments, subscription activation, and premium sync
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.api_auth import auth
from dotenv import load_dotenv

load_dotenv()

class PaymentFlowTester:
    def __init__(self):
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   → {details}")
    
    async def test_api_connectivity(self):
        """Test basic API connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        self.log_test("API Connectivity", "PASS", f"API responding on {self.api_base_url}")
                        return True
                    else:
                        self.log_test("API Connectivity", "FAIL", f"API returned status {response.status}")
                        return False
        except Exception as e:
            self.log_test("API Connectivity", "FAIL", f"Connection error: {e}")
            return False
    
    async def test_bot_authentication(self):
        """Test bot authentication with API"""
        try:
            headers = auth.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/auth/verify-bot",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Bot Authentication", "PASS", f"Bot authenticated: {data.get('bot_id', 'N/A')}")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_test("Bot Authentication", "FAIL", f"Auth failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.log_test("Bot Authentication", "FAIL", f"Auth error: {e}")
            return False
    
    async def test_user_creation(self):
        """Test user creation via Telegram auth"""
        try:
            test_telegram_id = 12345678  # Test user ID
            user_data = await auth.authenticate_user(
                telegram_id=test_telegram_id,
                username="test_user",
                first_name="Test User"
            )
            
            if user_data:
                self.log_test("User Creation", "PASS", f"User created/found: {user_data.get('id')}")
                return True
            else:
                self.log_test("User Creation", "FAIL", "Failed to create/authenticate user")
                return False
                
        except Exception as e:
            self.log_test("User Creation", "FAIL", f"User creation error: {e}")
            return False
    
    async def test_payment_creation(self):
        """Test cryptocurrency payment creation"""
        try:
            headers = auth.create_api_headers()
            payment_payload = {
                "plan": "premium_monthly",
                "amount": 9.99,
                "currency": "USD",
                "crypto_currency": "BTC",
                "telegram_id": 12345678,
                "metadata": {
                    "source": "telegram-bot",
                    "test": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/payments/create-crypto-payment",
                    json=payment_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status == 200:
                        payment_data = await response.json()
                        payment_id = payment_data.get("payment_id")
                        pay_address = payment_data.get("pay_address")
                        pay_amount = payment_data.get("pay_amount")
                        
                        self.log_test("Payment Creation", "PASS", 
                                    f"Payment created: {payment_id}, Address: {pay_address}, Amount: {pay_amount}")
                        return payment_data
                    else:
                        error_text = await response.text()
                        self.log_test("Payment Creation", "FAIL", f"Payment creation failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.log_test("Payment Creation", "FAIL", f"Payment creation error: {e}")
            return None
    
    async def test_payment_status_check(self, payment_id: str):
        """Test payment status checking"""
        try:
            headers = auth.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/payments/status/{payment_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        status_data = await response.json()
                        payment_status = status_data.get("payment_status")
                        self.log_test("Payment Status Check", "PASS", f"Status retrieved: {payment_status}")
                        return status_data
                    else:
                        self.log_test("Payment Status Check", "FAIL", f"Status check failed: {response.status}")
                        return None
                        
        except Exception as e:
            self.log_test("Payment Status Check", "FAIL", f"Status check error: {e}")
            return None
    
    async def test_premium_status_sync(self):
        """Test premium status synchronization"""
        try:
            test_telegram_id = 12345678
            is_premium = await auth.sync_premium_status(test_telegram_id)
            
            if is_premium is not None:
                self.log_test("Premium Status Sync", "PASS", f"Premium status: {is_premium}")
                return True
            else:
                self.log_test("Premium Status Sync", "FAIL", "Failed to sync premium status")
                return False
                
        except Exception as e:
            self.log_test("Premium Status Sync", "FAIL", f"Premium sync error: {e}")
            return False
    
    async def test_webhook_simulation(self):
        """Test webhook payment confirmation simulation"""
        try:
            headers = auth.create_api_headers()
            webhook_payload = {
                "payment_id": "test_payment_123",
                "payment_status": "finished",
                "telegram_id": 12345678,
                "amount": "9.99",
                "currency": "USD",
                "crypto_currency": "BTC",
                "transaction_hash": "test_tx_hash_123",
                "confirmed_at": datetime.now().isoformat(),
                "test_mode": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/webhooks/payment-confirmed",
                    json=webhook_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        self.log_test("Webhook Simulation", "PASS", "Payment confirmation webhook processed")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_test("Webhook Simulation", "FAIL", f"Webhook failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.log_test("Webhook Simulation", "FAIL", f"Webhook error: {e}")
            return False
    
    async def test_subscription_activation(self):
        """Test subscription activation after payment"""
        try:
            headers = auth.create_api_headers()
            activation_payload = {
                "telegram_id": 12345678,
                "plan": "premium_monthly",
                "payment_id": "test_payment_123",
                "activated_by": "webhook_test"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/subscriptions/activate",
                    json=activation_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        subscription_data = await response.json()
                        expires_at = subscription_data.get("expires_at")
                        self.log_test("Subscription Activation", "PASS", f"Subscription activated, expires: {expires_at}")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_test("Subscription Activation", "FAIL", f"Activation failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.log_test("Subscription Activation", "FAIL", f"Activation error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run complete payment flow test suite"""
        print("🧪 Starting Payment Flow End-to-End Tests")
        print("=" * 50)
        
        # Test 1: API Connectivity
        if not await self.test_api_connectivity():
            print("❌ API connectivity failed - aborting remaining tests")
            return False
        
        # Test 2: Bot Authentication
        if not await self.test_bot_authentication():
            print("⚠️  Bot authentication failed - some tests may fail")
        
        # Test 3: User Creation
        await self.test_user_creation()
        
        # Test 4: Payment Creation
        payment_data = await self.test_payment_creation()
        
        # Test 5: Payment Status Check
        if payment_data and payment_data.get("payment_id"):
            await self.test_payment_status_check(payment_data["payment_id"])
        
        # Test 6: Premium Status Sync
        await self.test_premium_status_sync()
        
        # Test 7: Webhook Simulation
        await self.test_webhook_simulation()
        
        # Test 8: Subscription Activation
        await self.test_subscription_activation()
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        warnings = sum(1 for result in self.test_results if result["status"] == "WARN")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Total: {len(self.test_results)}")
        
        # Save detailed results
        results_file = "payment_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        return failed == 0

async def main():
    """Run the payment flow tests"""
    tester = PaymentFlowTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All payment flow tests completed successfully!")
        print("💳 Payment system is ready for production")
    else:
        print("\n⚠️  Some tests failed - review results before production deployment")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())