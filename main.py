"""
Main script to run the complete data processing pipeline:
1. Extract DocGraph data from .txt files
2. Get NPI zip codes from NPI info
3. Join zip codes with DocGraph data
4. Create NetworkX graph from referral network data
"""

from extract import extract_docgraph_data
from get_npi_zip_codes import get_npi_zip_codes
from join_docgraph_with_zips import join_docgraph_with_zips
from create_graph import create_referral_graph, save_graph
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import os


def main():
    """Run the complete data processing pipeline."""
    print("=" * 80)
    print("Starting Data Processing Pipeline")
    print("=" * 80)
    
    # Step 1: Extract DocGraph data
    print("\n" + "=" * 80)
    print("Step 1: Extracting DocGraph Data")
    print("=" * 80)
    extract_docgraph_data()
    
    # Step 2: Get NPI zip codes
    print("\n" + "=" * 80)
    print("Step 2: Getting NPI Zip Codes")
    print("=" * 80)
    get_npi_zip_codes()
    
    # Step 3: Join zip codes with DocGraph data
    print("\n" + "=" * 80)
    print("Step 3: Joining Zip Codes with DocGraph Data")
    print("=" * 80)
    join_docgraph_with_zips()
    
    # Step 4: Create NetworkX graph
    print("\n" + "=" * 80)
    print("Step 4: Creating Referral Network Graph")
    print("=" * 80)
    G = create_referral_graph(
        weight_column="Pair_Count",
        directed=True,
        aggregate_duplicates=True
    )
    
    # Save the graph
    save_graph(G, format="graphml")
    
    # Step 5: Visualize a small subset of the graph
    print("\n" + "=" * 80)
    print("Step 5: Visualizing Small Subset of Graph")
    print("=" * 80)
    visualize_subgraph(G, max_nodes=30, output_path="data/docgraph-data/graph_subset_visualization.png")
    
    # Step 6: Compute referral volume by zip code
    print("\n" + "=" * 80)
    print("Step 6: Computing Referral Volume by Zip Code")
    print("=" * 80)
    zip_volume_df = compute_zip_referral_volume(G)
    
    print("\n" + "=" * 80)
    print("Pipeline Complete!")
    print("=" * 80)


