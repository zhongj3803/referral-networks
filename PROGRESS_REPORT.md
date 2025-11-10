# Progress Report: Physician Referral Network Analysis

## Clear Statement of Objectives

The primary objective of this project is to analyze physician referral networks using shared patient patterns from Medicare claims data. The project aims to:

1. **Construct a network representation** of physician referral relationships based on shared patient encounters
2. **Enrich network data** with geographic information (ZIP codes) to enable spatial analysis
3. **Analyze referral patterns** at both the physician and geographic levels
4. **Identify key network characteristics** such as referral volume, network structure, and geographic flow patterns
5. **Visualize network structures** to understand referral pathways and relationships

The ultimate goal is to understand how physicians are connected through patient referrals and how these patterns vary across geographic regions, which can inform healthcare delivery optimization and policy decisions.

---

## Materials & Cohort: Dataset(s), Description, Summary Tables

### Datasets

#### 1. **DocGraph Physician Shared Patient Patterns Data**
- **Source**: Medicare claims data from the DocGraph project
- **Format**: Tab-separated text files (`physician-shared-patient-patterns-YYYY-days180.txt`)
- **Years Available**: 2009-2015 (currently processing 2009 data)
- **Structure**: Each row represents a physician pair with shared patient encounters
- **Columns**:
  - `NPI_1`: First physician's National Provider Identifier
  - `NPI_2`: Second physician's National Provider Identifier
  - `Pair_Count`: Total number of shared patient encounters
  - `Unique_Beneficiaries`: Number of unique beneficiaries shared between the pair
  - `Same_Day_Count`: Number of same-day encounters (potential referrals)
- **File Size**: Large files (5+ GB each), processed in chunks for efficiency
- **Processing Status**: Currently limited to 500,000 rows for testing/development

#### 2. **NPI Provider Information**
- **Source**: NPI monthly full replacement data
- **Format**: CSV file (`npi_info.csv`)
- **Key Columns Used**:
  - `NPI`: National Provider Identifier
  - `Provider Business Practice Location Address Postal Code`: ZIP code for provider location
- **Purpose**: Enables geographic analysis by mapping physicians to their practice locations
- **Processing Status**: Currently limited to 500,000 rows for testing/development

### Data Processing Pipeline

The data undergoes the following processing steps:

1. **Extraction** (`extract.py`): Combines multiple year files into a single CSV
2. **ZIP Code Mapping** (`get_npi_zip_codes.py`): Extracts NPI-to-ZIP mappings
3. **Data Joining** (`join_docgraph_with_zips.py`): Enriches referral data with geographic information
4. **Graph Creation** (`create_graph.py`): Constructs NetworkX graph from processed data

### Summary Statistics

**Processed Data**:
- Total referral pairs processed: ~100,000 rows (limited for testing)
- Unique physicians (nodes): Varies based on graph construction
- Referral relationships (edges): Varies based on graph construction
- ZIP codes with referral activity: Multiple (see zip_referral_volume.csv)

**Data Quality**:
- Rows filtered for missing ZIP codes: Significant portion (exact count varies)
- Self-loops detected: Some physicians referring to themselves (flagged in processing)

---

## Methods

### Network Creation

#### Nodes
- **Definition**: Each node represents a unique physician identified by their National Provider Identifier (NPI)
- **Node Attributes**: 
  - NPI number (unique identifier)
  - ZIP code (geographic location, when available)

#### Edges
- **Definition**: An edge represents a referral relationship between two physicians based on shared patient patterns
- **Edge Direction**: 
  - **Directed Graph**: Edges represent directional referral flow (NPI_1 → NPI_2)
  - **Undirected Graph**: Edges represent bidirectional relationships (currently using directed)
- **Edge Creation Logic**: 
  - An edge exists between two physicians if they share patients (Pair_Count > 0)
  - Multiple entries for the same pair are aggregated by summing weights

#### Edge Weights
Three weight options are available:
1. **Pair_Count** (default): Total number of shared patient encounters
   - Represents the strength of the referral relationship
   - Higher values indicate more frequent patient sharing
2. **Unique_Beneficiaries**: Number of unique patients shared
   - Indicates the breadth of the referral relationship
3. **Same_Day_Count**: Number of same-day encounters
   - May indicate direct referrals or coordinated care

#### Directionality
- **Current Implementation**: **Directed graph** (`directed=True`)
  - Direction represents referral flow: NPI_1 → NPI_2
  - Captures asymmetric referral patterns (physician A refers to B, but not necessarily vice versa)
- **Alternative**: Undirected graph available for symmetric relationship analysis

#### Duplicate Handling
- **Aggregation**: When multiple records exist for the same physician pair, edge weights are summed (`aggregate_duplicates=True`)
- This accounts for:
  - Multiple years of data
  - Multiple entries in source files
  - Temporal aggregation

### One-mode vs. Two-mode Networks

**Current Implementation: One-mode Network**
- **Type**: Physician-to-physician network
- **Nodes**: Physicians only
- **Edges**: Direct relationships between physicians
- **Rationale**: Focuses on direct referral relationships and physician collaboration patterns

