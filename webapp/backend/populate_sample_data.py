"""
Populate database with sample BIN data for testing
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import BinData
from app.database import DATABASE_URL

# Sample BIN data for testing
SAMPLE_BINS = [
    {
        "bin": "411111",
        "brand": "visa", 
        "issuer": "Chase Bank",
        "type": "debit",
        "level": "standard",
        "country_code": "US",
        "country_name": "United States",
        "bank_phone": "+1-800-432-3117",
        "bank_url": "https://www.chase.com"
    },
    {
        "bin": "424242",
        "brand": "visa",
        "issuer": "Stripe Test Bank",
        "type": "credit", 
        "level": "classic",
        "country_code": "US",
        "country_name": "United States",
        "bank_phone": "+1-555-0123",
        "bank_url": "https://stripe.com"
    },
    {
        "bin": "400000",
        "brand": "visa",
        "issuer": "Wells Fargo Bank",
        "type": "credit",
        "level": "standard",
        "country_code": "US", 
        "country_name": "United States",
        "bank_phone": "+1-800-869-3557",
        "bank_url": "https://www.wellsfargo.com"
    },
    {
        "bin": "378282",
        "brand": "american express",
        "issuer": "American Express Company",
        "type": "credit",
        "level": "premium",
        "country_code": "US",
        "country_name": "United States",
        "bank_phone": "+1-800-528-4800", 
        "bank_url": "https://www.americanexpress.com"
    },
    {
        "bin": "555555",
        "brand": "mastercard",
        "issuer": "Mastercard Test Bank",
        "type": "credit",
        "level": "standard",
        "country_code": "US",
        "country_name": "United States", 
        "bank_phone": "+1-800-627-8372",
        "bank_url": "https://www.mastercard.us"
    },
    {
        "bin": "601100",
        "brand": "discover", 
        "issuer": "Discover Bank",
        "type": "credit",
        "level": "standard",
        "country_code": "US",
        "country_name": "United States",
        "bank_phone": "+1-800-347-2683",
        "bank_url": "https://www.discover.com"
    }
]

def populate_sample_bins():
    """Add sample BIN data to database"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_count = db.query(BinData).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} BIN records. Skipping population.")
            return
            
        # Add sample data
        for bin_info in SAMPLE_BINS:
            bin_record = BinData(**bin_info)
            db.add(bin_record)
        
        db.commit()
        print(f"✅ Successfully added {len(SAMPLE_BINS)} sample BIN records!")
        
        # Verify the data
        total_count = db.query(BinData).count()
        print(f"📊 Total BIN records in database: {total_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_sample_bins()