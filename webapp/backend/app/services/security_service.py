"""
Advanced Security & Fraud Detection Service
Protects against malicious users, bots, and abuse in the BIN/card generation niche
"""

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import geoip2.database
import geoip2.errors
import re
import asyncio
from collections import defaultdict, deque
import os

from app.database import get_redis
from app.models import User, UsageLog, SecurityEvent, ActionType

class SecurityService:
    """Advanced security and fraud detection for BIN/card services"""
    
    def __init__(self):
        self.redis = get_redis()
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.blocked_countries = set(os.getenv("BLOCKED_COUNTRIES", "").split(","))
        self.vpn_detection_enabled = bool(os.getenv("VPN_DETECTION_ENABLED", "true").lower() == "true")
        
    def _load_suspicious_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate malicious behavior"""
        return {
            "user_agents": [
                r"bot", r"crawler", r"spider", r"scraper", r"automated",
                r"python-requests", r"curl", r"wget", r"postman"
            ],
            "suspicious_bins": [
                # Commonly abused test BINs
                "411111", "424242", "555555", "444444", "400000",
                "371449", "378282", "378734", "341111", "5555555555554444"
            ],
            "suspicious_ips": [
                # Common VPN/proxy patterns
                r"^10\.", r"^192\.168\.", r"^172\.(1[6-9]|2[0-9]|3[01])\.",
                r"^127\.", r"^169\.254\."
            ]
        }
    
    async def analyze_request_risk(self, request: Request, user: Optional[User] = None) -> Dict[str, any]:
        """Comprehensive risk analysis of incoming request"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        risk_score = 0
        risk_factors = []
        
        # 1. IP-based analysis
        ip_risk = await self._analyze_ip_risk(client_ip)
        risk_score += ip_risk["score"]
        risk_factors.extend(ip_risk["factors"])
        
        # 2. User agent analysis
        ua_risk = self._analyze_user_agent(user_agent)
        risk_score += ua_risk["score"] 
        risk_factors.extend(ua_risk["factors"])
        
        # 3. Rate limiting analysis
        rate_risk = await self._analyze_rate_patterns(client_ip, user)
        risk_score += rate_risk["score"]
        risk_factors.extend(rate_risk["factors"])
        
        # 4. Behavioral analysis (if user exists)
        if user:
            behavior_risk = await self._analyze_user_behavior(user)
            risk_score += behavior_risk["score"] 
            risk_factors.extend(behavior_risk["factors"])
        
        # 5. Geographic analysis
        geo_risk = await self._analyze_geographic_risk(client_ip)
        risk_score += geo_risk["score"]
        risk_factors.extend(geo_risk["factors"])
        
        return {
            "risk_score": min(risk_score, 100),  # Cap at 100
            "risk_level": self._calculate_risk_level(risk_score),
            "risk_factors": risk_factors,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "should_block": risk_score >= 80,
            "should_challenge": risk_score >= 50,
            "requires_verification": risk_score >= 30
        }
    
    async def _analyze_ip_risk(self, ip: str) -> Dict[str, any]:
        """Analyze IP-based risk factors"""
        risk_score = 0
        factors = []
        
        # Check if IP is in our blocklist
        if await self._is_blocked_ip(ip):
            risk_score += 100
            factors.append("IP_BLOCKED")
            return {"score": risk_score, "factors": factors}
        
        # Check for suspicious IP patterns
        for pattern in self.suspicious_patterns["suspicious_ips"]:
            if re.match(pattern, ip):
                risk_score += 30
                factors.append(f"SUSPICIOUS_IP_PATTERN_{pattern}")
        
        # Check for high request rate from this IP
        request_rate = await self._get_ip_request_rate(ip)
        if request_rate > 100:  # More than 100 requests per hour
            risk_score += 40
            factors.append("HIGH_REQUEST_RATE")
        elif request_rate > 50:
            risk_score += 20
            factors.append("ELEVATED_REQUEST_RATE")
        
        # Check for VPN/Proxy (if detection enabled)
        if self.vpn_detection_enabled:
            if await self._is_vpn_or_proxy(ip):
                risk_score += 25
                factors.append("VPN_OR_PROXY")
        
        return {"score": risk_score, "factors": factors}
    
    async def _analyze_user_agent(self, user_agent: str) -> Dict[str, any]:
        """Analyze user agent for bot/automation signs"""
        risk_score = 0
        factors = []
        
        if not user_agent:
            risk_score += 30
            factors.append("MISSING_USER_AGENT")
            return {"score": risk_score, "factors": factors}
        
        user_agent_lower = user_agent.lower()
        
        # Check for suspicious user agent patterns
        for pattern in self.suspicious_patterns["user_agents"]:
            if re.search(pattern, user_agent_lower):
                risk_score += 40
                factors.append(f"SUSPICIOUS_USER_AGENT_{pattern.upper()}")
        
        # Check for minimal user agents (common in automation)
        if len(user_agent) < 20:
            risk_score += 15
            factors.append("MINIMAL_USER_AGENT")
        
        # Check for outdated browsers (often used by bots)
        if any(old in user_agent_lower for old in ["msie 6", "msie 7", "msie 8"]):
            risk_score += 25
            factors.append("OUTDATED_BROWSER")
        
        return {"score": risk_score, "factors": factors}
    
    async def _analyze_rate_patterns(self, ip: str, user: Optional[User]) -> Dict[str, any]:
        """Analyze request rate patterns for abuse"""
        risk_score = 0
        factors = []
        
        # Check IP-based rate patterns
        ip_key = f"security:ip_requests:{ip}"
        ip_requests = await self.redis.get(ip_key) or 0
        ip_requests = int(ip_requests)
        
        if ip_requests > 200:  # More than 200 requests per hour
            risk_score += 50
            factors.append("EXTREME_IP_RATE")
        elif ip_requests > 100:
            risk_score += 30
            factors.append("HIGH_IP_RATE")
        
        # Check user-based patterns (if user exists)
        if user:
            user_key = f"security:user_requests:{user.id}"
            user_requests = await self.redis.get(user_key) or 0
            user_requests = int(user_requests)
            
            if user_requests > 500:  # Premium users might have higher limits
                risk_score += 25
                factors.append("HIGH_USER_RATE")
        
        return {"score": risk_score, "factors": factors}
    
    async def _analyze_user_behavior(self, user: User) -> Dict[str, any]:
        """Analyze user behavioral patterns"""
        risk_score = 0
        factors = []
        
        # New account risk (accounts < 1 day old are higher risk)
        account_age = datetime.now(timezone.utc) - user.created_at
        if account_age < timedelta(hours=1):
            risk_score += 30
            factors.append("VERY_NEW_ACCOUNT")
        elif account_age < timedelta(days=1):
            risk_score += 15
            factors.append("NEW_ACCOUNT")
        
        # Check for suspicious email patterns
        email_lower = user.email.lower()
        if any(domain in email_lower for domain in ["10minutemail", "tempmail", "guerrillamail", "mailinator"]):
            risk_score += 40
            factors.append("TEMPORARY_EMAIL")
        
        # Pattern: Many failed login attempts
        failed_logins = await self._get_failed_login_count(user.id)
        if failed_logins > 10:
            risk_score += 30
            factors.append("EXCESSIVE_FAILED_LOGINS")
        elif failed_logins > 5:
            risk_score += 15
            factors.append("MULTIPLE_FAILED_LOGINS")
        
        return {"score": risk_score, "factors": factors}
    
    async def _analyze_geographic_risk(self, ip: str) -> Dict[str, any]:
        """Analyze geographic risk factors"""
        risk_score = 0
        factors = []
        
        try:
            # You'd need to implement GeoIP lookup here
            country_code = await self._get_country_from_ip(ip)
            
            if country_code in self.blocked_countries:
                risk_score += 60
                factors.append(f"BLOCKED_COUNTRY_{country_code}")
            
            # High-risk countries for financial fraud
            high_risk_countries = {"CN", "RU", "PK", "NG", "GH", "RO"}
            if country_code in high_risk_countries:
                risk_score += 25
                factors.append(f"HIGH_RISK_COUNTRY_{country_code}")
            
        except Exception:
            # If GeoIP lookup fails, add minor risk
            risk_score += 5
            factors.append("GEOLOCATION_UNAVAILABLE")
        
        return {"score": risk_score, "factors": factors}
    
    async def log_security_event(self, event_type: str, risk_analysis: Dict, user_id: Optional[int] = None):
        """Log security events for monitoring and analysis"""
        event_data = {
            "event_type": event_type,
            "risk_score": risk_analysis["risk_score"],
            "risk_level": risk_analysis["risk_level"],
            "risk_factors": risk_analysis["risk_factors"],
            "client_ip": risk_analysis["client_ip"],
            "user_agent": risk_analysis.get("user_agent", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        }
        
        # Store in Redis for real-time analysis
        event_key = f"security:events:{int(time.time())}"
        await self.redis.setex(event_key, 86400, json.dumps(event_data))  # Keep for 24 hours
        
        # Also log high-risk events to database
        if risk_analysis["risk_score"] >= 50:
            # You'd implement database logging here
            pass
    
    async def should_block_request(self, risk_analysis: Dict) -> bool:
        """Determine if request should be blocked"""
        return risk_analysis["should_block"] or risk_analysis["risk_score"] >= 80
    
    async def increment_ip_requests(self, ip: str):
        """Increment request counter for IP"""
        key = f"security:ip_requests:{ip}"
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1 hour expiry
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP (considering proxies)"""
        # Check various headers for real IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _calculate_risk_level(self, score: int) -> str:
        """Convert numeric score to risk level"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    # Helper methods (you'd implement these based on your infrastructure)
    async def _is_blocked_ip(self, ip: str) -> bool:
        """Check if IP is in blocklist"""
        blocked = await self.redis.get(f"security:blocked_ip:{ip}")
        return bool(blocked)
    
    async def _get_ip_request_rate(self, ip: str) -> int:
        """Get request rate for IP"""
        count = await self.redis.get(f"security:ip_requests:{ip}")
        return int(count) if count else 0
    
    async def _is_vpn_or_proxy(self, ip: str) -> bool:
        """Check if IP is VPN/proxy (implement with external service)"""
        # You'd integrate with a VPN detection service here
        return False
    
    async def _get_country_from_ip(self, ip: str) -> str:
        """Get country code from IP (implement with GeoIP)"""
        # You'd implement GeoIP lookup here
        return "XX"
    
    async def _get_failed_login_count(self, user_id: int) -> int:
        """Get failed login attempts for user"""
        count = await self.redis.get(f"security:failed_logins:{user_id}")
        return int(count) if count else 0

# Global instance
security_service = SecurityService()
