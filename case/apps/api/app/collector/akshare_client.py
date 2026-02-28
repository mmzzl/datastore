import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AkshareClient:
    INDEX_CODES = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
    }

    def __init__(self):
        pass

    def get_market_overview(self, date: str) -> Dict:
        date_str = date.replace("-", "")
        
        indices = []
        
        # 获取上证指数
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df[df['date'] == date]
            if not df.empty:
                row = df.iloc[0]
                indices.append({
                    "code": "sh.000001",
                    "name": "上证指数",
                    "close": float(row['close']),
                    "change": float(row['close']) - float(row['open']),
                    "pct_chg": float(row['close'] / row['open'] * 100 - 100) if row['open'] else 0,
                    "volume": float(row['volume']),
                })
        except Exception as e:
            logger.error(f"获取上证指数失败: {e}")
        
        # 获取深证成指
        try:
            df = ak.stock_zh_index_daily(symbol="sz399001")
            df = df[df['date'] == date]
            if not df.empty:
                row = df.iloc[0]
                indices.append({
                    "code": "sz.399001",
                    "name": "深证成指",
                    "close": float(row['close']),
                    "change": float(row['close']) - float(row['open']),
                    "pct_chg": float(row['close'] / row['open'] * 100 - 100) if row['open'] else 0,
                    "volume": float(row['volume']),
                })
        except Exception as e:
            logger.error(f"获取深证成指失败: {e}")
        
        # 获取创业板指
        try:
            df = ak.stock_zh_index_daily(symbol="sz399006")
            df = df[df['date'] == date]
            if not df.empty:
                row = df.iloc[0]
                indices.append({
                    "code": "sz.399006",
                    "name": "创业板指",
                    "close": float(row['close']),
                    "change": float(row['close']) - float(row['open']),
                    "pct_chg": float(row['close'] / row['open'] * 100 - 100) if row['open'] else 0,
                    "volume": float(row['volume']),
                })
        except Exception as e:
            logger.error(f"获取创业板指失败: {e}")
        
        # 获取市场涨跌统计
        try:
            sse_df = ak.stock_sse_summary()
            szse_df = ak.stock_szse_summary()
            
            up_count = int(sse_df.iloc[0].get('股票', 0)) if not sse_df.empty else 0
            down_count = 0
            limit_up = 0
            limit_down = 0
        except Exception as e:
            logger.error(f"获取市场统计失败: {e}")
            up_count = 0
            down_count = 0
            limit_up = 0
            limit_down = 0
        
        return {
            "date": date,
            "indices": indices,
            "stats": {
                "up_count": up_count,
                "down_count": down_count,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "break_board": 0,
            },
            "capital": {
                "north_money": 0,
                "margin": 0,
            }
        }

    def get_stock_data(self, date: str, limit: int = 100) -> List[Dict]:
        date_str = date.replace("-", "")
        
        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            data_list = []
            for _, row in df.head(limit).iterrows():
                code = row.get('代码', '')
                if code:
                    data_list.append({
                        "code": f"{'sh' if str(code).startswith('6') else 'sz'}.{code}",
                        "name": row.get('名称', ''),
                        "close": float(row.get('最新价', 0) or 0),
                        "pct_chg": float(row.get('涨跌幅', 0) or 0),
                        "volume": float(row.get('成交量', 0) or 0),
                        "turnover": float(row.get('成交额', 0) or 0),
                    })
            
            return data_list
        except Exception as e:
            logger.error(f"获取个股数据失败: {e}")
            return []

    def get_sector_data(self, date: str) -> List[Dict]:
        try:
            # 获取行业板块
            df = ak.stock_board_industry_name_em()
            
            data_list = []
            for _, row in df.iterrows():
                name = row.get('板块名称', '')
                pct_chg = row.get('涨跌幅', 0) or 0
                if name:
                    try:
                        pct_chg = float(pct_chg) if pct_chg else 0
                    except:
                        pct_chg = 0
                    data_list.append({
                        "code": "",
                        "name": name,
                        "pct_chg": pct_chg,
                    })
            
            # 按涨跌幅排序
            data_list.sort(key=lambda x: x['pct_chg'], reverse=True)
            return data_list[:30]
        except Exception as e:
            logger.error(f"获取板块数据失败: {e}")
            return []

    def get_capital_flow(self, date: str) -> Dict:
        try:
            # 获取主力资金流向
            df = ak.stock_fund_flow(stock="all")
            if not df.empty:
                main = float(df.iloc[0].get('今日', 0) or 0)
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
