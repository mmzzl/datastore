"""多数据源管理器 - 支持多个数据源自动故障转移"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DataSourceBase:
    """数据源基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票实时数据"""
        raise NotImplementedError
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> Optional[Dict[str, List[float]]]:
        """获取股票历史数据"""
        raise NotImplementedError


class AkshareDataSource(DataSourceBase):
    """Akshare数据源 - 东方财富"""
    
    def __init__(self):
        super().__init__("akshare_eastmoney")
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import akshare as ak
                self._client = ak
                logger.info("Akshare数据源初始化成功")
            except ImportError as e:
                logger.error(f"Akshare库导入失败: {e}")
                return None
        return self._client
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票实时数据"""
        try:
            client = self._get_client()
            if not client:
                return None
            
            # 转换股票代码格式
            if stock_code.startswith("sh") or stock_code.startswith("sz"):
                symbol = stock_code
            elif len(stock_code) == 6:
                if stock_code.startswith(("0", "3")):
                    symbol = f"sz{stock_code}"
                else:
                    symbol = f"sh{stock_code}"
            else:
                return None
            
            # 获取实时行情
            df = client.stock_zh_a_spot_em()
            
            # 过滤指定股票
            stock_row = df[df["代码"] == stock_code]
            if stock_row.empty:
                return None
            
            row = stock_row.iloc[0]
            return {
                "code": stock_code,
                "name": row.get("名称", ""),
                "current_price": float(row.get("最新价", 0)),
                "high_price": float(row.get("最高", 0)),
                "low_price": float(row.get("最低", 0)),
                "open_price": float(row.get("今开", 0)),
                "close_price": float(row.get("昨收", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume": int(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0))
            }
        except Exception as e:
            logger.warning(f"Akshare东方财富获取股票数据失败 {stock_code}: {e}")
            return None
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> Optional[Dict[str, List[float]]]:
        """获取股票历史K线数据"""
        try:
            client = self._get_client()
            if not client:
                return None
            
            # 转换股票代码格式
            if stock_code.startswith("sh") or stock_code.startswith("sz"):
                symbol = stock_code
            elif len(stock_code) == 6:
                if stock_code.startswith(("0", "3")):
                    symbol = f"sz{stock_code}"
                else:
                    symbol = f"sh{stock_code}"
            else:
                return None
            
            # 获取K线数据
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now()).strftime("%Y%m%d")
            
            df = client.stock_zh_a_hist(symbol=symbol, period="daily", 
                                       start_date=start_date, end_date=end_date,
                                       adjust="qfq")
            
            if df is None or df.empty:
                return None
            
            # 取最近days天的数据
            df = df.tail(days)
            
            return {
                "close": df["收盘"].tolist(),
                "high": df["最高"].tolist(),
                "low": df["最低"].tolist(),
                "open": df["开盘"].tolist(),
                "volume": df["成交量"].tolist()
            }
        except Exception as e:
            logger.warning(f"Akshare东方财富获取历史数据失败 {stock_code}: {e}")
            return None


class SinaDataSource(DataSourceBase):
    """新浪数据源 - 备用数据源"""
    
    def __init__(self):
        super().__init__("sina")
        self._session = None
    
    def _get_session(self):
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                logger.info("新浪数据源初始化成功")
            except ImportError as e:
                logger.error(f"requests库导入失败: {e}")
                return None
        return self._session
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票实时数据"""
        try:
            session = self._get_session()
            if not session:
                return None
            
            # 转换股票代码格式
            if stock_code.startswith("sh"):
                symbol = stock_code
            elif stock_code.startswith("sz"):
                symbol = stock_code
            elif len(stock_code) == 6:
                if stock_code.startswith(("0", "3")):
                    symbol = f"sz{stock_code}"
                else:
                    symbol = f"sh{stock_code}"
            else:
                return None
            
            # 新浪API
            url = f"https://hq.sinajs.cn/list={symbol}"
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            content = response.text
            if not content or "var hq_str" not in content:
                return None
            
            # 解析数据
            data_str = content.split("=")[1].strip('";\n')
            if not data_str:
                return None
            
            fields = data_str.split(",")
            if len(fields) < 10:
                return None
            
            return {
                "code": stock_code,
                "name": fields[0],
                "current_price": float(fields[1]) if fields[1] else 0,
                "open_price": float(fields[2]) if fields[2] else 0,
                "close_price": float(fields[3]) if fields[3] else 0,
                "high_price": float(fields[4]) if fields[4] else 0,
                "low_price": float(fields[5]) if fields[5] else 0,
                "volume": int(float(fields[8])) if fields[8] else 0,
                "amount": float(fields[9]) if fields[9] else 0
            }
        except Exception as e:
            logger.warning(f"新浪获取股票数据失败 {stock_code}: {e}")
            return None
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> Optional[Dict[str, List[float]]]:
        """获取股票历史数据 - 新浪不支持历史K线，尝试其他方式"""
        try:
            session = self._get_session()
            if not session:
                return None
            
            # 转换股票代码格式
            if stock_code.startswith("sh"):
                symbol = stock_code.replace("sh", "sh.")
            elif stock_code.startswith("sz"):
                symbol = stock_code.replace("sz", "sz.")
            else:
                if stock_code.startswith(("0", "3")):
                    symbol = f"sz.{stock_code}"
                else:
                    symbol = f"sh.{stock_code}"
            
            # 新浪历史数据API
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now()).strftime("%Y-%m-%d")
            
            url = f"https://finance.sina.com.cn/realstock/company/{symbol}/hisdata/klc_kl.js"
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # 新浪不支持历史K线，返回None让下一个数据源尝试
            logger.debug(f"新浪数据源不支持历史K线获取: {stock_code}")
            return None
        except Exception as e:
            logger.warning(f"新浪获取历史数据失败 {stock_code}: {e}")
            return None


class MongoDBDataSource(DataSourceBase):
    """MongoDB数据源 - 从本地MongoDB获取数据"""
    
    def __init__(self):
        super().__init__("mongodb")
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """从MongoDB获取最新行情数据"""
        try:
            from app.storage.mongo_client import MongoStorage
            from app.core.config import settings
            
            mongo = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_dbname,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            mongo.connect()
            
            # 获取最新K线数据
            kline_data = mongo.get_kline(stock_code, limit=1)
            mongo.close()
            
            if not kline_data:
                return None
            
            data = kline_data[0]
            return {
                "code": stock_code,
                "name": data.get("name", ""),
                "current_price": float(data.get("close", 0)),
                "high_price": float(data.get("high", 0)),
                "low_price": float(data.get("low", 0)),
                "open_price": float(data.get("open", 0)),
                "close_price": float(data.get("close", 0)),
                "change": float(data.get("pct_chg", 0)),
                "change_pct": float(data.get("pct_chg", 0)),
                "volume": int(data.get("volume", 0)),
                "amount": float(data.get("amount", 0))
            }
        except Exception as e:
            logger.warning(f"MongoDB获取股票数据失败 {stock_code}: {e}")
            return None
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> Optional[Dict[str, List[float]]]:
        """从MongoDB获取历史K线数据"""
        try:
            from app.storage.mongo_client import MongoStorage
            from app.core.config import settings
            from datetime import timedelta
            
            mongo = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_dbname,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            mongo.connect()
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            kline_data = mongo.get_kline(stock_code, start_date=start_date, 
                                        end_date=end_date, limit=days)
            mongo.close()
            
            if not kline_data:
                return None
            
            # 提取数据
            return {
                "close": [float(d.get("close", 0)) for d in kline_data],
                "high": [float(d.get("high", 0)) for d in kline_data],
                "low": [float(d.get("low", 0)) for d in kline_data],
                "open": [float(d.get("open", 0)) for d in kline_data],
                "volume": [int(d.get("volume", 0)) for d in kline_data]
            }
        except Exception as e:
            logger.warning(f"MongoDB获取历史数据失败 {stock_code}: {e}")
            return None


class MultiDataSourceManager:
    """多数据源管理器"""
    
    def __init__(self):
        self.sources = []
        self._init_sources()
    
    def _init_sources(self):
        """初始化数据源列表"""
        # 按优先级添加数据源
        self.sources = [
            AkshareDataSource(),    # 东方财富 - 首选
            SinaDataSource(),       # 新浪 - 备用1
            MongoDBDataSource()     # MongoDB - 备用2
        ]
        logger.info(f"多数据源初始化完成，共 {len(self.sources)} 个数据源")
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票数据，尝试多个数据源"""
        for source in self.sources:
            try:
                logger.debug(f"尝试从 {source.name} 获取股票数据: {stock_code}")
                data = source.get_stock_data(stock_code)
                if data:
                    logger.info(f"成功从 {source.name} 获取股票数据: {stock_code}")
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取失败: {e}")
                continue
        
        logger.error(f"所有数据源都无法获取股票数据: {stock_code}")
        return None
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> Optional[Dict[str, List[float]]]:
        """获取股票历史数据，尝试多个数据源"""
        for source in self.sources:
            try:
                logger.debug(f"尝试从 {source.name} 获取历史数据: {stock_code}")
                data = source.get_stock_history(stock_code, days)
                if data and data.get("close"):
                    logger.info(f"成功从 {source.name} 获取历史数据: {stock_code}")
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取历史数据失败: {e}")
                continue
        
        logger.error(f"所有数据源都无法获取历史数据: {stock_code}")
        return None
    
    def add_source(self, source: DataSourceBase):
        """添加数据源"""
        self.sources.append(source)
        logger.info(f"添加数据源: {source.name}")
    
    def remove_source(self, name: str):
        """移除数据源"""
        self.sources = [s for s in self.sources if s.name != name]
        logger.info(f"移除数据源: {name}")


# 全局实例
_data_source_manager = None

def get_data_source_manager() -> MultiDataSourceManager:
    """获取多数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = MultiDataSourceManager()
    return _data_source_manager
