import pandas as pd
from pathlib import Path
import baostock as bs

csv_dir = Path(r'C:\Users\life8\.qlib\stock_data\source\all_1d_original')

# 加载一个股票文件
df = pd.read_csv(csv_dir / 'SH600000.csv')
df = df[~df['date'].astype(str).str.contains('2026')]
df_2024 = df[df['date'].str.contains('2024-01-05')]

print("CSV 中的数据格式:")
print(df_2024[['symbol', 'date', 'close']])

# 获取行业分类
lg = bs.login()
if lg.error_code == '0':
    rs = bs.query_stock_industry()
    bs.logout()
    
    if rs.error_code == '0' and len(rs.data) > 0:
        industry_df = pd.DataFrame(rs.data, columns=rs.fields)
        
        print("\n行业分类数据格式:")
        print(industry_df[['code', 'code_name', 'industry']].head(5))
        
        # 查找 SH600000
        sh600000 = industry_df[industry_df['code'] == 'sh.600000']
        print(f"\n查找 sh.600000: {len(sh600000)} 条")
        
        # 查找 sh.600000
        sh600000_lower = industry_df[industry_df['code'] == 'sh.600000']
        print(f"查找 sh.600000 (lower): {len(sh600000_lower)} 条")
        
        # 查找 SH600000
        sh600000_upper = industry_df[industry_df['code'] == 'SH600000']
        print(f"查找 SH600000 (upper): {len(sh600000_upper)} 条")
