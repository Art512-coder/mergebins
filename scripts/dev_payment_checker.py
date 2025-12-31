#!/usr/bin/env python3
"""
Development Payment Status Checker
Polls payment status without requiring webhooks
"""

import asyncio
import time
from typing import Optional
from webapp.backend.app.services.crypto_payments import CryptoPaymentManager

class DevPaymentChecker:
    """Development-friendly payment status checker."""
    
    def __init__(self):
        self.crypto_manager = CryptoPaymentManager()
        self.active_payments = {}  # payment_id -> user_data
    
    def add_payment_to_watch(self, payment_id: str, user_data: dict):
        """Add a payment to watch for completion."""
        self.active_payments[payment_id] = {
            **user_data,
            "created_at": time.time(),
            "last_checked": 0
        }
        print(f"🔍 Now watching payment: {payment_id}")
    
    async def check_payment_status(self, payment_id: str, provider: str) -> Optional[dict]:
        """Check single payment status."""
        if provider == "coinbase":
            return await self.crypto_manager.coinbase.get_charge(payment_id)
        elif provider == "nowpayments":
            return await self.crypto_manager.nowpayments.get_payment_status(payment_id)
        return None
    
    async def poll_active_payments(self):
        """Poll all active payments for status updates."""
        for payment_id, payment_data in list(self.active_payments.items()):
            try:
                # Check every 30 seconds max
                if time.time() - payment_data["last_checked"] < 30:
                    continue
                
                payment_data["last_checked"] = time.time()
                
                # Get payment status
                status = await self.check_payment_status(
                    payment_id, 
                    payment_data.get("provider", "coinbase")
                )
                
                if status:
                    print(f"💰 Payment {payment_id}: {status.get('status', 'unknown')}")
                    
                    # Check if confirmed
                    if self.is_payment_confirmed(status, payment_data["provider"]):
                        print(f"✅ Payment {payment_id} CONFIRMED! Activating subscription...")
                        await self.activate_subscription(payment_data)
                        del self.active_payments[payment_id]
                    
                    # Remove expired payments (24 hours)
                    elif time.time() - payment_data["created_at"] > 86400:
                        print(f"⏰ Payment {payment_id} expired, removing from watch list")
                        del self.active_payments[payment_id]
                        
            except Exception as e:
                print(f"❌ Error checking payment {payment_id}: {e}")
    
    def is_payment_confirmed(self, status: dict, provider: str) -> bool:
        """Check if payment is confirmed based on provider."""
        if provider == "coinbase":
            # Check timeline for confirmed events
            timeline = status.get("timeline", [])
            return any(event.get("status") == "CONFIRMED" for event in timeline)
        
        elif provider == "nowpayments":
            return status.get("payment_status") == "finished"
        
        return False
    
    async def activate_subscription(self, payment_data: dict):
        """Activate user subscription (development version)."""
        user_email = payment_data.get("user_email")
        plan_type = payment_data.get("plan_type", "premium")
        
        print(f"🎉 SUBSCRIPTION ACTIVATED!")
        print(f"   User: {user_email}")
        print(f"   Plan: {plan_type}")
        print(f"   TODO: Update database with subscription")
        
        # In development, just log this
        # In production, this would update the database
    
    async def run_forever(self):
        """Run the payment checker continuously."""
        print("🚀 Development Payment Checker Started")
        print("   Checking for payment updates every 30 seconds...")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                await self.poll_active_payments()
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Payment checker stopped")

# Example usage
if __name__ == "__main__":
    checker = DevPaymentChecker()
    
    # Example: Add a payment to watch
    # checker.add_payment_to_watch("charge_123", {
    #     "user_email": "user@example.com",
    #     "plan_type": "premium",
    #     "provider": "coinbase"
    # })
    
    # Run the checker
    asyncio.run(checker.run_forever())
