import pandas as pd
import os
from tqdm import tqdm


def join_docgraph_with_zips(docgraph_csv=None, zip_file=None, output_path=None):
    """
    Join ZIP codes to DocGraph data for both NPI_1 and NPI_2 columns.
    
    Args:
        docgraph_csv: Path to docgraph_combined.csv. Defaults to "data/docgraph-data/docgraph_combined.csv"
        zip_file: Path to npi_zip_codes.csv. Defaults to "data/npi_info/npi_zip_codes.csv"
        output_path: Path for output CSV. Defaults to "data/docgraph-data/docgraph_with_zips.csv"
    
    Returns:
        pandas.DataFrame: DataFrame with ZIP codes joined to DocGraph data
    """
    if docgraph_csv is None:
        docgraph_csv = os.path.join("data", "docgraph-data", "docgraph_combined.csv")
    
    if zip_file is None:
        zip_file = os.path.join("data", "npi_info", "npi_zip_codes.csv")
    
    if output_path is None:
        output_path = os.path.join("data", "docgraph-data", "docgraph_with_zips.csv")
    
    # Prefer loading pre-extracted DocGraph CSV from docgraph-data directory
    if os.path.exists(docgraph_csv):
        print("Loading pre-extracted DocGraph CSV...")
        combined_df = pd.read_csv(docgraph_csv, dtype=str)
        # Normalize whitespace
        combined_df = combined_df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
        # Ensure numeric columns are integers
        numeric_cols = ["Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"]
        combined_df[numeric_cols] = combined_df[numeric_cols].astype(int)
    else:
        raise FileNotFoundError(f"DocGraph CSV not found at {docgraph_csv}. Please run extract.py first.")
    
    # Load NPI -> ZIP mapping and join ZIPs for both NPI columns
    if os.path.exists(zip_file):
        print("\nLoading NPI ZIP mapping...")
        # Read only the columns we need as strings
        zip_cols = ["NPI", "Provider Business Practice Location Address Postal Code"]
        npi_zip_df = pd.read_csv(zip_file, usecols=zip_cols, dtype=str)
        
        # Normalize column names
        zip_col = "Provider Business Practice Location Address Postal Code"
        npi_zip_df["NPI"] = npi_zip_df["NPI"].str.strip()
        npi_zip_df[zip_col] = npi_zip_df[zip_col].astype(str).str.strip()
        
        # Convert postal codes to 5-digit ZIP (keep only first 5 numeric chars)
        npi_zip_df["ZIP5"] = npi_zip_df[zip_col].str[:5].str.extract(r"(\d{5})", expand=False)
        
        # Keep one row per NPI, preferring rows where ZIP5 is present
        npi_zip_df = npi_zip_df.dropna(subset=["NPI"])  # require NPI
        # Sort so non-null ZIPs come first, then drop duplicates by NPI keeping first
        npi_zip_df["_has_zip"] = npi_zip_df["ZIP5"].notna()
        npi_zip_df = npi_zip_df.sort_values(["NPI", "_has_zip"], ascending=[True, False])
        npi_zip_df = npi_zip_df.drop_duplicates(subset=["NPI"], keep="first").drop(columns=[zip_col, "_has_zip"])
        
        # Ensure NPIs in combined_df are strings for joining
        combined_df["NPI_1"] = combined_df["NPI_1"].astype(str).str.strip()
        combined_df["NPI_2"] = combined_df["NPI_2"].astype(str).str.strip()
        
        # Join ZIP for NPI_1
        combined_df = combined_df.merge(
            npi_zip_df.rename(columns={"ZIP5": "NPI_1_Zip"}),
            left_on="NPI_1",
            right_on="NPI",
            how="left"
        ).drop(columns=["NPI"])  # drop the joined key to avoid confusion
        
        # Join ZIP for NPI_2
        combined_df = combined_df.merge(
            npi_zip_df.rename(columns={"ZIP5": "NPI_2_Zip"}),
            left_on="NPI_2",
            right_on="NPI",
            how="left"
        ).drop(columns=["NPI"])  # drop the joined key to avoid confusion
        
        # Brief summary of ZIP coverage before filtering
        total_rows_before = len(combined_df)
        n1_zip_matches = combined_df["NPI_1_Zip"].notna().sum()
        n2_zip_matches = combined_df["NPI_2_Zip"].notna().sum()
        both_zip_rows = combined_df[combined_df[["NPI_1_Zip", "NPI_2_Zip"]].notna().all(axis=1)].shape[0]
        
        print("\n✅ ZIPs joined (before filtering):")
        print(f"  NPI_1 with ZIP: {n1_zip_matches:,} / {total_rows_before:,}")
        print(f"  NPI_2 with ZIP: {n2_zip_matches:,} / {total_rows_before:,}")
        print(f"  Rows with both ZIPs present: {both_zip_rows:,} / {total_rows_before:,}")
        
        # Filter out rows where either NPI_1_Zip or NPI_2_Zip is null
        combined_df = combined_df[combined_df[["NPI_1_Zip", "NPI_2_Zip"]].notna().all(axis=1)].copy()
        rows_removed = total_rows_before - len(combined_df)
        
        print(f"\n📊 Filtering results:")
        print(f"  Rows removed (missing ZIPs): {rows_removed:,}")
        print(f"  Rows remaining (both ZIPs present): {len(combined_df):,}")
    else:
        print("\n⚠️ NPI ZIP mapping not found; skipping ZIP join.")
    
    # Write output to the same docgraph-data directory
    combined_df.to_csv(output_path, index=False)
    
    # Preview the result (with ZIPs if available)
    print("\n✅ ZIP-enriched data saved")
    print(f"Total rows: {len(combined_df)}")
    print(combined_df.head())
    print(f"\n💾 Saved to {output_path}")
    
    return combined_df


if __name__ == "__main__":
    join_docgraph_with_zips()
