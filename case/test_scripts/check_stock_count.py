import pandas as pd
from pathlib import Path

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 统计文件数
csv_files = list(csv_dir.glob("*.csv"))
print(f"CSV文件总数: {len(csv_files)}")

# 加载所有数据并统计唯一股票数
all_symbols = set()
for csv_file in csv_files:
    try:
        df = pd.read_csv(csv_file)
        if not df.empty and 'symbol' in df.columns:
            symbols = df['symbol'].unique()
            all_symbols.update(symbols)
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")

print(f"唯一股票数: {len(all_symbols)}")

# 检查是否有重复文件
symbol_files = {}
for csv_file in csv_files:
    symbol = csv_file.stem
    if symbol in symbol_files:
        print(f"重复文件: {symbol}")
    else:
        symbol_files[symbol] = csv_file

print(f"\n文件中的唯一股票数: {len(symbol_files)}")

# 检查数据完整性
print("\n检查数据完整性...")
sample_files = csv_files[:10]
for csv_file in sample_files:
    try:
        df = pd.read_csv(csv_file)
        print(f"{csv_file.name}: {len(df)} 行, 日期范围: {df['date'].min()} 到 {df['date'].max()}")
    except Exception as e:
        print(f"{csv_file.name}: 错误 - {e}")
