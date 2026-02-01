import pandas as pd
from pathlib import Path
from scripts.daily_brief_analyzer import DailyBriefAnalyzer

csv_dir = r'C:\Users\life8\.qlib\stock_data\source\all_1d_original'

analyzer = DailyBriefAnalyzer(csv_dir)

# 检查数据中的日期
print(f"数据中的日期范围:")
print(f"  最小: {analyzer.data['date'].min()}")
print(f"  最大: {analyzer.data['date'].max()}")

# 检查 get_latest_date()
latest_date = analyzer.get_latest_date()
print(f"\nget_latest_date() 返回: {latest_date}")

# 检查是否有 2026 年的数据
data_2026 = analyzer.data[analyzer.data['date'].astype(str).str.contains('2026')]
print(f"2026 年的数据: {len(data_2026)} 条")
