import pandas as pd
from pathlib import Path
import baostock as bs

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
    
    # 获取 2024-01-05 的数据
    df_date = data[data['date'].str.contains('2024-01-05')].copy()
    df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
    
    print(f"2024-01-05 的股票数: {len(df_date)}")
    
    # 计算涨跌幅
    df_date['change_pct'] = df_date.groupby('symbol')['close'].pct_change() * 100
    
    # 获取行业分类
    lg = bs.login()
    if lg.error_code == '0':
        rs = bs.query_stock_industry()
        bs.logout()
        
        if rs.error_code == '0' and len(rs.data) > 0:
            industry_df = pd.DataFrame(rs.data, columns=rs.fields)
            print(f"行业分类数据: {len(industry_df)} 条")
            
            # 将股票代码转换为统一格式
            df_date['code'] = df_date['symbol'].apply(lambda x: f"sh.{x[2:].lower()}" if x.startswith('SH') else f"sz.{x[2:].lower()}")
            
            print("\n转换后的代码示例:")
            print(df_date[['symbol', 'code']].head(5))
            
            # 合并数据
            merged_df = pd.merge(df_date, industry_df[['code', 'industry']], on='code', how='left')
            
            print(f"\n合并后的数据数: {len(merged_df)}")
            print(f"有行业分类的股票数: {len(merged_df[merged_df['industry'].notna() & (merged_df['industry'] != '')])}")
            
            # 过滤掉没有行业分类的股票
            merged_df = merged_df[merged_df['industry'].notna() & (merged_df['industry'] != '')]
            
            print(f"过滤后的数据数: {len(merged_df)}")
            
            # 按行业分组统计
            sector_stats = merged_df.groupby('industry').agg({
                'change_pct': 'mean',
                'symbol': 'count'
            }).reset_index()
            sector_stats.columns = ['industry', 'avg_change_pct', 'stock_count']
            
            # 排序
            sector_stats = sector_stats.sort_values('avg_change_pct', ascending=False)
            
            print(f"\n行业板块数: {len(sector_stats)}")
            print("\n涨幅榜 TOP10:")
            for i, row in sector_stats.head(10).iterrows():
                print(f"  {i+1}. {row[1]['industry']}: {row[1]['avg_change_pct']:.2f}% | 股票数: {row[1]['stock_count']}")
            
            print("\n跌幅榜 TOP10:")
            for i, row in sector_stats.sort_values('avg_change_pct', ascending=True).head(10).iterrows():
                print(f"  {i+1}. {row[1]['industry']}: {row[1]['avg_change_pct']:.2f}% | 股票数: {row[1]['stock_count']}")
