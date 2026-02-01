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
    
    # 获取所有唯一日期
    unique_dates = sorted(data['date'].astype(str).str[:10].unique())
    print(f"所有日期（共 {len(unique_dates)} 个）:")
    for date in unique_dates[-20:]:  # 显示最后20个日期
        print(f"  {date}")
    
    print(f"\n最新日期: {unique_dates[-1]}")
    
    # 检查最新日期的数据量
    latest_date = unique_dates[-1]
    df_latest = data[data['date'].astype(str).str[:10] == latest_date].copy()
    print(f"最新日期 {latest_date} 的数据:")
    print(f"  数据行数: {len(df_latest)}")
    print(f"  唯一股票数: {df_latest['symbol'].nunique()}")
