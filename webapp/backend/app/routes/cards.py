from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta, timezone
import json

from app.database import get_db, get_redis
from app.models import User, UsageLog, ActionType, UserTier
from app.utils.security import get_current_active_user
from app.utils.ip_rate_limit import ip_rate_limiter
from app.services.card_generator import generate_test_card, AVS_POSTAL_CODES
from app.services.security_service import SecurityService  # NEW
from app.services.premium_features import premium_service
import os

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
security_service = SecurityService()  # NEW

# Rate limits
FREE_IP_DAILY_LIMIT = int(os.getenv("FREE_IP_DAILY_LIMIT", "3"))  # 3 free per IP per 24h
PREMIUM_TIER_DAILY_LIMIT = int(os.getenv("PREMIUM_TIER_DAILY_LIMIT", "50"))  # 50 for premium users

# Pydantic models
class CardGenerationRequest(BaseModel):
    bin: str
    include_avs: bool = False
    avs_country: Optional[str] = None
    
    @validator('bin')
    def validate_bin(cls, v):
        if not v or len(str(v).strip()) < 6:
            raise ValueError('BIN must be at least 6 digits')
        return str(v).strip()[:6]
    
    @validator('avs_country')
    def validate_avs_country(cls, v, values):
        if values.get('include_avs') and v:
            if v.upper() not in AVS_POSTAL_CODES:
                supported = ', '.join(AVS_POSTAL_CODES.keys())
                raise ValueError(f'AVS country must be one of: {supported}')
        return v.upper() if v else None

