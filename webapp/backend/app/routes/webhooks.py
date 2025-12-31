"""
Secure Webhook Routes
Handles cryptocurrency payment webhooks with comprehensive security
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
import hmac
import hashlib
import json
import time
from datetime import datetime, timezone

from app.database import get_db, get_redis
from app.models import User, PaymentLog, UserTier
from app.services.security_service import SecurityService
from app.services.webhook_security import WebhookSecurityService
import os

router = APIRouter()
security_service = SecurityService()
webhook_security = WebhookSecurityService()

# Webhook secrets (store in environment variables)
COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "your-coinbase-webhook-secret")
CRYPTO_PAYMENT_SECRET = os.getenv("CRYPTO_PAYMENT_SECRET", "your-crypto-payment-secret")

class CoinbaseWebhookPayload(BaseModel):
    id: str
    resource: str
    resource_path: str
    type: str
    api_version: str
    created_at: str
    data: Dict[str, Any]

class PaymentWebhookPayload(BaseModel):
    transaction_id: str
    user_id: str
    amount: str
    currency: str
    status: str
    payment_method: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/coinbase-commerce")
async def handle_coinbase_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Coinbase Commerce webhooks with maximum security.
    This is CRITICAL - fake payments could give free premium access.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # CRITICAL: Verify webhook signature
    signature = request.headers.get('X-CC-Webhook-Signature')
    if not signature:
        await security_service.log_security_event(
            request, "MISSING_WEBHOOK_SIGNATURE", {"service": "coinbase"}
        )
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    # Verify Coinbase signature
    is_valid = webhook_security.verify_coinbase_signature(
        body, signature, COINBASE_WEBHOOK_SECRET
    )
    
    if not is_valid:
        await security_service.log_security_event(
            request, "INVALID_WEBHOOK_SIGNATURE", {
                "service": "coinbase",
                "signature": signature[:20] + "...",  # Partial signature for logging
                "ip": request.client.host
            }
        )
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Additional security: Check timestamp to prevent replay attacks
    timestamp = request.headers.get('X-CC-Webhook-Timestamp')
    if timestamp:
        webhook_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - webhook_time) > 600:  # 10 minutes tolerance
            await security_service.log_security_event(
                request, "WEBHOOK_REPLAY_ATTEMPT", {
                    "service": "coinbase",
                    "webhook_timestamp": webhook_time,
                    "current_timestamp": current_time,
                    "time_difference": abs(current_time - webhook_time)
                }
            )
            raise HTTPException(status_code=401, detail="Webhook timestamp too old")
    
    try:
        payload_data = json.loads(body.decode('utf-8'))
        payload = CoinbaseWebhookPayload(**payload_data)
        
        # Process the webhook in background to avoid blocking
        background_tasks.add_task(
            process_coinbase_payment,
            payload,
            request.client.host,
            db
        )
        
        return {"status": "received"}
        
    except Exception as e:
        await security_service.log_security_event(
            request, "WEBHOOK_PROCESSING_ERROR", {
                "service": "coinbase",
                "error": str(e),
                "payload_preview": body[:100].decode('utf-8', errors='ignore')
            }
        )
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@router.post("/crypto-payment")
async def handle_crypto_payment_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle generic crypto payment webhooks with advanced security.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # CRITICAL: IP whitelist check for crypto payment providers
    client_ip = request.client.host
    allowed_ips = os.getenv("CRYPTO_WEBHOOK_ALLOWED_IPS", "").split(",")
    if allowed_ips and client_ip not in allowed_ips:
        await security_service.log_security_event(
            request, "UNAUTHORIZED_WEBHOOK_IP", {
                "service": "crypto_payment",
                "client_ip": client_ip,
                "allowed_ips": allowed_ips
            }
        )
        raise HTTPException(status_code=403, detail="Unauthorized IP address")
    
    # Verify webhook signature using HMAC
    signature = request.headers.get('X-Webhook-Signature')
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    expected_signature = hmac.new(
        CRYPTO_PAYMENT_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, f"sha256={expected_signature}"):
        await security_service.log_security_event(
            request, "INVALID_CRYPTO_WEBHOOK_SIGNATURE", {
                "service": "crypto_payment",
                "provided_signature": signature[:20] + "...",
                "ip": client_ip
            }
        )
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Check for duplicate webhooks (replay attack prevention)
    webhook_id = request.headers.get('X-Webhook-ID')
    if webhook_id:
        redis_client = get_redis()
        duplicate_key = f"webhook_processed:{webhook_id}"
        if redis_client.exists(duplicate_key):
            await security_service.log_security_event(
                request, "DUPLICATE_WEBHOOK_DETECTED", {
                    "service": "crypto_payment",
                    "webhook_id": webhook_id,
                    "ip": client_ip
                }
            )
            return {"status": "duplicate", "message": "Webhook already processed"}
        
        # Mark as processed for 24 hours
        redis_client.setex(duplicate_key, 86400, "processed")
    
    try:
        payload_data = json.loads(body.decode('utf-8'))
        payload = PaymentWebhookPayload(**payload_data)
        
        # Process the payment in background
        background_tasks.add_task(
            process_crypto_payment,
            payload,
            request.client.host,
            db
        )
        
        return {"status": "received"}
        
    except Exception as e:
        await security_service.log_security_event(
            request, "CRYPTO_WEBHOOK_ERROR", {
                "error": str(e),
                "payload_preview": body[:100].decode('utf-8', errors='ignore')
            }
        )
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

async def process_coinbase_payment(
    payload: CoinbaseWebhookPayload,
    client_ip: str,
    db: Session
):
    """
    Process Coinbase payment webhook securely.
    """
    try:
        if payload.type == "charge:confirmed":
            charge_data = payload.data
            
            # Extract payment information
            charge_id = charge_data.get("id")
            amount = charge_data.get("pricing", {}).get("local", {}).get("amount")
            currency = charge_data.get("pricing", {}).get("local", {}).get("currency")
            
            # Find user by charge metadata (you'll need to store this when creating charges)
            user_id = charge_data.get("metadata", {}).get("user_id")
            if not user_id:
                return
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Log payment
            payment_log = PaymentLog(
                user_id=user.id,
                transaction_id=charge_id,
                amount=float(amount) if amount else 0.0,
                currency=currency or "USD",
                payment_method="coinbase",
                status="confirmed",
                webhook_ip=client_ip,
                raw_webhook_data=json.dumps(payload.dict())
            )
            db.add(payment_log)
            
            # Upgrade user to premium
            user.tier = UserTier.PREMIUM
            user.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            
            db.commit()
            
            # TODO: Send confirmation email
            
    except Exception as e:
        # Log error but don't raise (webhook should return 200)
        print(f"Error processing Coinbase webhook: {e}")

async def process_crypto_payment(
    payload: PaymentWebhookPayload,
    client_ip: str,
    db: Session
):
    """
    Process generic crypto payment webhook securely.
    """
    try:
        if payload.status == "confirmed":
            user = db.query(User).filter(User.id == payload.user_id).first()
            if not user:
                return
            
            # Log payment
            payment_log = PaymentLog(
                user_id=user.id,
                transaction_id=payload.transaction_id,
                amount=float(payload.amount),
                currency=payload.currency,
                payment_method=payload.payment_method,
                status=payload.status,
                webhook_ip=client_ip,
                raw_webhook_data=json.dumps(payload.dict())
            )
            db.add(payment_log)
            
            # Upgrade user based on payment amount
            if float(payload.amount) >= 10.0:  # $10+ for premium
                user.tier = UserTier.PREMIUM
                user.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            
            db.commit()
            
    except Exception as e:
        print(f"Error processing crypto payment webhook: {e}")

@router.get("/webhook-status")
async def webhook_status():
    """
    Health check endpoint for webhook services.
    """
    return {
        "status": "active",
        "supported_services": ["coinbase-commerce", "crypto-payment"],
        "security_features": [
            "HMAC signature verification",
            "IP whitelist filtering", 
            "Replay attack prevention",
            "Timestamp validation",
            "Duplicate detection"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
