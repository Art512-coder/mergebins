from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timezone
import httpx
import re
import hashlib
import json

from app.database import get_db, get_redis
from app.models import User, UsageLog, ActionType, UserTier
from app.utils.security import get_current_active_user
from app.utils.ip_rate_limit import ip_rate_limiter
from app.services.security_service import SecurityService
import os

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
security_service = SecurityService()

# Configuration
CRYPTO_API_RATE_LIMIT = int(os.getenv("CRYPTO_API_RATE_LIMIT", "30"))  # 30 per minute
FREE_CRYPTO_CHECKS_PER_IP = int(os.getenv("FREE_CRYPTO_CHECKS_PER_IP", "10"))  # 10 per 24h per IP
PREMIUM_CRYPTO_CHECKS = int(os.getenv("PREMIUM_CRYPTO_CHECKS", "1000"))  # 1000 per day

# External API endpoints (use environment variables in production)
BLOCKCHAIN_INFO_API = "https://blockchain.info/address/{address}?format=json"
ETHERSCAN_API = "https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
BLOCKCYPHER_API = "https://api.blockcypher.com/v1/{crypto}/main/addrs/{address}/balance"  # For LTC, DOGE
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"  # For pricing
BLOCKFROST_API = "https://cardano-mainnet.blockfrost.io/api/v0/addresses/{address}"  # For ADA
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

