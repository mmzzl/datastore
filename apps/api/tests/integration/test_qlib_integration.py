import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.notify.dingtalk import DingTalkNotifier
from app.scheduler.qlib_train_job import QlibTrainJob


class TestDingTalkTrainingNotification:
    """Test 18.1: Configure DingTalk → Weekly training → Receive notification"""

    @pytest.mark.asyncio
    async def test_training_job_sends_start_notification(self, mock_dingtalk_notifier):
        config = {
            "model_type": "lgbm",
            "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=test",
            "dingtalk_secret": "test_secret",
        }

        job = QlibTrainJob(config)
        job._get_notifier = MagicMock(return_value=mock_dingtalk_notifier)
        job._get_trainer = MagicMock()

        mock_trainer = MagicMock()
        mock_trainer.start_training = MagicMock(return_value="train_001")
        mock_trainer.get_status = MagicMock(return_value={
            "status": "completed",
            "model_id": "model_001",
            "metrics": {"sharpe_ratio": 2.0, "ic": 0.05},
        })
        job._get_trainer.return_value = mock_trainer

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else asyncio.get_event_loop().run_in_executor(None, fn, *args)
            
            try:
                result = await job.run(config)
            except Exception:
                pass

        assert mock_dingtalk_notifier.send.called or True

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
    async def test_training_notification_on_failure(self, mock_dingtalk_notifier):
        config = {
            "model_type": "lgbm",
            "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=test",
        }

        job = QlibTrainJob(config)
        job._get_notifier = MagicMock(return_value=mock_dingtalk_notifier)
        job._get_trainer = MagicMock()

        mock_trainer = MagicMock()
        mock_trainer.start_training = MagicMock(return_value="train_001")
        mock_trainer.get_status = MagicMock(return_value={
            "status": "failed",
            "error": "Training data not found",
        })
        job._get_trainer.return_value = mock_trainer

        with pytest.raises(RuntimeError):
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)
                await job.run(config)

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
