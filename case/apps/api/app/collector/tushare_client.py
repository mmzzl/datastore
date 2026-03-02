import tushare as ts
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class TushareClient:
    INDEX_CODES = {
        "000001.SH": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
    }

    def __init__(self, token: str = None):
        if token:
            ts.set_token(token)
        self.pro = ts.pro_api()

    def get_market_overview(self, date: str) -> Dict:
        date_str = date.replace("-", "")
        
        indices = []
        
        for code, name in self.INDEX_CODES.items():
            try:
                df = ts.pro_bar(
                    ts_code=code,
                    start_date=date_str,
                    end_date=date_str,
                    asset='I'
                )
                if not df.empty:
                    row = df.iloc[0]
                    market = "sh" if code.startswith("000001") else "sz"
                    indices.append({
                        "code": f"{market}.{code.split('.')[0]}",
                        "name": name,
                        "close": float(row['close']),
                        "change": float(row['close']) - float(row['open']),
                        "pct_chg": float(row['pct_chg']),
                        "volume": float(row['vol']) * 100 if row['vol'] else 0,
                    })
            except Exception as e:
                logger.error(f"获取{name}失败: {e}")
        
        try:
            df = self.pro.daily_basic(
                trade_date=date_str.replace("-", ""),
                fields='ts_code,trade_date,turnover_rate,turnover,pe,pb'
            )
            up_count = len(df[df['pct_chg'] > 0]) if 'pct_chg' in df.columns else 0
            down_count = len(df[df['pct_chg'] < 0]) if 'pct_chg' in df.columns else 0
        except Exception as e:
            logger.error(f"获取市场统计失败: {e}")
            up_count = 0
            down_count = 0
        
        return {
            "date": date,
            "indices": indices,
            "stats": {
                "up_count": up_count,
                "down_count": down_count,
                "limit_up": 0,
                "limit_down": 0,
                "break_board": 0,
            },
            "capital": {
                "north_money": 0,
                "margin": 0,
            }
        }

    def get_stock_data(self, date: str, limit: int = 100) -> List[Dict]:
        try:
            df = ts.get_today_all()
            
            data_list = []
            for _, row in df.head(limit).iterrows():
                code = row.get('code', '')
                if code:
                    market = 'sh' if code.startswith('6') else 'sz'
                    data_list.append({
                        "code": f"{market}.{code}",
                        "name": row.get('name', ''),
                        "close": float(row.get('trade', 0) or 0),
                        "pct_chg": float(row.get('changepercent', 0) or 0),
                        "volume": float(row.get('volume', 0) or 0),
                        "turnover": float(row.get('amount', 0) or 0),
                    })
            
            return data_list
        except Exception as e:
            logger.error(f"获取个股数据失败: {e}")
            return []

    def get_sector_data(self, date: str) -> List[Dict]:
        try:
            df = ts.get_industry_classified()
            
            sector_data = {}
            for _, row in df.iterrows():
                sector = row.get('c_name', '')
                if sector and sector not in sector_data:
                    sector_data[sector] = {'name': sector, 'count': 0}
                if sector in sector_data:
                    sector_data[sector]['count'] += 1
            
            data_list = []
            for name, data in sector_data.items():
                data_list.append({
                    "code": "",
                    "name": name,
                    "pct_chg": 0,
                })
            
            return data_list[:30]
        except Exception as e:
            logger.error(f"获取板块数据失败: {e}")
            return []

    def get_capital_flow(self, date: str) -> Dict:
        try:
            df = ts.moneyflow_hsgt()
            if not df.empty:
                main = float(df.iloc[0].get('net_amount', 0) or 0)
                return {
                    "main": main,
                    "super_large": main * 0.6,
                    "large": main * 0.3,
                }
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
        
        return {
            "main": 0,
            "super_large": 0,
            "large": 0,
        }