class BulkGenerationRequest(BaseModel):
    bin: str
    count: int
    include_avs: bool = False
    avs_country: Optional[str] = None
    
    @validator('bin')
    def validate_bin(cls, v):
        if not v or len(str(v).strip()) < 6:
            raise ValueError('BIN must be at least 6 digits')
        return str(v).strip()[:6]
    
    @validator('count')
    def validate_count(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Count must be between 1 and 1000')
        return v

class CardResponse(BaseModel):
    number: str
    cvv: str
    expiry: str
    bin: str
    brand: Optional[str] = None
    issuer: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    postal_code: Optional[str] = None
    generated_at: Optional[datetime] = None

class BulkCardResponse(BaseModel):
    cards: List[CardResponse]
    count: int
    bin: str
    metadata: dict

def check_rate_limit(user: Optional[User], request: Request) -> tuple[bool, str]:
    """
    Check if user or IP has exceeded their daily rate limit.
    Returns (is_allowed, error_message)
    """
    client_ip = request.client.host
    
    # For authenticated premium users, check user-based limits
    if user and user.tier in [UserTier.PREMIUM, UserTier.API]:
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
        end_of_day = datetime.combine(today, datetime.max.time().replace(tzinfo=timezone.utc))
        
        daily_usage = user.db.query(UsageLog).filter(
            UsageLog.user_id == user.id,
            UsageLog.action == ActionType.CARD_GENERATION,
            UsageLog.created_at >= start_of_day,
            UsageLog.created_at <= end_of_day
        ).count()
        
        if daily_usage >= PREMIUM_TIER_DAILY_LIMIT:
            return False, f"Daily limit exceeded. Premium tier allows {PREMIUM_TIER_DAILY_LIMIT} cards per day."
        
        return True, ""
    
    # For anonymous users or free users, check IP-based limits
    is_allowed, remaining = ip_rate_limiter.check_ip_limit(client_ip, "cc_generation", FREE_IP_DAILY_LIMIT, 24)
    
    if not is_allowed:
        return False, f"Daily limit exceeded. Free users get {FREE_IP_DAILY_LIMIT} card generations per 24 hours per IP address. Upgrade to Premium for {PREMIUM_TIER_DAILY_LIMIT} cards per day."
    
    return True, ""

def log_usage(user: Optional[User], db: Session, request: Request, action: ActionType, metadata: dict = None):
    """
    Log user action for rate limiting and analytics.
    """
    if user:
        # Log for authenticated users
        usage_log = UsageLog(
            user_id=user.id,
            action=action,
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent'),
            metadata=json.dumps(metadata) if metadata else None
        )
        db.add(usage_log)
        db.commit()
    
    # Always increment IP-based counter for card generation
    if action == ActionType.CARD_GENERATION:
        ip_rate_limiter.increment_ip_usage(request.client.host, "cc_generation", 24)

async def security_check(request: Request) -> tuple[bool, str]:
    """
    Comprehensive security check for all card generation endpoints.
    Returns (is_allowed, error_message)
    """
    analysis = await security_service.analyze_request_security(request)
    
    if analysis['risk_level'] == 'HIGH':
        return False, "Access denied: High-risk activity detected"
    elif analysis['risk_level'] == 'MEDIUM':
        # Log suspicious activity but allow with warnings
        await security_service.log_security_event(request, "SUSPICIOUS_CARD_GENERATION", analysis)
        return True, ""
    
    return True, ""

@router.get("/generate/{bin}", response_model=CardResponse)
@limiter.limit("10/minute")
async def generate_card_for_bin(
    bin: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Generate a single test card for a specific BIN (quick generation).
    """
    # Validate BIN
    if not bin or len(bin.strip()) < 6:
        raise HTTPException(status_code=400, detail="BIN must be at least 6 digits")
    bin = bin.strip()[:6]
    
    # SECURITY CHECK
    security_allowed, security_msg = await security_check(request)
    if not security_allowed:
        raise HTTPException(status_code=403, detail=security_msg)
    
    # Check rate limits
    is_allowed, error_msg = check_rate_limit(current_user, request)
    if not is_allowed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    try:
        # Generate card
        card_data = await generate_test_card(
            bin_input=bin,
            db=db,
            include_avs=False,
            avs_country=None
        )
        
        # Log usage
        security_analysis = await security_service.analyze_request_security(request)
        log_usage(
            user=current_user,
            db=db,
            request=request,
            action=ActionType.CARD_GENERATION,
            metadata={
                'bin': bin,
                'security_risk_level': security_analysis['risk_level'],
                'ip_risk_score': security_analysis['ip_analysis']['risk_score']
            }
        )
        
        # Add generated timestamp
        card_data['generated_at'] = datetime.now(timezone.utc)
        
        return CardResponse(**card_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Card generation failed")

@router.post("/generate", response_model=CardResponse)
@limiter.limit("10/minute")
async def generate_single_card(
    request: Request,
    card_request: CardGenerationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Generate a single test card with advanced security.
    """
    # SECURITY CHECK - NEW
    security_allowed, security_msg = await security_check(request)
    if not security_allowed:
        raise HTTPException(status_code=403, detail=security_msg)
    
    # Check rate limits
    is_allowed, error_msg = check_rate_limit(current_user, request)
    if not is_allowed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    # Premium feature check for AVS - only for authenticated users
    if card_request.include_avs and (not current_user or current_user.tier == UserTier.FREE):
        raise HTTPException(
            status_code=403,
            detail="AVS postal codes are a Premium feature. Upgrade to Premium to access this feature."
        )
    
    try:
        # Generate card
        card_data = await generate_test_card(
            bin_input=card_request.bin,
            db=db,
            include_avs=card_request.include_avs,
            avs_country=card_request.avs_country
        )
        
        # Log usage with security metadata
        security_analysis = await security_service.analyze_request_security(request)
        log_usage(
            user=current_user,
            db=db,
            request=request,
            action=ActionType.CARD_GENERATION,
            metadata={
                'bin': card_request.bin,
                'include_avs': card_request.include_avs,
                'avs_country': card_request.avs_country,
                'security_risk_level': security_analysis['risk_level'],  # NEW
                'ip_risk_score': security_analysis['ip_analysis']['risk_score']  # NEW
            }
        )
        
        # Add generated timestamp
        card_data['generated_at'] = datetime.now(timezone.utc)
        
        return CardResponse(**card_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Card generation failed")

@router.post("/generate/bulk", response_model=BulkCardResponse)
@limiter.limit("5/minute")
async def generate_bulk_cards(
    request: Request,
    bulk_request: BulkGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple test cards (Premium feature).
    """
    # Premium feature check
    if current_user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=403,
            detail="Bulk generation is a Premium feature. Please upgrade to access this feature."
        )
    
    # AVS check for free users (shouldn't reach here, but safety check)
    if bulk_request.include_avs and current_user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=403,
            detail="AVS generation is a Premium feature."
        )
    
    try:
        cards = []
        generation_errors = 0
        
        for _ in range(bulk_request.count):
            try:
                card_data = await generate_test_card(
                    bin_input=bulk_request.bin,
                    db=db,
                    include_avs=bulk_request.include_avs,
                    avs_country=bulk_request.avs_country
                )
                card_data['generated_at'] = datetime.now(timezone.utc)
                cards.append(CardResponse(**card_data))
                
            except Exception as e:
                generation_errors += 1
                # Continue generating other cards
                continue
        
        if not cards:
            raise HTTPException(status_code=400, detail="Failed to generate any cards")
        
        # Log bulk usage
        log_usage(
            user=current_user,
            db=db,
            request=request,
            action=ActionType.BULK_EXPORT,
            metadata={
                'bin': bulk_request.bin,
                'count_requested': bulk_request.count,
                'count_generated': len(cards),
                'include_avs': bulk_request.include_avs,
                'avs_country': bulk_request.avs_country
            }
        )
        
        return BulkCardResponse(
            cards=cards,
            count=len(cards),
            bin=bulk_request.bin,
            metadata={
                'requested_count': bulk_request.count,
                'generated_count': len(cards),
                'errors': generation_errors,
                'include_avs': bulk_request.include_avs,
                'avs_country': bulk_request.avs_country,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Bulk generation failed")

@router.get("/usage")
async def get_usage_stats(
    request: Request,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current usage statistics.
    Shows IP-based limits for anonymous users, user-based limits for authenticated users.
    """
    client_ip = request.client.host
    
    if current_user and current_user.tier in [UserTier.PREMIUM, UserTier.API]:
        # Authenticated premium user stats
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
        end_of_day = datetime.combine(today, datetime.max.time().replace(tzinfo=timezone.utc))
        
        today_generations = db.query(UsageLog).filter(
            UsageLog.user_id == current_user.id,
            UsageLog.action == ActionType.CARD_GENERATION,
            UsageLog.created_at >= start_of_day,
            UsageLog.created_at <= end_of_day
        ).count()
        
        # Get this month's usage
        first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_generations = db.query(UsageLog).filter(
            UsageLog.user_id == current_user.id,
            UsageLog.action == ActionType.CARD_GENERATION,
            UsageLog.created_at >= first_of_month
        ).count()
        
        daily_remaining = max(0, PREMIUM_TIER_DAILY_LIMIT - today_generations)
        
        return {
            "user_type": "premium_authenticated",
            "user_tier": current_user.tier.value,
            "daily_usage": today_generations,
            "daily_limit": PREMIUM_TIER_DAILY_LIMIT,
            "daily_remaining": daily_remaining,
            "monthly_usage": month_generations,
            "features": {
                "basic_generation": True,
                "avs_generation": True,
                "bulk_generation": True,
                "export_formats": True
            }
        }
    else:
        # Anonymous user or free user - IP-based limits
        usage_info = ip_rate_limiter.get_ip_usage_info(client_ip, "cc_generation")
        daily_remaining = max(0, FREE_IP_DAILY_LIMIT - usage_info.get('count', 0))
        
        return {
            "user_type": "anonymous_or_free",
            "user_tier": current_user.tier.value if current_user else "anonymous",
            "daily_usage": usage_info.get('count', 0),
            "daily_limit": FREE_IP_DAILY_LIMIT,
            "daily_remaining": daily_remaining,
            "reset_time": usage_info.get('reset_time'),
            "features": {
                "basic_generation": True,
                "avs_generation": False,
                "bulk_generation": False,
                "export_formats": False
            }
        }

@router.get("/ip-status")
async def get_ip_rate_limit_status(request: Request):
    """
    Get IP-based rate limit status for anonymous users.
    No authentication required.
    """
    client_ip = request.client.host
    usage_info = ip_rate_limiter.get_ip_usage_info(client_ip, "cc_generation")
    
    remaining = max(0, FREE_IP_DAILY_LIMIT - usage_info.get('count', 0))
    
    return {
        "ip_address": client_ip,
        "daily_usage": usage_info.get('count', 0),
        "daily_limit": FREE_IP_DAILY_LIMIT,
        "remaining": remaining,
        "reset_time": usage_info.get('reset_time'),
        "time_until_reset": usage_info.get('time_until_reset')
    }

@router.get("/avs/countries")
async def get_avs_countries():
    """
    Get list of supported AVS countries.
    """
    return {
        "supported_countries": list(AVS_POSTAL_CODES.keys()),
        "country_details": {
            "US": "United States",
            "IT": "Italy", 
            "GB": "United Kingdom",
            "CA": "Canada",
            "AU": "Australia",
            "DE": "Germany",
            "FR": "France"
        }
    }

# PREMIUM FEATURES ENDPOINTS

@router.post("/generate-avs", response_model=List[CardResponse])
async def generate_cards_with_avs(
    request: CardGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate cards with AVS postal codes (Premium Feature).
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="AVS generation requires premium subscription. Upgrade to access this feature."
        )
    
    if not request.include_avs or not request.avs_country:
        raise HTTPException(
            status_code=400,
            detail="AVS generation requires include_avs=true and avs_country parameter"
        )
    
    try:
        cards = await premium_service.generate_card_with_avs(
            bin_input=request.bin,
            country_code=request.avs_country,
            user=current_user,
            db=db,
            count=1
        )
        
        # Log usage
        log_usage(current_user, db, request, ActionType.CARD_GENERATION, {
            "bin": request.bin,
            "avs_country": request.avs_country,
            "premium_feature": "avs_generation"
        })
        
        return [CardResponse(**card) for card in cards]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AVS generation failed: {str(e)}")

@router.post("/generate-bulk", response_model=BulkCardResponse)
async def generate_cards_bulk(
    request: BulkGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk generate cards (Premium Feature).
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Bulk generation requires premium subscription. Upgrade to access this feature."
        )
    
    # Check rate limits
    rate_limits = premium_service.get_rate_limits(current_user, db)
    if request.count > rate_limits["bulk_generation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Bulk generation limit: {rate_limits['bulk_generation']} cards per request"
        )
    
    try:
        result = await premium_service.bulk_generate_cards(
            bin_input=request.bin,
            count=request.count,
            user=current_user,
            db=db,
            include_avs=request.include_avs,
            avs_country=request.avs_country
        )
        
        # Log usage
        log_usage(current_user, db, request, ActionType.BULK_EXPORT, {
            "bin": request.bin,
            "count": request.count,
            "premium_feature": "bulk_generation"
        })
        
        return BulkCardResponse(
            cards=[CardResponse(**card) for card in result["cards"]],
            count=result["count"],
            bin=result["bin"],
            metadata=result["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk generation failed: {str(e)}")

@router.post("/export/{format}")
async def export_cards(
    format: str,
    cards_data: List[dict],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export cards in various formats (Premium Feature).
    Supported formats: json, csv, xml
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Export feature requires premium subscription. Upgrade to access this feature."
        )
    
    supported_formats = ["json", "csv", "xml"]
    if format.lower() not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Use one of: {', '.join(supported_formats)}"
        )
    
    # Check daily export limit
    daily_exports = premium_service.get_user_daily_usage(current_user, db, ActionType.BULK_EXPORT)
    rate_limits = premium_service.get_rate_limits(current_user, db)
    
    if daily_exports >= rate_limits["export"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily export limit reached: {rate_limits['export']} exports per day"
        )
    
    try:
        exported_data = premium_service.export_cards(cards_data, format.lower())
        
        # Log usage
        log_usage(current_user, db, request, ActionType.BULK_EXPORT, {
            "format": format.lower(),
            "card_count": len(cards_data),
            "premium_feature": "export"
        })
        
        # Set appropriate content type
        content_types = {
            "json": "application/json",
            "csv": "text/csv",
            "xml": "application/xml"
        }
        
        filename = f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format.lower()}"
        
        return Response(
            content=exported_data,
            media_type=content_types[format.lower()],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/premium/features")
async def get_premium_features(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get available premium features and user's access level.
    """
    is_premium = premium_service.is_user_premium(current_user, db) if current_user else False
    rate_limits = premium_service.get_rate_limits(current_user, db)
    
    features = {
        "basic_generation": {
            "available": True,
            "description": "Generate single test cards",
            "daily_limit": rate_limits["card_generation"]
        },
        "avs_generation": {
            "available": is_premium,
            "description": "Generate cards with AVS postal codes",
            "supported_countries": list(AVS_POSTAL_CODES.keys()),
            "daily_limit": rate_limits["avs_generation"] if is_premium else 0
        },
        "bulk_generation": {
            "available": is_premium,
            "description": "Generate multiple cards at once",
            "max_per_request": rate_limits["bulk_generation"],
            "daily_limit": rate_limits["card_generation"] if is_premium else 0
        },
        "export_formats": {
            "available": is_premium,
            "description": "Export cards in JSON, CSV, XML formats",
            "supported_formats": ["json", "csv", "xml"],
            "daily_limit": rate_limits["export"] if is_premium else 0
        },
        "enhanced_bin_lookup": {
            "available": is_premium,
            "description": "Extended BIN data with fraud indicators and generation hints",
            "daily_limit": rate_limits["bin_lookup"] if is_premium else 0
        }
    }
    
    user_status = {
        "user_tier": current_user.tier if current_user else "anonymous",
        "is_premium": is_premium,
        "subscription_status": "active" if is_premium else "none"
    }
    
    if current_user and is_premium:
        # Get current usage
        daily_usage = {
            "card_generation": premium_service.get_user_daily_usage(current_user, db, ActionType.CARD_GENERATION),
            "bin_lookup": premium_service.get_user_daily_usage(current_user, db, ActionType.BIN_LOOKUP),
            "export": premium_service.get_user_daily_usage(current_user, db, ActionType.BULK_EXPORT)
        }
        user_status["daily_usage"] = daily_usage
    
    return {
        "features": features,
        "user_status": user_status,
        "rate_limits": rate_limits
    }
