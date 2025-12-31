"""
Secure API Authentication for Bot-Web Platform Integration
Handles JWT tokens, API keys, and user session synchronization
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
import logging

logger = logging.getLogger(__name__)

class APIAuthenticator:
    """Handles secure authentication between bot and web platform"""
    
    def __init__(self):
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "https://bin-search-api.arturovillanueva1994.workers.dev")
        self.bot_api_key = os.getenv("BOT_API_KEY", "production-bot-key-2024")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-jwt-secret-here")
        self.session_cache = {}
        
    def generate_bot_token(self) -> str:
        """Generate secure bot authentication token"""
        payload = {
            "iss": "binsearch-telegram-bot",
            "sub": "bot-service",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "scope": ["bot", "user-management", "premium-sync"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def create_api_headers(self) -> Dict[str, str]:
        """Create authenticated API request headers"""
        token = self.generate_bot_token()
        return {
            "Authorization": f"Bearer {token}",
            "X-Bot-API-Key": self.bot_api_key,
            "X-Client-Type": "telegram-bot",
            "Content-Type": "application/json",
            "User-Agent": "BINSearchBot/2.0"
        }
    
    async def authenticate_user(self, telegram_id: int, username: str = "", 
                               first_name: str = "") -> Optional[Dict[str, Any]]:
        """Authenticate Telegram user with web platform"""
        try:
            headers = self.create_api_headers()
            payload = {
                "telegram_id": telegram_id,
                "username": username or "",
                "first_name": first_name or "",
                "auth_type": "telegram",
                "platform": "telegram-bot"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/auth/telegram-login",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        user_data = await response.json()
                        # Cache user session
                        self.session_cache[telegram_id] = {
                            "user_data": user_data,
                            "cached_at": datetime.utcnow(),
                            "expires_at": datetime.utcnow() + timedelta(hours=1)
                        }
                        logger.info(f"User {telegram_id} authenticated successfully")
                        return user_data
                    elif response.status == 401:
                        logger.warning("Bot authentication failed - check API key")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"User authentication failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def sync_premium_status(self, telegram_id: int) -> Optional[bool]:
        """Sync premium status from web platform"""
        try:
            # Check cache first
            cached = self.session_cache.get(telegram_id)
            if cached and cached["expires_at"] > datetime.utcnow():
                return cached["user_data"].get("is_premium", False)
            
            headers = self.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/users/telegram/{telegram_id}/premium-status",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        is_premium = data.get("is_premium", False)
                        
                        # Update cache
                        if telegram_id in self.session_cache:
                            self.session_cache[telegram_id]["user_data"]["is_premium"] = is_premium
                        
                        return is_premium
                    else:
                        logger.warning(f"Premium status check failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Premium status sync error: {e}")
            return None
    
    async def update_user_activity(self, telegram_id: int, activity_type: str, 
                                 metadata: Dict[str, Any] = None) -> bool:
        """Update user activity on web platform"""
        try:
            headers = self.create_api_headers()
            payload = {
                "telegram_id": telegram_id,
                "activity_type": activity_type,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "telegram-bot",
                "metadata": metadata or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/users/activity",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Activity update error: {e}")
            return False
    
    async def get_user_limits(self, telegram_id: int) -> Dict[str, Any]:
        """Get user rate limits and usage from web platform"""
        try:
            headers = self.create_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/users/telegram/{telegram_id}/limits",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "daily_limit": 5,
                            "used_today": 0,
                            "is_premium": False,
                            "reset_time": None
                        }
                        
        except Exception as e:
            logger.error(f"Limits check error: {e}")
            return {
                "daily_limit": 5,
                "used_today": 0,
                "is_premium": False,
                "reset_time": None
            }
    
    async def record_generation(self, telegram_id: int, cards_generated: int) -> bool:
        """Record card generation activity"""
        try:
            headers = self.create_api_headers()
            payload = {
                "telegram_id": telegram_id,
                "cards_generated": cards_generated,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "telegram-bot"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/users/generation",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Generation recording error: {e}")
            return False
    
    def clear_cache(self, telegram_id: int = None):
        """Clear user session cache"""
        if telegram_id:
            self.session_cache.pop(telegram_id, None)
        else:
            self.session_cache.clear()
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, value in self.session_cache.items()
            if value["expires_at"] <= now
        ]
        for key in expired_keys:
            del self.session_cache[key]

# Global authenticator instance
auth = APIAuthenticator()

# Utility functions for bot handlers
async def get_user_session(telegram_id: int, username: str = "", first_name: str = "") -> Dict[str, Any]:
    """Get or create user session with authentication"""
    user_data = await auth.authenticate_user(telegram_id, username, first_name)
    if user_data:
        return {
            "id": user_data.get("id"),
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "is_premium": user_data.get("is_premium", False),
            "daily_generations": user_data.get("daily_generations", 0),
            "total_generations": user_data.get("total_generations", 0),
            "subscription_expires": user_data.get("subscription_expires"),
            "authenticated": True
        }
    else:
        # Return basic session if authentication fails
        return {
            "id": None,
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "is_premium": False,
            "daily_generations": 0,
            "total_generations": 0,
            "subscription_expires": None,
            "authenticated": False
        }

async def check_user_limits(telegram_id: int) -> Dict[str, Any]:
    """Check user generation limits"""
    return await auth.get_user_limits(telegram_id)

async def record_user_activity(telegram_id: int, activity: str, metadata: Dict[str, Any] = None):
    """Record user activity"""
    return await auth.update_user_activity(telegram_id, activity, metadata)

async def update_generation_count(telegram_id: int, count: int):
    """Update user generation count"""
    return await auth.record_generation(telegram_id, count)