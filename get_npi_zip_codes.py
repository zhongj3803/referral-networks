import pandas as pd
import os
from pathlib import Path


def get_npi_zip_codes(input_file=None, output_file=None, max_rows=500000):
    """
    Extract NPI and postal code columns from NPI info CSV and save to a new file.
    
    Args:
        input_file: Path to input npi_info.csv. Defaults to "data/npi_info/npi_info.csv"
        output_file: Path for output CSV. Defaults to "data/npi_info/npi_zip_codes.csv"
        max_rows: Maximum number of rows to process. Defaults to 500000 for testing.
    
    Returns:
        pandas.DataFrame: DataFrame with NPI and postal code columns
    """
    if input_file is None:
        data_dir = Path("data")
        input_file = data_dir / "npi_info" / "npi_info.csv"
    else:
        input_file = Path(input_file)
    
    if output_file is None:
        output_file = input_file.parent / "npi_zip_codes.csv"
    else:
        output_file = Path(output_file)
    
    # Columns we care about
    columns_to_read = ['NPI', 'Provider Business Practice Location Address Postal Code']
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file.resolve()}")
    
    print("=" * 80)
    print(f"File: {input_file}")
    print("=" * 80)
    
    try:
        # Get file size
        file_size = os.path.getsize(input_file) / (1024 * 1024)  # Size in MB
        print(f"File size: {file_size:.2f} MB")
        
        # Read only the columns we care about
        print(f"\nReading columns: {', '.join(columns_to_read)}")
        print(f"⚠️  Processing limited to first {max_rows:,} rows for testing")
        print("Loading data (this may take a moment for large files)...")
        
        # Specify dtypes to ensure postal code is read as string (not float)
        dtype_dict = {
            'NPI': str,
            'Provider Business Practice Location Address Postal Code': str
        }
        
        # Read the data with only the columns we need, limited to max_rows
        # Using dtype=str ensures postal codes are read as strings (no decimal conversion)
        df = pd.read_csv(input_file, usecols=columns_to_read, dtype=dtype_dict, keep_default_na=True, na_values=[''], nrows=max_rows)
        
        # Clean and normalize postal codes
        postal_col = 'Provider Business Practice Location Address Postal Code'
        df['NPI'] = df['NPI'].replace('nan', pd.NA)
        
        # Handle postal codes: strip whitespace and mark empty/missing values as NaN
        # Convert to string (NaN becomes 'nan'), strip whitespace, then mark empty/missing strings as NaN
        df[postal_col] = df[postal_col].astype(str)
        df[postal_col] = df[postal_col].str.strip()
        # Replace empty strings, 'nan' strings (from NaN conversion), and 'None' with pd.NA
        df.loc[df[postal_col].isin(['', 'nan', 'None']), postal_col] = pd.NA
        
        print(f"\nTotal rows before filtering: {len(df):,} (limited to {max_rows:,} for testing)")
        print(f"Columns read: {len(df.columns)}")
        print(f"\nColumn names: {', '.join(df.columns.tolist())}")
        
        # Display data types
        print(f"\nData types:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")
        
        # Display basic statistics before filtering
        print(f"\nData summary (before filtering):")
        print(f"  Total rows: {len(df):,}")
        print(f"  Rows with NPI: {df['NPI'].notna().sum():,}")
        print(f"  Rows with Postal Code: {df[postal_col].notna().sum():,}")
        print(f"  Missing NPI: {df['NPI'].isna().sum():,}")
        print(f"  Missing Postal Code: {df[postal_col].isna().sum():,}")
        
        # Filter out rows with empty/missing postal codes
        initial_count = len(df)
        df = df[df[postal_col].notna()].copy()
        filtered_count = len(df)
        rows_removed = initial_count - filtered_count
        
        print(f"\n📊 Filtering results:")
        print(f"  Rows removed (empty zip codes): {rows_removed:,}")
        print(f"  Rows remaining (with zip codes): {filtered_count:,}")
        
        # Display sample data
        print(f"\nFirst 10 rows (after filtering):")
        print(df.head(10).to_string())
        
        # Display basic statistics after filtering
        print(f"\nData summary (after filtering):")
        print(f"  Total rows: {len(df):,}")
        print(f"  Rows with NPI: {df['NPI'].notna().sum():,}")
        print(f"  Rows with Postal Code: {df[postal_col].notna().sum():,}")
        
        # Postal code statistics
        if df[postal_col].notna().sum() > 0:
            print(f"\nPostal Code Statistics:")
            print(f"  Unique postal codes: {df[postal_col].nunique():,}")
            print(f"  Most common postal codes (top 10):")
            print(df[postal_col].value_counts().head(10).to_string())
        
        # Save the processed dataframe to a new CSV file in the same directory as the input
        df.to_csv(output_file, index=False)
        print(f"\nSaved processed data to: {output_file.resolve()}")
        
        print("\n" + "=" * 80)
        print("CSV Data Reading Complete!")
        print("=" * 80)
        
        return df
        
    except Exception as e:
        print(f"Error reading {input_file}: {e}\n")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    get_npi_zip_codes()

