import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestActionEndpoint:
    @pytest.fixture
    def mock_action_runner(self):
        runner = MagicMock()
        runner.run_action = AsyncMock(return_value={
            "action_id": "action_123",
            "success": True,
            "task_id": "task_123",
        })
        return runner

    def test_run_action_backtest_success(self, sync_client, auth_headers, mock_action_runner):
        with patch("app.api.endpoints.action.get_action_runner", return_value=mock_action_runner):
            response = sync_client.post(
                "/api/action/run",
                json={
                    "command": "run_backtest",
                    "instance": {},
                    "param": {
                        "strategy": "ma_cross",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    },
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_id"] == "action_123"

    def test_run_action_missing_permission(self, sync_client, viewer_auth_headers, mock_action_runner):
        with patch("app.api.endpoints.action.get_action_runner", return_value=mock_action_runner):
            response = sync_client.post(
                "/api/action/run",
                json={
                    "command": "run_backtest",
                    "instance": {},
                    "param": {
                        "strategy": "ma_cross",
                    },
                },
                headers=viewer_auth_headers,
            )

        assert response.status_code == 403

    def test_run_action_unknown_command(self, sync_client, auth_headers):
        response = sync_client.post(
            "/api/action/run",
            json={
                "command": "unknown_command",
                "instance": {},
                "param": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 400


class TestBacktestPermission:
    def test_run_backtest_success_with_permission(self, sync_client, trader_auth_headers):
        with patch("app.api.endpoints.backtest.get_backtest_engine") as mock_engine_getter:
            mock_engine = MagicMock()
            mock_engine.run_backtest = AsyncMock(return_value="task_123")
            mock_engine_getter.return_value = mock_engine

            response = sync_client.post(
                "/api/backtest/run",
                json={
                    "strategy": "ma_cross",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "instruments": ["SH600000"],
                },
                headers=trader_auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task_123"

    def test_run_backtest_missing_permission(self, sync_client, viewer_auth_headers):
        response = sync_client.post(
            "/api/backtest/run",
            json={
                "strategy": "ma_cross",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
            headers=viewer_auth_headers,
        )

        assert response.status_code == 403

    def test_get_backtest_results_with_permission(self, sync_client, trader_auth_headers):
        with patch("app.api.endpoints.backtest.get_storage") as mock_storage_getter:
            mock_storage = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count_documents = MagicMock(return_value=0)
            mock_collection.find = MagicMock(return_value=[])
            mock_storage.db = {"backtest_results": mock_collection}
            mock_storage_getter.return_value = mock_storage

            response = sync_client.get(
                "/api/backtest/results",
                headers=trader_auth_headers,
            )

        assert response.status_code == 200

    def test_run_backtest_with_plugin_strategy(self, sync_client, trader_auth_headers):
        with patch("app.api.endpoints.backtest.get_backtest_engine") as mock_engine_getter:
            mock_engine = MagicMock()
            mock_engine.run_backtest = AsyncMock(return_value="task_456")
            mock_engine_getter.return_value = mock_engine

            response = sync_client.post(
                "/api/backtest/run",
                json={
                    "strategy": "plugin",
                    "plugin_id": "plugin_123",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "instruments": ["SH600000"],
                },
                headers=trader_auth_headers,
            )

        assert response.status_code == 200

    def test_run_backtest_plugin_missing_plugin_id(self, sync_client, trader_auth_headers):
        response = sync_client.post(
            "/api/backtest/run",
            json={
                "strategy": "plugin",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
            headers=trader_auth_headers,
        )

        assert response.status_code == 400


class TestQlibPermission:
    def test_select_stocks_with_permission(self, sync_client, trader_auth_headers):
        with patch("app.api.endpoints.qlib.get_predictor") as mock_predictor_getter:
            with patch("app.api.endpoints.qlib.get_model_manager") as mock_manager_getter:
                mock_predictor = MagicMock()
                mock_predictor.predict = MagicMock(return_value=[
                    {"code": "SH600000", "name": "浦发银行", "score": 0.85}
                ])
                mock_predictor_getter.return_value = mock_predictor

                mock_manager = MagicMock()
                mock_manager.get_latest_model = MagicMock(return_value={
                    "model_id": "model_123",
                    "status": "approved",
                })
                mock_manager_getter.return_value = mock_manager

                response = sync_client.post(
                    "/api/qlib/select",
                    json={
                        "topk": 50,
                    },
                    headers=trader_auth_headers,
                )

        assert response.status_code == 200

    def test_select_stocks_missing_permission(self, sync_client, viewer_auth_headers):
        response = sync_client.post(
            "/api/qlib/select",
            json={"topk": 50},
            headers=viewer_auth_headers,
        )

        assert response.status_code == 403


class TestSchedulerPermission:
    def test_list_jobs_with_permission(self, sync_client, auth_headers):
        with patch("app.api.endpoints.scheduler.get_job_manager") as mock_getter:
            mock_manager = MagicMock()
            mock_manager.list_jobs = AsyncMock(return_value=([], 0))
            mock_getter.return_value = mock_manager

            response = sync_client.get(
                "/api/scheduler/jobs",
                headers=auth_headers,
            )

        assert response.status_code == 200

    def test_list_jobs_missing_permission(self, sync_client, viewer_auth_headers):
        response = sync_client.get(
            "/api/scheduler/jobs",
            headers=viewer_auth_headers,
        )

        assert response.status_code == 403

    def test_create_job_with_permission(self, sync_client, auth_headers):
        with patch("app.api.endpoints.scheduler.get_job_manager") as mock_getter:
            mock_manager = MagicMock()
            mock_manager.create_job = AsyncMock(return_value="job_123")
            mock_manager.get_job = AsyncMock(return_value={
                "job_id": "job_123",
                "name": "Test Job",
                "job_type": "qlib_train",
                "cron_expression": "0 2 * * *",
                "enabled": True,
                "config": {},
            })
            mock_getter.return_value = mock_manager

            response = sync_client.post(
                "/api/scheduler/jobs",
                json={
                    "name": "Test Job",
                    "job_type": "qlib_train",
                    "cron_expression": "0 2 * * *",
                    "enabled": True,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200

    def test_create_job_missing_permission(self, sync_client, viewer_auth_headers):
        response = sync_client.post(
            "/api/scheduler/jobs",
            json={
                "name": "Test Job",
                "job_type": "qlib_train",
                "cron_expression": "0 2 * * *",
            },
            headers=viewer_auth_headers,
        )

        assert response.status_code == 403


class TestDingTalkPermission:
    def test_list_configs_with_permission(self, sync_client, auth_headers):
        with patch("app.api.endpoints.dingtalk.get_collection") as mock_getter:
            mock_collection = MagicMock()
            mock_collection.find = MagicMock(return_value=[])
            mock_getter.return_value = mock_collection

            response = sync_client.get(
                "/api/dingtalk/configs/user_123",
                headers=auth_headers,
            )

        assert response.status_code == 200

    def test_list_configs_missing_permission(self, sync_client):
        response = sync_client.get(
            "/api/dingtalk/configs/user_123",
        )

        assert response.status_code in [401, 403]


class TestRiskPermission:
    def test_get_reports_with_permission(self, sync_client, auth_headers):
        with patch("app.risk.api.get_storage") as mock_getter:
            mock_storage = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count_documents = MagicMock(return_value=0)
            mock_collection.find = MagicMock(return_value=[])
            mock_storage.db = MagicMock()
            mock_storage.db.get_collection = MagicMock(return_value=mock_collection)
            mock_getter.return_value = mock_storage

            response = sync_client.get(
                "/api/risk/reports",
                headers=auth_headers,
            )

        assert response.status_code == 200

    def test_get_reports_missing_permission(self, sync_client):
        response = sync_client.get(
            "/api/risk/reports",
        )

        assert response.status_code in [401, 403]
