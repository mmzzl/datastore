import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 加载所有数据
all_data = []
for csv_file in csv_dir.glob("*.csv"):
    try:
        df = pd.read_csv(csv_file)
        if not df.empty:
            if 'date' in df.columns:
                df = df[~df['date'].astype(str).str.contains('2026')]
            all_data.append(df)
    except Exception as e:
        pass

if all_data:
    data = pd.concat(all_data, ignore_index=True)
    
    # 获取所有唯一日期
    unique_dates = data['date'].astype(str).str[:10].unique()
    print(f"所有日期（共 {len(unique_dates)} 个）:")
    for date in sorted(unique_dates):
        print(f"  {date}")
    
    print(f"\n最新日期: {sorted(unique_dates)[-1]}")
