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


if __name__ == "__main__":
    # Example usage
    df = get_industry_data()
    print(f"Loaded {len(df)} stocks")
    print(df.head())
    print(f"Unique industries: {df['industry'].nunique()}")
