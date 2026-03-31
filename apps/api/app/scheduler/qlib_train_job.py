"""
Qlib Training Job Handler

Executes weekly Qlib model training with DingTalk notifications.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..qlib import QlibTrainer
from ..notify.dingtalk import DingTalkNotifier
from ..core.config import settings

logger = logging.getLogger(__name__)


class QlibTrainJob:
    """Weekly Qlib model training job."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._trainer: Optional[QlibTrainer] = None
        self._notifier: Optional[DingTalkNotifier] = None

    def _get_trainer(self) -> QlibTrainer:
        if self._trainer is None:
            self._trainer = QlibTrainer(
                model_dir=self.config.get("model_dir", "./models"),
                min_sharpe_ratio=self.config.get("min_sharpe_ratio", 1.5),
            )
        return self._trainer

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

    async def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        job_name = "Qlib模型训练"

        await self._send_notification(
            f"🔄 {job_name}开始",
            f"- 任务类型: Qlib模型训练\n- 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n- 模型类型: {config.get('model_type', 'lgbm')}",
        )

        try:
            trainer = self._get_trainer()

            training_config = {
                "instruments": config.get("instruments", "csi300"),
                "start_time": config.get("start_time", "2015-01-01"),
                "end_time": config.get("end_time", datetime.now().strftime("%Y-%m-%d")),
                "model_type": config.get("model_type", "lgbm"),
                "factor_type": config.get("factor_type", "alpha158"),
            }

            task_id = await asyncio.to_thread(
                trainer.start_training,
                training_config,
            )

            while True:
                status = trainer.get_status(task_id)
                current_status = status.get("status")

                if current_status in ("completed", "failed", "cancelled"):
                    break

                await asyncio.sleep(10)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if current_status == "completed":
                metrics = status.get("metrics", {})
                model_id = status.get("model_id", "")

                success_content = (
                    f"- 任务ID: {task_id}\n"
                    f"- 模型ID: {model_id}\n"
                    f"- 耗时: {duration:.1f}秒\n"
                    f"- Sharpe比率: {metrics.get('sharpe_ratio', 0):.4f}\n"
                    f"- IC: {metrics.get('ic', 0):.4f}\n"
                    f"- 预测数量: {metrics.get('num_predictions', 0)}"
                )

                await self._send_notification(
                    f"✅ {job_name}完成",
                    success_content,
                )

                return {
                    "task_id": task_id,
                    "model_id": model_id,
                    "metrics": metrics,
                    "duration": duration,
                    "status": "success",
                }
            else:
                error_msg = status.get("error", "Unknown error")

                await self._send_notification(
                    f"❌ {job_name}失败",
                    f"- 任务ID: {task_id}\n- 错误信息: {error_msg}\n- 耗时: {duration:.1f}秒",
                )

                raise RuntimeError(f"Training failed: {error_msg}")

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            await self._send_notification(
                f"❌ {job_name}异常",
                f"- 错误信息: {str(e)}\n- 耗时: {duration:.1f}秒",
            )

            logger.error(f"QlibTrainJob failed: {e}")
            raise


async def qlib_train_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    job = QlibTrainJob(config)
    return await job.run(config)
