"""
Database initialization script for BIN Search Pro
Creates all necessary tables and sets up the database schema.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
parent_dir = Path(__file__).parent
sys.path.append(str(parent_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, BinData, UserTier
from app.database import get_database_url
from app.utils.security import get_password_hash
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create all database tables."""
    database_url = get_database_url()
    logger.info(f"Creating database at: {database_url}")
    
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")
    
    return engine

def create_admin_user(engine):
    """Create an admin user for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_email = "admin@binsearchpro.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                password_hash=get_password_hash("AdminPass123!"),  # Change this in production
                tier=UserTier.API.value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(admin_user)
            db.commit()
            logger.info(f"✅ Admin user created: {admin_email}")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def import_bin_data(engine):
    """Import BIN data from CSV file."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if BIN data already exists
        existing_count = db.query(BinData).count()
        if existing_count > 0:
            logger.info(f"BIN data already exists ({existing_count} records)")
            return
        
        # Look for BIN data file in various locations
        possible_paths = [
            "../../data/merged_bin_data.csv",
            "../data/merged_bin_data.csv",
            "../../merged_bin_data.csv",
            "../merged_bin_data.csv",
            "merged_bin_data.csv"
        ]
        
        bin_file_path = None
        for path in possible_paths:
            full_path = Path(parent_dir) / path
            if full_path.exists():
                bin_file_path = full_path
                break
        
        if not bin_file_path:
            logger.warning("⚠️ BIN data file not found. Creating sample data...")
            create_sample_bin_data(db)
            return
        
        logger.info(f"Loading BIN data from: {bin_file_path}")
        
        # Read CSV in chunks for better performance
        chunk_size = 10000
        total_imported = 0
        
        for chunk in pd.read_csv(bin_file_path, chunksize=chunk_size):
            bin_records = []
            
            for _, row in chunk.iterrows():
                bin_record = BinData(
                    bin=str(row.get('bin', '')).zfill(6)[:6],
                    brand=row.get('brand', ''),
                    issuer=row.get('issuer', ''),
                    type=row.get('type', ''),
                    level=row.get('level', ''),
                    country_code=row.get('country_code', ''),
                    country_name=row.get('country', ''),
                    bank_phone=row.get('phone', ''),
                    bank_url=row.get('url', ''),
                    created_at=datetime.utcnow()
                )
                bin_records.append(bin_record)
            
            # Bulk insert for better performance
            db.bulk_save_objects(bin_records)
            db.commit()
            total_imported += len(bin_records)
            
            if total_imported % 50000 == 0:
                logger.info(f"Imported {total_imported} BIN records...")
        
        logger.info(f"✅ Successfully imported {total_imported} BIN records")
        
    except Exception as e:
        logger.error(f"Error importing BIN data: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_bin_data(db):
    """Create sample BIN data for testing."""
    sample_bins = [
        {"bin": "413567", "brand": "VISA", "issuer": "Chase Bank", "type": "CREDIT", "country": "United States"},
        {"bin": "424242", "brand": "VISA", "issuer": "Test Bank", "type": "CREDIT", "country": "United States"},
        {"bin": "555555", "brand": "MASTERCARD", "issuer": "Test Bank", "type": "CREDIT", "country": "United States"},
        {"bin": "378282", "brand": "AMERICAN EXPRESS", "issuer": "American Express", "type": "CREDIT", "country": "United States"},
        {"bin": "371449", "brand": "AMERICAN EXPRESS", "issuer": "American Express", "type": "CREDIT", "country": "United States"},
    ]
    
    for bin_info in sample_bins:
        bin_record = BinData(
            bin=bin_info["bin"],
            brand=bin_info["brand"],
            issuer=bin_info["issuer"],
            type=bin_info["type"],
            country_name=bin_info["country"],
            created_at=datetime.utcnow()
        )
        db.add(bin_record)
    
    db.commit()
    logger.info(f"✅ Created {len(sample_bins)} sample BIN records")

def main():
    """Main database initialization function."""
    logger.info("🚀 Starting database initialization...")
    
    try:
        # Create database tables
        engine = create_database_tables()
        
        # Create admin user
        create_admin_user(engine)
        
        # Import BIN data
        import_bin_data(engine)
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("\n📊 Database Summary:")
        
        # Get statistics
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        user_count = db.query(User).count()
        bin_count = db.query(BinData).count()
        
        logger.info(f"   Users: {user_count}")
        logger.info(f"   BIN Records: {bin_count}")
        
        db.close()
        
        logger.info("\n🔐 Admin Login:")
        logger.info("   Email: admin@binsearchpro.com")
        logger.info("   Password: AdminPass123!")
        logger.info("   ⚠️  Change the admin password in production!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)