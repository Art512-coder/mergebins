from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import os

from app.database import get_db, get_redis
from app.models import BinData, User, UserTier
from app.services.bin_import import search_bins, get_bin_stats
from app.services.d1_bin_service import d1_service, get_bin_from_d1
from app.services.premium_features import premium_service
from app.utils.security import get_current_active_user
import json

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Pydantic models
class BinResponse(BaseModel):
    bin: str
    brand: Optional[str] = None
    scheme: Optional[str] = None  # Added for frontend compatibility 
    issuer: Optional[str] = None
    bank: Optional[str] = None  # Alias for issuer
    bank_name: Optional[str] = None  # Additional alias
    type: Optional[str] = None
    level: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None  # Added for frontend compatibility
    country_name: Optional[str] = None
    bank_phone: Optional[str] = None
    bank_url: Optional[str] = None
    valid: bool = True  # Added for frontend compatibility

    class Config:
        from_attributes = True

class BinSearchRequest(BaseModel):
    brand: Optional[str] = None
    country: Optional[str] = None
    issuer: Optional[str] = None
    type: Optional[str] = None
    limit: int = 50

class BinStatsResponse(BaseModel):
    total_bins: int
    brands: int
    countries: int
    issuers: int

async def get_bin_data(bin_str: str, db: Session) -> Optional[dict]:
    """
    Unified function to get BIN data from D1 or SQLite with caching.
    """
    # Try Redis cache first
    redis_client = get_redis()
    cache_key = f"bin:{bin_str}"
    
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
        except Exception:
            pass
    
    # Try D1 database first
    try:
        bin_result = await d1_service.lookup_bin(bin_str)
        if bin_result:
            response_data = {
                "bin": bin_result["bin"],
                "brand": bin_result.get("brand"),
                "scheme": bin_result.get("brand"),
                "issuer": bin_result.get("issuer"),
                "bank": bin_result.get("issuer"),
                "bank_name": bin_result.get("issuer"),
                "type": bin_result.get("type"),
                "level": bin_result.get("category"),
                "country_code": None,
                "country": bin_result.get("country"),
                "country_name": bin_result.get("country"),
                "bank_phone": bin_result.get("bank_phone"),
                "bank_url": bin_result.get("bank_url"),
                "valid": True
            }
            
            # Cache the D1 result
            try:
                redis_client.setex(cache_key, 3600, json.dumps(response_data))
            except Exception:
                pass
            
            return response_data
    except Exception as e:
        print(f"D1 lookup failed for BIN {bin_str}: {e}")
    
    # Fallback to SQLite database
    bin_data = db.query(BinData).filter(BinData.bin == bin_str).first()
    
    if not bin_data:
        return None
    
    response_data = {
        "bin": bin_data.bin,
        "brand": bin_data.brand,
        "issuer": bin_data.issuer,
        "type": bin_data.type,
        "level": bin_data.level,
        "country_code": bin_data.country_code,
        "country_name": bin_data.country_name,
        "bank_phone": bin_data.bank_phone,
        "bank_url": bin_data.bank_url
    }
    
    # Cache the SQLite result
    try:
        redis_client.setex(cache_key, 3600, json.dumps(response_data))
    except Exception:
        pass
    
    return response_data

async def search_bin_data(search_request: BinSearchRequest, db: Session) -> List[dict]:
    """
    Unified function to search BIN data from D1 or SQLite.
    """
    limit = min(search_request.limit, 100)
    
    # Try D1 database first
    try:
        d1_results = await d1_service.search_bins(
            brand=search_request.brand,
            country=search_request.country,
            issuer=search_request.issuer,
            bin_type=search_request.type,
            limit=limit
        )
        
        if d1_results:
            response_list = []
            for result in d1_results:
                response_data = {
                    "bin": result["bin"],
                    "brand": result.get("brand"),
                    "issuer": result.get("issuer"),
                    "type": result.get("type"),
                    "level": result.get("category"),
                    "country_code": None,
                    "country_name": result.get("country"),
                    "bank_phone": result.get("bank_phone"),
                    "bank_url": result.get("bank_url")
                }
                response_list.append(response_data)
            return response_list
    except Exception as e:
        print(f"D1 search failed: {e}")
    
    # Fallback to SQLite
    results = search_bins(
        db=db,
        brand=search_request.brand,
        country=search_request.country,
        issuer=search_request.issuer,
        bin_type=search_request.type,
        limit=limit
    )
    
    if not results:
        return []
    
    return [result.__dict__ for result in results]

