# Referral Networks Analysis

This project processes physician shared patient pattern data from multiple years to analyze referral networks.

## Setup

### Prerequisites

- Python 3.13 (or compatible version)
- pip

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd referral-networks
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

The data files for this project are large (several GB each) and are not included in the repository.

**To obtain the data files:**
1. Open the Excel file `data/DocGraph_Teaming_Data_revised.xlsx`
2. The file contains download links for all required data files
3. Download the physician shared patient pattern files (`.txt` format) for the years you need
4. Place the downloaded `.txt` files in the `data/` folder

The expected file naming format is: `physician-shared-patient-patterns-YYYY-days180.txt` (e.g., `physician-shared-patient-patterns-2009-days180.txt`)

## Usage

Once you have the data files in the `data/` folder, run the extraction script:

```bash
python extract.py
```

The script will:
- Load all `.txt` files from the `data/` folder
- Process them in chunks to handle large file sizes efficiently
- Display progress bars for each file
- Combine all data into a single DataFrame
- Display a preview of the combined data

## Output

The script processes physician shared patient patterns and creates a combined dataset with the following columns:
- `NPI_1`: First physician NPI (National Provider Identifier)
- `NPI_2`: Second physician NPI
- `Pair_Count`: Number of shared patient encounters
- `Unique_Beneficiaries`: Number of unique beneficiaries shared
- `Same_Day_Count`: Number of same-day encounters
- `Source_File`: Source file name for tracking

## Notes

- The data files are very large (5+ GB each), so processing may take some time
- The script uses chunked reading to efficiently handle large files
- Progress bars will show the reading progress for each file

