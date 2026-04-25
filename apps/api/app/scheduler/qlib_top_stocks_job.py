import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..qlib import QlibPredictor
from ..experiment.tracker import ExperimentTracker
from ..qlib.top_stocks_manager import TopStocksManager
from ..notify.dingtalk import DingTalkNotifier
from ..core.config import settings

logger = logging.getLogger(__name__)


class QlibTopStocksJob:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._predictor: Optional[QlibPredictor] = None
        self._tracker: Optional[ExperimentTracker] = None
        self._top_stocks_mgr: Optional[TopStocksManager] = None
        self._notifier: Optional[DingTalkNotifier] = None

    def _get_predictor(self) -> QlibPredictor:
        if self._predictor is None:
            self._predictor = QlibPredictor()
        return self._predictor

    def _get_tracker(self) -> ExperimentTracker:
        if self._tracker is None:
            self._tracker = ExperimentTracker()
        return self._tracker

    def _get_top_stocks_manager(self) -> TopStocksManager:
        if self._top_stocks_mgr is None:
            self._top_stocks_mgr = TopStocksManager()
        return self._top_stocks_mgr

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

    async def _send_notification(self, title: str, content: str):
        notifier = self._get_notifier()
        if notifier:
            markdown = f"## {title}\n\n{content}"
            await asyncio.to_thread(notifier.send, markdown=markdown)

    async def run(self) -> Dict[str, Any]:
        try:
            tracker = self._get_tracker()
            best = tracker.get_best("backtest_result.sharpe_ratio")

            if best is None:
                logger.warning("No completed experiment found, skipping top stocks job")
                return {"status": "skipped", "reason": "no_completed_experiment"}

            model_id = best.get("model_id")
            if not model_id:
                logger.warning("Best experiment has no model_id, skipping")
                return {"status": "skipped", "reason": "no_model_id"}

            config = best.get("config", {})
            today = datetime.now().strftime("%Y-%m-%d")

            predictor = self._get_predictor()
            predictions = await asyncio.to_thread(
                predictor.predict,
                model_id=model_id,
                topk=10,
                date=today,
            )

            stocks = [
                {"rank": p.get("rank", i + 1), "code": p.get("code", ""), "name": p.get("name", ""), "score": p.get("score", 0.0)}
                for i, p in enumerate(predictions[:10])
            ]

            mgr = self._get_top_stocks_manager()
            mgr.save_top_stocks(
                date=today,
                model_id=model_id,
                model_type=config.get("model_type", "lgbm"),
                factor=config.get("factor_type", "alpha158"),
                stocks=stocks,
            )

            stock_list = "\n".join([f"{s['rank']}. {s['code']} {s['name']} ({s['score']:.4f})" for s in stocks])
            await self._send_notification(
                "Top10 Stock Prediction Done",
                f"- Date: {today}\n- Model: {model_id}\n- Top10:\n{stock_list}",
            )

            return {"status": "success", "date": today, "model_id": model_id, "count": len(stocks)}

        except Exception as e:
            logger.error(f"QlibTopStocksJob failed: {e}")
            await self._send_notification(
                "Top10 Stock Prediction Failed",
                f"Error: {str(e)}",
            )
            raise


async def qlib_top_stocks_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    job = QlibTopStocksJob(config)
    return await job.run()
