import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import baostock as bs
from datetime import datetime, timedelta
import logging
from .eastmoney_spider import EastMoneySpider
from .news_client import NewsClient

logger = logging.getLogger(__name__)


class DailyBriefAnalyzer:
    
    def __init__(self, news_api_config: Optional[Dict] = None):
        self.stock_names_cache = {}
        self.news_api_config = news_api_config or {}
        self.news_client = None
        self._load_stock_names()
    
    def _load_stock_names(self):
        lg = bs.login()
        if lg.error_code != '0':
            logger.warning(f"Baostock login failed: {lg.error_msg}")
            return
        
        rs = bs.query_stock_basic()
        if rs.error_code == '0' and len(rs.data) > 0:
            for row in rs.data:
                code = row[0]
                name = row[1]
                if code.startswith('sh.'):
                    symbol = f"SH{code[3:].upper()}"
                else:
                    symbol = f"SZ{code[3:].upper()}"
                self.stock_names_cache[symbol] = name
        bs.logout()
        logger.info(f"Loaded {len(self.stock_names_cache)} stock names")
    
    def get_stock_name(self, symbol: str) -> str:
        return self.stock_names_cache.get(symbol, symbol)
    
    def _ensure_news_client(self):
        if self.news_client is None and self.news_api_config:
            self.news_client = NewsClient(
                self.news_api_config.get("base_url", "http://localhost:8000"),
                self.news_api_config.get("username", "admin"),
                self.news_api_config.get("password", "admin")
            )
    
    def analyze_full(self, date: str) -> Dict:
        logger.info(f"[1/7] Analyzing market overview...")
        market_overview = self.analyze_market_overview(date)
        
        logger.info(f"[2/7] Analyzing sector performance...")
        sector_performance = self.analyze_sector_performance(date)
        
        logger.info(f"[3/7] Analyzing stock performance...")
        stock_performance = self.analyze_stock_performance(date)
        
        logger.info(f"[4/7] Analyzing news...")
        news = self.analyze_news(date)
        
        logger.info(f"[5/7] Analyzing external markets...")
        external_markets = self.analyze_external_markets()
        
        logger.info(f"[6/7] Analyzing commodities...")
        commodities = self.analyze_commodities()
        
        logger.info(f"[7/7] Generating next day strategy...")
        next_day_strategy = self.analyze_next_day_strategy(
            market_overview, sector_performance, news
        )
        
        return {
            "date": date,
            "market_overview": market_overview,
            "sector_performance": sector_performance,
            "stock_performance": stock_performance,
            "news": news,
            "external_markets": external_markets,
            "commodities": commodities,
            "next_day_strategy": next_day_strategy,
            "generated_at": datetime.now().isoformat()
        }
    
    def analyze_market_overview(self, date: str) -> Dict:
        lg = bs.login()
        if lg.error_code != '0':
            return {"error": f"Login failed: {lg.error_msg}"}
        
        try:
            index_codes = {
                "sh.000001": "上证指数",
                "sz.399001": "深证成指",
                "sz.399006": "创业板指",
            }
            
            index_data = {}
            for code, name in index_codes.items():
                rs = bs.query_history_k_data_plus(
                    code, "date,code,open,high,low,close,volume,amount,pctChg",
                    start_date=date, end_date=date, frequency="d", adjustflag="3"
                )
                if rs.error_code == '0' and len(rs.data) > 0:
                    row = rs.data[0]
                    index_data[name] = {
                        "open": float(row[2]) if row[2] else 0,
                        "high": float(row[3]) if row[3] else 0,
                        "low": float(row[4]) if row[4] else 0,
                        "close": float(row[5]) if row[5] else 0,
                        "volume": float(row[6]) if row[6] else 0,
                        "amount": float(row[7]) if row[7] else 0,
                        "change_pct": float(row[8]) if row[8] else 0,
                    }
            
            rs = bs.query_stock_basic()
            all_stocks = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if row[0] and row[0].startswith(('sh.6', 'sz.0', 'sz.3')):
                    all_stocks.append((row[0], row[1]))
            
            up_count = 0
            down_count = 0
            flat_count = 0
            limit_up = 0
            limit_down = 0
            total_amount = 0
            total_volume = 0
            change_list = []
            up_ratio = 0.5
            
            processed = 0
            for stock_code, stock_name in all_stocks:
                k_rs = bs.query_history_k_data_plus(
                    stock_code, "date,close,volume,amount,pctChg",
                    start_date=date, end_date=date, frequency="d"
                )
                if k_rs.error_code == '0' and k_rs.next():
                    row = k_rs.get_row_data()
                    if row[4]:
                        pct_chg = float(row[4])
                        change_list.append(pct_chg)
                        
                        if pct_chg > 0:
                            up_count += 1
                        elif pct_chg < 0:
                            down_count += 1
                        else:
                            flat_count += 1
                        
                        if pct_chg >= 9.9:
                            limit_up += 1
                        elif pct_chg <= -9.9:
                            limit_down += 1
                        
                        if row[3]:
                            total_amount += float(row[3])
                        if row[2]:
                            total_volume += float(row[2])
                
                processed += 1
                if processed % 500 == 0:
                    logger.info(f"  Processed {processed}/{len(all_stocks)} stocks...")
            
            avg_change = sum(change_list) / len(change_list) if change_list else 0
            
            total = up_count + down_count
            if total > 0:
                up_ratio = up_count / total
                if up_ratio >= 0.7:
                    sentiment = "普涨"
                elif up_ratio >= 0.5:
                    sentiment = "偏涨"
                elif up_ratio >= 0.3:
                    sentiment = "分化"
                elif up_ratio >= 0.1:
                    sentiment = "偏跌"
                else:
                    sentiment = "普跌"
            else:
                sentiment = "无数据"
                up_ratio = 0.5
            
            score = 5
            if up_ratio >= 0.8:
                score += 2
            elif up_ratio >= 0.6:
                score += 1
            elif up_ratio <= 0.2:
                score -= 2
            elif up_ratio <= 0.4:
                score -= 1
            if limit_up > 50:
                score += 2
            elif limit_up > 20:
                score += 1
            if limit_down > 50:
                score -= 2
            elif limit_down > 20:
                score -= 1
            if avg_change > 2:
                score += 1
            elif avg_change < -2:
                score -= 1
            score = max(1, min(10, score))
            
            return {
                "date": date,
                "total_stocks": len(change_list),
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "avg_change_pct": round(avg_change, 2),
                "limit_up": limit_up,
                "limit_down": limit_down,
                "market_sentiment": sentiment,
                "market_score": score,
                "total_amount": round(total_amount / 1e8, 2),
                "total_volume": round(total_volume / 1e8, 2),
                "index_performance": index_data
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_market_overview: {e}")
            return {"error": str(e)}
        finally:
            bs.logout()
    
    def analyze_sector_performance(self, date: str) -> Dict:
        lg = bs.login()
        if lg.error_code != '0':
            return {"error": f"Login failed: {lg.error_msg}"}
        
        try:
            industry_rs = bs.query_stock_industry()
            industry_map = {}
            while industry_rs.error_code == '0' and industry_rs.next():
                row = industry_rs.get_row_data()
                code = row[0]
                industry = row[3] if len(row) > 3 else row[1]
                if code and industry:
                    industry_map[code] = industry
            
            rs = bs.query_stock_basic()
            all_stocks = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if row[0] and row[0].startswith(('sh.6', 'sz.0', 'sz.3')):
                    all_stocks.append(row[0])
            
            sector_data = {}
            processed = 0
            
            for stock_code in all_stocks:
                k_rs = bs.query_history_k_data_plus(
                    stock_code, "date,close,volume,amount,pctChg",
                    start_date=date, end_date=date, frequency="d"
                )
                
                if k_rs.error_code == '0' and k_rs.next():
                    row = k_rs.get_row_data()
                    if row[4]:
                        pct_chg = float(row[4])
                        amount = float(row[3]) if row[3] else 0
                        industry = industry_map.get(stock_code, "其他")
                        
                        if industry not in sector_data:
                            sector_data[industry] = {
                                "change_list": [],
                                "amount_list": [],
                                "stock_count": 0
                            }
                        sector_data[industry]["change_list"].append(pct_chg)
                        sector_data[industry]["amount_list"].append(amount)
                        sector_data[industry]["stock_count"] += 1
                
                processed += 1
                if processed % 500 == 0:
                    logger.info(f"  Processed {processed}/{len(all_stocks)} stocks for sector...")
            
            sector_stats = []
            for industry, data in sector_data.items():
                if data["stock_count"] > 0:
                    avg_change = sum(data["change_list"]) / len(data["change_list"])
                    total_amount = sum(data["amount_list"])
                    sector_stats.append({
                        "industry": industry,
                        "avg_change_pct": round(avg_change, 2),
                        "stock_count": data["stock_count"],
                        "total_amount": round(total_amount / 1e8, 2)
                    })
            
            sector_stats.sort(key=lambda x: x["avg_change_pct"], reverse=True)
            
            top_gainers = sector_stats[:10]
            top_losers = sector_stats[-10:][::-1]
            
            return {
                "date": date,
                "total_sectors": len(sector_stats),
                "top_gainers": top_gainers,
                "top_losers": top_losers
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_sector_performance: {e}")
            return {"error": str(e)}
        finally:
            bs.logout()
    
    def analyze_stock_performance(self, date: str) -> Dict:
        lg = bs.login()
        if lg.error_code != '0':
            return {"error": f"Login failed: {lg.error_msg}"}
        
        try:
            rs = bs.query_stock_basic()
            all_stocks = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if row[0] and row[0].startswith(('sh.6', 'sz.0', 'sz.3')):
                    all_stocks.append((row[0], row[1]))
            
            stock_data = []
            processed = 0
            
            for stock_code, stock_name in all_stocks:
                k_rs = bs.query_history_k_data_plus(
                    stock_code, "date,open,high,low,close,volume,amount,pctChg",
                    start_date=date, end_date=date, frequency="d"
                )
                
                if k_rs.error_code == '0' and k_rs.next():
                    row = k_rs.get_row_data()
                    if row[7]:
                        pct_chg = float(row[7]) if row[7] else 0
                        high = float(row[3]) if row[3] else 0
                        low = float(row[4]) if row[4] else 0
                        amplitude = ((high - low) / low * 100) if low > 0 else 0
                        
                        symbol = f"SH{stock_code[3:]}" if stock_code.startswith('sh.') else f"SZ{stock_code[3:]}"
                        
                        stock_data.append({
                            "symbol": symbol,
                            "name": stock_name,
                            "close": float(row[5]) if row[5] else 0,
                            "pct_chg": round(pct_chg, 2),
                            "amplitude": round(amplitude, 2),
                            "volume": float(row[6]) if row[6] else 0,
                            "amount": float(row[7]) if row[7] else 0
                        })
                
                processed += 1
                if processed % 500 == 0:
                    logger.info(f"  Processed {processed}/{len(all_stocks)} stocks for performance...")
            
            stock_data.sort(key=lambda x: x["pct_chg"], reverse=True)
            top_gainers = stock_data[:20]
            top_losers = stock_data[-20:][::-1]
            
            stock_data.sort(key=lambda x: x["amplitude"], reverse=True)
            top_amplitude = stock_data[:20]
            
            stock_data.sort(key=lambda x: x["amount"], reverse=True)
            top_amount = stock_data[:20]
            
            limit_up_stocks = [s for s in stock_data if s["pct_chg"] >= 9.9]
            limit_down_stocks = [s for s in stock_data if s["pct_chg"] <= -9.9]
            
            return {
                "date": date,
                "total_stocks": len(stock_data),
                "top_gainers": top_gainers,
                "top_losers": top_losers,
                "top_amplitude": top_amplitude,
                "top_amount": top_amount,
                "limit_up_count": len(limit_up_stocks),
                "limit_down_count": len(limit_down_stocks),
                "limit_up_stocks": limit_up_stocks[:10],
                "limit_down_stocks": limit_down_stocks[:10]
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_stock_performance: {e}")
            return {"error": str(e)}
        finally:
            bs.logout()
    
    def analyze_news(self, date: str) -> Dict:
        try:
            self._ensure_news_client()
            
            result = {
                "date": date,
                "daily_news": [],
                "weekly_news": [],
                "monthly_news": [],
                "total_count": 0,
                "analysis": {}
            }
            
            if not self.news_client:
                result["message"] = "News API not configured"
                return result
            
            daily_news = self.news_client.get_daily_news(date, limit=20)
            weekly_news = self.news_client.get_weekly_news(date, limit=10)
            monthly_news = self.news_client.get_monthly_news(date, limit=10)
            
            daily_items = daily_news.get("items", [])
            weekly_items = weekly_news.get("items", [])
            monthly_items = monthly_news.get("items", [])
            
            result["daily_news"] = daily_items
            result["weekly_news"] = weekly_items
            result["monthly_news"] = monthly_items
            result["total_count"] = len(daily_items) + len(weekly_items) + len(monthly_items)
            
            all_news = daily_items + weekly_items + monthly_items
            result["analysis"] = self._analyze_news_sentiment(all_news)
            
            return result
                
        except Exception as e:
            logger.error(f"Error in analyze_news: {e}")
            return {"error": str(e), "date": date}
    
    def _analyze_news_sentiment(self, news_items: List[Dict]) -> Dict:
        if not news_items:
            return {"sentiment": "中性", "hot_topics": [], "stock_mentions": {}}
        
        positive_keywords = [
            "利好", "上涨", "突破", "增长", "盈利", "涨停", "大涨", "创新高",
            "收购", "合并", "中标", "签约", "获批", "回购", "增持", "分红",
            "业绩预增", "扭亏", "订单", "扩产", "合作", "重组"
        ]
        
        negative_keywords = [
            "利空", "下跌", "亏损", "跌停", "大跌", "暴跌", "破位", "新低",
            "减持", "质押", "诉讼", "处罚", "调查", "违约", "退市", "风险",
            "业绩预亏", "下滑", "裁员", "停产", "召回"
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        stock_mentions = {}
        hot_topics = []
        
        for item in news_items:
            title = item.get("title", "")
            summary = item.get("summary", "")
            content = f"{title} {summary}"
            
            pos_score = sum(1 for kw in positive_keywords if kw in content)
            neg_score = sum(1 for kw in negative_keywords if kw in content)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
            
            stock_list = item.get("stockList", [])
            for stock in stock_list:
                if stock not in stock_mentions:
                    stock_mentions[stock] = 0
                stock_mentions[stock] += 1
            
            if title:
                hot_topics.append({
                    "title": title[:60],
                    "sentiment": "利好" if pos_score > neg_score else ("利空" if neg_score > pos_score else "中性"),
                    "stocks": stock_list[:3]
                })
        
        total = positive_count + negative_count + neutral_count
        if total > 0:
            pos_ratio = positive_count / total
            neg_ratio = negative_count / total
            
            if pos_ratio > 0.6:
                sentiment = "偏多"
            elif neg_ratio > 0.6:
                sentiment = "偏空"
            elif pos_ratio > neg_ratio:
                sentiment = "谨慎偏多"
            elif neg_ratio > pos_ratio:
                sentiment = "谨慎偏空"
            else:
                sentiment = "中性"
        else:
            sentiment = "中性"
        
        sorted_stocks = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "sentiment": sentiment,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "hot_topics": hot_topics[:10],
            "top_mentioned_stocks": [{"code": s[0], "count": s[1]} for s in sorted_stocks]
        }
    
    def analyze_external_markets(self) -> Dict:
        try:
            spider = EastMoneySpider()
            return spider.get_external_markets()
        except Exception as e:
            logger.error(f"Error in analyze_external_markets: {e}")
            return {"error": str(e)}
    
    def analyze_commodities(self) -> Dict:
        try:
            spider = EastMoneySpider()
            return spider.get_commodities()
        except Exception as e:
            logger.error(f"Error in analyze_commodities: {e}")
            return {"error": str(e)}
    
    def analyze_next_day_strategy(self, market: Dict, sector: Dict, news: Dict) -> Dict:
        try:
            market_score = market.get('market_score', 5)
            avg_change = market.get('avg_change_pct', 0)
            limit_up = market.get('limit_up', 0)
            limit_down = market.get('limit_down', 0)
            sentiment = market.get('market_sentiment', '分化')
            
            if market_score >= 8:
                market_expectation = "高开/震荡上行"
                position = "乐观，可重仓（70-80%）"
            elif market_score >= 6:
                market_expectation = "震荡/方向不明"
                position = "中性，中等仓位（40-60%）"
            elif market_score >= 4:
                market_expectation = "低开/震荡下行"
                position = "谨慎，轻仓（20-30%）"
            else:
                market_expectation = "低开/下跌"
                position = "悲观，空仓观望"
            
            leading_sectors = sector.get('top_gainers', [])
            if leading_sectors and leading_sectors[0].get('avg_change_pct', 0) > 2:
                mainline = f"聚焦最强板块：{leading_sectors[0]['industry']}"
                mainline_clear = True
            elif leading_sectors and leading_sectors[0].get('avg_change_pct', 0) > 0:
                mainline = f"关注板块：{leading_sectors[0]['industry']}"
                mainline_clear = False
            else:
                mainline = "无明显主线，观望为主"
                mainline_clear = False
            
            news_analysis = news.get('analysis', {})
            news_sentiment = news_analysis.get('sentiment', '中性')
            
            if news_sentiment == "偏多":
                market_expectation += "，新闻面偏暖"
            elif news_sentiment == "偏空":
                market_expectation += "，新闻面偏冷"
            
            risk_points = []
            if limit_down > limit_up:
                risk_points.append(f"跌停数({limit_down})多于涨停数({limit_up})")
            if avg_change < -1:
                risk_points.append(f"平均跌幅较大({avg_change:.2f}%)")
            if news_sentiment == "偏空":
                risk_points.append("新闻面偏空")
            
            return {
                "market_expectation": market_expectation,
                "position_suggestion": position,
                "mainline_suggestion": mainline,
                "mainline_clear": mainline_clear,
                "news_sentiment": news_sentiment,
                "risk_points": risk_points,
                "key_sectors": [s.get('industry', '') for s in leading_sectors[:3]]
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_next_day_strategy: {e}")
            return {"error": str(e)}
