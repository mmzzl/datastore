# Stock Industry Data Fetcher

使用 baostock 库获取A股股票行业分类数据。

## 触发条件

当用户需要以下功能时触发此skill：
- 获取A股股票行业分类数据
- 查询股票所属板块/行业
- 批量获取股票行业信息
- 使用 baostock 库获取股票数据

## 核心功能

1. 检查本地是否存在缓存的CSV文件
2. 如无缓存，调用 baostock API 获取行业分类数据
3. 保存数据到CSV文件
4. 读取CSV并转换为 pandas DataFrame 返回

## 使用方法

```python
from stock_industry_skill import get_industry_data

# 获取行业数据（自动处理缓存）
df = get_industry_data()
print(df.head())
```

## 实现代码

```python
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
```

## 数据字段说明

| 字段 | 说明 |
|------|------|
| code | 股票代码 (sh.600000) |
| code_name | 股票名称 |
| industry | 所属行业 |
| industryClassification | 行业分类 |
| updateDate | 更新日期 |

## 依赖

```bash
pip install baostock pandas
```
