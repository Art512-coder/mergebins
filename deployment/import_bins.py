import pandas as pd
import subprocess
import os
import json
from pathlib import Path

def batch_import_bins():
    """Import BIN data to Cloudflare D1 in batches"""
    csv_file = Path("../data/merged_bin_data.csv")
    
    print(f"📊 Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"📈 Total records: {len(df)}")
    
    # Split into batches of 1000 records each
    batch_size = 1000
    batches = [df[i:i+batch_size] for i in range(0, len(df), batch_size)]
    
    print(f"🔄 Processing {len(batches)} batches...")
    
    for i, batch in enumerate(batches):
        print(f"📤 Importing batch {i+1}/{len(batches)} ({len(batch)} records)")
        
        # Create SQL INSERT statements
        sql_commands = []
        for _, row in batch.iterrows():
            # Handle None/NaN values
            bin_val = str(row['bin']) if pd.notna(row['bin']) else ''
            brand = str(row['brand']).replace("'", "''") if pd.notna(row['brand']) else ''
            type_val = str(row['type']).replace("'", "''") if pd.notna(row['type']) else ''
            category = str(row['category']).replace("'", "''") if pd.notna(row['category']) else ''
            issuer = str(row['issuer']).replace("'", "''") if pd.notna(row['issuer']) else ''
            country = str(row['country']).replace("'", "''") if pd.notna(row['country']) else ''
            bank_phone = str(row['bank_phone']).replace("'", "''") if pd.notna(row['bank_phone']) else ''
            bank_url = str(row['bank_url']).replace("'", "''") if pd.notna(row['bank_url']) else ''
            
            sql = f"INSERT OR IGNORE INTO bins (bin, brand, type, category, issuer, country, bank_phone, bank_url) VALUES ('{bin_val}', '{brand}', '{type_val}', '{category}', '{issuer}', '{country}', '{bank_phone}', '{bank_url}');"
            sql_commands.append(sql)
        
        # Write batch to temp SQL file
        sql_file = f"batch_{i+1}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_commands))
        
        # Execute batch with wrangler using PowerShell
        try:
            # Use PowerShell to execute the command
            cmd = f'npx wrangler d1 execute bin-search-db --remote --file {sql_file}'
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                print(f"✅ Batch {i+1} imported successfully")
            else:
                print(f"❌ Batch {i+1} failed: {result.stderr}")
                print(f"Command: {cmd}")
        except Exception as e:
            print(f"❌ Error importing batch {i+1}: {e}")
        
        # Clean up temp file
        try:
            os.remove(sql_file)
        except:
            pass
        
        # Small delay to avoid rate limits
        import time
        time.sleep(2)
        
        # Stop after first few batches for testing
        if i >= 2:  # Import only first 3 batches for testing
            print("🧪 Testing mode - stopping after 3 batches")
            break
    
    print("🎉 Import complete!")

if __name__ == "__main__":
    batch_import_bins()