**Potential Future Extension: Two-mode Network**
- Could include:
  - Physicians ↔ Patients (bipartite)
  - Physicians ↔ Healthcare Facilities
  - Physicians ↔ Specialties
- **Current Limitation**: Data structure focuses on physician pairs, not patient-level detail

### Metrics Applied and How They Link to Outcomes

#### Network-Level Metrics (Implemented)
1. **Basic Graph Statistics**:
   - Number of nodes (physicians)
   - Number of edges (referral relationships)
   - Edge weight statistics (min, max, mean, total)
   - Self-loop detection

2. **Geographic Analysis** (`compute_zip_referral_volume`):
   - **Outgoing Volume**: Total referrals sent from each ZIP code
   - **Incoming Volume**: Total referrals received by each ZIP code
   - **Total Volume**: Combined incoming and outgoing referrals
   - **Net Volume**: Difference between incoming and outgoing (positive = net receiver, negative = net sender)
   - **Outcome Link**: Identifies geographic hubs and referral flow patterns, which can inform:
     - Healthcare resource allocation
     - Identification of referral centers vs. referring communities
     - Regional healthcare access patterns

#### Node-Level Metrics (Available but not yet computed)
- **In-degree**: Number of physicians referring TO a given physician
  - *Outcome Link*: Identifies highly referred-to specialists or referral centers
- **Out-degree**: Number of physicians a given physician refers TO
  - *Outcome Link*: Identifies physicians who coordinate care across many specialists
- **Weighted in-degree**: Total volume of referrals received
  - *Outcome Link*: Measures referral importance/reputation
- **Weighted out-degree**: Total volume of referrals sent
  - *Outcome Link*: Measures care coordination activity

#### Network Structure Metrics (Available but not yet computed)
- **Centrality Measures**:
  - Betweenness centrality: Physicians who act as bridges in the network
  - Closeness centrality: Physicians with short paths to others
  - PageRank: Influence/importance in the referral network
- **Community Detection**:
  - Identify clusters of physicians who frequently refer to each other
  - May represent care teams, specialties, or geographic regions
- **Path Analysis**:
  - Average path length: How many steps between any two physicians
  - Diameter: Longest shortest path
  - *Outcome Link*: Understanding information flow and care coordination efficiency

---

## Results (Preliminary): Early Analyses, Tables, or Visualizations

### 1. Network Graph Construction

**Graph Characteristics**:
- **Type**: Directed graph
- **Weight Metric**: Pair_Count (shared patient encounters)
- **Format**: Saved as GraphML (`referral_network_directed.graphml`) for compatibility with visualization tools

### 2. Geographic Referral Volume Analysis

**ZIP Code Referral Statistics** (from `zip_referral_volume.csv`):

Top ZIP codes by total referral volume show significant variation:
- **95035**: Highest total volume (21,240,716), primarily outgoing (net sender)
- **32960**: High volume (1,121,379), balanced send/receive
- **29204**: High volume (845,916), primarily outgoing
- **90720**: Receives 497,209 referrals but sends 0 (pure referral center)
- **94598**: Receives 275,002 but sends only 19,321 (net receiver)

**Key Observations**:
- Some ZIP codes are **net senders** (negative Net_Volume): Act as referring communities
- Some ZIP codes are **net receivers** (positive Net_Volume): Act as referral centers/specialty hubs
- Geographic referral patterns reveal regional healthcare structures

### 3. Network Visualization

**Subgraph Visualization** (`graph_subset_visualization.png`):
- Created a 30-node subgraph starting from a high out-degree node
- Uses BFS (Breadth-First Search) to capture local network structure
- Visualized with:
  - Node size proportional to degree
  - Edge width proportional to weight (referral volume)
  - Directed arrows showing referral direction
  - Spring layout for node positioning

**Visualization Characteristics**:
- Demonstrates network structure and clustering
- Shows referral pathways and relationships
- Edge weights visually represent relationship strength

### 4. Data Processing Pipeline Results

**Processing Statistics**:
- Successfully extracted and combined DocGraph data from multiple years
- Successfully mapped NPIs to ZIP codes
- Successfully joined geographic data with referral patterns
- Successfully created and saved network graph

**Data Quality Metrics**:
- Rows with both ZIP codes present: Filtered dataset
- Self-loops detected: Some physicians referring to themselves (flagged)
- Missing data handled: Rows with missing ZIP codes filtered out

---

## Tools Used

### Primary Tools

1. **NetworkX (v3.3)**
   - Graph construction and manipulation
   - Graph statistics computation
   - Graph export (GraphML format)
   - Network analysis algorithms (available for future use)

2. **Pandas (v2.3.3)**
   - Data loading and processing
   - CSV file manipulation
   - Data joining and merging
   - Data aggregation

3. **Matplotlib (v3.10.7)**
   - Network visualization
   - Subgraph plotting
   - Figure generation and export

### Supporting Tools

4. **NumPy (v2.3.4)**
   - Numerical computations
   - Array operations for visualization

5. **tqdm (v4.67.1)**
   - Progress bars for long-running operations
   - User feedback during data processing

