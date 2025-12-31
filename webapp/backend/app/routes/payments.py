from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import uuid
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import User, Subscription, SubscriptionStatus, UserTier
from app.utils.security import get_current_active_user
from app.services.crypto_payments import CryptoPaymentManager

router = APIRouter()

# Initialize crypto payment manager
crypto_manager = CryptoPaymentManager()

# Pydantic models
class CreateCryptoPaymentRequest(BaseModel):
    currency: str  # btc, eth, usdt, etc.
    plan_type: str = "premium"  # premium, api
    success_url: str
    cancel_url: str

class CryptoPaymentResponse(BaseModel):
    payment_id: str
    payment_url: str
    amount_usd: float
    currency: str
    crypto_amount: Optional[str] = None
    expires_at: Optional[str] = None
    qr_code_url: Optional[str] = None

class PriceEstimateRequest(BaseModel):
    currency: str
    plan_type: str = "premium"

class PriceEstimateResponse(BaseModel):
    currency: str
    amount_usd: float
    crypto_amount: str
    exchange_rate: float

class SubscriptionResponse(BaseModel):
    id: int
    status: SubscriptionStatus
    plan_type: str
    amount: int
    currency: str
    payment_method: str
    start_date: datetime
    end_date: Optional[datetime]

    class Config:
        from_attributes = True

# Plan pricing
PLANS = {
    "premium": {"price_usd": 9.99, "duration_days": 30},
    "api": {"price_usd": 29.99, "duration_days": 30}
}

@router.get("/currencies")
async def get_supported_currencies():
    """Get list of supported cryptocurrencies."""
    currencies = await crypto_manager.get_available_currencies()
    return {
        "supported_currencies": currencies,
        "popular": ["btc", "eth", "usdt", "usdc", "ltc"],
        "providers": {
            "nowpayments": "Supports 200+ cryptocurrencies",
            "coinbase": "Major cryptocurrencies with high reliability"
        }
    }

