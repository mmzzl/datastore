import baostock as bs
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaostockClient:
    def __init__(self):
        self.connected = False
        self._connect()
    
    def _connect(self):
        try:
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"登录失败: {lg.error_msg}")
                self.connected = False
            else:
                self.connected = True
                logger.info("Baostock 登录成功")
        except Exception as e:
            logger.error(f"登录异常: {e}")
            self.connected = False
    
    def _ensure_connected(self):
        if not self.connected:
            self._connect()
    
    def get_market_overview(self, date_str: str) -> Dict[str, Any]:
        self._ensure_connected()
        
        try:
            # 获取指数数据
            rs = bs.query_history_k_data_plus(
                "sh.000001,sh.000300,sz.399001,sz.399006",
                "date,code,open,high,low,close,preclose,volume,amount,pctChg",
                start_date=date_str,
                end_date=date_str,
                frequency="d",
                adjustflag="3"
            )
            
            indices = []
            while (rs.error_code == '0') & rs.next():
                data = rs.get_row_data()
                indices.append({
                    "code": data[1],
                    "name": self._get_index_name(data[1]),
                    "close": float(data[5]),
                    "pct_chg": float(data[9])
                })
            
            return {
                "date": date_str,
                "indices": indices
            }
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {"date": date_str, "indices": []}
    
    def get_sector_data(self, date_str: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        
        try:
            # 获取行业数据
            rs = bs.query_sector_performance(
                start_date=date_str,
                end_date=date_str
            )
            
            sectors = []
            while (rs.error_code == '0') & rs.next():
                data = rs.get_row_data()
                sectors.append({
                    "code": data[1],
                    "name": data[2],
                    "pct_chg": float(data[3])
                })
            
            # 按涨跌幅排序
            sectors.sort(key=lambda x: x["pct_chg"], reverse=True)
            return sectors[:20]  # 返回前20个行业
        except Exception as e:
            logger.error(f"获取行业数据失败: {e}")
            return []
    
    def get_capital_flow(self, date_str: str) -> Dict[str, Any]:
        self._ensure_connected()
        
        try:
            # 获取资金流向数据
            rs = bs.query_stock_basic(code_name="")
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                data = rs.get_row_data()
                if data[1] == '1' or data[1] == '2':  # 只处理A股
                    stock_list.append(data[0])
            
            # 这里简化处理，返回资金流向概览
            return {
                "date": date_str,
                "total_stocks": len(stock_list),
                "market_type": "A股"
            }
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return {"date": date_str, "total_stocks": 0, "market_type": "A股"}
    
    def _get_index_name(self, code: str) -> str:
        index_map = {
            "sh.000001": "上证指数",
            "sh.000300": "沪深300",
            "sz.399001": "深证成指",
            "sz.399006": "创业板指"
        }
        return index_map.get(code, code)
    
    def close(self):
        try:
            bs.logout()
            self.connected = False
            logger.info("Baostock 登出成功")
        except Exception as e:
            logger.error(f"登出异常: {e}")
    
    def __del__(self):
        self.close()