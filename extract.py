import pandas as pd
import os
from tqdm import tqdm


def extract_docgraph_data(data_dir=None, output_path=None, max_rows=500000):
    """
    Extract and combine all DocGraph .txt files into a single CSV.
    
    Args:
        data_dir: Directory containing .txt data files. Defaults to "data/docgraph-data"
        output_path: Path for output CSV. Defaults to "data/docgraph-data/docgraph_combined.csv"
        max_rows: Maximum number of rows to process. Defaults to 500000 for testing.
    
    Returns:
        pandas.DataFrame: Combined dataframe with all extracted data
    """
    if data_dir is None:
        data_dir = os.path.join("data", "docgraph-data")
    
    if output_path is None:
        output_path = os.path.join(data_dir, "docgraph_combined.csv")
    
    # List all .txt files in the folder except README.txt (case-insensitive)
    files = [f for f in os.listdir(data_dir) if f.endswith(".txt") and f.lower() != "readme.txt"]
    
    # Prepare an empty list to store DataFrames
    dfs = []
    total_rows_processed = 0
    
    print(f"⚠️  Processing limited to first {max_rows:,} rows for testing")
    
    # Loop through all files and read each one
    for filename in files:
        if total_rows_processed >= max_rows:
            print(f"\n⚠️  Reached limit of {max_rows:,} rows. Stopping processing.")
            break
            
        file_path = os.path.join(data_dir, filename)
        print(f"Loading {filename}...")
        
        # Read file in chunks to show progress
        chunk_list = []
        chunk_size = 10000  # Read 10k rows at a time
        
        # First, get total number of lines for progress bar
        with open(file_path, 'r') as f:
            total_lines = sum(1 for _ in f)
        
        # Read in chunks with progress bar
        chunk_reader = pd.read_csv(
            file_path,
            header=None,
            names=["NPI_1", "NPI_2", "Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"],
            dtype=str,
            chunksize=chunk_size
        )
        
        rows_read = 0
        remaining_rows = max_rows - total_rows_processed
        pbar = tqdm(total=min(total_lines, remaining_rows), desc=f"Reading {filename}", unit="rows")
        
        for chunk in chunk_reader:
            # Check if we've reached the limit
            if total_rows_processed >= max_rows:
                break
            
            # Trim chunk if it would exceed the limit
            rows_needed = max_rows - total_rows_processed
            if len(chunk) > rows_needed:
                chunk = chunk.head(rows_needed)
            
            # Clean whitespace
            chunk = chunk.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
            
            # Convert numeric columns
            numeric_cols = ["Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"]
            chunk[numeric_cols] = chunk[numeric_cols].astype(int)
            
            # Optionally add a source column to track which file it came from
            chunk["Source_File"] = filename
            
            chunk_list.append(chunk)
            rows_read += len(chunk)
            total_rows_processed += len(chunk)
            pbar.update(len(chunk))
            
            if total_rows_processed >= max_rows:
                break
        
        pbar.close()
        
        # Combine chunks into single DataFrame
        if chunk_list:
            df = pd.concat(chunk_list, ignore_index=True)
            print(f"  Completed: {rows_read:,} rows read from {filename}")
            dfs.append(df)
        
        if total_rows_processed >= max_rows:
            break
    
    # Combine all files into one DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Write combined output to CSV in the same directory
    combined_df.to_csv(output_path, index=False)
    
    # Preview the result
    print("\n✅ Combined Data Loaded Successfully!")
    print(f"Total rows: {len(combined_df):,} (limited to {max_rows:,} for testing)")
    print(combined_df.head())
    print(f"\n💾 Saved combined CSV to {output_path}")
    
    return combined_df


if __name__ == "__main__":
    extract_docgraph_data()