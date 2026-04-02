import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.action.runner import ActionRunner


class TestActionRunner:
    @pytest.fixture
    def action_runner(self):
        return ActionRunner()

    @pytest.mark.asyncio
    async def test_run_action_unknown_command(self, action_runner):
        action = {
            "command": "unknown_command",
            "user_id": "test_user",
            "param": {},
        }

        result = await action_runner.run_action(action)

        assert result["success"] is False
        assert "Unknown command" in result["error"]

    @pytest.mark.asyncio
    async def test_run_backtest_success(self, action_runner):
        mock_engine = MagicMock()
        mock_engine.run_backtest = AsyncMock(return_value="task_123")

        with patch.object(action_runner, "_get_backtest_engine", return_value=mock_engine):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "run_backtest",
                    "user_id": "test_user",
                    "param": {
                        "strategy": "ma_cross",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                        "instruments": ["SH600000"],
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is True
                assert result["task_id"] == "task_123"
                assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_run_backtest_validation_error(self, action_runner):
        mock_engine = MagicMock()
        mock_engine.run_backtest = AsyncMock(side_effect=ValueError("Invalid config"))

        with patch.object(action_runner, "_get_backtest_engine", return_value=mock_engine):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "run_backtest",
                    "user_id": "test_user",
                    "param": {
                        "strategy": "invalid_strategy",
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is False
                assert "Invalid config" in result["error"]

    @pytest.mark.asyncio
    async def test_run_selection_with_model_id(self, action_runner):
        mock_predictor = MagicMock()
        mock_predictor.predict = MagicMock(return_value=[
            {"code": "SH600000", "name": "浦发银行", "score": 0.85},
            {"code": "SH600001", "name": "邯郸钢铁", "score": 0.82},
        ])

        mock_model_manager = MagicMock()
        mock_model_manager.get_model_metadata = MagicMock(return_value={
            "model_id": "model_123",
            "status": "approved",
        })

        with patch.object(action_runner, "_get_predictor", return_value=mock_predictor):
            with patch.object(action_runner, "_get_model_manager", return_value=mock_model_manager):
                with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                    action = {
                        "command": "run_selection",
                        "user_id": "test_user",
                        "param": {
                            "model_id": "model_123",
                            "topk": 50,
                        },
                    }

                    result = await action_runner.run_action(action)

                    assert result["success"] is True
                    assert result["model_id"] == "model_123"
                    assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_run_selection_no_approved_model(self, action_runner):
        mock_model_manager = MagicMock()
        mock_model_manager.get_latest_model = MagicMock(return_value=None)

        with patch.object(action_runner, "_get_model_manager", return_value=mock_model_manager):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "run_selection",
                    "user_id": "test_user",
                    "param": {
                        "topk": 50,
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is False
                assert "No approved model" in result["error"]

    @pytest.mark.asyncio
    async def test_run_selection_model_not_found(self, action_runner):
        mock_model_manager = MagicMock()
        mock_model_manager.get_model_metadata = MagicMock(return_value=None)

        with patch.object(action_runner, "_get_model_manager", return_value=mock_model_manager):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "run_selection",
                    "user_id": "test_user",
                    "param": {
                        "model_id": "nonexistent_model",
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is False
                assert "Model not found" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_plugin_missing_zip_path(self, action_runner):
        with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
            action = {
                "command": "validate_plugin",
                "user_id": "test_user",
                "param": {},
            }

            result = await action_runner.run_action(action)

            assert result["success"] is False
            assert "zip_path is required" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_plugin_success(self, action_runner):
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.manifest = {"name": "test_plugin"}
        mock_result.strategy_files = ["strategy.py"]
        mock_validator.validate_all = MagicMock(return_value=mock_result)

        with patch.object(action_runner, "_get_plugin_validator", return_value=mock_validator):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "validate_plugin",
                    "user_id": "test_user",
                    "param": {
                        "zip_path": "/path/to/plugin.zip",
                        "manifest": {"name": "test_plugin", "version": "1.0.0"},
                        "strategy_code": "class TestStrategy: pass",
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is True
                assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_plugin_with_errors(self, action_runner):
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.valid = False
        mock_result.errors = ["Missing required field: name"]
        mock_result.warnings = []
        mock_result.manifest = None
        mock_result.strategy_files = []
        mock_validator.validate_all = MagicMock(return_value=mock_result)

        with patch.object(action_runner, "_get_plugin_validator", return_value=mock_validator):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock):
                action = {
                    "command": "validate_plugin",
                    "user_id": "test_user",
                    "param": {
                        "zip_path": "/path/to/plugin.zip",
                    },
                }

                result = await action_runner.run_action(action)

                assert result["success"] is False
                assert "Missing required field" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_save_action_log(self, action_runner):
        mock_storage = MagicMock()
        mock_collection = MagicMock()
        mock_storage.db = {"action_logs": mock_collection}

        with patch.object(action_runner, "_get_storage", return_value=mock_storage):
            await action_runner._save_action_log(
                action_id="action_123",
                command="run_backtest",
                user_id="user_123",
                instance={},
                param={"strategy": "ma_cross"},
                result={"success": True, "task_id": "task_123"},
                success=True,
                start_time=datetime.now(),
            )

            mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_action_logs_exception(self, action_runner):
        mock_engine = MagicMock()
        mock_engine.run_backtest = AsyncMock(side_effect=Exception("Unexpected error"))

        with patch.object(action_runner, "_get_backtest_engine", return_value=mock_engine):
            with patch.object(action_runner, "_save_action_log", new_callable=AsyncMock) as mock_log:
                action = {
                    "command": "run_backtest",
                    "user_id": "test_user",
                    "param": {},
                }

                result = await action_runner.run_action(action)

                assert result["success"] is False
                assert "Unexpected error" in result["error"]
                mock_log.assert_called()
