import pandas as pd
from pathlib import Path

def generate_import_sql():
    """Generate SQL files for manual import"""
    csv_file = Path("../data/merged_bin_data.csv")
    
    print(f"📊 Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"📈 Total records: {len(df)}")
    
    # Create one large SQL file
    sql_commands = []
    for _, row in df.iterrows():
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
    
    # Write to SQL file
    with open('all_bins_import.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_commands))
    
    print(f"✅ Generated all_bins_import.sql with {len(sql_commands)} INSERT statements")
    print("🔧 Run manually with: npx wrangler d1 execute bin-search-db --remote --file all_bins_import.sql")

if __name__ == "__main__":
    generate_import_sql()