6. **OpenPyXL (v3.1.5)**
   - Excel file reading (for data source information)

### File Formats

- **Input**: 
  - Tab-separated text files (.txt) for DocGraph data
  - CSV files for NPI information
- **Output**: 
  - CSV files for processed data
  - GraphML format (.graphml) for network graphs
  - PNG images for visualizations

### Future Tool Considerations

- **Gephi**: For advanced network visualization and analysis
- **Cytoscape**: For interactive network exploration
- **Additional NetworkX algorithms**: For centrality, community detection, and path analysis

---

## Challenges: Problems Encountered and Possible Solutions

### 1. **Large File Size and Memory Constraints**

**Problem**: 
- DocGraph data files are extremely large (5+ GB each)
- Loading entire files into memory causes memory errors
- Processing multiple years compounds the issue

**Solution Implemented**:
- Implemented chunked reading (10,000 rows at a time)
- Added progress bars to track processing
- Limited processing to 500,000 rows for initial testing/development
- Used efficient data types (string for NPIs, integer for counts)

**Future Solutions**:
- Process files year-by-year and combine results
- Use database storage (SQLite) for intermediate results
- Implement streaming processing for very large datasets
- Use Dask or similar tools for distributed processing

### 2. **Missing Geographic Data**

**Problem**:
- Not all NPIs have associated ZIP codes in the NPI dataset
- Missing ZIP codes prevent geographic analysis
- Some postal codes are malformed or incomplete

**Solution Implemented**:
- Filtered out rows where either NPI_1 or NPI_2 lacks a ZIP code
- Extracted 5-digit ZIP codes from longer postal codes
- Prioritized rows with valid ZIP codes when multiple entries exist per NPI
- Provided statistics on ZIP code coverage

**Future Solutions**:
- Use alternative data sources for missing ZIP codes
- Implement fuzzy matching for incomplete postal codes
- Use provider address information as fallback
- Analyze patterns in missing data to understand bias

### 3. **Data Quality Issues**

**Problem**:
- Self-loops detected (physicians referring to themselves)
- Duplicate entries for same physician pairs
- Inconsistent data formats across years

**Solution Implemented**:
- Detected and flagged self-loops during graph creation
- Aggregated duplicate edges by summing weights
- Normalized data formats (string stripping, type conversion)
- Added data validation checks

**Future Solutions**:
- Investigate self-loops to determine if they represent data errors or valid patterns
- Implement more sophisticated duplicate detection
- Add data quality metrics and reporting
- Validate against known physician specialties and relationships

### 4. **Graph Visualization Challenges**

**Problem**:
- Full network too large to visualize effectively
- Standard layouts produce cluttered, unreadable visualizations
- Edge weights vary widely, making visualization difficult

**Solution Implemented**:
- Created subgraph visualizations (30 nodes) using BFS from high-degree nodes
- Adjusted layout parameters (k-value, iterations) for better spacing
- Scaled edge widths proportionally to weights
- Used directed arrows to show referral direction

**Future Solutions**:
- Implement hierarchical or clustered layouts
- Use edge filtering (threshold-based) to show only strong relationships
- Create multiple visualizations at different scales
- Export to Gephi/Cytoscape for interactive exploration
- Implement geographic layouts (map-based visualization)

### 5. **Processing Time and Efficiency**

**Problem**:
- Iterating through large DataFrames is slow
- Graph construction for large networks takes significant time
- Multiple file processing requires sequential execution

**Solution Implemented**:
- Used vectorized operations where possible
- Implemented progress bars for user feedback
- Optimized edge aggregation logic
- Chunked file reading

**Future Solutions**:
- Parallelize file processing across multiple years
- Use more efficient graph construction methods
- Cache intermediate results
- Optimize data types and memory usage
- Consider using graph databases for very large networks

### 6. **Limited Data Scope**

**Problem**:
- Currently processing only 500,000 rows for testing
- Only one year (2009) fully processed
- Missing temporal analysis capabilities

**Future Solutions**:
- Remove row limits and process full datasets
- Process multiple years for temporal analysis
- Implement time-windowed network analysis
- Track network evolution over time
- Compare referral patterns across years

### 7. **Network Analysis Depth**

**Problem**:
- Currently only computing basic statistics
- Missing advanced network metrics (centrality, communities, etc.)
- No outcome linkage yet established

**Future Solutions**:
- Implement centrality measures (betweenness, closeness, PageRank)
- Perform community detection to identify care teams
- Calculate path metrics (average path length, diameter)
- Link network metrics to healthcare outcomes
- Compare network structures across regions/specialties

---

## Next Steps

1. **Expand Data Processing**: Remove row limits and process full datasets across all available years
2. **Implement Network Metrics**: Compute centrality measures, community detection, and path analysis
3. **Temporal Analysis**: Compare networks across years to understand evolution
4. **Outcome Linkage**: Connect network metrics to healthcare outcomes (if outcome data available)
5. **Advanced Visualization**: Create geographic maps and interactive network visualizations
6. **Validation**: Validate network structures against known healthcare patterns and literature

---

*Report Generated: Based on current project state as of latest code review*

