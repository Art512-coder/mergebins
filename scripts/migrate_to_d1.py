import csv
import subprocess
import json
import os
import sys
from typing import List, Dict
import tempfile

def sanitize_sql_value(value: str) -> str:
    """Sanitize SQL values to prevent injection and handle special characters"""
    if not value:
        return 'NULL'
    # Escape single quotes by doubling them
    value = value.replace("'", "''")
    return f"'{value}'"

def create_batch_sql(batch: List[Dict], table_name: str = 'bins') -> str:
    """Create SQL INSERT statement for a batch of records"""
    if not batch:
        return ""
    
    columns = ['bin', 'brand', 'type', 'category', 'issuer', 'country', 'bank_phone', 'bank_url']
    
    values_list = []
    for record in batch:
        values = []
        for col in columns:
            val = record.get(col, '').strip()
            values.append(sanitize_sql_value(val) if val else 'NULL')
        values_list.append(f"({', '.join(values)})")
    
    columns_str = ', '.join(columns)
    values_str = ',\n    '.join(values_list)
    
    return f"""INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES
    {values_str};"""

def upload_batch_to_d1(sql_content: str, database_name: str):
    """Upload a batch of data to D1 using wrangler"""
    try:
        # Create temporary SQL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(sql_content)
            temp_file_path = temp_file.name
        
        # Execute wrangler command
        cmd = ['wrangler', 'd1', 'execute', database_name, '--file', temp_file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if result.returncode != 0:
            print(f"Error executing batch: {result.stderr}")
            return False
        else:
            print(f"✅ Batch uploaded successfully")
            return True
            
    except Exception as e:
        print(f"Error uploading batch: {e}")
        return False

def migrate_csv_to_d1(csv_file_path: str, database_name: str, batch_size: int = 1000):
    """Migrate CSV data to D1 database in batches"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print(f"🚀 Starting migration from {csv_file_path} to D1 database {database_name}")
    print(f"📦 Batch size: {batch_size}")
    
    total_processed = 0
    batch_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            batch = []
            
            for row_num, row in enumerate(reader, 1):
                # Clean and validate data
                bin_data = {
                    'bin': row.get('bin', '').strip(),
                    'brand': row.get('brand', '').strip(),
                    'type': row.get('type', '').strip(),
                    'category': row.get('category', '').strip(),
                    'issuer': row.get('issuer', '').strip(),
                    'country': row.get('country', '').strip(),
                    'bank_phone': row.get('bank_phone', '').strip(),
                    'bank_url': row.get('bank_url', '').strip()
                }
                
                # Skip rows with empty BIN
                if not bin_data['bin']:
                    continue
                
                batch.append(bin_data)
                
                # Process batch when it reaches batch_size
                if len(batch) >= batch_size:
                    batch_count += 1
                    print(f"\n📤 Uploading batch {batch_count} (records {total_processed + 1}-{total_processed + len(batch)})")
                    
                    sql_content = create_batch_sql(batch)
                    if upload_batch_to_d1(sql_content, database_name):
                        total_processed += len(batch)
                        print(f"✅ Total processed: {total_processed}")
                    else:
                        print(f"❌ Failed to upload batch {batch_count}")
                        return False
                    
                    batch = []
                
                # Progress indicator
                if row_num % 10000 == 0:
                    print(f"📊 Processed {row_num} rows from CSV...")
            
            # Upload remaining records
            if batch:
                batch_count += 1
                print(f"\n📤 Uploading final batch {batch_count} (records {total_processed + 1}-{total_processed + len(batch)})")
                
                sql_content = create_batch_sql(batch)
                if upload_batch_to_d1(sql_content, database_name):
                    total_processed += len(batch)
                else:
                    print(f"❌ Failed to upload final batch")
                    return False
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Total records migrated: {total_processed}")
        print(f"📦 Total batches processed: {batch_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_d1_connection(database_name: str):
    """Test D1 database connection and show sample data"""
    try:
        print(f"🔍 Testing D1 database connection for {database_name}...")
        
        # Test query
        test_sql = "SELECT COUNT(*) as total_records FROM bins LIMIT 1;"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_sql)
            temp_file_path = temp_file.name
        
        cmd = ['wrangler', 'd1', 'execute', database_name, '--file', temp_file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            print(f"✅ Database connection successful")
            print(f"📊 Query result: {result.stdout}")
        else:
            print(f"❌ Database connection failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    # Configuration
    CSV_FILE = "merged_bin_data.csv"
    DATABASE_NAME = "bin-search-db"
    BATCH_SIZE = 500  # Smaller batches to avoid timeout
    
    print("🏦 D1 BIN Database Migration Tool")
    print("=" * 40)
    
    # Test connection first
    test_d1_connection(DATABASE_NAME)
    
    # Confirm migration
    response = input(f"\n🤔 Ready to migrate {CSV_FILE} to {DATABASE_NAME}? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled by user")
        sys.exit(0)
    
    # Start migration
    success = migrate_csv_to_d1(CSV_FILE, DATABASE_NAME, BATCH_SIZE)
    
    if success:
        print(f"\n🎉 Migration completed! Test your database:")
        print(f"wrangler d1 execute {DATABASE_NAME} --command=\"SELECT COUNT(*) FROM bins;\"")
        test_d1_connection(DATABASE_NAME)
    else:
        print(f"\n❌ Migration failed. Check errors above.")
        sys.exit(1)
