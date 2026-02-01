import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 加载所有数据
all_data = []
for csv_file in csv_dir.glob("*.csv"):
    try:
        df = pd.read_csv(csv_file)
        if not df.empty:
            all_data.append(df)
    except Exception as e:
        pass

if all_data:
    data = pd.concat(all_data, ignore_index=True)
    
    # 检查 2026-01-30 的数据
    df_date = data[data['date'].astype(str).str[:10] == '2026-01-30'].copy()
    print(f"2026-01-30 的数据行数: {len(df_date)}")
    print(f"唯一股票数: {df_date['symbol'].nunique()}")
    print(f"重复股票数: {len(df_date) - df_date['symbol'].nunique()}")
    
    # 检查前10个股票的重复情况
    print(f"\n前10个股票的重复情况:")
    for symbol in df_date['symbol'].unique()[:10]:
        count = len(df_date[df_date['symbol'] == symbol])
        print(f"  {symbol}: {count} 条")
