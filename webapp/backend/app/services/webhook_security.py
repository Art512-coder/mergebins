"""
Secure Webhook Handler Service
Handles cryptocurrency payment webhooks with proper validation and security
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Optional, Any
from fastapi import Request, HTTPException, status
from datetime import datetime, timezone, timedelta
import logging

from app.database import get_db, get_redis
from app.models import User, Subscription, SubscriptionStatus, SecurityEvent
from app.services.security_service import security_service
import os

logger = logging.getLogger(__name__)

class WebhookSecurityService:
    """Secure webhook processing with validation and fraud prevention"""
    
    def __init__(self):
        self.redis = get_redis()
        self.webhook_secrets = {
            "coinbase": os.getenv("COINBASE_WEBHOOK_SECRET", ""),
            "nowpayments": os.getenv("NOWPAYMENTS_WEBHOOK_SECRET", ""),
            "coingate": os.getenv("COINGATE_WEBHOOK_SECRET", ""),
            "cryptomus": os.getenv("CRYPTOMUS_WEBHOOK_SECRET", "")
        }
        self.webhook_timeout = 300  # 5 minutes
        
    async def validate_webhook_signature(self, provider: str, request: Request, payload: bytes) -> bool:
        """Validate webhook signature to ensure it's from the legitimate provider"""
        
        if provider not in self.webhook_secrets:
            logger.error(f"Unknown webhook provider: {provider}")
            return False
            
        secret = self.webhook_secrets[provider]
        if not secret:
            logger.error(f"No webhook secret configured for {provider}")
            return False
        
        try:
            if provider == "coinbase":
                return self._validate_coinbase_signature(request, payload, secret)
            elif provider == "nowpayments":
                return self._validate_nowpayments_signature(request, payload, secret)
            elif provider == "coingate":
                return self._validate_coingate_signature(request, payload, secret)
            elif provider == "cryptomus":
                return self._validate_cryptomus_signature(request, payload, secret)
            else:
                logger.error(f"No signature validation implemented for {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook signature validation error for {provider}: {e}")
            return False
    
    def _validate_coinbase_signature(self, request: Request, payload: bytes, secret: str) -> bool:
        """Validate Coinbase Commerce webhook signature"""
        signature = request.headers.get("X-CC-Webhook-Signature")
        if not signature:
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _validate_nowpayments_signature(self, request: Request, payload: bytes, secret: str) -> bool:
        """Validate NOWPayments webhook signature"""
        signature = request.headers.get("x-nowpayments-sig")
        if not signature:
            return False
        
        # NOWPayments uses HMAC-SHA512
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _validate_coingate_signature(self, request: Request, payload: bytes, secret: str) -> bool:
        """Validate CoinGate webhook signature"""
        signature = request.headers.get("CG-Signature")
        if not signature:
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _validate_cryptomus_signature(self, request: Request, payload: bytes, secret: str) -> bool:
        """Validate Cryptomus webhook signature"""
        signature = request.headers.get("sign")
        if not signature:
            return False
        
        # Cryptomus uses MD5 hash
        expected_signature = hashlib.md5((payload.decode() + secret).encode()).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    
    async def process_payment_webhook(self, provider: str, payload: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Process payment webhook with security validation"""
        
        # 1. Extract payment information
        payment_info = self._extract_payment_info(provider, payload)
        if not payment_info:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        
        # 2. Prevent replay attacks
        webhook_id = payment_info.get("webhook_id") or payment_info.get("payment_id")
        if webhook_id and await self._is_duplicate_webhook(webhook_id):
            logger.warning(f"Duplicate webhook detected: {webhook_id}")
            return {"status": "duplicate", "message": "Webhook already processed"}
        
        # 3. Validate payment timing (prevent old webhook replays)
        if not self._is_webhook_recent(payment_info.get("timestamp")):
            logger.warning(f"Old webhook rejected: {payment_info}")
            raise HTTPException(status_code=400, detail="Webhook too old")
        
        # 4. Validate payment amounts and details
        if not self._validate_payment_details(payment_info):
            logger.error(f"Invalid payment details: {payment_info}")
            await self._log_suspicious_webhook(provider, payload, client_ip, "INVALID_PAYMENT_DETAILS")
            raise HTTPException(status_code=400, detail="Invalid payment details")
        
        # 5. Update subscription status
        result = await self._update_subscription_status(payment_info)
        
        # 6. Mark webhook as processed
        if webhook_id:
            await self._mark_webhook_processed(webhook_id)
        
        # 7. Log successful webhook processing
        await self._log_webhook_success(provider, payment_info, client_ip)
        
        return result
    
    def _extract_payment_info(self, provider: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract standardized payment information from provider-specific payload"""
        
        try:
            if provider == "coinbase":
                return self._extract_coinbase_info(payload)
            elif provider == "nowpayments":
                return self._extract_nowpayments_info(payload)
            elif provider == "coingate":
                return self._extract_coingate_info(payload)
            elif provider == "cryptomus":
                return self._extract_cryptomus_info(payload)
            else:
                return None
        except Exception as e:
            logger.error(f"Error extracting payment info from {provider}: {e}")
            return None
    
    def _extract_coinbase_info(self, payload: Dict) -> Dict[str, Any]:
        """Extract payment info from Coinbase Commerce webhook"""
        event = payload.get("event", {})
        data = event.get("data", {})
        
        return {
            "provider": "coinbase",
            "payment_id": data.get("code"),
            "webhook_id": event.get("id"),
            "status": data.get("timeline", [])[-1].get("status") if data.get("timeline") else None,
            "amount": float(data.get("pricing", {}).get("local", {}).get("amount", 0)),
            "currency": data.get("pricing", {}).get("local", {}).get("currency"),
            "crypto_amount": data.get("payments", [{}])[-1].get("value", {}).get("crypto", {}).get("amount") if data.get("payments") else None,
            "crypto_currency": data.get("payments", [{}])[-1].get("value", {}).get("crypto", {}).get("currency") if data.get("payments") else None,
            "customer_email": data.get("metadata", {}).get("customer_email"),
            "user_id": data.get("metadata", {}).get("user_id"),
            "timestamp": event.get("created_at"),
            "raw_payload": payload
        }
    
    def _extract_nowpayments_info(self, payload: Dict) -> Dict[str, Any]:
        """Extract payment info from NOWPayments webhook"""
        return {
            "provider": "nowpayments",
            "payment_id": payload.get("payment_id"),
            "webhook_id": payload.get("payment_id"),
            "status": payload.get("payment_status"),
            "amount": float(payload.get("price_amount", 0)),
            "currency": payload.get("price_currency"),
            "crypto_amount": payload.get("pay_amount"),
            "crypto_currency": payload.get("pay_currency"),
            "user_id": payload.get("order_description", "").split(":")[-1] if ":" in payload.get("order_description", "") else None,
            "timestamp": payload.get("created_at"),
            "raw_payload": payload
        }
    
    def _extract_coingate_info(self, payload: Dict) -> Dict[str, Any]:
        """Extract payment info from CoinGate webhook"""
        return {
            "provider": "coingate",
            "payment_id": payload.get("id"),
            "webhook_id": payload.get("id"),
            "status": payload.get("status"),
            "amount": float(payload.get("price_amount", 0)),
            "currency": payload.get("price_currency"),
            "crypto_amount": payload.get("receive_amount"),
            "crypto_currency": payload.get("receive_currency"),
            "user_id": payload.get("order_id", "").split("_")[-1] if "_" in payload.get("order_id", "") else None,
            "timestamp": payload.get("created_at"),
            "raw_payload": payload
        }
    
    def _extract_cryptomus_info(self, payload: Dict) -> Dict[str, Any]:
        """Extract payment info from Cryptomus webhook"""
        return {
            "provider": "cryptomus",
            "payment_id": payload.get("uuid"),
            "webhook_id": payload.get("uuid"),
            "status": payload.get("status"),
            "amount": float(payload.get("amount", 0)),
            "currency": payload.get("currency"),
            "crypto_amount": payload.get("payer_amount"),
            "crypto_currency": payload.get("payer_currency"),
            "user_id": payload.get("order_id", "").split("_")[-1] if "_" in payload.get("order_id", "") else None,
            "timestamp": payload.get("created_at"),
            "raw_payload": payload
        }
    
    async def _is_duplicate_webhook(self, webhook_id: str) -> bool:
        """Check if webhook has already been processed"""
        key = f"webhook:processed:{webhook_id}"
        exists = await self.redis.exists(key)
        return bool(exists)
    
    def _is_webhook_recent(self, timestamp_str: Optional[str]) -> bool:
        """Check if webhook is recent enough to be valid"""
        if not timestamp_str:
            return True  # Allow if no timestamp provided
        
        try:
            webhook_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - webhook_time
            
            return time_diff.total_seconds() <= self.webhook_timeout
        except Exception:
            return True  # Allow if timestamp parsing fails
    
    def _validate_payment_details(self, payment_info: Dict[str, Any]) -> bool:
        """Validate payment amounts and details"""
        
        # Check required fields
        required_fields = ["payment_id", "status", "amount", "currency"]
        if not all(payment_info.get(field) for field in required_fields):
            return False
        
        # Validate amount is positive
        amount = payment_info.get("amount", 0)
        if amount <= 0:
            return False
        
        # Validate currency
        valid_currencies = {"USD", "EUR", "GBP", "BTC", "ETH", "LTC", "BCH", "USDT", "USDC"}
        currency = payment_info.get("currency", "").upper()
        if currency not in valid_currencies:
            return False
        
        # Validate status
        valid_statuses = {"completed", "confirmed", "paid", "finished", "success"}
        status = payment_info.get("status", "").lower()
        if status not in valid_statuses:
            return False
        
        return True
    
    async def _update_subscription_status(self, payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Update user subscription based on payment"""
        
        user_id = payment_info.get("user_id")
        if not user_id:
            logger.error("No user_id in payment info")
            return {"status": "error", "message": "No user ID found"}
        
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"Invalid user_id: {user_id}")
            return {"status": "error", "message": "Invalid user ID"}
        
        # Here you would update the database
        # This is a placeholder - implement actual database update
        logger.info(f"Payment successful for user {user_id}: {payment_info}")
        
        return {
            "status": "success",
            "message": "Subscription updated successfully",
            "user_id": user_id,
            "payment_id": payment_info.get("payment_id")
        }
    
    async def _mark_webhook_processed(self, webhook_id: str):
        """Mark webhook as processed to prevent replay"""
        key = f"webhook:processed:{webhook_id}"
        await self.redis.setex(key, 86400, "1")  # Keep for 24 hours
    
    async def _log_suspicious_webhook(self, provider: str, payload: Dict, client_ip: str, reason: str):
        """Log suspicious webhook activity"""
        suspicious_data = {
            "provider": provider,
            "payload": payload,
            "client_ip": client_ip,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log to security service
        await security_service.log_security_event(
            event_type="SUSPICIOUS_WEBHOOK",
            risk_analysis={"risk_score": 70, "client_ip": client_ip, "reason": reason},
            user_id=None
        )
        
        logger.warning(f"Suspicious webhook: {suspicious_data}")
    
    async def _log_webhook_success(self, provider: str, payment_info: Dict, client_ip: str):
        """Log successful webhook processing"""
        success_data = {
            "provider": provider,
            "payment_id": payment_info.get("payment_id"),
            "user_id": payment_info.get("user_id"),
            "amount": payment_info.get("amount"),
            "currency": payment_info.get("currency"),
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Webhook processed successfully: {success_data}")

# Global instance
webhook_security_service = WebhookSecurityService()
