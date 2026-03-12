import sys
import os

sys.path.insert(0, r'C:\Users\life8\.trae-cn\skills\stock_industry_skill')

from stock_industry_skill import get_industry_data

def get_stocks_by_industry(industry_name: str = None):
    """根据行业名称获取股票代码
    
    Args:
        industry_name: 行业名称，如 "能源"、"人工智能" 等
    """
    try:
        # 获取行业数据
        df = get_industry_data()
        
        print(f"总共获取到 {len(df)} 条行业分类数据")
        print("\n数据字段:", df.columns.tolist())
        print("\n前10条数据:")
        print(df.head(10))
        
        # 显示所有行业
        print("\n所有行业列表:")
        industries = df['industry'].unique()
        for i, ind in enumerate(industries[:20], 1):
            print(f"{i}. {ind}")
        print(f"... 共 {len(industries)} 个行业")
        
        # 如果指定了行业名称，筛选该行业的股票
        if industry_name:
            print(f"\n筛选行业: {industry_name}")
            
            # 模糊匹配行业名称
            matched_stocks = df[df['industry'].str.contains(industry_name, na=False)]
            
            if matched_stocks.empty:
                print(f"未找到包含 '{industry_name}' 的行业")
                return []
            
            print(f"找到 {len(matched_stocks)} 只股票")
            print("\n股票列表:")
            for _, row in matched_stocks.iterrows():
                print(f"  {row['code']} - {row['code_name']} - {row['industry']}")
            
            return matched_stocks['code'].tolist()
        
        return []
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='根据行业获取股票代码')
    parser.add_argument('--industry', type=str, help='行业名称')
    
    args = parser.parse_args()
    
    if args.industry:
        get_stocks_by_industry(args.industry)
    else:
        get_stocks_by_industry()
