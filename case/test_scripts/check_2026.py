import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 检查前10个文件
csv_files = list(csv_dir.glob("*.csv"))

for csv_file in csv_files[:10]:
    try:
        df = pd.read_csv(csv_file)
        if 'date' in df.columns:
            dates = df['date'].astype(str).str[:10].unique()
            if any('2026' in d for d in dates):
                print(f"{csv_file.name}: {dates}")
    except:
        pass
