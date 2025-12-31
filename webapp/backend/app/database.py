from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
def get_database_url():
    """Get database URL from environment variables."""
    return os.getenv("DATABASE_URL", "sqlite:///./bin_search_dev.db")

DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=300,
    # SQLite specific options
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup - with fallback for local development
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
except (redis.ConnectionError, redis.TimeoutError):
    print("⚠️ Warning: Redis not available. Running without cache.")
    redis_client = None

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis dependency  
def get_redis():
    return redis_client
