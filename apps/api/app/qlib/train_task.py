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


@celery_app.task(bind=True, max_retries=0)
def run_training(self, config: dict):
    task_id = self.request.id
    coll = _get_executions_collection()
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

    trainer = QlibTrainer(
        model_dir=config.get("model_dir", settings.qlib_model_dir),
        min_sharpe_ratio=config.get("min_sharpe_ratio", settings.qlib_min_sharpe_ratio),
    )

    training_config = {
        "instruments": config.get("instruments", "csi300"),
        "start_time": config.get("start_time", "2015-01-01"),
        "end_time": config.get("end_time", datetime.now().strftime("%Y-%m-%d")),
        "model_type": config.get("model_type", "lgbm"),
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

            if self.is_revoked():
                logger.info(f"Task {task_id} revoked by user")
                coll.update_one(
                    {"task_id": task_id},
                    {"$set": {"status": "revoked", "message": "Cancelled by user", "completed_at": datetime.now()}}
                )
                trainer.close()
                return {"status": "revoked", "message": "Cancelled by user"}

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
            raise RuntimeError(error)

    except Exception as e:
        coll.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(),
            }}
        )
        raise

    finally:
        trainer.close()
