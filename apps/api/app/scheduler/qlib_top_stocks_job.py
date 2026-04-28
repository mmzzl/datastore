import logging
from typing import Any, Dict

from .top_stocks_task import refresh_top_stocks

logger = logging.getLogger(__name__)


class QlibTopStocksJob:
    """
    Job handler for refreshing top stocks.
    Submits the task to Celery instead of executing directly,
    so it won't block the main FastAPI service.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def run(self) -> Dict[str, Any]:
        """
        Submit the top stocks refresh task to Celery.
        
        Returns:
            Dictionary with task status and task_id
        """
        try:
            logger.info("Submitting top stocks refresh task to Celery")
            
            # Submit task to Celery
            task = refresh_top_stocks.delay(self.config)
            
            logger.info(f"Top stocks refresh task submitted with id: {task.id}")
            
            return {
                "status": "submitted",
                "task_id": task.id,
                "message": "Top stocks refresh task has been queued"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit top stocks refresh task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to queue top stocks refresh task"
            }


async def qlib_top_stocks_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for JobManager.
    """
    job = QlibTopStocksJob(config)
    return await job.run()
