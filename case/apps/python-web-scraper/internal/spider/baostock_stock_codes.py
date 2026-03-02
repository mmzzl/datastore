import baostock as bs
import pandas as pd
import os
import logging
from ..utils.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_stock_codes():
    """获取所有A股股票代码"""
    config = load_config()
    stock_codes_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        config['storage']['stock_codes_file']
    )
    
    os.makedirs(os.path.dirname(stock_codes_file), exist_ok=True)
    
    if os.path.exists(stock_codes_file):
        logger.info(f"股票代码文件已存在: {stock_codes_file}")
        df = pd.read_csv(stock_codes_file)
        return df
    
    logger.info("开始获取A股股票代码...")
    lg = bs.login()
    logger.info(f"登录返回: {lg.error_code} - {lg.error_msg}")
    
    rs = bs.query_stock_industry()
    
    if rs.error_code != '0':
        logger.error(f"获取股票代码失败: {rs.error_msg}")
        bs.logout()
        return pd.DataFrame()
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    bs.logout()
    
    if data_list:
        df = pd.DataFrame(data_list, columns=['date', 'code', 'name', 'industry', 'industry_type'])
        df = df[['code', 'name']]
        df.to_csv(stock_codes_file, index=False, encoding='utf-8')
        logger.info(f"股票代码已保存到: {stock_codes_file}, 共 {len(df)} 只股票")
        return df
    else:
        logger.error("获取股票代码失败: 返回数据为空")
        return pd.DataFrame()


def load_stock_codes():
    """加载股票代码"""
    config = load_config()
    stock_codes_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        config['storage']['stock_codes_file']
    )
    
    if os.path.exists(stock_codes_file):
        df = pd.read_csv(stock_codes_file)
        return df
    else:
        return get_stock_codes()


if __name__ == '__main__':
    get_stock_codes()
