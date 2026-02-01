import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 检查前10个文件
csv_files = list(csv_dir.glob("*.csv"))[:10]

for csv_file in csv_files:
    try:
        df = pd.read_csv(csv_file)
        print(f"\n{csv_file.name} 的列名:")
        print(df.columns.tolist())
        print(f"\n前3行数据:")
        print(df.head(3))
        break
    except Exception as e:
        print(f"Error: {e}")
