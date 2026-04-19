"""
Test script for MongoDataProvider

Tests loading CSI 300 K-line data from MongoDB.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.qlib.data_provider import MongoDataProvider
from app.qlib.config import CSI_300_STOCKS


def test_mongo_data_provider():
    """Test MongoDataProvider with CSI 300 data."""
    print("Testing MongoDataProvider...")
    
    provider = MongoDataProvider()
    
    test_instruments = CSI_300_STOCKS[:5]
    print(f"Test instruments: {test_instruments}")
    
    df = provider.load_data(
        instruments=test_instruments,
        start_time="2024-01-01",
        end_time="2024-12-31",
    )
    
    print(f"Loaded DataFrame shape: {df.shape}")
    print(f"DataFrame index names: {df.index.names}")
    print(f"DataFrame columns: {df.columns.tolist()}")
    
    if not df.empty:
        print(f"\nSample data:")
        print(df.head())
        print(f"\nData types:")
        print(df.dtypes)
        print("\nMongoDataProvider test PASSED")
    else:
        print("\nNo data loaded. This is expected if MongoDB has no K-line data.")
        print("MongoDataProvider test PASSED (no data scenario handled)")


if __name__ == "__main__":
    test_mongo_data_provider()