@router.get("/lookup/{bin_number}", response_model=BinResponse)
@limiter.limit("60/minute")  # Increased rate limit since it's free
async def lookup_bin(
    bin_number: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Lookup specific BIN information.
    Completely free for all users with generous rate limiting.
    Uses Cloudflare D1 as primary source with SQLite fallback for maximum performance.
    """
    # Clean BIN input
    bin_str = str(bin_number).strip()[:6]
    
    if len(bin_str) < 6:
        raise HTTPException(status_code=400, detail="BIN must be at least 6 digits")
    
    data = await get_bin_data(bin_str, db)
    
    if not data:
        raise HTTPException(status_code=404, detail="BIN not found in database")
    
    return BinResponse(**data)

@router.post("/search", response_model=List[BinResponse])
@limiter.limit("20/minute")
async def search_bin_database(
    search_request: BinSearchRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Search BIN database with filters.
    Completely free for all users. Rate limited to 20 requests per minute.
    Uses Cloudflare D1 as primary source with SQLite fallback.
    """
    results = await search_bin_data(search_request, db)
    
    if not results:
        raise HTTPException(status_code=404, detail="No BINs found matching criteria")
    
    return [BinResponse(**data) for data in results]

@router.get("/search", response_model=List[BinResponse])
@limiter.limit("20/minute")
async def search_bin_database_get(
    request: Request,
    brand: Optional[str] = Query(None, description="Card brand (e.g., VISA, MASTERCARD)"),
    country: Optional[str] = Query(None, description="Country name"),
    issuer: Optional[str] = Query(None, description="Issuer/bank name"),
    bin_type: Optional[str] = Query(None, description="Card type (e.g., CREDIT, DEBIT)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results (max 100)"),
    db: Session = Depends(get_db)
):
    """
    Search BIN database with GET parameters.
    Completely free for all users. Rate limited to 20 requests per minute.
    Uses Cloudflare D1 as primary source with SQLite fallback.
    """
    # Try D1 database first
    try:
        d1_results = await d1_service.search_bins(
            brand=brand,
            country=country,
            issuer=issuer,
            bin_type=bin_type,
            limit=limit
        )
        
        if d1_results:
            response_list = []
            for result in d1_results:
                response_data = {
                    "bin": result["bin"],
                    "brand": result.get("brand"),
                    "issuer": result.get("issuer"),
                    "type": result.get("type"),
                    "level": result.get("category"),  # D1 uses 'category' field
                    "country_code": None,  # Not available in D1 schema
                    "country_name": result.get("country"),
                    "bank_phone": result.get("bank_phone"),
                    "bank_url": result.get("bank_url")
                }
                response_list.append(BinResponse(**response_data))
            return response_list
    except Exception as e:
        # Log D1 error but continue to fallback
        print(f"D1 search failed: {e}")
    
    # Fallback to SQLite
    results = search_bins(
        db=db,
        brand=brand,
        country=country,
        issuer=issuer,
        bin_type=bin_type,
        limit=limit
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="No BINs found matching criteria")
    
    return [BinResponse.from_orm(result) for result in results]

@router.get("/stats", response_model=BinStatsResponse)
async def get_database_stats(
    db: Session = Depends(get_db)
):
    """
    Get BIN database statistics.
    Completely free for all users.
    """
    # Try cache first
    redis_client = get_redis()
    cache_key = "bin_stats"
    
    try:
        cached_stats = redis_client.get(cache_key)
        if cached_stats:
            stats_data = json.loads(cached_stats)
            return BinStatsResponse(**stats_data)
    except Exception:
        pass
    
    # Generate fresh stats
    stats = get_bin_stats(db)
    
    # Cache for 10 minutes
    try:
        redis_client.setex(cache_key, 600, json.dumps(stats))
    except Exception:
        pass
    
    return BinStatsResponse(**stats)

@router.get("/brands", response_model=List[str])
async def get_available_brands(
    db: Session = Depends(get_db)
):
    """
    Get list of available card brands.
    Completely free for all users.
    """
    brands = db.query(BinData.brand).filter(BinData.brand.isnot(None)).distinct().all()
    return [brand[0] for brand in brands if brand[0]]

@router.get("/countries", response_model=List[str])
async def get_available_countries(
    db: Session = Depends(get_db)
):
    """
    Get list of available countries.
    Completely free for all users.
    """
    countries = db.query(BinData.country_name).filter(BinData.country_name.isnot(None)).distinct().all()
    return [country[0] for country in countries if country[0]]

# PREMIUM BIN LOOKUP ENDPOINTS

@router.get("/lookup-premium/{bin}")
async def premium_bin_lookup(
    bin: str,
    include_extended: bool = True,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Premium BIN lookup with extended data and analytics.
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Premium BIN lookup requires subscription. Upgrade to access extended data."
        )
    
    # Validate BIN format
    if not bin or len(bin.strip()) < 6:
        raise HTTPException(status_code=400, detail="BIN must be at least 6 digits")
    
    bin_clean = bin.strip()[:6]
    
    try:
        result = await premium_service.enhanced_bin_lookup(
            bin_input=bin_clean,
            user=current_user,
            db=db,
            include_extended_data=include_extended
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Premium lookup failed: {str(e)}")

@router.post("/analyze-multiple")
async def analyze_multiple_bins(
    bins: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze multiple BINs at once (Premium Feature).
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Multi-BIN analysis requires premium subscription."
        )
    
    if len(bins) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 BINs per request")
    
    results = []
    for bin_input in bins:
        try:
            result = await premium_service.enhanced_bin_lookup(
                bin_input=bin_input.strip()[:6],
                user=current_user,
                db=db,
                include_extended_data=True
            )
            results.append(result)
        except Exception as e:
            results.append({
                "bin": bin_input,
                "error": str(e),
                "valid": False
            })
    
    return {
        "results": results,
        "total_processed": len(bins),
        "successful": len([r for r in results if r.get("valid", False)]),
        "failed": len([r for r in results if not r.get("valid", True)]),
        "processed_at": datetime.utcnow().isoformat()
    }

@router.get("/premium/insights")
async def get_premium_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get premium insights and analytics about BIN database.
    """
    if not premium_service.is_user_premium(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Premium insights require subscription."
        )
    
    # Get comprehensive statistics
    total_bins = db.query(BinData).count()
    
    # Brand distribution
    brand_stats = db.query(BinData.brand, db.func.count(BinData.id)).group_by(BinData.brand).all()
    brand_distribution = {brand: count for brand, count in brand_stats if brand}
    
    # Country distribution (top 10)
    country_stats = db.query(BinData.country_name, db.func.count(BinData.id)).group_by(BinData.country_name).order_by(db.func.count(BinData.id).desc()).limit(10).all()
    top_countries = {country: count for country, count in country_stats if country}
    
    # Type distribution
    type_stats = db.query(BinData.type, db.func.count(BinData.id)).group_by(BinData.type).all()
    type_distribution = {card_type: count for card_type, count in type_stats if card_type}
    
    return {
        "database_overview": {
            "total_bins": total_bins,
            "last_updated": datetime.utcnow().isoformat(),
            "coverage": "Global BIN database with 458K+ records"
        },
        "brand_distribution": brand_distribution,
        "top_countries": top_countries,
        "type_distribution": type_distribution,
        "premium_features": {
            "avs_supported_countries": len(premium_service.AVS_POSTAL_CODES),
            "export_formats": ["JSON", "CSV", "XML"],
            "bulk_generation_limit": 1000
        }
    }