@router.post("/estimate", response_model=PriceEstimateResponse)
async def get_price_estimate(
    request: PriceEstimateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Get cryptocurrency price estimate for subscription."""
    if request.plan_type not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    amount_usd = PLANS[request.plan_type]["price_usd"]
    
    # Get estimate from crypto service
    estimate = await crypto_manager.get_price_estimate(amount_usd, request.currency)
    
    if not estimate:
        raise HTTPException(
            status_code=400, 
            detail=f"Unable to get price estimate for {request.currency.upper()}"
        )
    
    return PriceEstimateResponse(
        currency=request.currency.upper(),
        amount_usd=amount_usd,
        crypto_amount=estimate.get("estimated_amount", "0"),
        exchange_rate=float(estimate.get("estimated_amount", 0)) / amount_usd if amount_usd > 0 else 0
    )

@router.post("/create-crypto-payment", response_model=CryptoPaymentResponse)
async def create_crypto_payment(
    request: CreateCryptoPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create cryptocurrency payment for subscription."""
    
    # Validate plan
    if request.plan_type not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    # Check if user already has active subscription
    active_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if active_subscription:
        raise HTTPException(status_code=400, detail="User already has an active subscription")
    
    # Generate unique order ID
    order_id = f"sub_{current_user.id}_{uuid.uuid4().hex[:8]}"
    amount_usd = PLANS[request.plan_type]["price_usd"]
    
    try:
        # Create payment with crypto service
        payment_result = await crypto_manager.create_payment(
            amount_usd=amount_usd,
            currency=request.currency,
            order_id=order_id,
            user_email=current_user.email,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        if not payment_result:
            raise HTTPException(status_code=500, detail="Failed to create payment")
        
        # Store pending subscription
        pending_subscription = Subscription(
            user_id=current_user.id,
            status=SubscriptionStatus.UNPAID,
            plan_type=request.plan_type,
            amount=int(amount_usd * 100),  # Store in cents
            currency="USD",
            start_date=datetime.utcnow(),
            # Store payment metadata in a JSON field (you might want to add this to your model)
        )
        
        db.add(pending_subscription)
        db.commit()
        
        # Format response based on provider
        if "payment_url" in payment_result:
            # NOWPayments response
            response = CryptoPaymentResponse(
                payment_id=payment_result.get("payment_id", order_id),
                payment_url=payment_result.get("payment_url", ""),
                amount_usd=amount_usd,
                currency=request.currency.upper(),
                crypto_amount=payment_result.get("pay_amount"),
                expires_at=payment_result.get("created_at")  # Add expiry calculation
            )
        else:
            # Coinbase Commerce response
            response = CryptoPaymentResponse(
                payment_id=payment_result.get("id", order_id),
                payment_url=payment_result.get("hosted_url", ""),
                amount_usd=amount_usd,
                currency=request.currency.upper(),
                expires_at=payment_result.get("expires_at")
            )
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@router.get("/payment/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    provider: str = "coinbase",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment status manually (development friendly)."""
    try:
        if provider == "coinbase":
            status = await crypto_manager.coinbase.get_charge(payment_id)
        elif provider == "nowpayments":
            status = await crypto_manager.nowpayments.get_payment_status(payment_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        if not status:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if payment is confirmed and update subscription
        is_confirmed = False
        if provider == "coinbase":
            timeline = status.get("timeline", [])
            is_confirmed = any(event.get("status") == "CONFIRMED" for event in timeline)
        elif provider == "nowpayments":
            is_confirmed = status.get("payment_status") == "finished"
        
        # Auto-activate subscription if confirmed (development helper)
        if is_confirmed and current_user.subscription_tier == "free":
            await activate_subscription(current_user, "premium", db)
            status["subscription_activated"] = True
        
        return {
            "payment_id": payment_id,
            "provider": provider,
            "status": status,
            "is_confirmed": is_confirmed
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error checking payment: {str(e)}")

@router.post("/webhook/nowpayments")
async def nowpayments_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle NOWPayments IPN callbacks."""
    payload = await request.body()
    signature = request.headers.get("x-nowpayments-sig", "")
    
    # Verify signature
    if not crypto_manager.verify_webhook("nowpayments", payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
        await process_payment_update(data, "nowpayments", db)
        return {"status": "success"}
    except Exception as e:
        print(f"NOWPayments webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@router.post("/webhook/coinbase")
async def coinbase_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Coinbase Commerce webhooks."""
    payload = await request.body()
    signature = request.headers.get("x-cc-webhook-signature", "")
    
    # Verify signature
    if not crypto_manager.verify_webhook("coinbase", payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
        await process_payment_update(data, "coinbase", db)
        return {"status": "success"}
    except Exception as e:
        print(f"Coinbase webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

async def process_payment_update(data: Dict, provider: str, db: Session):
    """Process payment status updates from webhooks."""
    
    if provider == "nowpayments":
        order_id = data.get("order_id")
        payment_status = data.get("payment_status")
        
        # Find user by order ID pattern
        if order_id and order_id.startswith("sub_"):
            user_id = int(order_id.split("_")[1])
            user = db.query(User).filter(User.id == user_id).first()
            
            if user and payment_status == "finished":
                await activate_subscription(user, data.get("order_description", "premium"), db)
                
    elif provider == "coinbase":
        event_type = data.get("event", {}).get("type")
        charge_data = data.get("event", {}).get("data", {})
        
        if event_type == "charge:confirmed":
            metadata = charge_data.get("metadata", {})
            
            # Only process payments for this app
            if metadata.get("app_name") != "bin_search":
                print(f"Ignoring webhook for app: {metadata.get('app_name', 'unknown')}")
                return
            
            user_email = metadata.get("user_email")
            
            if user_email:
                user = db.query(User).filter(User.email == user_email).first()
                if user:
                    await activate_subscription(user, "premium", db)

async def activate_subscription(user: User, plan_type: str, db: Session):
    """Activate user subscription after successful payment."""
    
    # Find pending subscription
    pending_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.UNPAID
    ).first()
    
    if pending_sub:
        # Update existing subscription
        pending_sub.status = SubscriptionStatus.ACTIVE
        pending_sub.start_date = datetime.utcnow()
        pending_sub.end_date = datetime.utcnow() + timedelta(days=PLANS[plan_type]["duration_days"])
        pending_sub.payment_method = "cryptocurrency"
    else:
        # Create new subscription
        new_subscription = Subscription(
            user_id=user.id,
            status=SubscriptionStatus.ACTIVE,
            plan_type=plan_type,
            amount=int(PLANS[plan_type]["price_usd"] * 100),
            currency="USD",
            payment_method="cryptocurrency",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=PLANS[plan_type]["duration_days"])
        )
        db.add(new_subscription)
    
    # Update user tier
    if plan_type == "premium":
        user.tier = UserTier.PREMIUM
    elif plan_type == "api":
        user.tier = UserTier.API
    
    db.commit()

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's current subscription."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc()).first()
    
    if not subscription:
        return None
    
    return SubscriptionResponse.from_orm(subscription)

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel user's current subscription."""
    
    # Find active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Update subscription status
    subscription.status = SubscriptionStatus.CANCELED
    subscription.end_date = datetime.utcnow()
    current_user.tier = UserTier.FREE
    
    db.commit()
    
    return {"message": "Subscription canceled successfully"}

@router.get("/plans")
async def get_available_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "5 card generations per day",
                    "Basic BIN lookup",
                    "Standard card generation"
                ]
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": PLANS["premium"]["price_usd"],
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Unlimited card generation",
                    "AVS postal code generation",
                    "Bulk generation (up to 1000 cards)",
                    "Export in JSON/CSV/XML formats",
                    "Priority support"
                ]
            },
            {
                "id": "api",
                "name": "API Access",
                "price": PLANS["api"]["price_usd"],
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Everything in Premium",
                    "API access with high rate limits",
                    "Webhook support",
                    "Priority support",
                    "Custom integrations"
                ]
            }
        ],
        "payment_methods": {
            "cryptocurrency": {
                "supported": True,
                "popular_currencies": ["BTC", "ETH", "USDT", "USDC", "LTC"],
                "total_supported": "200+ cryptocurrencies",
                "providers": ["NOWPayments", "Coinbase Commerce"]
            },
            "paypal": {
                "supported": False,
                "note": "Coming soon as backup option"
            }
        }
    }

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current subscription.
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc()).first()
    
    if not subscription:
        return None
    
    return SubscriptionResponse.from_orm(subscription)

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel user's current subscription.
    """
    # Find active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        # Cancel in Stripe
        if subscription.stripe_subscription_id:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update local record
        subscription.status = SubscriptionStatus.CANCELED
        subscription.end_date = datetime.utcnow()
        current_user.tier = UserTier.FREE
        
        db.commit()
        
        return {"message": "Subscription canceled successfully"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

@router.get("/plans")
async def get_available_plans():
    """
    Get available subscription plans.
    """
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "5 card generations per day",
                    "Basic BIN lookup",
                    "Standard card generation"
                ]
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 999,  # $9.99 in cents
                "currency": "USD",
                "interval": "month",
                "stripe_price_id": STRIPE_PRICE_ID_PREMIUM,
                "features": [
                    "Unlimited card generation",
                    "AVS postal code generation",
                    "Bulk generation (up to 1000 cards)",
                    "Export in JSON/CSV/XML formats",
                    "Priority support"
                ]
            }
        ]
    }
