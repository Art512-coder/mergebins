"""
Initialize database and create tables
"""
from sqlalchemy import create_engine
from app.models import Base
from app.database import DATABASE_URL
import os

def init_database():
    """Create all database tables"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_database()