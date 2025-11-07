import pandas as pd
import os
from tqdm import tqdm

# Folder containing all your .txt data files
data_dir = "data"

# List all .txt files in the folder
files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]

# Prepare an empty list to store DataFrames
dfs = []

# Loop through all files and read each one
for filename in files:
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
    pbar = tqdm(total=total_lines, desc=f"Reading {filename}", unit="rows")
    for chunk in chunk_reader:
        # Clean whitespace
        chunk = chunk.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
        
        # Convert numeric columns
        numeric_cols = ["Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"]
        chunk[numeric_cols] = chunk[numeric_cols].astype(int)
        
        # Optionally add a source column to track which file it came from
        chunk["Source_File"] = filename
        
        chunk_list.append(chunk)
        rows_read += len(chunk)
        pbar.update(len(chunk))
    pbar.close()
    
    # Combine chunks into single DataFrame
    df = pd.concat(chunk_list, ignore_index=True)
    print(f"  Completed: {rows_read:,} rows read from {filename}")
    dfs.append(df)

# Combine all files into one DataFrame
combined_df = pd.concat(dfs, ignore_index=True)

# Preview the result
print("\n✅ Combined Data Loaded Successfully!")
print(f"Total rows: {len(combined_df)}")
print(combined_df.head())
