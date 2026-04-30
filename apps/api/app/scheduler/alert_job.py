from datetime import datetime
from typing import Dict, Any, Optional
import logging

from app.monitor.alert_orchestrator import AlertOrchestrator
from app.monitor.notification.priority_notifier import PriorityNotifier
from app.notify.dingtalk import DingTalkNotifier
from app.storage.mongo_client import MongoStorage
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertOrchestratorJob:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.orchestrator = None
        self.notifier = None

    def _init_notifier(self):
        after_market = self.config.get("after_market", {})
        webhook = after_market.get("dingtalk_webhook")
        secret = after_market.get("dingtalk_secret")

        if webhook:
            dingtalk = DingTalkNotifier(webhook_url=webhook, secret=secret or "")
            self.notifier = PriorityNotifier(dingtalk_client=dingtalk)
        else:
            self.notifier = PriorityNotifier(dingtalk_client=None)
            logger.warning(
                "DingTalk webhook not configured, notifications will be logged only"
            )

    def _get_watchlist(self) -> list:
        config_watchlist = self.config.get("watchlist", [])

        # 合并 DailySignalScanner 扫描出的 watch_list
        db_symbols = []
        try:
            storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            storage.connect()
            db_symbols = storage.get_watch_list()
            storage.close()
        except Exception as e:
            logger.error(f"Failed to load watch_list from DB: {e}")

        # 去重合并
        existing_codes = {item.get("code") for item in config_watchlist if item.get("code")}
        merged = list(config_watchlist)
        for symbol in db_symbols:
            if symbol not in existing_codes:
                merged.append({"code": symbol, "name": symbol})
                existing_codes.add(symbol)

        if not merged:
            merged = [
                {"code": "SH600000", "name": "浦发银行"},
                {"code": "SH600519", "name": "贵州茅台"},
            ]

        logger.info(
            f"Watchlist loaded: {len(merged)} stocks "
            f"({len(config_watchlist)} from config, "
            f"{len(merged) - len(config_watchlist)} from daily scanner)"
        )
        return merged

    def _get_news_keywords(self) -> dict:
        return self.config.get(
            "news_keywords",
            {
                "政策": ["降准", "加息", "LPR", "监管"],
                "利好": ["业绩预增", "订单", "合作", "重组"],
                "利空": ["业绩预减", "减持", "诉讼"],
                "黑天鹅": ["疫情", "地震", "制裁", "断供", "退市"],
            },
        )

    def run(self) -> str:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if now.weekday() >= 5:
            logger.info(f"Weekend, skipping alert orchestrator job")
            return "周末跳过预警任务"

        logger.info(f"Starting AlertOrchestratorJob at {date_str}")

        try:
            self._init_notifier()

            watchlist = self._get_watchlist()
            news_keywords = self._get_news_keywords()
            strategy_type = self.config.get("strategy_type", "all")

            self.orchestrator = AlertOrchestrator(
                interval_sec=60,
                watchlist=watchlist,
                strategy_type=strategy_type,
                news_keywords=news_keywords,
            )

            self.orchestrator.run_once()

            signals = self.orchestrator.signals_log
            critical_count = sum(1 for s in signals if s.get("priority") == "critical")
            high_count = sum(1 for s in signals if s.get("priority") == "high")
            medium_count = sum(1 for s in signals if s.get("priority") == "medium")
            low_count = sum(1 for s in signals if s.get("priority") == "low")

            for sig_dict in signals:
                from app.monitor.models.alert_signal import AlertSignal

                sig = AlertSignal(
                    timestamp=datetime.now(),
                    code=sig_dict.get("code", ""),
                    name=sig_dict.get("name", ""),
                    signal=sig_dict.get("signal", "hold"),
                    confidence=sig_dict.get("confidence", 0.5),
                    priority=sig_dict.get("priority", "medium"),
                    reasons=sig_dict.get("reasons", []),
                    price=sig_dict.get("price", 0.0),
                    alert_type=sig_dict.get("alert_type", "technical"),
                )
                self.notifier.send(sig)

            logger.info(
                f"AlertOrchestratorJob completed: "
                f"critical={critical_count}, high={high_count}, "
                f"medium={medium_count}, low={low_count}"
            )

            return (
                f"预警任务完成: critical={critical_count}, "
                f"high={high_count}, medium={medium_count}, low={low_count}"
            )

        except Exception as e:
            logger.error(f"AlertOrchestratorJob failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            raise
