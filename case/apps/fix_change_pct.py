import pandas as pd
import logging
from datetime import datetime
from pymongo import MongoClient
import yaml
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'api', 'config.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        return config_data
    else:
        logger.error(f"配置文件不存在: {config_path}")
        return {}


def fix_change_pct_from_mongodb():
    """从 MongoDB 中修复涨跌幅"""
    try:
        # 加载配置
        config = load_config()
        mongodb_config = config.get('mongodb', {})
        
        # 连接 MongoDB
        logger.info(f"连接 MongoDB: {mongodb_config.get('host')}:{mongodb_config.get('port')}")
        client = MongoClient(
            host=mongodb_config.get('host', 'localhost'),
            port=mongodb_config.get('port', 27017),
            username=mongodb_config.get('username', ''),
            password=mongodb_config.get('password', ''),
        )
        db = client[mongodb_config.get('database', 'eastmoney_news')]
        kline_collection = db[mongodb_config.get('kline_collection', 'stock_kline')]
        
        # 获取所有股票代码
        logger.info("获取所有股票代码...")
        stock_codes = kline_collection.distinct('code')
        logger.info(f"共找到 {len(stock_codes)} 只股票")
        
        total_updated = 0
        total_processed = 0
        
        # 遍历每只股票
        for idx, code in enumerate(stock_codes, 1):
            try:
                # 获取该股票的所有 K 线数据
                cursor = kline_collection.find({'code': code}).sort('date', 1)
                klines = list(cursor)
                
                if len(klines) < 2:
                    logger.debug(f"股票 {code} 数据不足，跳过")
                    continue
                
                # 转换为 DataFrame
                df = pd.DataFrame(klines)
                
                # 确保日期格式正确
                df['date'] = pd.to_datetime(df['date'])
                
                # 按日期排序
                df = df.sort_values('date')
                
                # 记录原始涨跌幅统计
                if 'pct_chg' in df.columns:
                    original_zero_count = (df['pct_chg'] == 0).sum()
                    logger.debug(f"{code} 原始涨跌幅为0的记录数: {original_zero_count}")
                
                # 计算涨跌幅（相对于前一天）
                df['pct_chg'] = df['close'].pct_change() * 100
                df['pct_chg'] = df['pct_chg'].fillna(0)
                
                # 记录修复后的涨跌幅统计
                fixed_zero_count = (df['pct_chg'] == 0).sum()
                non_zero_count = (df['pct_chg'] != 0).sum()
                
                logger.debug(f"{code} 修复后涨跌幅为0: {fixed_zero_count}, 不为0: {non_zero_count}")
                
                # 更新 MongoDB
                updated_count = 0
                for _, row in df.iterrows():
                    kline_collection.update_one(
                        {'_id': row['_id']},
                        {'$set': {'pct_chg': row['pct_chg']}}
                    )
                    updated_count += 1
                
                total_updated += updated_count
                total_processed += 1
                
                if idx % 100 == 0:
                    logger.info(f"进度: {idx}/{len(stock_codes)}, 已更新 {total_updated} 条记录")
                
            except Exception as e:
                logger.error(f"处理股票 {code} 失败: {e}")
                continue
        
        # 关闭连接
        client.close()
        
        logger.info("=" * 60)
        logger.info(f"涨跌幅修复完成！")
        logger.info(f"共处理 {total_processed} 只股票")
        logger.info(f"共更新 {total_updated} 条记录")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"修复涨跌幅失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("MongoDB 涨跌幅修复脚本")
    logger.info("=" * 60)
    
    result = fix_change_pct_from_mongodb()
    
    if result:
        logger.info("涨跌幅修复成功！")
    else:
        logger.error("涨跌幅修复失败！")
    
    logger.info("=" * 60)
