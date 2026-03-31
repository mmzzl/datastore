"""
Risk Report Job Handler

Executes daily risk report generation with DingTalk notifications.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from ..risk import RiskReportGenerator
from ..notify.dingtalk import DingTalkNotifier
from ..core.config import settings
from ..storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)


class RiskReportJob:
    """Daily risk report generation job."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._generator: Optional[RiskReportGenerator] = None
        self._notifier: Optional[DingTalkNotifier] = None
        self._storage: Optional[MongoStorage] = None

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
                klines = await asyncio.to_thread(
                    storage.get_kline,
                    code,
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
            return [
                {
                    "code": doc.get("code"),
                    "name": doc.get("name"),
                    "quantity": doc.get("quantity", 0),
                    "average_cost": doc.get("average_cost", 0),
                }
                for doc in cursor
                if doc.get("quantity", 0) > 0
            ]
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

                    results.append({
                        "user_id": user_id,
                        "report_id": report.report_id,
                        "risk_score": report.risk_score,
                        "risk_level": report.risk_level,
                        "total_value": report.portfolio_risk.total_value,
                        "recommendations_count": len(report.recommendations),
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

            summary_lines = [
                f"- 耗时: {duration:.1f}秒",
                f"- 成功: {success_count}个",
                f"- 失败: {failed_count}个",
            ]

            for r in results:
                if "report_id" in r:
                    level_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                        r.get("risk_level", "low"), "⚪"
                    )
                    summary_lines.append(
                        f"- 用户 {r['user_id']}: 风险评分 {r['risk_score']} {level_emoji}"
                    )

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
