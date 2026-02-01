import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 检查 2024-01-05 的数据
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
    
    # 检查 2024-01-05 的数据
    df_date = data[data['date'].astype(str).str[:10] == '2024-01-05'].copy()
    print(f"2024-01-05 的数据行数: {len(df_date)}")
    print(f"唯一股票数: {df_date['symbol'].nunique()}")
    
    # 检查前10个股票
    print(f"\n前10个股票:")
    for symbol in df_date['symbol'].unique()[:10]:
        print(f"  {symbol}")
