import scrapy
import logging
import time
import os
import pandas as pd
from datetime import datetime, timedelta
from ..utils.config import load_config
from ..storage.mongo_storage import MongoStorage

logger = logging.getLogger(__name__)


class AkshareKlineSpider(scrapy.Spider):
    name = 'akshare_kline'
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 60,
    }
    
    def __init__(self, *args, **kwargs):
        super(AkshareKlineSpider, self).__init__(*args, **kwargs)
        self.config = load_config()
        self.storage = MongoStorage()
        
        # 获取 apps 目录（stock_zh_a_spot.csv 所在目录）
        # file__ = .../python-web-scraper/internal/spider/akshare_kline_spider.py
        # 需要向上 4 层到 apps 目录
        apps_root = os.path.dirname(os.path.dirname(__file__))
        logger.info("apps_root: %s", apps_root)
        self.spot_csv_file = os.path.join(apps_root, 'stock_zh_a_spot.csv')
        
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.today_str = datetime.now().strftime('%Y%m%d')
        self.processed_count = 0
        self.skip_count = 0
        self.error_count = 0
        
        collector_config = self.config.get('akshare_kline', {})
        self.batch_size = collector_config.get('batch_size', 50)
        self.default_days = collector_config.get('default_days', 30)
    
    def start_requests(self):
        stock_list = self._load_stock_list()
        if stock_list.empty:
            logger.error("没有股票代码，退出")
            return
        
        logger.info(f"开始处理 {len(stock_list)} 只股票，每批 {self.batch_size} 只")
        
        total = len(stock_list)
        for i in range(0, total, self.batch_size):
            batch = stock_list.iloc[i:min(i+self.batch_size, total)]
            logger.info(f"处理第 {i//self.batch_size + 1} 批股票 ({i+1}-{min(i+self.batch_size, total)})")
            
            for _, row in batch.iterrows():
                symbol = row['symbol']
                name = row['name']
                
                # 直接处理每只股票，不使用 scrapy.Request
                self._process_stock(symbol, name)
            
            logger.info(f"采集任务进度: 已处理 {self.processed_count} 只, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")
            
            # 每批处理完后延迟，避免请求过快
            time.sleep(2)
    
    def _process_stock(self, symbol, name):
        """处理单个股票"""
        import akshare as ak  # 延迟导入，避免 atexit 冲突
        try:
            # 获取数据库中最新的日期
            latest_date = self.storage.get_latest_kline_date(symbol)
            
            # 确定开始和结束日期
            if latest_date:
                latest_date_obj = datetime.strptime(latest_date, "%Y-%m-%d")
                
                # 如果最新日期已经是今天，跳过
                if latest_date_obj.strftime('%Y-%m-%d') >= self.today:
                    logger.info(f"跳过 {symbol}({name}): 已采集到最新日期 {latest_date}")
                    self.skip_count += 1
                    return
                
                # 从最新日期的下一天开始
                start_date = (latest_date_obj + timedelta(days=1)).strftime('%Y%m%d')
                end_date = self.today_str
                logger.info(f"增量更新 {symbol}({name}): {start_date} - {end_date}")
            else:
                # 没有历史数据，获取最近一个月的数据
                start_date = (datetime.now() - timedelta(days=self.default_days)).strftime('%Y%m%d')
                end_date = self.today_str
                logger.info(f"首次采集 {symbol}({name}): {start_date} - {end_date}")
            
            # 转换股票代码格式
            ak_symbol = symbol.replace('.', '')
            
            # 获取历史数据
            historical_df = ak.stock_zh_a_daily(
                symbol=ak_symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if historical_df.empty:
                logger.warning(f"无K线数据 {symbol}({name})")
                self.skip_count += 1
                return
            
            # 转换数据格式
            klines = self._convert_to_klines(symbol, name, historical_df)
            
            # 保存到数据库
            inserted, skipped = self.storage.save_kline(symbol, klines)
            
            if inserted > 0:
                self.processed_count += 1
                logger.info(f"成功采集 {symbol}({name}): {len(klines)} 条数据, 新增: {inserted}, 跳过: {skipped}")
            else:
                logger.info(f"数据已存在 {symbol}({name}): 跳过 {skipped} 条")
                self.skip_count += 1
                
        except Exception as e:
            logger.error(f"处理股票失败 {symbol}({name}): {e}")
            self.error_count += 1
    
    def _load_stock_list(self):
        """从 stock_zh_a_spot.csv 文件中读取股票列表"""
        import akshare as ak  # 延迟导入，避免 atexit 冲突
        try:
            logger.info(f"从 {self.spot_csv_file} 读取股票列表...")
            
            if not pd.io.common.file_exists(self.spot_csv_file):
                logger.warning(f"{self.spot_csv_file} 文件不存在，尝试使用 API 获取")
                stock_list_df = ak.stock_zh_a_spot_em()
                return stock_list_df[['代码', '名称']].rename(columns={'代码': 'symbol', '名称': 'name'})
            
            stock_list_df = pd.read_csv(self.spot_csv_file)
            
            # 检查文件中是否有必要的列
            if 'symbol' in stock_list_df.columns and 'name' in stock_list_df.columns:
                logger.info(f"从文件中读取到 {len(stock_list_df)} 只股票")
                return stock_list_df[['symbol', 'name']].drop_duplicates()
            elif '代码' in stock_list_df.columns and '名称' in stock_list_df.columns:
                logger.info(f"从文件中读取到 {len(stock_list_df)} 只股票（使用旧列名）")
                return stock_list_df[['代码', '名称']].rename(columns={'代码': 'symbol', '名称': 'name'}).drop_duplicates()
            else:
                logger.warning(f"{self.spot_csv_file} 文件格式不正确，使用 API 获取股票列表")
                stock_list_df = ak.stock_zh_a_spot_em()
                return stock_list_df[['代码', '名称']].rename(columns={'代码': 'symbol', '名称': 'name'})
                
        except Exception as e:
            logger.error(f"读取股票列表失败: {e}")
            return pd.DataFrame()
    
    def _convert_to_klines(self, symbol, name, df):
        """将 DataFrame 转换为 K 线数据格式"""
        klines = []
        
        # 按日期排序
        df = df.sort_values('date')
        
        # 计算涨跌幅（相对于前一天）
        df['change_pct'] = df['close'].pct_change() * 100
        df['change_pct'] = df['change_pct'].fillna(0)
        
        for _, row in df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            
            # 使用计算后的涨跌幅
            pct_chg = row['change_pct']
            
            # 计算振幅
            if pd.notna(row['high']) and pd.notna(row['low']) and row['low'] > 0:
                amplitude = ((row['high'] - row['low']) / row['low']) * 100
            else:
                amplitude = 0
            
            # 计算换手率
            turnover = 0
            if pd.notna(row.get('turnover')) and pd.notna(row.get('outstanding_share')) and row['outstanding_share'] > 0:
                turnover = (row['turnover'] / row['outstanding_share']) * 100
            
            open_val = row['open'] if pd.notna(row['open']) else '-'
            close_val = row['close'] if pd.notna(row['close']) else '-'
            high_val = row['high'] if pd.notna(row['high']) else '-'
            low_val = row['low'] if pd.notna(row['low']) else '-'
            volume_val = row['volume'] if pd.notna(row['volume']) else '-'
            amount_val = row['amount'] if pd.notna(row['amount']) else '-'
            pct_chg_val = pct_chg if pd.notna(pct_chg) else '-'
            amplitude_val = amplitude if pd.notna(amplitude) else '-'
            turnover_val = turnover if pd.notna(turnover) else '-'
            
            kline_str = f"{date_str},{open_val},{close_val},{high_val},{low_val},{volume_val},{amount_val},{pct_chg_val},{amplitude_val},{turnover_val}"
            
            klines.append(kline_str)
        
        return klines
    
    def closed(self, reason):
        logger.info(f"爬虫关闭: {reason}, 共处理 {self.processed_count} 只股票, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")
        self.storage.close()
