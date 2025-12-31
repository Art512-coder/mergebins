import csv
import os
import sys

def sanitize_sql_value(value: str) -> str:
    """Sanitize SQL values to prevent injection and handle special characters"""
    if not value or value.strip() == '':
        return 'NULL'
    # Escape single quotes by doubling them
    value = value.replace("'", "''")
    return f"'{value}'"

def create_migration_files(csv_file_path: str, batch_size: int = 1000):
    """Create SQL migration files from CSV data"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print(f"🚀 Creating migration files from {csv_file_path}")
    print(f"📦 Batch size: {batch_size}")
    
    # Create migrations directory
    migrations_dir = "migrations"
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    batch_count = 0
    current_batch = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
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
                
                current_batch.append(bin_data)
                
                # Write batch when it reaches batch_size
                if len(current_batch) >= batch_size:
                    batch_count += 1
                    write_batch_file(current_batch, batch_count, migrations_dir)
                    current_batch = []
                
                # Progress indicator
                if row_num % 10000 == 0:
                    print(f"📊 Processed {row_num} rows from CSV...")
            
            # Write remaining records
            if current_batch:
                batch_count += 1
                write_batch_file(current_batch, batch_count, migrations_dir)
        
        print(f"\n🎉 Migration files created successfully!")
        print(f"📊 Total batches: {batch_count}")
        print(f"📁 Files location: {migrations_dir}/")
        
        # Create upload script
        create_upload_script(batch_count, migrations_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration file creation failed: {e}")
        return False

def write_batch_file(batch, batch_num, migrations_dir):
    """Write a batch of data to SQL file"""
    filename = f"{migrations_dir}/batch_{batch_num:04d}.sql"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"-- Batch {batch_num} - {len(batch)} records\n")
        f.write("BEGIN TRANSACTION;\n\n")
        
        # Write INSERT statements
        columns = ['bin', 'brand', 'type', 'category', 'issuer', 'country', 'bank_phone', 'bank_url']
        
        for i in range(0, len(batch), 100):  # Sub-batches of 100 for better performance
            sub_batch = batch[i:i+100]
            values_list = []
            
            for record in sub_batch:
                values = []
                for col in columns:
                    val = record.get(col, '').strip()
                    values.append(sanitize_sql_value(val) if val else 'NULL')
                values_list.append(f"({', '.join(values)})")
            
            columns_str = ', '.join(columns)
            values_str = ',\n    '.join(values_list)
            
            f.write(f"INSERT OR REPLACE INTO bins ({columns_str}) VALUES\n    {values_str};\n\n")
        
        f.write("COMMIT;\n")
    
    print(f"✅ Created {filename} with {len(batch)} records")

def create_upload_script(batch_count, migrations_dir):
    """Create PowerShell script to upload all batches"""
    script_path = "upload_to_d1.ps1"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("# D1 Database Upload Script\n")
        f.write("# This script uploads all migration batches to D1\n\n")
        f.write("$database = 'bin-search-db'\n")
        f.write(f"$totalBatches = {batch_count}\n\n")
        f.write("Write-Host '🚀 Starting D1 upload process...'\n")
        f.write("Write-Host \"📦 Total batches to upload: $totalBatches\"\n\n")
        
        f.write("for ($i = 1; $i -le $totalBatches; $i++) {\n")
        f.write("    $batchFile = 'migrations/batch_{0:D4}.sql' -f $i\n")
        f.write("    Write-Host \"📤 Uploading batch $i of $totalBatches...\"\n")
        f.write("    \n")
        f.write("    $result = wrangler d1 execute $database --file=$batchFile\n")
        f.write("    \n")
        f.write("    if ($LASTEXITCODE -eq 0) {\n")
        f.write("        Write-Host \"✅ Batch $i uploaded successfully\" -ForegroundColor Green\n")
        f.write("    } else {\n")
        f.write("        Write-Host \"❌ Batch $i failed\" -ForegroundColor Red\n")
        f.write("        Write-Host \"Error: $result\" -ForegroundColor Red\n")
        f.write("        break\n")
        f.write("    }\n")
        f.write("    \n")
        f.write("    # Small delay to avoid rate limiting\n")
        f.write("    Start-Sleep -Milliseconds 500\n")
        f.write("}\n\n")
        
        f.write("Write-Host '🎉 Upload process completed!'\n")
        f.write("Write-Host 'Verifying data...'\n")
        f.write("wrangler d1 execute $database --command=\"SELECT COUNT(*) as total_records FROM bins;\"\n")
    
    print(f"📜 Created upload script: {script_path}")
    print(f"   Run with: .\\{script_path}")

if __name__ == "__main__":
    # Configuration
    CSV_FILE = "merged_bin_data.csv"
    BATCH_SIZE = 500  # Smaller batches to avoid timeout
    
    print("🏦 D1 BIN Database Migration File Creator")
    print("=" * 45)
    
    success = create_migration_files(CSV_FILE, BATCH_SIZE)
    
    if success:
        print(f"\n🎯 Next steps:")
        print(f"1. Review the migration files in ./migrations/")
        print(f"2. Run the upload script: .\\upload_to_d1.ps1")
        print(f"3. Monitor the upload progress")
    else:
        print(f"\n❌ Migration file creation failed.")
        sys.exit(1)
