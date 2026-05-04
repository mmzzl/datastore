import logging
import time
from datetime import datetime

from pymongo import MongoClient

from app.celery_app import celery_app
from app.qlib.trainer import QlibTrainer
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_executions_collection():
    client = MongoClient(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    return client[settings.mongodb_database]["job_executions"]


def _get_notifier():
    """Get DingTalk notifier if configured."""
    try:
        from app.notify.dingtalk import DingTalkNotifier

        webhook = settings.after_market_dingtalk_webhook
        secret = settings.after_market_dingtalk_secret
        if webhook:
            return DingTalkNotifier(webhook_url=webhook, secret=secret)
    except Exception:
        pass
    return None


def _send_dingtalk(title: str, content: str):
    notifier = _get_notifier()
    if notifier:
        try:
            markdown = f"## {title}\n\n{content}"
            notifier.send(markdown=markdown)
        except Exception as e:
            logger.warning(f"Failed to send DingTalk notification: {e}")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def run_training(self, config: dict):
    task_id = self.request.id
    coll = _get_executions_collection()

    job_name = "Qlib模型训练"
    model_type = config.get("model_type", "lgbm")
    instruments = config.get("instruments", "csi300")

    try:
        coll.insert_one({
            "task_id": task_id,
            "job_id": "qlib_train",
            "job_type": "qlib_train",
            "status": "running",
            "progress": 0,
            "message": "starting",
            "config": config,
            "created_at": datetime.now(),
            "started_at": datetime.now(),
        })
    except Exception:
        coll.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "running",
                "progress": 0,
                "message": "starting",
                "updated_at": datetime.now(),
            }}
        )

    _send_dingtalk(
        f"\U0001f504 {job_name}开始",
        f"- 任务类型: Qlib模型训练\n"
        f"- 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型类型: {model_type}\n"
        f"- 股票池: {instruments}",
    )

    trainer = QlibTrainer(
        model_dir=config.get("model_dir", settings.qlib_model_dir),
        min_sharpe_ratio=config.get("min_sharpe_ratio", settings.qlib_min_sharpe_ratio),
    )

    training_config = {
        "instruments": instruments,
        "start_time": config.get("start_time", "2015-01-01"),
        "end_time": config.get("end_time", datetime.now().strftime("%Y-%m-%d")),
        "model_type": model_type,
        "factor_type": config.get("factor_type", "alpha158"),
    }

    internal_task_id = trainer.start_training(training_config)

    try:
        while True:
            status = trainer.get_status(internal_task_id)
            current_status = status.get("status")
            progress = status.get("progress", 0)
            message = status.get("progress_message", "")

            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "running",
                    "progress": progress,
                    "message": message,
                    "updated_at": datetime.now(),
                }}
            )
            self.update_state(state="PROGRESS", meta={"progress": progress, "message": message})

            try:
                from celery.app.control import Inspect
                i = Inspect(app=celery_app)
                revoked = i.revoked()
                if revoked and task_id in revoked:
                    logger.info(f"Task {task_id} revoked by user")
                    coll.update_one(
                        {"task_id": task_id},
                        {"$set": {"status": "revoked", "message": "Cancelled by user", "completed_at": datetime.now()}}
                    )
                    _send_dingtalk(
                        f"⚠️ {job_name}已取消",
                        f"- 任务ID: {task_id}\n- 取消时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    )
                    del trainer
                    return {"status": "revoked", "message": "Cancelled by user"}
            except Exception:
                pass

            if current_status in ("completed", "failed", "cancelled"):
                break

            time.sleep(10)

        if current_status == "completed":
            metrics = status.get("metrics", {})
            model_id = status.get("model_id", "")
            result = {"model_id": model_id, "metrics": metrics, "status": "success"}
            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "success",
                    "progress": 100,
                    "result": result,
                    "message": "completed",
                    "completed_at": datetime.now(),
                }}
            )

            _send_dingtalk(
                f"✅ {job_name}完成",
                f"- 任务ID: {task_id}\n"
                f"- 模型ID: {model_id}\n"
                f"- Sharpe比率: {metrics.get('sharpe_ratio', 0):.4f}\n"
                f"- IC: {metrics.get('ic', 0):.4f}\n"
                f"- 预测数量: {metrics.get('num_predictions', 0)}",
            )

            return result
        else:
            error = status.get("error", "Unknown error")
            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "failed",
                    "error_message": error,
                    "completed_at": datetime.now(),
                }}
            )

            _send_dingtalk(
                f"❌ {job_name}失败",
                f"- 任务ID: {task_id}\n"
                f"- 错误信息: {error}\n"
                f"- 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            )

            raise RuntimeError(error)

    except Exception as e:
        is_mongo_error = "ServerSelectionTimeoutError" in str(e) or "Connection refused" in str(e) or "AutoReconnect" in str(e)
        if is_mongo_error and self.request.retries < self.max_retries:
            logger.warning(f"MongoDB unavailable, will retry ({self.request.retries + 1}/{self.max_retries}): {e}")
            raise self.retry(exc=e)

        _send_dingtalk(
            f"❌ {job_name}异常",
            f"- 任务ID: {task_id}\n"
            f"- 错误信息: {str(e)}\n"
            f"- 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

        coll_none = _get_executions_collection()
        try:
            coll_none.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.now(),
                }}
            )
        except Exception:
            pass
        raise
