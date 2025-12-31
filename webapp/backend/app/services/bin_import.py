from typing import Optional
import pandas as pd
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models import BinData, BlockedBin

async def import_bin_data():
    """
    Import BIN data from CSV file into database.
    This runs on application startup.
    """
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_count = db.query(BinData).count()
        if existing_count > 0:
            print(f"✅ BIN data already imported ({existing_count:,} records)")
            return
        
        # Path to your CSV file
        csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "merged_bin_data.csv")
        
        if not os.path.exists(csv_path):
            print(f"❌ BIN data file not found at: {csv_path}")
            return
        
        print(f"📊 Importing BIN data from: {csv_path}")
        
        # Read CSV with pandas
        df = pd.read_csv(csv_path)
        print(f"📈 Loaded {len(df):,} records from CSV")
        
        # Clean and prepare data
        df = df.dropna(subset=['bin'])  # Remove rows without BIN
        df['bin'] = df['bin'].astype(str).str.strip()
        df = df[df['bin'].str.len() >= 6]  # Only keep valid BINs
        df['bin'] = df['bin'].str[:6]  # Take first 6 digits
        df = df.drop_duplicates(subset=['bin'])  # Remove duplicates
        
        print(f"🧹 Cleaned data: {len(df):,} unique BINs")
        
        # Batch insert for performance
        batch_size = 1000
        imported_count = 0
        
        for _ in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]
            
            bin_records = []
            for _, row in batch_df.iterrows():
                bin_record = BinData(
                    bin=str(row.get('bin', ''))[:6],
                    brand=str(row.get('brand', ''))[:50] if pd.notna(row.get('brand')) else None,
                    issuer=str(row.get('issuer', ''))[:255] if pd.notna(row.get('issuer')) else None,
                    type=str(row.get('type', ''))[:50] if pd.notna(row.get('type')) else None,
                    level=str(row.get('category', ''))[:50] if pd.notna(row.get('category')) else None,
                    country_code=str(row.get('alpha_2', ''))[:2] if pd.notna(row.get('alpha_2')) else None,
                    country_name=str(row.get('country', ''))[:100] if pd.notna(row.get('country')) else None,
                    bank_phone=str(row.get('bank_phone', ''))[:50] if pd.notna(row.get('bank_phone')) else None,
                    bank_url=str(row.get('bank_url', ''))[:255] if pd.notna(row.get('bank_url')) else None
                )
                bin_records.append(bin_record)
            
            # Bulk insert
            db.bulk_save_objects(bin_records)
            db.commit()
            
            imported_count += len(bin_records)
            if imported_count % 10000 == 0:
                print(f"📥 Imported {imported_count:,} BINs...")
        
        print(f"✅ Successfully imported {imported_count:,} BIN records")
        
        # Create indexes for performance
        print("🔧 Creating database indexes...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_bin_data_bin ON bin_data(bin)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_bin_data_brand ON bin_data(brand)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_bin_data_country ON bin_data(country_code)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_bin_data_issuer ON bin_data(issuer)"))
        db.commit()
        
        # Insert blocked test BINs
        test_bins = [
            ("411111", "Test BIN - Visa"),
            ("555555", "Test BIN - Mastercard"),
            ("378282", "Test BIN - American Express"),
            ("378734", "Test BIN - American Express"),
            ("371449", "Test BIN - American Express"),
            ("601111", "Test BIN - Discover"),
            ("630495", "Test BIN - Discover"),
            ("630490", "Test BIN - Discover"),
            ("360000", "Test BIN - Diners Club"),
            ("305693", "Test BIN - Diners Club"),
            ("385200", "Test BIN - Diners Club"),
            ("601100", "Test BIN - Diners Club"),
            ("353011", "Test BIN - Diners Club"),
            ("356600", "Test BIN - Diners Club")
        ]
        
        blocked_records = [
            BlockedBin(bin=bin_num, reason=reason) 
            for bin_num, reason in test_bins
        ]
        
        db.bulk_save_objects(blocked_records)
        db.commit()
        
        print(f"🚫 Added {len(blocked_records)} blocked test BINs")
        print("🎉 BIN data import completed successfully!")
        
    except Exception as e:
        print(f"❌ Error importing BIN data: {str(e)}")
        db.rollback()
    finally:
        db.close()

def search_bins(
    db: Session, 
    brand: Optional[str] = None, 
    country: Optional[str] = None, 
    issuer: Optional[str] = None, 
    bin_type: Optional[str] = None,
    limit: int = 50
):
    """
    Search BIN database with filters.
    """
    query = db.query(BinData)
    
    if brand:
        query = query.filter(BinData.brand.ilike(f"%{brand}%"))
    if country:
        query = query.filter(BinData.country_name.ilike(f"%{country}%"))
    if issuer:
        query = query.filter(BinData.issuer.ilike(f"%{issuer}%"))
    if bin_type:
        query = query.filter(BinData.type.ilike(f"%{bin_type}%"))
    
    return query.limit(limit).all()

def get_bin_stats(db: Session):
    """
    Get database statistics.
    """
    total_bins = db.query(BinData).count()
    brands = db.query(BinData.brand).distinct().count()
    countries = db.query(BinData.country_name).distinct().count()
    issuers = db.query(BinData.issuer).distinct().count()
    
    return {
        "total_bins": total_bins,
        "brands": brands,
        "countries": countries,
        "issuers": issuers
    }
