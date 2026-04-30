"""
持仓卖出信号汇总 Job

盘后扫描所有持仓，检查止损/止盈/追踪止损触发情况，汇总通过 DingTalk 推送。
无触发信号时不推送，避免噪音。
"""

import logging
from datetime import datetime

from app.storage.mongo_client import MongoStorage
from app.core.config import settings
from app.notify.dingtalk import DingTalkNotifier
from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)


class HoldingsSellAlertJob:
    def __init__(self, config: dict):
        self.config = config

    def _init_notifier(self) -> DingTalkNotifier:
        after_market = self.config.get("after_market", {})
        webhook = after_market.get("dingtalk_webhook") or settings.after_market_dingtalk_webhook
        secret = after_market.get("dingtalk_secret") or settings.after_market_dingtalk_secret
        if not webhook:
            logger.warning("DingTalk webhook not configured")
        return DingTalkNotifier(webhook_url=webhook or "", secret=secret or "")

    def _get_storage(self) -> MongoStorage:
        storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        storage.connect()
        return storage

    def run(self) -> str:
        now = datetime.now()
        if now.weekday() >= 5:
            logger.info("Weekend, skipping holdings sell alert")
            return "周末跳过"

        date_str = now.strftime("%Y-%m-%d")
        logger.info(f"Starting holdings sell alert scan for {date_str}")

        notifier = self._init_notifier()
        dm = DataSourceManager()

        try:
            storage = self._get_storage()
            holdings_coll = storage.db.get_collection("holdings")

            if holdings_coll is None:
                logger.warning("Holdings collection not found")
                return "无持仓集合"

            holdings = list(holdings_coll.find({"quantity": {"$gt": 0}}))
            if not holdings:
                logger.info("No holdings found")
                return "无持仓"

            stop_loss_signals = []
            profit_target_signals = []
            trailing_stop_signals = []

            for h in holdings:
                code = h.get("code", "")
                name = h.get("name", code)
                cost_price = h.get("average_cost", 0)
                if cost_price <= 0:
                    continue

                exit_rule = h.get("exit_rule", {
                    "stop_loss": 0.05,
                    "profit_target": 0.10,
                    "trailing_stop_pct": 0.03,
                })

                # Get current price
                current_price = cost_price
                try:
                    rt = dm.get_realtime_data(code)
                    if isinstance(rt, dict):
                        current_price = float(rt.get("price") or rt.get("close") or cost_price)
                except Exception:
                    continue

                if current_price <= 0:
                    continue

                profit_pct = (current_price - cost_price) / cost_price * 100

                # Check stop loss
                stop_loss_pct = exit_rule.get("stop_loss", 0.05)
                stop_loss_price = cost_price * (1 - stop_loss_pct)
                if current_price <= stop_loss_price:
                    stop_loss_signals.append({
                        "code": code, "name": name,
                        "cost": cost_price, "current": current_price,
                        "pct": profit_pct,
                    })
                    continue  # Don't double-alert

                # Check profit target (fixed strategy)
                profit_target = exit_rule.get("profit_target", 0.10)
                if profit_pct >= profit_target * 100:
                    profit_target_signals.append({
                        "code": code, "name": name,
                        "cost": cost_price, "current": current_price,
                        "pct": profit_pct,
                    })
                    continue

                # Check trailing stop
                highest_price = h.get("highest_price", cost_price)
                if current_price > highest_price:
                    highest_price = current_price
                    holdings_coll.update_one(
                        {"_id": h["_id"]},
                        {"$set": {"highest_price": highest_price}},
                    )

                trailing_pct = exit_rule.get("trailing_stop_pct", 0.03)
                trailing_stop_price = highest_price * (1 - trailing_pct)
                if current_price <= trailing_stop_price and highest_price > cost_price:
                    drawdown = (current_price - highest_price) / highest_price * 100
                    trailing_stop_signals.append({
                        "code": code, "name": name,
                        "cost": cost_price, "current": current_price,
                        "highest": highest_price, "drawdown": drawdown,
                    })

            storage.close()

            # Build notification
            has_signals = stop_loss_signals or profit_target_signals or trailing_stop_signals
            if not has_signals:
                logger.info("No sell signals triggered today")
                return "无卖出信号"

            lines = [f"## 持仓卖出提醒 ({date_str})\n"]

            if stop_loss_signals:
                lines.append("### ⚠️ 止损信号")
                for s in stop_loss_signals:
                    lines.append(
                        f"- **{s['code']} {s['name']}**: "
                        f"成本 {s['cost']:.2f}, 现价 {s['current']:.2f}, "
                        f"亏损 {s['pct']:.1f}%, 已触发止损"
                    )
                lines.append("")

            if profit_target_signals:
                lines.append("### 📈 止盈信号")
                for s in profit_target_signals:
                    lines.append(
                        f"- **{s['code']} {s['name']}**: "
                        f"成本 {s['cost']:.2f}, 现价 {s['current']:.2f}, "
                        f"盈利 {s['pct']:.1f}%, 已触发止盈"
                    )
                lines.append("")

            if trailing_stop_signals:
                lines.append("### 📉 追踪止损信号")
                for s in trailing_stop_signals:
                    lines.append(
                        f"- **{s['code']} {s['name']}**: "
                        f"最高 {s['highest']:.2f}, 现价 {s['current']:.2f}, "
                        f"回撤 {s['drawdown']:.1f}%, 已触发追踪止损"
                    )
                lines.append("")

            lines.append("> 仅供参考，不构成投资建议")

            markdown = "\n".join(lines)
            notifier.send(markdown=markdown)

            total = len(stop_loss_signals) + len(profit_target_signals) + len(trailing_stop_signals)
            logger.info(f"Holdings sell alert sent: {total} signals")
            return f"卖出信号 {total} 条"

        except Exception as e:
            logger.error(f"Holdings sell alert failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            try:
                dm.close_all()
            except Exception:
                pass


def holdings_sell_alert_handler(config: dict):
    """Handler for JobManager."""
    job = HoldingsSellAlertJob(config)
    return job.run()
