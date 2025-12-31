"""
Comprehensive Input Validation Models
Secure Pydantic models for API request validation to prevent injection attacks
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
import re
from datetime import datetime

class BinLookupRequest(BaseModel):
    """Secure BIN lookup request validation."""
    bin: str = Field(..., min_length=6, max_length=8, description="Bank Identification Number (6-8 digits)")
    
    @validator('bin')
    def validate_bin(cls, v):
        """Strict BIN validation to prevent injection attacks."""
        if not isinstance(v, str):
            raise ValueError('BIN must be a string')
        
        # Remove any whitespace
        v = v.strip()
        
        # Validate format: only digits, 6-8 characters
        if not re.match(r'^\d{6,8}$', v):
            raise ValueError('BIN must contain only digits and be 6-8 characters long')
        
        return v

class CardGenerationRequest(BaseModel):
    """Secure card generation request validation."""
    bin: str = Field(..., min_length=6, max_length=8)
    quantity: int = Field(default=1, ge=1, le=10, description="Number of cards to generate (1-10)")
    cvv_length: int = Field(default=3, ge=3, le=4, description="CVV length (3 or 4 digits)")
    
    @validator('bin')
    def validate_bin(cls, v):
        v = v.strip()
        if not re.match(r'^\d{6,8}$', v):
            raise ValueError('BIN must be 6-8 digits only')
        return v
    
    @validator('cvv_length')
    def validate_cvv_length(cls, v):
        if v not in [3, 4]:
            raise ValueError('CVV length must be 3 or 4')
        return v

class CryptoWalletRequest(BaseModel):
    """Secure crypto wallet validation request."""
    address: str = Field(..., min_length=10, max_length=100, description="Cryptocurrency wallet address")
    network: str = Field(..., min_length=2, max_length=20, description="Blockchain network")
    
    @validator('address')
    def validate_address(cls, v):
        """Validate crypto address format."""
        if not isinstance(v, str):
            raise ValueError('Address must be a string')
        
        v = v.strip()
        
        # Basic validation - alphanumeric with some special chars
        if not re.match(r'^[a-zA-Z0-9]{10,100}$', v):
            raise ValueError('Invalid address format')
        
        # Prevent common injection patterns
        dangerous_patterns = ['<', '>', '"', "'", ';', '--', '/*', '*/', 'union', 'select', 'drop', 'delete']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError('Invalid characters in address')
        
        return v
    
    @validator('network')
    def validate_network(cls, v):
        """Validate network name."""
        allowed_networks = ['bitcoin', 'ethereum', 'litecoin', 'dogecoin', 'bsc', 'polygon', 'tron']
        v = v.strip().lower()
        
        if v not in allowed_networks:
            raise ValueError(f'Network must be one of: {", ".join(allowed_networks)}')
        
        return v

class SearchRequest(BaseModel):
    """Secure search request validation."""
    field: str = Field(..., min_length=2, max_length=20, description="Field to search in")
    value: str = Field(..., min_length=1, max_length=100, description="Search value")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum results to return")
    
    @validator('field')
    def validate_field(cls, v):
        """Validate search field."""
        allowed_fields = ['brand', 'country', 'issuer', 'type', 'level', 'bank']
        v = v.strip().lower()
        
        if v not in allowed_fields:
            raise ValueError(f'Field must be one of: {", ".join(allowed_fields)}')
        
        return v
    
    @validator('value')
    def validate_value(cls, v):
        """Validate search value to prevent injection."""
        if not isinstance(v, str):
            raise ValueError('Search value must be a string')
        
        v = v.strip()
        
        # Length check
        if len(v) > 100:
            raise ValueError('Search value too long (max 100 characters)')
        
        # Prevent SQL injection and XSS attempts
        dangerous_patterns = [
            '<script', '</script>', '<iframe', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
            'union select', 'drop table', 'delete from', 'update set', 'insert into',
            '--', '/*', '*/', ';--', "'; ", '"; '
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError('Invalid search value detected')
        
        # Allow only safe characters
        if not re.match(r'^[a-zA-Z0-9\s\-_.,&()]+$', v):
            raise ValueError('Search value contains invalid characters')
        
        return v

class UserRegistrationRequest(BaseModel):
    """Secure user registration validation."""
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=12, max_length=128, description="Strong password")
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="User's name")
    telegram_id: Optional[int] = Field(None, ge=1, le=9999999999, description="Telegram user ID")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Enforce strong password policy."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123', 'admin']
        v_lower = v.lower()
        for pattern in common_patterns:
            if pattern in v_lower:
                raise ValueError('Password contains common patterns and is not secure')
        
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate user name."""
        if v is None:
            return v
        
        v = v.strip()
        
        # Allow only letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        return v

class UserLoginRequest(BaseModel):
    """Secure user login validation."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

class TokenRefreshRequest(BaseModel):
    """Token refresh request validation."""
    refresh_token: str = Field(..., min_length=10, description="Valid refresh token")
    
    @validator('refresh_token')
    def validate_refresh_token(cls, v):
        """Basic refresh token validation."""
        v = v.strip()
        
        # Basic format check - JWT tokens are base64 encoded
        if not re.match(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$', v):
            raise ValueError('Invalid token format')
        
        return v

class PaymentRequest(BaseModel):
    """Secure payment request validation."""
    amount: float = Field(..., gt=0, le=1000, description="Payment amount")
    currency: str = Field(..., min_length=3, max_length=10, description="Payment currency")
    plan: str = Field(..., min_length=3, max_length=20, description="Subscription plan")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate payment currency."""
        allowed_currencies = ['USD', 'EUR', 'BTC', 'ETH', 'LTC', 'DOGE']
        v = v.upper().strip()
        
        if v not in allowed_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(allowed_currencies)}')
        
        return v
    
    @validator('plan')
    def validate_plan(cls, v):
        """Validate subscription plan."""
        allowed_plans = ['premium_monthly', 'premium_yearly', 'enterprise']
        v = v.lower().strip()
        
        if v not in allowed_plans:
            raise ValueError(f'Plan must be one of: {", ".join(allowed_plans)}')
        
        return v

class AdminActionRequest(BaseModel):
    """Secure admin action validation."""
    action: str = Field(..., min_length=3, max_length=20, description="Admin action")
    target_user_id: Optional[int] = Field(None, ge=1, description="Target user ID")
    reason: Optional[str] = Field(None, max_length=500, description="Action reason")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate admin action."""
        allowed_actions = ['ban_user', 'unban_user', 'reset_limits', 'upgrade_user', 'downgrade_user']
        v = v.lower().strip()
        
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        """Validate reason text."""
        if v is None:
            return v
        
        v = v.strip()
        
        # Basic sanitization
        if len(v) > 500:
            raise ValueError('Reason too long (max 500 characters)')
        
        # Prevent injection attempts
        if re.search(r'[<>"\';]', v):
            raise ValueError('Reason contains invalid characters')
        
        return v