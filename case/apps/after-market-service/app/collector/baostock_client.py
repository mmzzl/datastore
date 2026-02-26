import baostock as bs
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class BaoStockClient:
    INDEX_CODES = {
        "sh.000001": "上证指数",
        "sz.399001": "深证成指",
        "sz.399006": "创业板指",
    }

    def __init__(self):
        self._login()

    def _login(self):
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(f"baostock login failed: {lg.error_msg}")

    def _logout(self):
        bs.logout()

    def _query_to_list(self, rs) -> List[Dict]:
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        return data_list

    def _query_to_df(self, rs) -> pd.DataFrame:
        data_list = []
        fields = rs.fields
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        if data_list:
            return pd.DataFrame(data_list, columns=fields)
        return pd.DataFrame()

    def get_market_overview(self, date: str) -> Dict:
        indices = []
        for code, name in self.INDEX_CODES.items():
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,pctchg",
                start_date=date,
                end_date=date,
                frequency="d"
            )
            df = self._query_to_df(rs)
            if not df.empty:
                row = df.iloc[0]
                indices.append({
                    "code": code,
                    "name": name,
                    "close": float(row['close']) if row['close'] else 0,
                    "change": float(row['close']) - float(row['open']) if row['close'] and row['open'] else 0,
                    "pct_chg": float(row['pctchg']) if row['pctchg'] else 0,
                    "volume": float(row['volume']) if row['volume'] else 0,
                })

        return {
            "date": date,
            "indices": indices,
            "stats": {
                "up_count": 0,
                "down_count": 0,
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
        rs = bs.query_stock_basic()
        data_list = []
        count = 0
        while rs.error_code == '0' and rs.next() and count < limit:
            row = rs.get_row_data()
            if row[0] and row[0].startswith(('sh.', 'sz.')):
                stock_code = row[0]
                stock_name = row[1]
                
                k_rs = bs.query_history_k_data_plus(
                    stock_code,
                    "date,open,high,low,close,volume,amount,pctchg,turn,tradestatus",
                    start_date=date,
                    end_date=date,
                    frequency="d"
                )
                k_df = self._query_to_df(k_rs)
                
                if not k_df.empty:
                    k_row = k_df.iloc[0]
                    data_list.append({
                        "code": stock_code,
                        "name": stock_name,
                        "open": float(k_row['open']) if k_row['open'] else 0,
                        "high": float(k_row['high']) if k_row['high'] else 0,
                        "low": float(k_row['low']) if k_row['low'] else 0,
                        "close": float(k_row['close']) if k_row['close'] else 0,
                        "pct_chg": float(k_row['pctchg']) if k_row['pctchg'] else 0,
                        "turnover": float(k_row['turn']) if k_row['turn'] else 0,
                        "volume": float(k_row['volume']) if k_row['volume'] else 0,
                    })
                    count += 1

        return data_list

    def get_sector_data(self, date: str) -> List[Dict]:
        rs = bs.query_stock_sector()
        data_list = []
        while rs.error_code == '0' and rs.next():
            row = rs.get_row_data()
            if row[0] and row[3]:
                try:
                    pct_chg = float(row[3]) if row[3] else 0
                    data_list.append({
                        "code": row[0],
                        "name": row[1],
                        "pct_chg": pct_chg,
                    })
                except (ValueError, TypeError):
                    pass
        
        data_list.sort(key=lambda x: x['pct_chg'], reverse=True)
        return data_list[:30]

    def get_capital_flow(self, date: str) -> Dict:
        return {
            "main": 0,
            "super_large": 0,
            "large": 0,
        }