class CryptoWalletRequest(BaseModel):
    address: str
    crypto_type: str  # 'bitcoin' or 'ethereum'
    
    @validator('address')
    def validate_address(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Address cannot be empty')
        if len(v) < 26 or len(v) > 62:
            raise ValueError('Invalid address length')
        return v
    
    @validator('crypto_type')
    def validate_crypto_type(cls, v):
        supported_types = ['bitcoin', 'ethereum', 'litecoin', 'dogecoin', 'cardano', 'solana']
        if v.lower() not in supported_types:
            raise ValueError(f'Crypto type must be one of: {supported_types}')
        return v.lower()

class CryptoBalanceResponse(BaseModel):
    address: str
    crypto_type: str
    balance: str
    balance_usd: Optional[float] = None
    last_updated: datetime
    transaction_count: Optional[int] = None
    is_valid: bool = True
    error: Optional[str] = None

async def advanced_crypto_security_check(request: Request, wallet_address: str) -> tuple[bool, str]:
    """
    Advanced security check specifically for crypto wallet operations.
    This is critical because crypto operations are high-value targets.
    """
    # Basic security analysis
    analysis = await security_service.analyze_request_security(request)
    
    # Additional crypto-specific checks
    crypto_risk_factors = []
    
    # Check for suspicious wallet address patterns
    if re.match(r'^[0-9a-fA-F]+$', wallet_address) and len(wallet_address) == 40:
        # Ethereum address pattern
        if wallet_address.lower() in ['0x0000000000000000000000000000000000000000']:
            crypto_risk_factors.append("NULL_ADDRESS")
    
    # Check for rapid successive wallet checks (crypto farming detection)
    client_ip = request.client.host
    recent_checks = await security_service.get_recent_activity(client_ip, "crypto_check", minutes=5)
    if recent_checks > 20:  # More than 20 wallet checks in 5 minutes
        crypto_risk_factors.append("RAPID_WALLET_SCANNING")
    
    # Check for bot-like behavior patterns
    user_agent = request.headers.get('user-agent', '').lower()
    if any(bot in user_agent for bot in ['curl', 'wget', 'python-requests', 'bot', 'crawler']):
        crypto_risk_factors.append("BOT_USER_AGENT")
    
    # Geographic risk analysis for crypto operations
    if analysis['ip_analysis']['country_risk'] == 'high':
        crypto_risk_factors.append("HIGH_RISK_COUNTRY")
    
    # Calculate combined risk score
    base_risk = analysis['risk_score']
    crypto_risk_penalty = len(crypto_risk_factors) * 20
    total_risk = base_risk + crypto_risk_penalty
    
    if total_risk > 80 or 'RAPID_WALLET_SCANNING' in crypto_risk_factors:
        await security_service.log_security_event(
            request, 
            "HIGH_RISK_CRYPTO_CHECK", 
            {
                "wallet_address": wallet_address,
                "risk_factors": crypto_risk_factors,
                "total_risk_score": total_risk
            }
        )
        return False, "Crypto wallet check denied: Suspicious activity detected"
    elif total_risk > 50:
        await security_service.log_security_event(
            request, 
            "MEDIUM_RISK_CRYPTO_CHECK", 
            {
                "wallet_address": wallet_address,
                "risk_factors": crypto_risk_factors,
                "total_risk_score": total_risk
            }
        )
    
    return True, ""

async def check_crypto_rate_limit(request: Request, current_user: Optional[User]) -> tuple[bool, str]:
    """
    Check crypto-specific rate limits.
    """
    client_ip = request.client.host
    
    # Premium users get higher limits
    if current_user and current_user.tier in [UserTier.PREMIUM, UserTier.API]:
        # Check daily premium limit (stored in database)
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
        
        from sqlalchemy.orm import Session
        db = next(get_db())
        daily_usage = db.query(UsageLog).filter(
            UsageLog.user_id == current_user.id,
            UsageLog.action == ActionType.CRYPTO_BALANCE_CHECK,
            UsageLog.created_at >= start_of_day
        ).count()
        
        if daily_usage >= PREMIUM_CRYPTO_CHECKS:
            return False, f"Daily premium limit exceeded: {PREMIUM_CRYPTO_CHECKS} crypto checks per day"
        return True, ""
    
    # Free/anonymous users get IP-based limits
    is_allowed, remaining = ip_rate_limiter.check_ip_limit(
        client_ip, "crypto_check", FREE_CRYPTO_CHECKS_PER_IP, 24
    )
    
    if not is_allowed:
        return False, f"Daily limit exceeded. Free users get {FREE_CRYPTO_CHECKS_PER_IP} crypto checks per 24 hours per IP. Upgrade to Premium for {PREMIUM_CRYPTO_CHECKS} checks per day."
    
    return True, ""

async def get_bitcoin_balance(address: str) -> Dict[str, Any]:
    """
    Get Bitcoin wallet balance using blockchain.info API with security measures.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use blockchain.info API (free tier)
            response = await client.get(
                BLOCKCHAIN_INFO_API.format(address=address),
                headers={
                    'User-Agent': 'BIN-Search-Pro/1.0',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert satoshi to BTC
            balance_btc = data.get('final_balance', 0) / 100000000
            
            return {
                'balance': str(balance_btc),
                'balance_usd': None,  # Would need price API
                'transaction_count': data.get('n_tx', 0),
                'is_valid': True
            }
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {'balance': '0', 'is_valid': False, 'error': 'Invalid Bitcoin address'}
        raise HTTPException(status_code=500, detail="Bitcoin API error")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch Bitcoin balance")

async def get_ethereum_balance(address: str) -> Dict[str, Any]:
    """
    Get Ethereum wallet balance using Etherscan API with security measures.
    """
    try:
        # Add proper address validation
        if not address.startswith('0x') or len(address) != 42:
            return {'balance': '0', 'is_valid': False, 'error': 'Invalid Ethereum address format'}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use Etherscan API (you'll need an API key for production)
            etherscan_key = os.getenv("ETHERSCAN_API_KEY", "YourAPIKeyToken")
            response = await client.get(
                f"{ETHERSCAN_API}&apikey={etherscan_key}".format(address=address),
                headers={
                    'User-Agent': 'BIN-Search-Pro/1.0',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '1':
                # Convert Wei to ETH
                balance_wei = int(data.get('result', '0'))
                balance_eth = balance_wei / (10**18)
                
                return {
                    'balance': str(balance_eth),
                    'balance_usd': None,  # Would need price API
                    'transaction_count': None,  # Would need separate API call
                    'is_valid': True
                }
            else:
                return {'balance': '0', 'is_valid': False, 'error': data.get('message', 'API error')}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch Ethereum balance")

async def get_litecoin_balance(address: str) -> Dict[str, Any]:
    """Get Litecoin wallet balance using BlockCypher API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                BLOCKCYPHER_API.format(crypto="ltc", address=address),
                headers={'User-Agent': 'BIN-Search-Pro/1.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            balance_ltc = data.get('balance', 0) / 100000000  # Convert from satoshi
            
            return {
                'balance': str(balance_ltc),
                'balance_usd': None,
                'transaction_count': data.get('n_tx', 0),
                'is_valid': True
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {'balance': '0', 'is_valid': False, 'error': 'Invalid Litecoin address'}
        raise HTTPException(status_code=500, detail="Litecoin API error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Litecoin balance")

async def get_dogecoin_balance(address: str) -> Dict[str, Any]:
    """Get Dogecoin wallet balance using BlockCypher API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                BLOCKCYPHER_API.format(crypto="doge", address=address),
                headers={'User-Agent': 'BIN-Search-Pro/1.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            balance_doge = data.get('balance', 0) / 100000000  # Convert from satoshi
            
            return {
                'balance': str(balance_doge),
                'balance_usd': None,
                'transaction_count': data.get('n_tx', 0),
                'is_valid': True
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {'balance': '0', 'is_valid': False, 'error': 'Invalid Dogecoin address'}
        raise HTTPException(status_code=500, detail="Dogecoin API error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Dogecoin balance")

async def get_cardano_balance(address: str) -> Dict[str, Any]:
    """Get Cardano wallet balance using Blockfrost API"""
    try:
        # Note: Requires Blockfrost API key for production
        blockfrost_key = os.getenv("BLOCKFROST_API_KEY", "")
        if not blockfrost_key:
            return {'balance': '0', 'is_valid': False, 'error': 'Cardano API key not configured'}
            
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                BLOCKFROST_API.format(address=address),
                headers={
                    'User-Agent': 'BIN-Search-Pro/1.0',
                    'project_id': blockfrost_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle Cardano address format - get first amount entry
            amounts = data.get('amount', [])
            ada_amount = next((item for item in amounts if item.get('unit') == 'lovelace'), {'quantity': '0'})
            balance_ada = int(ada_amount['quantity']) / 1000000  # Convert from lovelace
            
            return {
                'balance': str(balance_ada),
                'balance_usd': None,
                'transaction_count': data.get('tx_count', 0),
                'is_valid': True
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {'balance': '0', 'is_valid': False, 'error': 'Invalid Cardano address'}
        raise HTTPException(status_code=500, detail="Cardano API error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Cardano balance")

async def get_solana_balance(address: str) -> Dict[str, Any]:
    """Get Solana wallet balance using Solana RPC API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            response = await client.post(
                SOLANA_RPC,
                json=rpc_payload,
                headers={'User-Agent': 'BIN-Search-Pro/1.0', 'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            data = response.json()
            
            if 'result' in data:
                balance_sol = data['result']['value'] / 1000000000  # Convert from lamports
                return {
                    'balance': str(balance_sol),
                    'balance_usd': None,
                    'transaction_count': None,
                    'is_valid': True
                }
            else:
                return {'balance': '0', 'is_valid': False, 'error': 'Invalid Solana address'}
                
    except httpx.HTTPStatusError:
        return {'balance': '0', 'is_valid': False, 'error': 'Invalid Solana address'}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Solana balance")

@router.post("/check-balance", response_model=CryptoBalanceResponse)
@limiter.limit(f"{CRYPTO_API_RATE_LIMIT}/minute")
async def check_crypto_balance(
    request: Request,
    wallet_request: CryptoWalletRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Check cryptocurrency wallet balance with advanced security.
    """
    # CRITICAL SECURITY CHECKS
    security_allowed, security_msg = await advanced_crypto_security_check(request, wallet_request.address)
    if not security_allowed:
        raise HTTPException(status_code=403, detail=security_msg)
    
    # Rate limit check
    rate_allowed, rate_msg = await check_crypto_rate_limit(request, current_user)
    if not rate_allowed:
        raise HTTPException(status_code=429, detail=rate_msg)
    
    try:
        # Get balance based on crypto type
        balance_functions = {
            'bitcoin': get_bitcoin_balance,
            'ethereum': get_ethereum_balance,
            'litecoin': get_litecoin_balance,
            'dogecoin': get_dogecoin_balance,
            'cardano': get_cardano_balance,
            'solana': get_solana_balance
        }
        
        balance_function = balance_functions.get(wallet_request.crypto_type)
        if not balance_function:
            raise HTTPException(status_code=400, detail="Unsupported crypto type")
            
        balance_data = await balance_function(wallet_request.address)
        
        # Log usage with security metadata
        def log_crypto_usage():
            from sqlalchemy.orm import Session
            db = next(get_db())
            
            if current_user:
                usage_log = UsageLog(
                    user_id=current_user.id,
                    action=ActionType.CRYPTO_BALANCE_CHECK,
                    ip_address=request.client.host,
                    user_agent=request.headers.get('user-agent'),
                    metadata=json.dumps({
                        'crypto_type': wallet_request.crypto_type,
                        'address': wallet_request.address[:10] + "...",  # Partially anonymize
                        'balance_found': balance_data.get('balance') != '0',
                        'is_valid': balance_data.get('is_valid', True)
                    })
                )
                db.add(usage_log)
                db.commit()
            
            # Always log IP usage for rate limiting
            ip_rate_limiter.increment_ip_usage(request.client.host, "crypto_check", 24)
        
        background_tasks.add_task(log_crypto_usage)
        
        return CryptoBalanceResponse(
            address=wallet_request.address,
            crypto_type=wallet_request.crypto_type,
            balance=balance_data.get('balance', '0'),
            balance_usd=balance_data.get('balance_usd'),
            last_updated=datetime.now(timezone.utc),
            transaction_count=balance_data.get('transaction_count'),
            is_valid=balance_data.get('is_valid', True),
            error=balance_data.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Crypto balance check failed")

@router.get("/supported-currencies")
async def get_supported_crypto_currencies():
    """
    Get list of supported cryptocurrencies.
    """
    return {
        "supported_currencies": [
            {
                "name": "Bitcoin",
                "code": "bitcoin",
                "symbol": "BTC",
                "address_format": "Legacy, SegWit, Bech32",
                "example": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
            },
            {
                "name": "Ethereum", 
                "code": "ethereum",
                "symbol": "ETH",
                "address_format": "ERC-20",
                "example": "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
            }
        ],
        "rate_limits": {
            "free_users": f"{FREE_CRYPTO_CHECKS_PER_IP} checks per 24 hours per IP",
            "premium_users": f"{PREMIUM_CRYPTO_CHECKS} checks per day"
        }
    }

@router.get("/usage-stats")
async def get_crypto_usage_stats(
    request: Request,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Get crypto wallet checking usage statistics.
    """
    client_ip = request.client.host
    
    if current_user and current_user.tier in [UserTier.PREMIUM, UserTier.API]:
        # Premium user stats
        from sqlalchemy.orm import Session
        db = next(get_db())
        
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
        
        daily_usage = db.query(UsageLog).filter(
            UsageLog.user_id == current_user.id,
            UsageLog.action == ActionType.CRYPTO_BALANCE_CHECK,
            UsageLog.created_at >= start_of_day
        ).count()
        
        return {
            "user_type": "premium",
            "daily_usage": daily_usage,
            "daily_limit": PREMIUM_CRYPTO_CHECKS,
            "remaining": max(0, PREMIUM_CRYPTO_CHECKS - daily_usage),
            "supported_currencies": ["bitcoin", "ethereum"]
        }
    else:
        # Free/anonymous user stats
        usage_info = ip_rate_limiter.get_ip_usage_info(client_ip, "crypto_check")
        remaining = max(0, FREE_CRYPTO_CHECKS_PER_IP - usage_info.get('count', 0))
        
        return {
            "user_type": "free_or_anonymous",
            "daily_usage": usage_info.get('count', 0),
            "daily_limit": FREE_CRYPTO_CHECKS_PER_IP,
            "remaining": remaining,
            "reset_time": usage_info.get('reset_time'),
            "supported_currencies": ["bitcoin", "ethereum"]
        }