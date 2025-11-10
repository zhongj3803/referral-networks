"""
Create a NetworkX graph from the referral network data with edges weighted by patient volume.
"""

import pandas as pd
import networkx as nx
import os
from tqdm import tqdm


def create_referral_graph(
    data_path=None,
    weight_column="Pair_Count",
    directed=False,
    aggregate_duplicates=True
):
    """
    Create a NetworkX graph from referral network data.
    
    Args:
        data_path: Path to the CSV file with referral data. 
                   Defaults to "data/docgraph-data/docgraph_with_zips.csv"
        weight_column: Column name to use as edge weight. Options:
                       - "Pair_Count": Total number of shared patients (default)
                       - "Unique_Beneficiaries": Number of unique beneficiaries
                       - "Same_Day_Count": Number of same-day referrals
        directed: If True, creates a directed graph. If False, creates an undirected graph.
                 Defaults to False (undirected).
        aggregate_duplicates: If True, aggregates weights for duplicate edges (same pair).
                              If False, keeps the last value. Defaults to True.
    
    Returns:
        networkx.Graph or networkx.DiGraph: The referral network graph
    """
    if data_path is None:
        data_path = os.path.join("data", "docgraph-data", "docgraph_with_zips.csv")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Please run the data processing pipeline first."
        )
    
    print(f"Loading referral data from {data_path}...")
    df = pd.read_csv(data_path, dtype=str)
    
    # Convert numeric columns
    numeric_cols = ["Pair_Count", "Unique_Beneficiaries", "Same_Day_Count"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Validate weight column
    if weight_column not in df.columns:
        raise ValueError(
            f"Weight column '{weight_column}' not found in data. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Create graph
    if directed:
        G = nx.DiGraph()
        print("Creating directed graph...")
    else:
        G = nx.Graph()
        print("Creating undirected graph...")
    
    # Process edges with progress bar
    print(f"Adding edges weighted by '{weight_column}'...")
    
    if aggregate_duplicates:
        # Aggregate weights for duplicate edges
        edge_weights = {}
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing edges"):
            npi1 = str(row["NPI_1"]).strip()
            npi2 = str(row["NPI_2"]).strip()
            weight = row[weight_column]
            
            # Create edge key (handle undirected by sorting)
            if not directed:
                edge = tuple(sorted([npi1, npi2]))
            else:
                edge = (npi1, npi2)
            
            # Aggregate weights
            if edge in edge_weights:
                edge_weights[edge] += weight
            else:
                edge_weights[edge] = weight
        
        # Add edges to graph
        for edge, weight in tqdm(edge_weights.items(), desc="Adding edges to graph"):
            G.add_edge(edge[0], edge[1], weight=weight)
    else:
        # Add edges directly (last value wins for duplicates)
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Adding edges"):
            npi1 = str(row["NPI_1"]).strip()
            npi2 = str(row["NPI_2"]).strip()
            weight = row[weight_column]
            
            if not directed:
                # For undirected graphs, check if edge exists and aggregate
                if G.has_edge(npi1, npi2):
                    G[npi1][npi2]["weight"] += weight
                else:
                    G.add_edge(npi1, npi2, weight=weight)
            else:
                # For directed graphs, check if edge exists and aggregate
                if G.has_edge(npi1, npi2):
                    G[npi1][npi2]["weight"] += weight
                else:
                    G.add_edge(npi1, npi2, weight=weight)
    
    # Print graph statistics
    print("\n" + "=" * 80)
    print("Graph Statistics")
    print("=" * 80)
    print(f"Graph type: {'Directed' if directed else 'Undirected'}")
    print(f"Number of nodes (physicians): {G.number_of_nodes():,}")
    print(f"Number of edges (referral relationships): {G.number_of_edges():,}")
    
    if G.number_of_edges() > 0:
        weights = [data["weight"] for _, _, data in G.edges(data=True)]
        print(f"Edge weight statistics (using '{weight_column}'):")
        print(f"  Min weight: {min(weights):,}")
        print(f"  Max weight: {max(weights):,}")
        print(f"  Mean weight: {sum(weights) / len(weights):.2f}")
        print(f"  Total weight: {sum(weights):,}")
    
    # Check for self-loops
    self_loops = list(nx.selfloop_edges(G))
    if self_loops:
        print(f"\n⚠️  Warning: Found {len(self_loops)} self-loops (physician referring to themselves)")
    
    return G


def save_graph(G, output_path=None, format="graphml"):
    """
    Save the graph to a file.
    
    Args:
        G: NetworkX graph to save
        output_path: Path to save the graph. If None, uses default based on format.
        format: Format to save in. Options: "graphml", "gexf", "gml", "pickle"
    
    Returns:
        str: Path where the graph was saved
    """
    if output_path is None:
        graph_type = "directed" if G.is_directed() else "undirected"
        base_name = f"referral_network_{graph_type}"
        
        if format == "graphml":
            output_path = os.path.join("data", "docgraph-data", f"{base_name}.graphml")
        elif format == "gexf":
            output_path = os.path.join("data", "docgraph-data", f"{base_name}.gexf")
        elif format == "gml":
            output_path = os.path.join("data", "docgraph-data", f"{base_name}.gml")
        elif format == "pickle":
            output_path = os.path.join("data", "docgraph-data", f"{base_name}.pkl")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    print(f"\nSaving graph to {output_path}...")
    
    if format == "graphml":
        nx.write_graphml(G, output_path)
    elif format == "gexf":
        nx.write_gexf(G, output_path)
    elif format == "gml":
        nx.write_gml(G, output_path)
    elif format == "pickle":
        nx.write_gpickle(G, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    print(f"✅ Graph saved successfully!")
    
    return output_path


if __name__ == "__main__":
    # Create directed graph with Pair_Count as weight
    print("=" * 80)
    print("Creating Referral Network Graph")
    print("=" * 80)
    
    G = create_referral_graph(
        weight_column="Pair_Count",
        directed=True,
        aggregate_duplicates=True
    )
    
    # Save the graph
    save_graph(G, format="graphml")
    
    print("\n" + "=" * 80)
    print("Graph Creation Complete!")
    print("=" * 80)

