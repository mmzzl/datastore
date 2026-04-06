import sys

sys.path.insert(0, "D:/work/datastore/apps/api")

print("Testing StockSelectionEngine...")
from app.stock_selection.engine import StockSelectionEngine

engine = StockSelectionEngine()
print(f"Done. Check the backend logs for the connection test.")
