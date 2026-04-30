"""
每日选股推荐 Job

收盘后运行 StockSelectionEngine，取 Top 10 结果，通过 DingTalk 推送。
"""

import asyncio
import logging
from datetime import datetime

from app.notify.dingtalk import DingTalkNotifier
from app.core.config import settings

logger = logging.getLogger(__name__)


class DailyRecommendationJob:
    def __init__(self, config: dict):
        self.config = config

    def _init_notifier(self) -> DingTalkNotifier:
        after_market = self.config.get("after_market", {})
        webhook = after_market.get("dingtalk_webhook") or settings.after_market_dingtalk_webhook
        secret = after_market.get("dingtalk_secret") or settings.after_market_dingtalk_secret
        if not webhook:
            logger.warning("DingTalk webhook not configured")
        return DingTalkNotifier(webhook_url=webhook or "", secret=secret or "")

    async def run(self) -> str:
        now = datetime.now()
        if now.weekday() >= 5:
            logger.info("Weekend, skipping daily recommendation")
            return "周末跳过"

        notifier = self._init_notifier()
        date_str = now.strftime("%Y-%m-%d")

        logger.info(f"Starting daily recommendation for {date_str}")

        try:
            from app.stock_selection.engine import get_selection_engine
            from app.schemas.stock_selection import StockPoolType, SelectionStatus

            engine = get_selection_engine()

            strategy_type = self.config.get("recommendation_strategy", "macd_cross")
            strategy_params = self.config.get("recommendation_params", {})
            stock_pool = StockPoolType(self.config.get("recommendation_pool", "all"))

            task_id = await engine.run_selection(
                strategy_type=strategy_type,
                strategy_params=strategy_params,
                stock_pool=stock_pool,
            )

            task = engine.get_task(task_id)
            if not task or task.status == SelectionStatus.FAILED:
                error_msg = task.error if task else "任务丢失"
                logger.error(f"Daily recommendation failed: {error_msg}")
                notifier.send(markdown=f"## 选股推荐失败 ({date_str})\n\n{error_msg}")
                return f"选股失败: {error_msg}"

            results = task.results[:10]
            if not results:
                logger.info("No stocks selected today")
                return "今日无推荐股票"

            # Build markdown table
            lines = [f"## 每日选股推荐 Top{len(results)} ({date_str})\n"]
            lines.append("| 排名 | 代码 | 名称 | 评分 | 行业 | 信号强度 |")
            lines.append("|------|------|------|------|------|---------|")

            for i, r in enumerate(results, 1):
                lines.append(
                    f"| {i} | {r.code} | {r.name} | {r.score:.1f} | "
                    f"{r.industry or '-'} | {r.signal_strength} |"
                )

            if task.ai_result and task.ai_result.summary:
                lines.append(f"\n> AI 分析：{task.ai_result.summary}")

            lines.append("\n> 仅供参考，不构成投资建议")

            markdown = "\n".join(lines)
            notifier.send(markdown=markdown)

            logger.info(f"Daily recommendation sent: {len(results)} stocks")
            return f"推荐 {len(results)} 只股票"

        except Exception as e:
            logger.error(f"Daily recommendation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                notifier.send(markdown=f"## 选股推荐失败 ({date_str})\n\n{e}")
            except Exception:
                pass
            raise


def daily_recommendation_handler(config: dict):
    """Async handler for JobManager."""
    job = DailyRecommendationJob(config)
    return job.run()
