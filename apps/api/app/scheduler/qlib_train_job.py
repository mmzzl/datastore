"""
Qlib Training Job Handler

Submits Qlib model training to Celery (fire-and-forget),
so it won't block the main FastAPI/APScheduler process.
"""

import logging
from typing import Any, Dict

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


class QlibTrainJob:
    """Submits Qlib model training to Celery."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Submitting Qlib training task to Celery")

            task = celery_app.send_task(
                "app.qlib.train_task.run_training",
                kwargs={"config": config},
            )

            logger.info(f"Qlib training task submitted with id: {task.id}")

            return {
                "status": "submitted",
                "task_id": task.id,
                "message": "Qlib training task has been queued",
            }

        except Exception as e:
            logger.error(f"Failed to submit Qlib training task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to queue Qlib training task",
            }


async def qlib_train_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    job = QlibTrainJob(config)
    return await job.run(config)
