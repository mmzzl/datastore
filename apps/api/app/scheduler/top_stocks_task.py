"""
Celery Task for Refreshing Top Stocks

This module provides Celery task to refresh top stock recommendations
without blocking the main FastAPI service.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from app.celery_app import celery_app
from app.qlib import QlibPredictor
from app.experiment.tracker import ExperimentTracker
from app.qlib.top_stocks_manager import TopStocksManager
from app.notify.dingtalk import DingTalkNotifier
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_top_stocks(self, config: Dict[str, Any]):
    """
    Celery task to refresh top stock recommendations.
    
    Args:
        config: Configuration dictionary for the task
            - dingtalk_webhook: Webhook for DingTalk notifications
            - dingtalk_secret: Secret for DingTalk notifications
            
    Returns:
        Task result dictionary
    """
    task_id = self.request.id
    logger.info(f"Starting top stocks refresh task {task_id}")
    
    try:
        tracker = ExperimentTracker()
        best = tracker.get_best("backtest_result.sharpe_ratio")
        
        if best is None:
            logger.warning("No completed experiment found, skipping top stocks job")
            return {"status": "skipped", "reason": "no_completed_experiment"}
        
        model_id = best.get("model_id")
        if not model_id:
            logger.warning("Best experiment has no model_id, skipping")
            return {"status": "skipped", "reason": "no_model_id"}
        
        model_config = best.get("config", {})
        today = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Using model {model_id} to predict top stocks for {today}")
        
        predictor = QlibPredictor()
        predictions = predictor.predict(
            model_id=model_id,
            topk=10,
            date=today
        )
        
        stocks = [
            {"rank": p.get("rank", i + 1), "code": p.get("code", ""), 
             "name": p.get("name", ""), "score": p.get("score", 0.0)}
            for i, p in enumerate(predictions[:10])
        ]
        
        manager = TopStocksManager()
        manager.save_top_stocks(
            date=today,
            model_id=model_id,
            model_type=model_config.get("model_type", "lgbm"),
            factor=model_config.get("factor_type", "alpha158"),
            stocks=stocks
        )
        
        logger.info(f"Top stocks saved successfully for {today}")
        
        # Send DingTalk notification
        webhook = config.get("dingtalk_webhook", settings.after_market_dingtalk_webhook)
        secret = config.get("dingtalk_secret", settings.after_market_dingtalk_secret)
        
        if webhook:
            try:
                notifier = DingTalkNotifier(webhook_url=webhook, secret=secret)
                stock_list = "\n".join([f"{s['rank']}. {s['code']} {s['name']} ({s['score']:.4f})" for s in stocks])
                markdown = f"# Top10 股票推荐已更新\n\n- **日期**: {today}\n- **模型**: {model_id}\n\n## Top10 股票\n{stock_list}"
                notifier.send(markdown=markdown)
                logger.info("DingTalk notification sent")
            except Exception as e:
                logger.warning(f"Failed to send DingTalk notification: {e}")
        
        result = {
            "status": "success",
            "date": today,
            "model_id": model_id,
            "count": len(stocks),
            "stocks": stocks
        }
        
        logger.info(f"Top stocks refresh task {task_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Top stocks refresh task {task_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Send failure notification
        try:
            webhook = config.get("dingtalk_webhook", settings.after_market_dingtalk_webhook)
            secret = config.get("dingtalk_secret", settings.after_market_dingtalk_secret)
            if webhook:
                notifier = DingTalkNotifier(webhook_url=webhook, secret=secret)
                markdown = f"# Top10 股票推荐更新失败\n\n- **错误**: {str(e)}"
                notifier.send(markdown=markdown)
        except Exception as notify_e:
            logger.warning(f"Failed to send failure notification: {notify_e}")
        
        # Retry on certain errors
        is_retryable = any(keyword in str(e).lower() for keyword in 
                          ["timeout", "connection", "unavailable", "retry"])
        if is_retryable and self.request.retries < self.max_retries:
            logger.warning(f"Will retry task {task_id} ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        raise
