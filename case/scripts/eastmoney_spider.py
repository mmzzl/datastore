# -*- coding: utf-8 -*-
# 东方财富数据爬虫
import requests
from datetime import datetime, timedelta
import re
import json
from typing import Dict, List


class EastMoneySpider:
    """东方财富数据爬虫"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_policy_news(self, date: str = None) -> Dict:
        """获取政策利好/利空新闻"""
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # 这里简化处理，返回模拟数据
            # 实际使用时需要根据东方财富API文档调整
            
            return {
                'date': date,
                'total_count': 0,
                'good_news': [],
                'bad_news': [],
                'neutral_news': [],
                'message': '新闻API需要进一步调试'
            }
        
        except Exception as e:
            return {'error': str(e), 'date': date}
    
    def get_external_markets(self) -> Dict:
        """获取外围市场数据（美股、A50、汇率）"""
        try:
            markets = {}
            
            # 获取美股三大指数
            us_stocks = self._get_us_stocks()
            markets['us_stocks'] = us_stocks
            
            # 获取A50期指
            a50 = self._get_a50_index()
            markets['a50'] = a50
            
            # 获取汇率
            exchange_rate = self._get_exchange_rate()
            markets['exchange_rate'] = exchange_rate
            
            return markets
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_us_stocks(self) -> Dict:
        """获取美股三大指数"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '105.DJI,105.NDAQ,105.SPX',  # 道琼斯、纳斯达克、标普500
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if 'data' in data and 'diff' in data['data']:
                        stocks = []
                        
                        for item in data['data']['diff']:
                            name = item.get('f14', '')
                            current = item.get('f2', 0)
                            change = item.get('f4', 0)
                            change_pct = item.get('f3', 0)
                            high = item.get('f15', 0)
                            low = item.get('f16', 0)
                            open_price = item.get('f17', 0)
                            
                            stocks.append({
                                'name': name,
                                'current': current,
                                'change': change,
                                'change_pct': change_pct,
                                'high': high,
                                'low': low,
                                'open': open_price
                            })
                        
                        return {'stocks': stocks}
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch US stocks'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_a50_index(self) -> Dict:
        """获取A50期指"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '113.CN00Y',  # A50期指
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
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
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch A50 index'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_exchange_rate(self) -> Dict:
        """获取汇率（美元/人民币）"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '116.USD_CNY',  # 美元/人民币
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
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
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch exchange rate'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_commodities(self) -> Dict:
        """获取大宗商品数据（原油、黄金、铜）"""
        try:
            commodities = {}
            
            # 获取原油
            oil = self._get_oil_price()
            commodities['oil'] = oil
            
            # 获取黄金
            gold = self._get_gold_price()
            commodities['gold'] = gold
            
            # 获取铜
            copper = self._get_copper_price()
            commodities['copper'] = copper
            
            return commodities
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_oil_price(self) -> Dict:
        """获取原油价格"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '113.CL00',  # 原油期货
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                        item = data['data']['diff'][0]
                        
                        return {
                            'name': item.get('f14', '原油'),
                            'current': item.get('f2', 0),
                            'change': item.get('f4', 0),
                            'change_pct': item.get('f3', 0),
                            'high': item.get('f15', 0),
                            'low': item.get('f16', 0),
                            'open': item.get('f17', 0)
                        }
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch oil price'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_gold_price(self) -> Dict:
        """获取黄金价格"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '113.GC00',  # 黄金期货
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                        item = data['data']['diff'][0]
                        
                        return {
                            'name': item.get('f14', '黄金'),
                            'current': item.get('f2', 0),
                            'change': item.get('f4', 0),
                            'change_pct': item.get('f3', 0),
                            'high': item.get('f15', 0),
                            'low': item.get('f16', 0),
                            'open': item.get('f17', 0)
                        }
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch gold price'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_copper_price(self) -> Dict:
        """获取铜价格"""
        try:
            url = "http://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2',
                'invt': '2',
                'secids': '113.HG00',  # 铜期货
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if 'data' in data and 'diff' in data['data'] and len(data['data']['diff']) > 0:
                        item = data['data']['diff'][0]
                        
                        return {
                            'name': item.get('f14', '伦铜'),
                            'current': item.get('f2', 0),
                            'change': item.get('f4', 0),
                            'change_pct': item.get('f3', 0),
                            'high': item.get('f15', 0),
                            'low': item.get('f16', 0),
                            'open': item.get('f17', 0)
                        }
                    else:
                        return {'error': 'No data available'}
                except json.JSONDecodeError:
                    return {'error': 'JSON解析失败'}
            
            return {'error': 'Failed to fetch copper price'}
        
        except Exception as e:
            return {'error': str(e)}


if __name__ == "__main__":
    spider = EastMoneySpider()
    
    print("=" * 80)
    print("测试东方财富爬虫")
    print("=" * 80)
    
    # 测试政策新闻
    print("\n【政策新闻】")
    policy_news = spider.get_policy_news()
    if 'error' not in policy_news:
        print(f"  日期: {policy_news['date']}")
        print(f"  总数: {policy_news['total_count']}")
        print(f"  利好: {len(policy_news['good_news'])}条")
        print(f"  利空: {len(policy_news['bad_news'])}条")
        print(f"  中性: {len(policy_news['neutral_news'])}条")
        print(f"  消息: {policy_news.get('message', '')}")
    else:
        print(f"  错误: {policy_news.get('error', 'Unknown')}")
    
    # 测试外围市场
    print("\n【外围市场】")
    external_markets = spider.get_external_markets()
    if 'error' not in external_markets:
        if 'us_stocks' in external_markets and 'stocks' in external_markets['us_stocks']:
            print("  美股:")
            for stock in external_markets['us_stocks']['stocks']:
                print(f"    {stock['name']}: {stock['current']:.2f} ({stock['change_pct']:.2f}%)")
        
        if 'a50' in external_markets and 'error' not in external_markets['a50']:
            a50 = external_markets['a50']
            print(f"  A50期指: {a50['current']:.2f} ({a50['change_pct']:.2f}%)")
        
        if 'exchange_rate' in external_markets and 'error' not in external_markets['exchange_rate']:
            rate = external_markets['exchange_rate']
            print(f"  美元/人民币: {rate['current']:.4f} ({rate['change_pct']:.2f}%)")
    else:
        print(f"  错误: {external_markets.get('error', 'Unknown')}")
    
    # 测试大宗商品
    print("\n【大宗商品】")
    commodities = spider.get_commodities()
    if 'error' not in commodities:
        if 'oil' in commodities and 'error' not in commodities['oil']:
            oil = commodities['oil']
            print(f"  {oil['name']}: {oil['current']:.2f} ({oil['change_pct']:.2f}%)")
        
        if 'gold' in commodities and 'error' not in commodities['gold']:
            gold = commodities['gold']
            print(f"  {gold['name']}: {gold['current']:.2f} ({gold['change_pct']:.2f}%)")
        
        if 'copper' in commodities and 'error' not in commodities['copper']:
            copper = commodities['copper']
            print(f"  {copper['name']}: {copper['current']:.2f} ({copper['change_pct']:.2f}%)")
    else:
        print(f"  错误: {commodities.get('error', 'Unknown')}")
    
    print("\n" + "=" * 80)