def compute_zip_referral_volume(G, data_path=None, output_path=None):
    """
    Compute total referral volume (incoming and outgoing) for each zip code.
    
    Args:
        G: NetworkX graph with referral relationships
        data_path: Path to docgraph_with_zips.csv. Defaults to "data/docgraph-data/docgraph_with_zips.csv"
        output_path: Path to save results CSV. Defaults to "data/docgraph-data/zip_referral_volume.csv"
    
    Returns:
        pandas.DataFrame: DataFrame with zip code referral volume statistics
    """
    if data_path is None:
        data_path = os.path.join("data", "docgraph-data", "docgraph_with_zips.csv")
    
    if output_path is None:
        output_path = os.path.join("data", "docgraph-data", "zip_referral_volume.csv")
    
    print("Loading zip code data...")
    # Load the data with zip codes
    df = pd.read_csv(data_path, dtype=str)
    
    # Convert numeric columns
    numeric_cols = ["Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Create NPI to zip code mapping
    print("Creating NPI to zip code mapping...")
    npi_to_zip = {}
    
    # Map from NPI_1
    for _, row in df.iterrows():
        npi1 = str(row["NPI_1"]).strip()
        zip1 = row.get("NPI_1_Zip")
        if pd.notna(zip1) and str(zip1).strip():
            npi_to_zip[npi1] = str(zip1).strip()
    
    # Map from NPI_2
    for _, row in df.iterrows():
        npi2 = str(row["NPI_2"]).strip()
        zip2 = row.get("NPI_2_Zip")
        if pd.notna(zip2) and str(zip2).strip():
            npi_to_zip[npi2] = str(zip2).strip()
    
    print(f"Mapped {len(npi_to_zip):,} NPIs to zip codes")
    
    # Initialize dictionaries to track volumes
    outgoing_volume = {}  # zip -> total volume of referrals FROM this zip
    incoming_volume = {}  # zip -> total volume of referrals TO this zip
    
    print("Computing referral volumes by zip code...")
    from tqdm import tqdm
    
    # Iterate through all edges in the graph
    for source, target, data in tqdm(G.edges(data=True), desc="Processing edges", total=G.number_of_edges()):
        weight = data.get('weight', 0)
        
        source_zip = npi_to_zip.get(str(source).strip())
        target_zip = npi_to_zip.get(str(target).strip())
        
        # Outgoing volume: source zip sends referrals
        if source_zip:
            outgoing_volume[source_zip] = outgoing_volume.get(source_zip, 0) + weight
        
        # Incoming volume: target zip receives referrals
        if target_zip:
            incoming_volume[target_zip] = incoming_volume.get(target_zip, 0) + weight
    
    # Get all unique zip codes
    all_zips = set(outgoing_volume.keys()) | set(incoming_volume.keys())
    
    # Create results DataFrame
    results = []
    for zip_code in sorted(all_zips):
        results.append({
            'Zip_Code': zip_code,
            'Outgoing_Volume': outgoing_volume.get(zip_code, 0),
            'Incoming_Volume': incoming_volume.get(zip_code, 0),
            'Total_Volume': outgoing_volume.get(zip_code, 0) + incoming_volume.get(zip_code, 0),
            'Net_Volume': incoming_volume.get(zip_code, 0) - outgoing_volume.get(zip_code, 0)  # Positive = net receiver
        })
    
    zip_volume_df = pd.DataFrame(results)
    zip_volume_df = zip_volume_df.sort_values('Total_Volume', ascending=False)
    
    # Save results
    zip_volume_df.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to {output_path}")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("Zip Code Referral Volume Summary")
    print("=" * 80)
    print(f"Total zip codes: {len(zip_volume_df):,}")
    print(f"\nTop 10 zip codes by total volume:")
    print(zip_volume_df.head(10).to_string(index=False))
    
    print(f"\nStatistics:")
    print(f"  Total outgoing volume: {zip_volume_df['Outgoing_Volume'].sum():,}")
    print(f"  Total incoming volume: {zip_volume_df['Incoming_Volume'].sum():,}")
    print(f"  Average outgoing volume per zip: {zip_volume_df['Outgoing_Volume'].mean():.2f}")
    print(f"  Average incoming volume per zip: {zip_volume_df['Incoming_Volume'].mean():.2f}")
    
    # Net receivers (positive net volume) vs net senders (negative net volume)
    net_receivers = zip_volume_df[zip_volume_df['Net_Volume'] > 0]
    net_senders = zip_volume_df[zip_volume_df['Net_Volume'] < 0]
    balanced = zip_volume_df[zip_volume_df['Net_Volume'] == 0]
    
    print(f"\n  Net receivers (receive more than send): {len(net_receivers):,}")
    print(f"  Net senders (send more than receive): {len(net_senders):,}")
    print(f"  Balanced (equal send/receive): {len(balanced):,}")
    
    return zip_volume_df


def visualize_subgraph(G, max_nodes=50, output_path=None):
    """
    Visualize a small subset of the graph.
    
    Args:
        G: NetworkX graph to visualize
        max_nodes: Maximum number of nodes to include in the visualization
        output_path: Path to save the visualization image
    """
    if output_path is None:
        output_path = os.path.join("data", "docgraph-data", "graph_subset_visualization.png")
    
    print(f"Creating subgraph with up to {max_nodes} nodes...")
    
    # Find a node with high out-degree to start from (a physician who refers to many others)
    if G.is_directed():
        # Get node with highest out-degree
        out_degrees = dict(G.out_degree())
        start_node = max(out_degrees, key=out_degrees.get)
        print(f"Starting from node {start_node} (out-degree: {out_degrees[start_node]})")
        
        # Create subgraph using BFS from start node
        nodes_to_include = {start_node}
        queue = [start_node]
        
        while queue and len(nodes_to_include) < max_nodes:
            current = queue.pop(0)
            # Add neighbors (outgoing edges)
            for neighbor in G.successors(current):
                if neighbor not in nodes_to_include and len(nodes_to_include) < max_nodes:
                    nodes_to_include.add(neighbor)
                    queue.append(neighbor)
                if len(nodes_to_include) >= max_nodes:
                    break
        
        # Create subgraph
        subgraph = G.subgraph(nodes_to_include).copy()
    else:
        # For undirected graphs, just take first max_nodes nodes
        nodes_to_include = list(G.nodes())[:max_nodes]
        subgraph = G.subgraph(nodes_to_include).copy()
    
    print(f"Subgraph created: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
    
    # Create visualization
    plt.figure(figsize=(24, 20))
    
    # Use spring layout with very high k for maximum spacing
    # k parameter: ideal distance between nodes (higher = more spacing)
    print("Computing layout with maximum spacing...")
    k_value = max(8.0, (50.0 / (subgraph.number_of_nodes() ** 0.5)))
    pos = nx.spring_layout(
        subgraph, 
        k=k_value,  # Very high k for maximum spacing
        iterations=1000,  # Many iterations for best convergence
        seed=42,
        pos=None
    )
    
    # Apply aggressive scaling to spread nodes out much more
    import numpy as np
    pos_array = np.array(list(pos.values()))
    if len(pos_array) > 0:
        # Scale positions to use much more of the available space
        scale_factor = 2.5  # Increased from 1.5 to 2.5
        center = pos_array.mean(axis=0)
        pos = {node: ((pos[node][0] - center[0]) * scale_factor + center[0], 
                      (pos[node][1] - center[1]) * scale_factor + center[1]) 
               for node in pos.keys()}
    
    # Get edge weights for visualization
    edges = subgraph.edges()
    weights = [subgraph[u][v].get('weight', 1) for u, v in edges]
    
    # Normalize weights for edge width (min width 0.5, max width 5)
    if weights:
        min_weight = min(weights)
        max_weight = max(weights)
        if max_weight > min_weight:
            edge_widths = [0.5 + 4.5 * (w - min_weight) / (max_weight - min_weight) for w in weights]
        else:
            edge_widths = [2.0] * len(weights)
    else:
        edge_widths = [1.0] * len(edges)
    
    # Draw edges
    if subgraph.is_directed():
        # Use FancyArrowPatches for directed graphs to show arrows properly
        nx.draw_networkx_edges(
            subgraph, pos,
            width=edge_widths,
            alpha=0.6,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1',
            min_source_margin=15,
            min_target_margin=15
        )
    else:
        # For undirected graphs, use simple edges
        nx.draw_networkx_edges(
            subgraph, pos,
            width=edge_widths,
            alpha=0.6,
            edge_color='gray'
        )
    
    # Draw nodes
    node_sizes = [300 + 100 * subgraph.degree(n) for n in subgraph.nodes()]
    nx.draw_networkx_nodes(
        subgraph, pos,
        node_size=node_sizes,
        node_color='lightblue',
        alpha=0.9,
        edgecolors='black',
        linewidths=1
    )
    
    # Draw labels (full NPI numbers)
    labels = {n: str(n) for n in subgraph.nodes()}
    nx.draw_networkx_labels(
        subgraph, pos,
        labels=labels,
        font_size=8,
        font_weight='bold'
    )
    
    plt.title(f"Referral Network Subgraph\n({subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges)", 
              fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Save the figure
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved to {output_path}")
    
    plt.close()


if __name__ == "__main__":
    main()

