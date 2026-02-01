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
    
    # 检查日期范围
    print(f"\n日期范围:")
    print(f"  最早: {data['date'].min()}")
    print(f"  最晚: {data['date'].max()}")
    
    # 检查是否还有 2026 年的数据
    data_2026 = data[data['date'].astype(str).str.contains('2026')]
    print(f"\n2026 年的数据: {len(data_2026)} 条")
    
    if len(data_2026) > 0:
        print("警告：过滤失败！仍有 2026 年的数据")
        print(data_2026[['symbol', 'date']].head(5))
