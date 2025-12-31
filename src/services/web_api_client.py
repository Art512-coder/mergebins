"""
API Client for BIN Search Bot - Web API Integration
Connects Telegram bot with the web platform API
"""

import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BINData:
    """BIN data structure matching API response"""
    bin_number: str
    brand: str
    country: str
    country_code: str
    bank_name: str
    card_type: str
    card_level: str
    
@dataclass
class UserSession:
    """User session data structure"""
    user_id: str
    telegram_id: int
    premium_status: bool
    daily_generations: int
    total_generations: int
    subscription_expires: Optional[str] = None

class WebAPIClient:
    """HTTP client for connecting bot to web API"""
    
    def __init__(self):
        self.base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        self.api_key = os.getenv("BOT_API_KEY", "")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TelegramBot/1.0"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif response.status == 403:
                    raise Exception("Access denied. Bot may need API key configuration.")
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise Exception("Network error. Please try again later.")
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    # BIN Lookup Methods
    async def lookup_bin(self, bin_number: str) -> Optional[BINData]:
        """Look up BIN information"""
        try:
            data = await self._make_request("GET", f"/api/v1/bins/lookup/{bin_number}")
            if data and "bin_data" in data:
                bin_info = data["bin_data"]
                return BINData(
                    bin_number=bin_info.get("bin", ""),
                    brand=bin_info.get("brand", ""),
                    country=bin_info.get("country", ""),
                    country_code=bin_info.get("country_code", ""),
                    bank_name=bin_info.get("bank_name", ""),
                    card_type=bin_info.get("type", ""),
                    card_level=bin_info.get("level", "")
                )
            return None
        except Exception as e:
            logger.error(f"BIN lookup failed: {e}")
            return None
    
    async def search_bins(self, **filters) -> List[BINData]:
        """Search BINs with filters"""
        try:
            params = {k: v for k, v in filters.items() if v}
            data = await self._make_request("GET", "/api/v1/bins/search", params=params)
            
            bins = []
            if data and "bins" in data:
                for bin_info in data["bins"]:
                    bins.append(BINData(
                        bin_number=bin_info.get("bin", ""),
                        brand=bin_info.get("brand", ""),
                        country=bin_info.get("country", ""),
                        country_code=bin_info.get("country_code", ""),
                        bank_name=bin_info.get("bank_name", ""),
                        card_type=bin_info.get("type", ""),
                        card_level=bin_info.get("level", "")
                    ))
            return bins
        except Exception as e:
            logger.error(f"BIN search failed: {e}")
            return []
    
    async def get_bin_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            return await self._make_request("GET", "/api/v1/bins/stats")
        except Exception as e:
            logger.error(f"Stats request failed: {e}")
            return {}
    
    # Card Generation Methods
    async def generate_cards(self, bin_number: str = "", count: int = 1, include_avs: bool = False, 
                           country_code: str = "US") -> Dict[str, Any]:
        """Generate credit cards"""
        try:
            payload = {
                "bin": bin_number,
                "count": count,
                "include_avs": include_avs,
                "country_code": country_code if include_avs else None
            }
            return await self._make_request("POST", "/api/v1/cards/generate", json=payload)
        except Exception as e:
            logger.error(f"Card generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # User Management Methods
    async def get_or_create_user(self, telegram_id: int, username: str = "", 
                                first_name: str = "") -> Optional[UserSession]:
        """Get or create user session"""
        try:
            payload = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name
            }
            data = await self._make_request("POST", "/api/v1/users/telegram-auth", json=payload)
            
            if data and "user" in data:
                user_data = data["user"]
                return UserSession(
                    user_id=user_data.get("id", ""),
                    telegram_id=telegram_id,
                    premium_status=user_data.get("is_premium", False),
                    daily_generations=user_data.get("daily_generations", 0),
                    total_generations=user_data.get("total_generations", 0),
                    subscription_expires=user_data.get("subscription_expires")
                )
            return None
        except Exception as e:
            logger.error(f"User auth failed: {e}")
            return None
    
    async def update_user_usage(self, telegram_id: int, generation_count: int = 0) -> bool:
        """Update user usage statistics"""
        try:
            payload = {
                "telegram_id": telegram_id,
                "generations_used": generation_count
            }
            await self._make_request("POST", "/api/v1/users/update-usage", json=payload)
            return True
        except Exception as e:
            logger.error(f"Usage update failed: {e}")
            return False
    
    # Crypto Balance Methods
    async def check_wallet_balance(self, chain: str, address: str) -> Dict[str, Any]:
        """Check cryptocurrency wallet balance"""
        try:
            params = {"chain": chain, "address": address}
            return await self._make_request("GET", "/api/v1/crypto/balance", params=params)
        except Exception as e:
            logger.error(f"Crypto balance check failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Payment Methods
    async def create_premium_subscription(self, telegram_id: int) -> Dict[str, Any]:
        """Create premium subscription payment"""
        try:
            payload = {
                "telegram_id": telegram_id,
                "plan": "premium_monthly",
                "amount": 9.99
            }
            return await self._make_request("POST", "/api/v1/payments/create-crypto-payment", json=payload)
        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check payment status"""
        try:
            return await self._make_request("GET", f"/api/v1/payments/status/{payment_id}")
        except Exception as e:
            logger.error(f"Payment status check failed: {e}")
            return {"success": False, "error": str(e)}

# Global API client instance
api_client = WebAPIClient()

# Cleanup function for graceful shutdown
async def cleanup_api_client():
    """Cleanup function to close HTTP sessions"""
    await api_client.close()