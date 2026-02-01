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
    
    # 获取最新日期
    latest_date = data['date'].max()
    print(f"最新日期: {latest_date}")
    
    # 筛选最新日期的数据
    df_date = data[data['date'] == latest_date].copy()
    
    print(f"最新日期的记录数（去重前）: {len(df_date)}")
    
    # 去重
    df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
    print(f"最新日期的记录数（去重后）: {len(df_date)}")
    
    # 计算涨跌幅
    df_date['change_pct'] = df_date.groupby('symbol')['close'].pct_change() * 100
    
    # 统计
    up_count = len(df_date[df_date['change_pct'] > 0])
    down_count = len(df_date[df_date['change_pct'] < 0])
    flat_count = len(df_date[df_date['change_pct'] == 0])
    
    print(f"\n统计结果:")
    print(f"  上涨: {up_count}")
    print(f"  下跌: {down_count}")
    print(f"  平盘: {flat_count}")
    print(f"  总计: {up_count + down_count + flat_count}")
