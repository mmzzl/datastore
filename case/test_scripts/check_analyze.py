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
    
    # 检查 2024-01-05 的数据
    df_date = data[data['date'].astype(str).str.contains('2024-01-05')].copy()
    print(f"2024-01-05 的数据行数: {len(df_date)}")
    
    if not df_date.empty:
        print(f"列名: {df_date.columns.tolist()}")
        print(f"前5行数据:")
        print(df_date[['symbol', 'date', 'close']].head())
    else:
        print("没有找到 2024-01-05 的数据")
        print(f"所有日期（前10个）:")
        print(data['date'].unique()[:10])
