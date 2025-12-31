from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import enum

Base = declarative_base()

class UserTier(enum.Enum):
    FREE = "free"
    PREMIUM = "premium" 
    API = "api"

class ActionType(enum.Enum):
    BIN_LOOKUP = "bin_lookup"
    CARD_GENERATION = "card_generation" 
    BULK_EXPORT = "bulk_export"
    CRYPTO_BALANCE_CHECK = "crypto_balance_check"
    WEBHOOK_PAYMENT = "webhook_payment"
    SECURITY_EVENT = "security_event"

class SubscriptionStatus(enum.Enum):
    UNPAID = "unpaid"
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"

# Updated User model to match existing database schema
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Changed from hashed_password
    telegram_id = Column(BigInteger, nullable=True)  # Added telegram_id
    tier = Column(String(7), nullable=False)  # Changed from Enum to String
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)  # Made nullable
    
    # Relationships
    usage_logs = relationship("UsageLog", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")

# Updated UsageLog model to match existing schema
class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Made not nullable
    action = Column(String(15), nullable=False)  # Changed from Enum to String
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)  # Changed from String
    request_data = Column(Text, nullable=True)  # Added request_data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")

# Subscription model (new)
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_payment_id = Column(String(255), nullable=True)
    paypal_subscription_id = Column(String(255), nullable=True)
    status = Column(String(8), nullable=False)
    plan_type = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=True)
    payment_method = Column(String(50), nullable=True)
    crypto_currency = Column(String(10), nullable=True)
    crypto_amount = Column(String(50), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")

# ApiKey model (new)
class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

# BIN Data Model (for your 458K records)
class BinData(Base):
    __tablename__ = "bin_data"
    
    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(6), unique=True, index=True, nullable=False)
    brand = Column(String(50), nullable=True)
    issuer = Column(String(255), nullable=True)
    type = Column(String(50), nullable=True)  # Changed from String(20)
    level = Column(String(50), nullable=True)
    country_code = Column(String(2), nullable=True)
    country_name = Column(String(100), nullable=True)
    bank_phone = Column(String(50), nullable=True)
    bank_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Blocked BINs Model
class BlockedBin(Base):
    __tablename__ = "blocked_bins"
    
    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(6), unique=True, index=True, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)