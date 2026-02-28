import requests
from datetime import datetime
import json
from typing import Dict, List


class EastMoneySpider:
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_external_markets(self) -> Dict:
        try:
            markets = {}
            us_stocks = self._get_us_stocks()
            markets['us_stocks'] = us_stocks
            a50 = self._get_a50_index()
            markets['a50'] = a50
            exchange_rate = self._get_exchange_rate()
            markets['exchange_rate'] = exchange_rate
            return markets
        except Exception as e:
            return {'error': str(e)}
    
    def _get_us_stocks(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '105.DJI,105.NDAQ,105.SPX',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data']:
                    stocks = []
                    for item in data['data']['diff']:
                        stocks.append({
                            'name': item.get('f14', ''),
                            'current': item.get('f2', 0),
                            'change': item.get('f4', 0),
                            'change_pct': item.get('f3', 0),
                            'high': item.get('f15', 0),
                            'low': item.get('f16', 0),
                            'open': item.get('f17', 0)
                        })
                    return {'stocks': stocks}
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_a50_index(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '113.CN00Y',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                    item = data['data']['diff'][0]
                    return {
                        'name': item.get('f14', 'A50期指'),
                        'current': item.get('f2', 0),
                        'change': item.get('f4', 0),
                        'change_pct': item.get('f3', 0),
                        'high': item.get('f15', 0),
                        'low': item.get('f16', 0),
                        'open': item.get('f17', 0)
                    }
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_exchange_rate(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '116.USD_CNY',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                    item = data['data']['diff'][0]
                    return {
                        'name': item.get('f14', '美元/人民币'),
                        'current': item.get('f2', 0),
                        'change': item.get('f4', 0),
                        'change_pct': item.get('f3', 0),
                        'high': item.get('f15', 0),
                        'low': item.get('f16', 0),
                        'open': item.get('f17', 0)
                    }
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_commodities(self) -> Dict:
        try:
            commodities = {}
            commodities['oil'] = self._get_oil_price()
            commodities['gold'] = self._get_gold_price()
            commodities['copper'] = self._get_copper_price()
            return commodities
        except Exception as e:
            return {'error': str(e)}
    
    def _get_oil_price(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {'fltt': '2', 'invt': '2', 'secids': '113.CL00',
                     'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18'}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                    item = data['data']['diff'][0]
                    return {
                        'name': item.get('f14', '原油'),
                        'current': item.get('f2', 0),
                        'change': item.get('f4', 0),
                        'change_pct': item.get('f3', 0)
                    }
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_gold_price(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {'fltt': '2', 'invt': '2', 'secids': '113.GC00',
                     'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18'}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                    item = data['data']['diff'][0]
                    return {
                        'name': item.get('f14', '黄金'),
                        'current': item.get('f2', 0),
                        'change': item.get('f4', 0),
                        'change_pct': item.get('f3', 0)
                    }
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_copper_price(self) -> Dict:
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {'fltt': '2', 'invt': '2', 'secids': '113.HG00',
                     'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18'}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                    item = data['data']['diff'][0]
                    return {
                        'name': item.get('f14', '伦铜'),
                        'current': item.get('f2', 0),
                        'change': item.get('f4', 0),
                        'change_pct': item.get('f3', 0)
                    }
            return {'error': 'No data'}
        except Exception as e:
            return {'error': str(e)}
