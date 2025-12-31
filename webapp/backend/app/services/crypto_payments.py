import requests
import hashlib
import hmac
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
import os
from coinbase_commerce.client import Client
from coinbase_commerce.webhook import Webhook

class NOWPaymentsService:
    """NOWPayments API integration for crypto payments."""
    
    def __init__(self):
        self.api_key = os.getenv("NOWPAYMENTS_API_KEY")
        self.ipn_secret = os.getenv("NOWPAYMENTS_IPN_SECRET")
        self.base_url = "https://api.nowpayments.io/v1"
        
        if not self.api_key:
            raise ValueError("NOWPAYMENTS_API_KEY not found in environment")
    
    def get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_available_currencies(self) -> list:
        """Get list of available cryptocurrencies."""
        try:
            response = requests.get(
                f"{self.base_url}/currencies",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json().get("currencies", [])
        except Exception as e:
            print(f"Error fetching currencies: {e}")
            return ["btc", "eth", "usdt", "ltc", "bch"]  # Fallback popular currencies
    
    async def get_estimate(self, amount_usd: float, currency: str) -> Optional[Dict]:
        """Get cryptocurrency amount estimate for USD price."""
        try:
            response = requests.get(
                f"{self.base_url}/estimate",
                params={
                    "amount": amount_usd,
                    "currency_from": "usd",
                    "currency_to": currency.lower()
                },
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting estimate for {currency}: {e}")
            return None
    
    async def create_payment(
        self, 
        amount_usd: float, 
        currency: str, 
        order_id: str, 
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new payment."""
        try:
            payload = {
                "price_amount": amount_usd,
                "price_currency": "usd",
                "pay_currency": currency.lower(),
                "order_id": order_id,
                "order_description": "BIN Search Premium Subscription",
                "ipn_callback_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/v1/payments/webhook/nowpayments",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": user_email
            }
            
            response = requests.post(
                f"{self.base_url}/payment",
                json=payload,
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error creating payment: {e}")
            return None
    
    def verify_ipn_signature(self, payload: bytes, signature: str) -> bool:
        """Verify IPN callback signature."""
        if not self.ipn_secret:
            return False
        
        expected_signature = hmac.new(
            self.ipn_secret.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict]:
        """Get payment status."""
        try:
            response = requests.get(
                f"{self.base_url}/payment/{payment_id}",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting payment status: {e}")
            return None


class CoinbaseCommerceService:
    """Coinbase Commerce API integration for crypto payments."""
    
    def __init__(self):
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.webhook_secret = os.getenv("COINBASE_WEBHOOK_SECRET")
        
        if not self.api_key:
            raise ValueError("COINBASE_API_KEY not found in environment")
        
        self.client = Client(api_key=self.api_key)
    
    async def create_charge(
        self, 
        amount_usd: float, 
        order_id: str, 
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new charge."""
        try:
            charge_data = {
                "name": "BIN Search Premium Subscription",
                "description": "Monthly premium subscription for unlimited BIN lookups and card generation",
                "local_price": {
                    "amount": str(amount_usd),
                    "currency": "USD"
                },
                "pricing_type": "fixed_price",
                "metadata": {
                    "app_name": "bin_search",  # Distinguish from other apps
                    "order_id": order_id,
                    "user_email": user_email,
                    "service": "premium_subscription"
                },
                "redirect_url": success_url,
                "cancel_url": cancel_url
            }
            
            charge = self.client.charge.create(**charge_data)
            return {
                "id": charge.id,
                "hosted_url": charge.hosted_url,
                "expires_at": charge.expires_at,
                "pricing": charge.pricing
            }
            
        except Exception as e:
            print(f"Error creating Coinbase charge: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        if not self.webhook_secret:
            return False
        
        try:
            return Webhook.verify_signature(payload, signature, self.webhook_secret)
        except Exception:
            return False
    
    async def get_charge(self, charge_id: str) -> Optional[Dict]:
        """Get charge details."""
        try:
            charge = self.client.charge.retrieve(charge_id)
            return {
                "id": charge.id,
                "code": charge.code,
                "timeline": charge.timeline,
                "payments": charge.payments
            }
        except Exception as e:
            print(f"Error getting charge: {e}")
            return None


class CryptoPaymentManager:
    """Main crypto payment manager that coordinates between providers."""
    
    def __init__(self):
        self.nowpayments = NOWPaymentsService()
        self.coinbase = CoinbaseCommerceService()
        
        # Supported cryptocurrencies with user-friendly names
        self.supported_currencies = {
            "btc": {"name": "Bitcoin", "symbol": "BTC", "provider": "both"},
            "eth": {"name": "Ethereum", "symbol": "ETH", "provider": "both"},
            "usdt": {"name": "Tether", "symbol": "USDT", "provider": "nowpayments"},
            "usdc": {"name": "USD Coin", "symbol": "USDC", "provider": "both"},
            "ltc": {"name": "Litecoin", "symbol": "LTC", "provider": "both"},
            "bch": {"name": "Bitcoin Cash", "symbol": "BCH", "provider": "nowpayments"},
            "ada": {"name": "Cardano", "symbol": "ADA", "provider": "nowpayments"},
            "dot": {"name": "Polkadot", "symbol": "DOT", "provider": "nowpayments"},
            "matic": {"name": "Polygon", "symbol": "MATIC", "provider": "nowpayments"}
        }
    
    async def get_available_currencies(self) -> Dict[str, Dict]:
        """Get all available cryptocurrencies."""
        return self.supported_currencies
    
    async def create_payment(
        self,
        amount_usd: float,
        currency: str,
        order_id: str,
        user_email: str,
        provider: str = "auto",
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create payment with specified provider or auto-select.
        """
        currency_lower = currency.lower()
        
        if currency_lower not in self.supported_currencies:
            raise ValueError(f"Unsupported currency: {currency}")
        
        # Auto-select provider if not specified
        if provider == "auto":
            currency_info = self.supported_currencies[currency_lower]
            if currency_info["provider"] == "both":
                provider = "nowpayments"  # Prefer NOWPayments for broader support
            else:
                provider = currency_info["provider"]
        
        try:
            if provider == "nowpayments":
                return await self.nowpayments.create_payment(
                    amount_usd, currency, order_id, user_email, success_url, cancel_url
                )
            elif provider == "coinbase":
                return await self.coinbase.create_charge(
                    amount_usd, order_id, user_email, success_url, cancel_url
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
        except Exception as e:
            print(f"Error creating payment with {provider}: {e}")
            
            # Fallback to alternative provider
            if provider == "nowpayments" and self.supported_currencies[currency_lower]["provider"] == "both":
                print("Falling back to Coinbase Commerce...")
                return await self.coinbase.create_charge(
                    amount_usd, order_id, user_email, success_url, cancel_url
                )
            
            return None
    
    async def get_price_estimate(self, amount_usd: float, currency: str) -> Optional[Dict]:
        """Get price estimate for cryptocurrency."""
        try:
            return await self.nowpayments.get_estimate(amount_usd, currency)
        except Exception as e:
            print(f"Error getting price estimate: {e}")
            return None
    
    def verify_webhook(self, provider: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for specified provider."""
        if provider == "nowpayments":
            return self.nowpayments.verify_ipn_signature(payload, signature)
        elif provider == "coinbase":
            return self.coinbase.verify_webhook_signature(payload, signature)
        return False
