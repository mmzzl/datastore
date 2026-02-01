import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 加载所有数据（模拟 load_all_data 的逻辑）
all_data = []
for csv_file in csv_dir.glob("*.csv"):
    try:
        df = pd.read_csv(csv_file)
        if not df.empty:
            # 过滤掉 2026 年的错误数据
            if 'date' in df.columns:
                df = df[~df['date'].astype(str).str.contains('2026')]
            all_data.append(df)
    except Exception as e:
        pass

if all_data:
    data = pd.concat(all_data, ignore_index=True)
    
    print(f"总数据行数: {len(data)}")
    
    # 获取最新日期
    latest_date = data['date'].max()
    print(f"最新日期: {latest_date}")
    print(f"最新日期类型: {type(latest_date)}")
    
    # 检查是否还有 2026 年的数据
    data_2026 = data[data['date'].astype(str).str.contains('2026')]
    print(f"2026 年的数据: {len(data_2026)} 条")
