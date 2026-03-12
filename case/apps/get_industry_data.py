import os
import baostock as bs
import pandas as pd

def get_industry_data(csv_path: str = "D:/stock_industry.csv") -> pd.DataFrame:
    """
    获取A股股票行业分类数据
    
    Args:
        csv_path: CSV文件保存路径
        
    Returns:
        pandas DataFrame，包含股票行业分类数据
    """
    # 检查CSV文件是否存在
    if os.path.exists(csv_path):
        print(f"读取缓存文件: {csv_path}")
        df = pd.read_csv(csv_path, encoding="gbk")
        return df
    
    # 登录baostock
    print("正在登录 baostock...")
    lg = bs.login()
    if lg.error_code != '0':
        raise Exception(f"登录失败: {lg.error_msg}")
    print(f"登录成功: {lg.error_msg}")
    
    # 获取行业分类数据
    print("正在获取行业分类数据...")
    rs = bs.query_stock_industry()
    if rs.error_code != '0':
        bs.logout()
        raise Exception(f"查询失败: {rs.error_msg}")
    
    # 解析结果
    industry_list = []
    while rs.next():
        industry_list.append(rs.get_row_data())
    
    result = pd.DataFrame(industry_list, columns=rs.fields)
    
    # 保存到CSV
    result.to_csv(csv_path, encoding="gbk", index=False)
    print(f"数据已保存到: {csv_path}")
    
    # 登出
    bs.logout()
    print("已登出 baostock")
    
    return result

def get_stocks_by_industry(industry_name: str, csv_path: str = "D:/stock_industry.csv") -> list:
    """根据行业名称获取股票代码列表
    
    Args:
        industry_name: 行业名称，如 "能源"、"人工智能" 等
        csv_path: CSV文件路径
        
    Returns:
        股票代码列表
    """
    # 获取行业数据
    df = get_industry_data(csv_path)
    
    # 模糊匹配行业名称
    matched_stocks = df[df['industry'].str.contains(industry_name, na=False)]
    
    if matched_stocks.empty:
        print(f"未找到包含 '{industry_name}' 的行业")
        return []
    
    print(f"找到 {len(matched_stocks)} 只股票")
    return matched_stocks['code'].tolist()

def get_all_industries(csv_path: str = "D:/stock_industry.csv") -> list:
    """获取所有行业列表
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        行业名称列表
    """
    df = get_industry_data(csv_path)
    return df['industry'].unique().tolist()

def test_industry():
    """测试行业数据获取"""
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
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_industry()
