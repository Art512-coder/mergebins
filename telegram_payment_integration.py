"""
Enhanced Telegram Bot with Real Crypto Payment Integration
Integrates with NOWPayments and Coinbase Commerce for premium subscriptions
"""
import os
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional

# Payment integration
class TelegramPaymentManager:
    """Payment manager for Telegram Bot integration with crypto providers"""
    
    def __init__(self):
        self.nowpayments_api_key = os.getenv("NOWPAYMENTS_API_KEY")
        self.nowpayments_secret = os.getenv("NOWPAYMENTS_IPN_SECRET")
        self.coinbase_api_key = os.getenv("COINBASE_API_KEY")
        self.base_url = os.getenv("API_BASE_URL", "https://cryptobinchecker.cc/api/v1")
        
    async def create_payment_for_user(self, telegram_user_id: int, currency: str = "btc") -> Optional[Dict]:
        """Create a payment for Telegram user"""
        try:
            import requests
            
            # Create payment via web API
            payment_data = {
                "currency": currency,
                "plan_type": "premium",
                "success_url": f"https://t.me/YourBotUsername?start=payment_success",
                "cancel_url": f"https://t.me/YourBotUsername?start=payment_cancelled"
            }
            
            # Include telegram user ID in metadata
            headers = {
                "Content-Type": "application/json",
                "X-Telegram-User-ID": str(telegram_user_id)
            }
            
            response = requests.post(
                f"{self.base_url}/payments/create-crypto-payment",
                json=payment_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Payment creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating payment: {e}")
            return None
    
    def get_supported_currencies(self) -> list:
        """Get supported crypto currencies"""
        return ["btc", "eth", "ltc", "usdt", "bch", "doge"]
    
    async def check_payment_status(self, payment_id: str) -> Optional[Dict]:
        """Check payment status"""
        try:
            import requests
            
            response = requests.get(
                f"{self.base_url}/payments/payment/{payment_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Error checking payment status: {e}")
            return None