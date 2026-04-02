"""
Risk Report Job Handler

Executes daily risk report generation with DingTalk notifications.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
import os
import pandas as pd

from ..risk import RiskReportGenerator
from ..notify.dingtalk import DingTalkNotifier
from ..core.config import settings
from ..storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)


class IndustryMapper:
    """Industry mapper for stocks."""
    
    def __init__(self):
        self.industry_map = self._load_industry_data()
    
    def _load_industry_data(self) -> Dict[str, str]:
        """Load industry data from CSV file using pandas."""
        industry_map = {}
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'all_stock.csv')
        
        try:
            # Read CSV using pandas for better performance
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # Create a mapping from code to industry
            for _, row in df.iterrows():
                code = row.get('code') or row.get('股票代码') or row.get('代码')
                code_name = row.get('code_name') or row.get('名称')
                if code:
                    # Extract industry from code name for ETFs
                    industry = self._extract_industry_from_name(code_name)
                    industry_map[code] = industry
            
            logger.info(f"Loaded industry data for {len(industry_map)} stocks using pandas from all_stock.csv")
        except Exception as e:
            logger.error(f"Failed to load industry data: {e}")
        
        return industry_map
    
    def _extract_industry_from_name(self, name: str) -> str:
        """Extract industry from stock name."""
        if not name:
            return '未知'
        
        # Common industry keywords in ETF names
        industry_keywords = {
            '能源': '能源',
            '医药': '医药',
            '医疗': '医药',
            '科技': '科技',
            '电子': '电子',
            '金融': '金融',
            '银行': '银行',
            '证券': '金融',
            '保险': '金融',
            '消费': '消费',
            '食品': '消费',
            '饮料': '消费',
            '农业': '农业',
            '军工': '军工',
            '国防': '军工',
            '环保': '环保',
            '新能源': '新能源',
            '汽车': '汽车',
            '钢铁': '钢铁',
            '煤炭': '煤炭',
            '有色': '有色金属',
            '金属': '有色金属',
            '化工': '化工',
            '建材': '建材',
            '地产': '房地产',
            '房地产': '房地产',
            '公用': '公用事业',
            '电力': '公用事业',
            '通信': '通信',
            '传媒': '传媒',
            '互联网': '互联网',
            '计算机': '计算机',
            '人工智能': '人工智能',
            '半导体': '半导体',
            '芯片': '半导体',
            '光伏': '新能源',
            '风电': '新能源',
            '氢能': '新能源',
            '锂电': '新能源',
            '电池': '新能源',
            '物联网': '物联网',
            '5G': '通信',
            '一带一路': '一带一路',
            '央企': '央企',
            '国企': '国企',
            '民企': '民企',
            '红利': '红利',
            '价值': '价值',
            '成长': '成长',
            '低波': '低波',
            '质量': '质量',
            'ESG': 'ESG',
            '碳中和': '环保',
            '碳交易': '环保',
            '创新': '创新',
            '科技': '科技',
            '高端制造': '制造业',
            '制造业': '制造业',
            '工业': '工业',
            '材料': '材料',
            '资源': '资源',
            '黄金': '贵金属',
            '白银': '贵金属',
            '商品': '商品',
            '原油': '能源',
            '天然气': '能源',
            '煤炭': '能源',
            '有色': '有色金属',
            '钢铁': '钢铁',
            '化工': '化工',
            '建材': '建材',
            '基建': '基建',
            '建筑': '建筑',
            '运输': '交通运输',
            '物流': '交通运输',
            '航空': '交通运输',
            '航运': '交通运输',
            '铁路': '交通运输',
            '公路': '交通运输',
            '港口': '交通运输',
            '地产': '房地产',
            '房地产': '房地产',
            '物业': '房地产',
            '公用': '公用事业',
            '电力': '公用事业',
            '水务': '公用事业',
            '燃气': '公用事业',
            '通信': '通信',
            '传媒': '传媒',
            '互联网': '互联网',
            '计算机': '计算机',
            '软件': '计算机',
            '人工智能': '人工智能',
            '半导体': '半导体',
            '芯片': '半导体',
            '光伏': '新能源',
            '风电': '新能源',
            '氢能': '新能源',
            '锂电': '新能源',
            '电池': '新能源',
            '物联网': '物联网',
            '5G': '通信',
            '一带一路': '一带一路',
        }
        
        # Check for industry keywords in the name
        for keyword, industry in industry_keywords.items():
            if keyword in name:
                return industry
        
        # Default to 'ETF' if no industry found
        if 'ETF' in name:
            return 'ETF'
        
        return '未知'
    
    def get_industry(self, code: str) -> Optional[str]:
        """Get industry for a stock code."""
        # Remove SH/SZ prefix if present
        if code.startswith('SH'):
            code = code[2:]
        elif code.startswith('SZ'):
            code = code[2:]
        
        # Also remove any suffix like .SH or .SZ if present
        if code.endswith('.SH'):
            code = code[:-3]
        elif code.endswith('.SZ'):
            code = code[:-3]
        
        # Try exact match first
        if code in self.industry_map:
            return self.industry_map[code]
        
        # Try matching with sz. or sh. prefix
        sz_code = f"sz.{code}"
        if sz_code in self.industry_map:
            return self.industry_map[sz_code]
        
        sh_code = f"sh.{code}"
        if sh_code in self.industry_map:
            return self.industry_map[sh_code]
        
        return '未知'


class RiskReportJob:
    """Daily risk report generation job."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._generator: Optional[RiskReportGenerator] = None
        self._notifier: Optional[DingTalkNotifier] = None
        self._storage: Optional[MongoStorage] = None
        self._industry_mapper = IndustryMapper()

    def _get_storage(self) -> MongoStorage:
        if self._storage is None:
            self._storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self._storage.connect()
        return self._storage

    def _get_generator(self) -> RiskReportGenerator:
        if self._generator is None:
            self._generator = RiskReportGenerator(storage=self._get_storage())
        return self._generator

    def _get_notifier(self) -> Optional[DingTalkNotifier]:
        if self._notifier is None:
            webhook = self.config.get(
                "dingtalk_webhook",
                settings.after_market_dingtalk_webhook,
            )
            secret = self.config.get(
                "dingtalk_secret",
                settings.after_market_dingtalk_secret,
            )
            if webhook:
                self._notifier = DingTalkNotifier(webhook_url=webhook, secret=secret)
        return self._notifier

    async def _send_notification(self, title: str, content: str, at_all: bool = False):
        notifier = self._get_notifier()
        if notifier:
            markdown = f"## {title}\n\n{content}"
            await asyncio.to_thread(notifier.send, markdown=markdown, at_all=at_all)

    def _get_price_fetcher(self, kline_data: Dict[str, Dict[str, float]]):
        def price_fetcher(code: str) -> float:
            return kline_data.get(code, {}).get("close", 0.0)
        return price_fetcher

    async def _fetch_latest_prices(self, codes: List[str]) -> Dict[str, Dict[str, float]]:
        storage = self._get_storage()
        today = datetime.now().strftime("%Y-%m-%d")
        prices = {}

        for code in codes:
            try:
                # Remove SH/SZ prefix for K-line query
                query_code = code
                if code.startswith("SH"):
                    query_code = code[2:]
                elif code.startswith("SZ"):
                    query_code = code[2:]
                
                klines = await asyncio.to_thread(
                    storage.get_kline,
                    query_code,
                    start_date=None,
                    end_date=today,
                    limit=5,
                )
                if klines:
                    latest = klines[0]
                    prices[code] = {
                        "close": latest.get("close", 0.0),
                        "date": latest.get("date", ""),
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch price for {code}: {e}")
                prices[code] = {"close": 0.0, "date": ""}

        return prices

    async def _get_user_holdings(self, user_id: str) -> List[Dict[str, Any]]:
        storage = self._get_storage()
        try:
            collection = storage.db.get_collection("holdings")
            cursor = await asyncio.to_thread(
                lambda: list(collection.find({"user_id": user_id}))
            )
            holdings = []
            for doc in cursor:
                quantity = doc.get("quantity", 0)
                if quantity > 0:
                    code = doc.get("code")
                    holding = {
                        "code": code,
                        "name": doc.get("name"),
                        "quantity": quantity,
                        "average_cost": doc.get("average_cost", 0),
                    }
                    # Add industry information
                    if code:
                        holding["industry"] = self._industry_mapper.get_industry(code)
                    holdings.append(holding)
            return holdings
        except Exception as e:
            logger.error(f"Failed to get holdings for user {user_id}: {e}")
            return []

    async def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        job_name = "风险报告生成"

        user_ids = config.get("user_ids", [])
        if not user_ids:
            user_ids = [config.get("user_id", "default")]

        await self._send_notification(
            f"🔄 {job_name}开始",
            f"- 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n- 用户数: {len(user_ids)}",
        )

        try:
            generator = self._get_generator()
            results = []

            for user_id in user_ids:
                try:
                    holdings = await self._get_user_holdings(user_id)

                    if not holdings:
                        logger.info(f"No holdings found for user {user_id}")
                        continue

                    codes = [h.get("code") for h in holdings if h.get("code")]
                    prices = await self._fetch_latest_prices(codes)
                    price_fetcher = self._get_price_fetcher(prices)

                    report = await generator.generate_report(
                        user_id=user_id,
                        holdings=holdings,
                        price_fetcher=price_fetcher,
                    )

                    await generator.save_report(report)

                    # Get key recommendations
                    key_recommendations = []
                    for rec in report.recommendations[:3]:  # Top 3 recommendations
                        key_recommendations.append(rec)

                    # Get current holdings with industry info
                    current_holdings = []
                    for holding in holdings:
                        current_price = price_fetcher(holding.get("code", ""))
                        total_value = current_price * holding.get("quantity", 0)
                        pnl_pct = ((current_price - holding.get("average_cost", 0)) / holding.get("average_cost", 1)) * 100 if holding.get("average_cost", 0) > 0 else 0
                        current_holdings.append({
                            "code": holding.get("code"),
                            "name": holding.get("name"),
                            "industry": holding.get("industry"),
                            "quantity": holding.get("quantity"),
                            "average_cost": holding.get("average_cost"),
                            "current_price": current_price,
                            "total_value": total_value,
                            "pnl_pct": pnl_pct
                        })

                    # Get industry distribution from holdings
                    industry_info = []
                    industry_counts = {}
                    total_holdings = len(current_holdings)
                    
                    for holding in current_holdings:
                        industry = holding.get("industry", "未知")
                        industry_counts[industry] = industry_counts.get(industry, 0) + 1
                    
                    for industry, count in industry_counts.items():
                        percentage = (count / total_holdings) * 100 if total_holdings > 0 else 0
                        industry_info.append(f"{industry}: {percentage:.1f}%")
                    
                    # Sort by percentage descending
                    industry_info.sort(key=lambda x: float(x.split(': ')[1].rstrip('%')), reverse=True)

                    results.append({
                        "user_id": user_id,
                        "report_id": report.report_id,
                        "risk_score": report.risk_score,
                        "risk_level": report.risk_level,
                        "total_value": report.portfolio_risk.total_value,
                        "recommendations_count": len(report.recommendations),
                        "industry_info": industry_info,
                        "key_recommendations": key_recommendations,
                        "portfolio_var_95": report.portfolio_risk.portfolio_var_95,
                        "current_holdings": current_holdings
                    })

                except Exception as e:
                    logger.error(f"Failed to generate report for user {user_id}: {e}")
                    results.append({
                        "user_id": user_id,
                        "error": str(e),
                    })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            success_count = sum(1 for r in results if "report_id" in r)
            failed_count = sum(1 for r in results if "error" in r)

            summary_lines = []

            for r in results:
                if "report_id" in r:
                    level_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                        r.get("risk_level", "low"), "⚪"
                    )
                    summary_lines.append(
                        f"- 用户 {r['user_id']}: 风险评分 {r['risk_score']} {level_emoji}"
                    )
                    summary_lines.append(
                        f"- 总持仓价值: {r['total_value']:.2f}元"
                    )
                    if r.get("portfolio_var_95"):
                        summary_lines.append(
                            f"- 单日最大风险: {r['portfolio_var_95']:.2f}元"
                        )
                    
                    # Add current holdings
                    if r.get("current_holdings"):
                        summary_lines.append("- 当前持仓:")
                        for holding in r['current_holdings']:
                            pnl_emoji = "📈" if holding.get("pnl_pct", 0) >= 0 else "📉"
                            summary_lines.append(
                                f"  • {holding.get('code')} ({holding.get('industry', '未知')}): {holding.get('quantity')}股, 成本 {holding.get('average_cost'):.2f}, 现价 {holding.get('current_price'):.2f}, {pnl_emoji} {holding.get('pnl_pct', 0):.1f}%"
                            )
                    
                    # Add industry distribution
                    if r.get("industry_info"):
                        summary_lines.append("- 行业分布:")
                        for industry in r['industry_info']:
                            summary_lines.append(f"  • {industry}")
                    
                    # Add key recommendations
                    if r.get("key_recommendations"):
                        summary_lines.append("- 关键建议:")
                        for rec in r['key_recommendations']:
                            summary_lines.append(f"  • {rec}")

            await self._send_notification(
                f"✅ {job_name}完成" if failed_count == 0 else f"⚠️ {job_name}部分完成",
                "\n".join(summary_lines),
            )

            return {
                "results": results,
                "success_count": success_count,
                "failed_count": failed_count,
                "duration": duration,
                "status": "success" if failed_count == 0 else "partial",
            }

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._send_notification(
                f"❌ {job_name}异常",
                f"- 错误信息: {str(e)}\n- 耗时: {duration:.1f}秒",
            )

            logger.error(f"RiskReportJob failed: {e}")
            raise

        finally:
            generator = self._get_generator()
            if generator:
                generator.close()


async def risk_report_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    job = RiskReportJob(config)
    return await job.run(config)
