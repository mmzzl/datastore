---
name: stock-industry-classification
description: Fetches A-share stock industry classification data using baostock API. Use this skill whenever the user needs to get stock industry data, check stock classifications, or retrieve sector information for Chinese stocks. Automatically handles caching by checking for existing CSV files and only fetching fresh data when needed.
---

# Stock Industry Classification Skill

This skill fetches A-share stock industry classification data using the baostock library. It automatically handles caching by checking for existing CSV files and only fetching fresh data from the API when needed.

## Core Functionality

1. **Check for cached CSV file**: Looks for existing industry data file
2. **Fetch from API if needed**: Uses baostock API to get fresh industry classification data
3. **Save to CSV**: Stores data locally for future use
4. **Return DataFrame**: Provides data as a pandas DataFrame for easy analysis

## Usage

When the user asks for:
- Stock industry classification data
- A-share sector information
- Stock classification lookup
- Industry data for Chinese stocks

The skill will:
1. Check if the CSV file exists at the specified path
2. If it exists, read from the CSV and return DataFrame
3. If not, fetch from baostock API, save to CSV, and return DataFrame

## Implementation

```python
import os
import baostock as bs
import pandas as pd

def get_industry_data(csv_path: str = "D:/stock_industry.csv") -> pd.DataFrame:
    """
    Get A-share stock industry classification data
    
    Args:
        csv_path: Path to save/read CSV file
        
    Returns:
        pandas DataFrame with stock industry classification data
    """
    # Check if CSV file exists
    if os.path.exists(csv_path):
        print(f"Reading cached file: {csv_path}")
        df = pd.read_csv(csv_path, encoding="gbk")
        return df
    
    # Login to baostock
    print("Logging into baostock...")
    lg = bs.login()
    if lg.error_code != '0':
        raise Exception(f"Login failed: {lg.error_msg}")
    print(f"Login successful: {lg.error_msg}")
    
    # Get industry classification data
    print("Fetching industry classification data...")
    rs = bs.query_stock_industry()
    if rs.error_code != '0':
        bs.logout()
        raise Exception(f"Query failed: {rs.error_msg}")
    
    # Parse results
    industry_list = []
    while rs.next():
        industry_list.append(rs.get_row_data())
    
    result = pd.DataFrame(industry_list, columns=rs.fields)
    
    # Save to CSV
    result.to_csv(csv_path, encoding="gbk", index=False)
    print(f"Data saved to: {csv_path}")
    
    # Logout
    bs.logout()
    print("Logged out from baostock")
    
    return result
```

## Data Fields

The returned DataFrame contains the following columns:

| Column | Description |
|--------|-------------|
| code | Stock code (e.g., sh.600000) |
| code_name | Stock name |
| industry | Industry classification |
| industryClassification | Industry category |
| updateDate | Last update date |

## Dependencies

```bash
pip install baostock pandas
```

## Error Handling

The skill includes robust error handling:
- Checks baostock login status
- Validates API response codes
- Handles file I/O errors
- Provides clear error messages

## Example Usage

```python
# Get industry data (automatically handles caching)
df = get_industry_data()
print(df.head())

# Get data for specific stock
stock_data = df[df['code'] == 'sh.600000']
print(stock_data)

# Count stocks per industry
industry_counts = df['industry'].value_counts()
print(industry_counts.head())
```

## When to Use This Skill

Use this skill whenever the user needs:
- A-share stock industry classification data
- Sector information for Chinese stocks
- Stock classification lookup
- Industry data analysis for Chinese market
- Cached industry data to avoid repeated API calls
