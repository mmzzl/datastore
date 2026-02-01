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
    
    # 检查 2026-01-28 的数据
    df_28 = data[data['date'].astype(str).str[:10] == '2026-01-28'].copy()
    print(f"2026-01-28 的数据:")
    print(f"  数据行数: {len(df_28)}")
    print(f"  唯一股票数: {df_28['symbol'].nunique()}")
    
    # 检查 2026-01-29 的数据
    df_29 = data[data['date'].astype(str).str[:10] == '2026-01-29'].copy()
    print(f"\n2026-01-29 的数据:")
    print(f"  数据行数: {len(df_29)}")
    print(f"  唯一股票数: {df_29['symbol'].nunique()}")
    
    # 检查某个股票是否有连续两天的数据
    symbol = 'SH600000'
    df_symbol = data[data['symbol'] == symbol].copy()
    df_symbol['date_short'] = df_symbol['date'].astype(str).str[:10]
    print(f"\n股票 {symbol} 的日期:")
    print(df_symbol[['date_short', 'close']].tail(10))
