"""Unified Action Runner

Provides a unified entry point for executing actions like backtests,
stock selection, and plugin validation.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.storage import MongoStorage
from app.backtest.async_engine import AsyncBacktestEngine
from app.backtest.plugin.validator import PluginValidator
from app.qlib import QlibPredictor, ModelManager

logger = logging.getLogger(__name__)


class ActionRunner:
    """Unified action runner for executing various system actions.

    Supported commands:
    - run_backtest: Execute a backtest task
    - run_selection: Run stock selection using Qlib model
    - validate_plugin: Validate a plugin package

    Example:
        >>> runner = ActionRunner()
        >>> result = await runner.run_action({
        ...     "command": "run_backtest",
        ...     "user_id": "user_123",
        ...     "param": {
        ...         "strategy": "ma_cross",
        ...         "start_date": "2023-01-01",
        ...         "end_date": "2023-12-31",
        ...     }
        ... })
    """

    def __init__(self):
        self._storage: Optional[MongoStorage] = None
        self._backtest_engine: Optional[AsyncBacktestEngine] = None
        self._plugin_validator: Optional[PluginValidator] = None
        self._predictor: Optional[QlibPredictor] = None
        self._model_manager: Optional[ModelManager] = None

    def _get_storage(self) -> MongoStorage:
        if self._storage is None:
            self._storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self._storage.connect()
        return self._storage

    def _get_backtest_engine(self) -> AsyncBacktestEngine:
        if self._backtest_engine is None:
            self._backtest_engine = AsyncBacktestEngine()
        return self._backtest_engine

    def _get_plugin_validator(self) -> PluginValidator:
        if self._plugin_validator is None:
            self._plugin_validator = PluginValidator()
        return self._plugin_validator

    def _get_predictor(self) -> QlibPredictor:
        if self._predictor is None:
            self._predictor = QlibPredictor()
        return self._predictor

    def _get_model_manager(self) -> ModelManager:
        if self._model_manager is None:
            self._model_manager = ModelManager()
        return self._model_manager

    async def run_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action from unified entry point.

        Args:
            action: Action configuration dict
                - command: Action type (run_backtest, run_selection, validate_plugin)
                - user_id: User initiating the action
                - instance: Optional instance config
                - param: Command-specific parameters

        Returns:
            Result dict with success/error info
        """
        command = action.get("command")
        user_id = action.get("user_id", "unknown")
        instance = action.get("instance", {})
        params = action.get("param", {})

        action_id = str(uuid.uuid4())
        start_time = datetime.now()

        handlers = {
            "run_backtest": self._run_backtest,
            "run_selection": self._run_selection,
            "validate_plugin": self._validate_plugin,
        }

        handler = handlers.get(command)
        if not handler:
            error_result = {
                "action_id": action_id,
                "success": False,
                "error": f"Unknown command: {command}",
            }
            await self._save_action_log(
                action_id=action_id,
                command=command,
                user_id=user_id,
                instance=instance,
                param=params,
                result=error_result,
                success=False,
                start_time=start_time,
            )
            return error_result

        try:
            result = await handler(user_id, instance, params)
            result["action_id"] = action_id

            await self._save_action_log(
                action_id=action_id,
                command=command,
                user_id=user_id,
                instance=instance,
                param=params,
                result=result,
                success=result.get("success", True),
                start_time=start_time,
            )

            return result

        except Exception as e:
            logger.error(f"Action {command} failed: {e}")
            error_result = {
                "action_id": action_id,
                "success": False,
                "error": str(e),
            }

            await self._save_action_log(
                action_id=action_id,
                command=command,
                user_id=user_id,
                instance=instance,
                param=params,
                result=error_result,
                success=False,
                start_time=start_time,
            )

            return error_result

    async def _run_backtest(
        self,
        user_id: str,
        instance: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a backtest task.

        Args:
            user_id: User ID
            instance: Instance config (optional)
            params: Backtest parameters
                - strategy: Strategy type
                - params: Strategy parameters
                - start_date: Start date (YYYY-MM-DD)
                - end_date: End date (YYYY-MM-DD)
                - initial_capital: Initial capital
                - instruments: List of stock codes

        Returns:
            Result dict with task_id and status
        """
        engine = self._get_backtest_engine()

        config = {
            "strategy": params.get("strategy", "ma_cross"),
            "params": params.get("params", {}),
            "start_date": params.get("start_date", ""),
            "end_date": params.get("end_date", ""),
            "initial_capital": params.get("initial_capital", 100000.0),
            "instruments": params.get("instruments", []),
        }

        if instance:
            config["instance"] = instance

        try:
            task_id = await engine.run_backtest(config)
            logger.info(f"Backtest started: task_id={task_id}, user={user_id}")

            return {
                "success": True,
                "task_id": task_id,
                "status": "pending",
                "message": "Backtest task started successfully",
            }

        except ValueError as e:
            logger.error(f"Invalid backtest config: {e}")
            return {
                "success": False,
                "error": str(e),
            }

        except Exception as e:
            logger.error(f"Failed to start backtest: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _run_selection(
        self,
        user_id: str,
        instance: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run stock selection using Qlib model.

        Args:
            user_id: User ID
            instance: Instance config (optional)
            params: Selection parameters
                - model_id: Model ID (optional, uses latest approved if not provided)
                - date: Selection date (optional)
                - topk: Number of stocks to select

        Returns:
            Result dict with selection results
        """
        predictor = self._get_predictor()
        model_manager = self._get_model_manager()

        model_id = params.get("model_id")
        date = params.get("date")
        topk = params.get("topk", 50)

        if model_id is None:
            latest_model = model_manager.get_latest_model(status="approved")
            if latest_model is None:
                return {
                    "success": False,
                    "error": "No approved model found. Please train a model first.",
                }
            model_id = latest_model.get("model_id")
        else:
            metadata = model_manager.get_model_metadata(model_id)
            if metadata is None:
                return {
                    "success": False,
                    "error": f"Model not found: {model_id}",
                }

        try:
            results = predictor.predict(
                model_id=model_id,
                topk=topk,
                date=date,
            )

            selection_results = [
                {
                    "rank": i + 1,
                    "code": r.get("code", ""),
                    "name": r.get("name"),
                    "score": r.get("score", 0.0),
                }
                for i, r in enumerate(results)
            ]

            logger.info(f"Selection completed: model={model_id}, count={len(results)}, user={user_id}")

            return {
                "success": True,
                "model_id": model_id,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "results": selection_results,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Stock selection failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _validate_plugin(
        self,
        user_id: str,
        instance: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate a plugin package.

        Args:
            user_id: User ID
            instance: Instance config (optional)
            params: Validation parameters
                - zip_path: Path to plugin ZIP file
                - manifest: Plugin manifest dict
                - strategy_code: Strategy source code
                - existing_versions: List of existing plugin versions

        Returns:
            Result dict with validation outcome
        """
        validator = self._get_plugin_validator()

        zip_path = params.get("zip_path")
        manifest = params.get("manifest", {})
        strategy_code = params.get("strategy_code", "")
        existing_versions = params.get("existing_versions", [])

        if not zip_path:
            return {
                "success": False,
                "error": "zip_path is required for plugin validation",
            }

        try:
            result = validator.validate_all(
                zip_path=zip_path,
                manifest=manifest,
                strategy_code=strategy_code,
                existing_versions=existing_versions,
            )

            return {
                "success": result.valid,
                "valid": result.valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "manifest": result.manifest,
                "strategy_files": result.strategy_files,
            }

        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _save_action_log(
        self,
        action_id: str,
        command: str,
        user_id: str,
        instance: Dict[str, Any],
        param: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
        start_time: datetime,
    ) -> None:
        """Save action log to MongoDB.

        Args:
            action_id: Unique action ID
            command: Command type
            user_id: User ID
            instance: Instance config
            param: Action parameters
            result: Action result
            success: Whether action succeeded
            start_time: Action start time
        """
        storage = self._get_storage()

        try:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            doc = {
                "action_id": action_id,
                "command": command,
                "user_id": user_id,
                "instance": instance,
                "param": param,
                "result": result,
                "success": success,
                "duration_ms": duration_ms,
                "created_at": end_time,
            }

            collection = storage.db["action_logs"]
            await asyncio.to_thread(collection.insert_one, doc)
            logger.info(f"Saved action log: action_id={action_id}, command={command}")

        except Exception as e:
            logger.error(f"Failed to save action log: {e}")

        finally:
            if self._storage:
                self._storage.close()
                self._storage = None
