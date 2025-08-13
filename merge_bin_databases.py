import pandas as pd

def merge_bin_csvs(file1_path, file2_path, output_path='merged_bin_data.csv'):
    """
    Merge two BIN database CSV files into a single deduplicated CSV for Telegram bot usage.
    
    Args:
        file1_path (str): Path to first CSV file (binlist-data.csv format)
        file2_path (str): Path to second CSV file (bin-list-data.csv format)
        output_path (str): Path for merged output CSV file
    
    Returns:
        pd.DataFrame: Merged DataFrame with standardized columns
    """
    try:
        print("Loading CSV files...")
        
        # Load CSVs with memory optimization
        df1 = pd.read_csv(file1_path, dtype=str, na_values=['', 'NULL', 'null', 'None'])
        df2 = pd.read_csv(file2_path, dtype=str, na_values=['', 'NULL', 'null', 'None'])
        
        print(f"Loaded {len(df1)} records from {file1_path}")
        print(f"Loaded {len(df2)} records from {file2_path}")
        
        # Standardize column names for second file (bin-list-data.csv format)
        column_mapping = {
            'BIN': 'bin',
            'Brand': 'brand', 
            'Type': 'type',
            'Category': 'category',
            'Issuer': 'issuer',
            'IssuerPhone': 'bank_phone',
            'IssuerUrl': 'bank_url',
            'CountryName': 'country'
        }
        df2 = df2.rename(columns=column_mapping)
        
        # Define final columns for Telegram bot (drop unnecessary columns)
        final_columns = ['bin', 'brand', 'type', 'category', 'issuer', 'country', 'bank_phone', 'bank_url']
        
        # Keep only required columns and add missing ones
        for df in [df1, df2]:
            # Add missing columns with None values
            for col in final_columns:
                if col not in df.columns:
                    df[col] = None
            # Keep only required columns
            for col in list(df.columns):
                if col not in final_columns:
                    df.drop(col, axis=1, inplace=True)
        
        # Clean and standardize 'bin' column for consistent merging
        df1['bin'] = df1['bin'].astype(str).str.strip().str.upper()
        df2['bin'] = df2['bin'].astype(str).str.strip().str.upper()
        
        # Remove invalid BIN entries (should be numeric)
        df1 = df1[df1['bin'].str.isdigit()]
        df2 = df2[df2['bin'].str.isdigit()]
        
        print("Merging and deduplicating records...")
        
        # Combine DataFrames
        df_combined = pd.concat([df1, df2], ignore_index=True)
        
        # Custom deduplication: keep record with most non-null fields
        def get_best_record(group):
            """Select record with most non-null values for each BIN"""
            non_null_counts = group.notna().sum(axis=1)
            best_idx = non_null_counts.idxmax()
            return group.loc[best_idx]
        
        # Group by 'bin' and apply custom deduplication
        df_deduplicated = df_combined.groupby('bin').apply(get_best_record).reset_index(drop=True)
        
        # Sort by BIN for better organization
        df_deduplicated = df_deduplicated.sort_values('bin').reset_index(drop=True)
        
        # Save merged CSV with optimal settings
        df_deduplicated.to_csv(output_path, index=False, na_rep='')
        
        print(f"✅ Merged database saved to {output_path}")
        print(f"📊 Total unique BINs: {len(df_deduplicated)}")
        print(f"🔄 Duplicates removed: {len(df_combined) - len(df_deduplicated)}")
        
        return df_deduplicated
    
    except FileNotFoundError as e:
        print(f"❌ Error: CSV file not found - {e}")
        return None
    except pd.errors.EmptyDataError:
        print("❌ Error: One of the CSV files is empty")
        return None
    except pd.errors.ParserError as e:
        print(f"❌ Error: Failed to parse CSV file - {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def validate_merged_data(df):
    """
    Validate the merged DataFrame for Telegram bot usage.
    
    Args:
        df (pd.DataFrame): Merged DataFrame to validate
    
    Returns:
        bool: True if data is valid for bot usage
    """
    if df is None or df.empty:
        print("❌ Validation failed: DataFrame is empty")
        return False
    
    required_columns = ['bin', 'brand', 'type', 'category', 'issuer', 'country', 'bank_phone', 'bank_url']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Validation failed: Missing columns {missing_columns}")
        return False
    
    # Check for valid BIN format (should be numeric strings)
    invalid_bins = df[~df['bin'].str.isdigit()]
    if not invalid_bins.empty:
        print(f"⚠️  Warning: Found {len(invalid_bins)} invalid BIN entries")
    
    print("✅ Data validation passed")
    return True

if __name__ == "__main__":
    # Configuration for BIN database merging
    file1 = 'binlist-data.csv'      # First BIN database
    file2 = 'bin-list-data.csv'     # Second BIN database  
    output_file = 'merged_bin_data.csv'
    
    print("🚀 Starting BIN database merge for Telegram bot...")
    print("=" * 50)
    
    # Merge the databases
    merged_df = merge_bin_csvs(file1, file2, output_file)
    
    # Validate the merged data
    if validate_merged_data(merged_df):
        print("=" * 50)
        print("🎉 BIN database merge completed successfully!")
        print(f"📁 Output file: {output_file}")
        print("🤖 Ready for Telegram bot integration!")
    else:
        print("❌ Merge completed with validation errors")