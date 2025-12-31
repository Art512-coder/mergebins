from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum  # Add this import

Base = declarative_base()

class UserTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    API = "api"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"

class ActionType(str, enum.Enum):
    BIN_LOOKUP = "bin_lookup"
    CARD_GENERATION = "card_generation"
    BULK_EXPORT = "bulk_export"
    AVS_GENERATION = "avs_generation"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    payment_logs = relationship("PaymentLog", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_payment_id = Column(String(255), unique=True, nullable=True)  # NOWPayments/Coinbase payment ID
    paypal_subscription_id = Column(String(255), unique=True, nullable=True)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    plan_type = Column(String(50), nullable=False)  # premium, api
    amount = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), default="cryptocurrency")  # cryptocurrency, paypal
    crypto_currency = Column(String(10), nullable=True)  # btc, eth, usdt, etc.
    crypto_amount = Column(String(50), nullable=True)  # amount in crypto
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")

class BinData(Base):
    __tablename__ = "bin_data"

    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(6), unique=True, nullable=False, index=True)
    brand = Column(String(50), index=True)
    issuer = Column(String(255), index=True)
    type = Column(String(50), index=True)
    level = Column(String(50))
    country_code = Column(String(2), index=True)
    country_name = Column(String(100), index=True)
    bank_phone = Column(String(50))
    bank_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlockedBin(Base):
    __tablename__ = "blocked_bins"

    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(6), unique=True, nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(ActionType), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_data = Column(Text)  # JSON string for additional data (renamed from metadata)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    event_type = Column(String(50), nullable=False)  # "REQUEST_BLOCKED", "SUSPICIOUS_ACTIVITY", etc.
    risk_level = Column(String(10), nullable=False)  # "LOW", "MEDIUM", "HIGH"
    details = Column(Text)  # JSON string with event details
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    provider = Column(String(50))
    provider_response = Column(Text)
    webhook_data = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
