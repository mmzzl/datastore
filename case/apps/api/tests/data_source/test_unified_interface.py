import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, api_dir)

print(f"Added to path: {api_dir}")
print(f"Python version: {sys.version}")

def test_unified_interface():
    """测试统一数据源接口"""
    from app.data_source import DataSourceManager, StockKLine, StockInfo
    
    # 创建数据源管理器
    manager = DataSourceManager()
    
    print(f"数据源管理器创建成功")
    print(f"可用数据源: {list(manager._adapters.keys())}")
    
    # 测试获取股票列表
    stocks = manager.get_stock_list(provider="baostock")
    print(f"获取到 {len(stocks)} 只股票")
    
    if stocks:
        sample_stock = stocks[0]
        print(f"示例股票: {sample_stock.code} - {sample_stock.name}")
        
        # 测试获取K线数据
        klines = manager.get_kline(
            code=sample_stock.code,
            start_date="2026-03-01",
            end_date="2026-03-17",
            provider="baostock"
        )
        print(f"获取到 {len(klines)} 条K线数据")
        
        if klines:
            sample_kline = klines[0]
            print(f"示例K线: {sample_kline.date} 收盘价: {sample_kline.close}")
    
    print("\n统一数据源接口测试通过！")

if __name__ == "__main__":
    test_unified_interface()
