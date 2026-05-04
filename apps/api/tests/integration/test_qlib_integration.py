import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.notify.dingtalk import DingTalkNotifier
from app.scheduler.qlib_train_job import QlibTrainJob


class TestDingTalkTrainingNotification:
    """Test 18.1: Configure DingTalk → Weekly training → Receive notification"""

    @pytest.mark.asyncio
    async def test_training_job_dispatches_to_celery(self):
        config = {
            "model_type": "lgbm",
            "instruments": "csi300",
        }

        with patch("app.scheduler.qlib_train_job.celery_app") as mock_celery:
            mock_task = MagicMock()
            mock_task.id = "celery_task_001"
            mock_celery.send_task.return_value = mock_task

            job = QlibTrainJob(config)
            result = await job.run(config)

        mock_celery.send_task.assert_called_once_with(
            "app.qlib.train_task.run_training",
            kwargs={"config": config},
        )
        assert result == {
            "status": "submitted",
            "task_id": "celery_task_001",
            "message": "Qlib training task has been queued",
        }

    @pytest.mark.asyncio
    async def test_training_job_returns_failed_on_celery_error(self):
        config = {"model_type": "lgbm"}

        with patch("app.scheduler.qlib_train_job.celery_app") as mock_celery:
            mock_celery.send_task.side_effect = Exception("Redis unavailable")

            job = QlibTrainJob(config)
            result = await job.run(config)

        assert result["status"] == "failed"
        assert "Redis unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_dingtalk_config_round_trip(self, test_db):
        from app.core.encryption import encrypt_value, decrypt_value

        webhook = "https://oapi.dingtalk.com/robot/send?access_token=test123"
        secret = "SEC123456"

        encrypted_webhook = encrypt_value(webhook)
        encrypted_secret = encrypt_value(secret)

        assert decrypt_value(encrypted_webhook) == webhook
        assert decrypt_value(encrypted_secret) == secret

    @pytest.mark.asyncio
    async def test_dingtalk_skip_when_no_webhook(self):
        notifier = DingTalkNotifier(webhook_url="", secret="")
        result = notifier.send(msg="test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_dingtalk_config_storage_and_retrieval(self, test_db):
        from app.core.encryption import encrypt_value
        
        collection = test_db["dingtalk_configs"]
        
        config_doc = {
            "user_id": "test_user_001",
            "name": "Test DingTalk",
            "webhook": encrypt_value("https://oapi.dingtalk.com/robot/send?access_token=test"),
            "secret": encrypt_value("test_secret"),
            "is_active": True,
            "created_at": datetime.now(),
        }
        
        collection.insert_one(config_doc)
        
        retrieved = collection.find_one({"user_id": "test_user_001", "is_active": True})
        assert retrieved is not None
        assert retrieved["user_id"] == "test_user_001"

        collection.delete_many({"user_id": "test_user_001"})
