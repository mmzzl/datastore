"""
Stock Selection Engine

Core engine for strategy-based stock selection.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd

from ..storage import MongoStorage
from ..core.config import settings
from ..backtest.strategies.factory import StrategyFactory
from ..backtest.strategies.base import SignalType
from ..schemas.stock_selection import (
    StockPoolType,
    SelectionStatus,
    StockSelectionTask,
    SelectionStockResult,
    StockIndicator,
    MarketTrendData,
    SelectionAIResult,
)
from .stock_pool import StockPoolService
from .market_trend import MarketTrendAnalyzer
from .ai_analyzer import AIAnalyzer
from ..collector.llm_client import LLMClient

logger = logging.getLogger(__name__)


class StockSelectionEngine:
    """
    Engine for strategy-based stock selection.

    Orchestrates the selection process:
    1. Load stock pool
    2. Create strategy instance
    3. Process each stock
    4. Calculate indicators and scores
    5. Analyze market trend
    6. Run AI analysis
    7. Save results
    """

    def __init__(self, storage: MongoStorage = None):
        """
        Initialize StockSelectionEngine.

        Args:
            storage: MongoDB storage instance (optional, created if not provided)
        """
        if storage:
            self.storage = storage
        else:
            self.storage = self._create_storage()
            # Must call connect() to establish DB connection
            self.storage.connect()

        # Force connection
        _ = self.storage.db

        collection = self.storage.db["stock_selections"]

        # Test write
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        collection.insert_one({"_id": test_id, "test": True})
        collection.delete_one({"_id": test_id})
        logger.info(f"StockSelectionEngine DB write test OK")

        count = collection.count_documents({})
        logger.info(
            f"StockSelectionEngine connected to DB: {self.storage.db_name}, collection size: {count}"
        )

        self.stock_pool_service = StockPoolService()
        self._tasks: Dict[str, StockSelectionTask] = {}

    def _create_storage(self) -> MongoStorage:
        """Create MongoDB storage instance."""
        return MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )

    def _create_strategy(
        self,
        strategy_type: str,
        strategy_params: Dict[str, Any],
        plugin_id: Optional[str] = None,
    ):
        """
        Create strategy instance.

        Args:
            strategy_type: Type of strategy
            strategy_params: Strategy parameters
            plugin_id: Plugin ID (if using plugin strategy)

        Returns:
            Strategy instance
        """
        params = strategy_params.copy()

        if strategy_type == "plugin" and plugin_id:
            params["plugin_id"] = plugin_id

        return StrategyFactory.create(strategy_type, **params)

    async def run_selection(
        self,
        strategy_type: str,
        strategy_params: Dict[str, Any],
        stock_pool: StockPoolType,
        plugin_id: Optional[str] = None,
    ) -> str:
        """
        Run stock selection.

        Args:
            strategy_type: Type of strategy
            strategy_params: Strategy parameters
            stock_pool: Stock pool type
            plugin_id: Plugin ID (if using plugin strategy)

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        # Create task
        task = StockSelectionTask(
            id=task_id,
            strategy_type=strategy_type,
            strategy_params=strategy_params,
            plugin_id=plugin_id,
            stock_pool=stock_pool,
            status=SelectionStatus.PENDING,
            created_at=datetime.now(),
        )

        # Save initial task
        self._tasks[task_id] = task
        self._save_task(task)

        try:
            # Run selection in background
            await self._run_selection_task(task_id)

        except Exception as e:
            logger.error(f"Selection task {task_id} failed: {e}")
            task.status = SelectionStatus.FAILED
            task.error = str(e)
            self._save_task(task)

        return task_id

    async def _run_selection_task(self, task_id: str) -> None:
        """
        Execute selection task.

        Args:
            task_id: Task identifier
        """
        logger.warning(f"_run_selection_task STARTED for {task_id}")

        task = self._tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found in _tasks")
            return

        try:
            logger.info(f"Task {task_id} status: {task.status}")

            # Update status
            task.status = SelectionStatus.RUNNING
            self._save_task(task)

            logger.info(
                f"Task {task_id} stock_pool: {task.stock_pool}, value: {task.stock_pool.value}"
            )

            # Load stock pool
            codes = self.stock_pool_service.get_codes(task.stock_pool.value)
            logger.info(f"Task {task_id} got {len(codes)} codes from stock pool")
            task.total_stocks = len(codes)

            # Load industry map
            industry_map = self.stock_pool_service.load_industry_map()
            logger.info(
                f"Task {task_id} loaded industry map: {len(industry_map)} items"
            )

            # Create strategy
            strategy = self._create_strategy(
                task.strategy_type,
                task.strategy_params,
                task.plugin_id,
            )

            # Process stocks
            results = []
            all_indicators: Dict[str, StockIndicator] = {}

            for code in codes:
                # Get K-line data
                klines = self.storage.get_kline(code, limit=100)

                if not klines or len(klines) < 30:
                    continue

                df = pd.DataFrame(klines)
                if "close" not in df.columns:
                    continue

                # Calculate indicators for market trend
                indicators = MarketTrendAnalyzer.calculate_indicators(df)
                all_indicators[code] = indicators

                # Generate signal
                try:
                    signal = strategy.generate_signals(df)
                except Exception as e:
                    logger.warning(f"Signal generation failed for {code}: {e}")
                    continue

                # Only keep BUY signals
                if signal.signal_type != SignalType.BUY:
                    continue

                # Calculate score
                score = MarketTrendAnalyzer.calculate_score(
                    signal.confidence, indicators
                )
                strength = MarketTrendAnalyzer.get_strength(signal.confidence)

                # Get industry
                industry = industry_map.get(code, "")

                # Create result
                result = SelectionStockResult(
                    code=code,
                    name=self.stock_pool_service.get_stock_name(code),
                    score=score,
                    signal_type=signal.signal_type.value,
                    signal_strength=strength,
                    confidence=signal.confidence,
                    indicators=indicators,
                    industry=industry,
                )
                results.append(result)

            # Sort by score and take top 20
            results.sort(key=lambda x: x.score, reverse=True)
            top_results = results[:20]

            task.results = top_results
            task.selected_count = len(top_results)

            # Analyze market trend
            selected_codes = {r.code for r in top_results}
            market_trend = MarketTrendAnalyzer.analyze_market_trend(
                all_indicators, selected_codes
            )
            task.market_trend = market_trend

            # Run AI analysis
            task.status = SelectionStatus.ANALYZING
            self._save_task(task)

            ai_result = await self._run_ai_analysis(task)
            task.ai_result = ai_result

            # Complete task
            task.status = SelectionStatus.COMPLETED
            task.completed_at = datetime.now()
            self._save_task(task)

            logger.info(
                f"Selection task {task_id} completed: {len(top_results)} stocks selected"
            )

        except Exception as e:
            logger.error(f"Selection task {task_id} failed: {e}")
            task.status = SelectionStatus.FAILED
            task.error = str(e)
            self._save_task(task)
            raise

    async def _run_ai_analysis(
        self, task: StockSelectionTask
    ) -> Optional[SelectionAIResult]:
        """
        Run AI analysis on selection results.

        Args:
            task: Selection task

        Returns:
            SelectionAIResult or None
        """
        if not task.results:
            return None

        try:
            # Create LLM client
            llm_client = LLMClient(
                provider=settings.llm_provider,
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                base_url=settings.llm_base_url,
            )

            # Create analyzer
            analyzer = AIAnalyzer(llm_client)

            # Run analysis (in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                analyzer.analyze_selection,
                task,
                task.market_trend,
            )

            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    def _save_task(self, task: StockSelectionTask) -> None:
        """
        Save task to MongoDB.

        Args:
            task: Task to save
        """
        logger.warning(f"_save_task CALLED for {task.id}, status={task.status}")

        try:
            collection = self.storage.db["stock_selections"]

            doc = task.to_dict()
            doc["_id"] = task.id

            logger.info(f"_save_task: saving task {task.id} with status {task.status}")

            # Upsert
            result = collection.update_one(
                {"_id": task.id},
                {"$set": doc},
                upsert=True,
            )
            logger.info(
                f"Saved task {task.id}, modified: {result.modified_count}, upserted: {result.upserted_id}"
            )

            # Verify it was saved
            verify = collection.find_one({"_id": task.id})
            if verify:
                logger.info(f"Verified task {task.id} exists in DB")
            else:
                logger.error(f"Task {task.id} not found after save!")

        except Exception as e:
            logger.error(f"Failed to save task {task.id}: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def get_task(self, task_id: str) -> Optional[StockSelectionTask]:
        """
        Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            StockSelectionTask or None
        """
        logger.warning(f"get_task called for {task_id}")

        # Check memory cache
        if task_id in self._tasks:
            logger.warning(f"Task {task_id} found in memory cache")
            return self._tasks[task_id]

        # Load from database
        try:
            collection = self.storage.db["stock_selections"]
            doc = collection.find_one({"_id": task_id})

            logger.warning(f"Task {task_id} doc from DB: {doc is not None}")

            if doc:
                task = self._doc_to_task(doc)
                self._tasks[task_id] = task
                return task

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            import traceback

            logger.error(traceback.format_exc())

        return None

    def get_history(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Get selection history with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Page size
            filters: Optional filters (status, stock_pool, etc.)

        Returns:
            Dictionary with items, total, page, page_size
        """
        try:
            collection = self.storage.db["stock_selections"]

            query = filters or {}
            logger.info(
                f"get_history query: {query}, page: {page}, page_size: {page_size}"
            )

            # Count total
            total = collection.count_documents(query)
            logger.info(f"Total documents: {total}")

            # Get items
            skip = (page - 1) * page_size
            docs = list(
                collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(page_size)
            )
            logger.info(f"Found {len(docs)} docs")

            items = []
            for doc in docs:
                items.append(
                    {
                        "id": doc.get("_id", ""),
                        "task_id": doc.get("task_id", ""),
                        "strategy_type": doc.get("strategy_type", ""),
                        "stock_pool": doc.get("stock_pool", ""),
                        "created_at": doc.get("created_at", ""),
                        "selected_count": doc.get("selected_count", 0),
                        "status": doc.get("status", ""),
                    }
                )

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def _doc_to_task(self, doc: Dict[str, Any]) -> StockSelectionTask:
        """
        Convert MongoDB document to StockSelectionTask.

        Args:
            doc: MongoDB document

        Returns:
            StockSelectionTask object
        """
        # Convert results
        results = []
        for r in doc.get("results", []):
            ind = r.get("indicators", {})
            indicators = StockIndicator(
                ma5=ind.get("ma5"),
                ma10=ind.get("ma10"),
                ma20=ind.get("ma20"),
                rsi=ind.get("rsi"),
                macd=ind.get("macd"),
                macd_signal=ind.get("macd_signal"),
                macd_hist=ind.get("macd_hist"),
                boll_upper=ind.get("boll_upper"),
                boll_mid=ind.get("boll_mid"),
                boll_lower=ind.get("boll_lower"),
            )

            results.append(
                SelectionStockResult(
                    code=r.get("code", ""),
                    name=r.get("name", ""),
                    score=r.get("score", 0),
                    signal_type=r.get("signal_type", ""),
                    signal_strength=r.get("signal_strength", ""),
                    confidence=r.get("confidence", 0),
                    indicators=indicators,
                    industry=r.get("industry", ""),
                    ai_analysis=None,  # Will be populated from ai_result
                )
            )

        # Convert market trend
        mt = doc.get("market_trend") or {}
        market_trend = None
        if mt:
            market_trend = MarketTrendData(
                total_stocks=mt.get("total_stocks", 0),
                analyzed_stocks=mt.get("analyzed_stocks", 0),
                macd_golden_cross_count=mt.get("macd_golden_cross_count", 0),
                macd_golden_cross_ratio=mt.get("macd_golden_cross_ratio", 0),
                ma_golden_cross_count=mt.get("ma_golden_cross_count", 0),
                ma_golden_cross_ratio=mt.get("ma_golden_cross_ratio", 0),
                full_bullish_alignment_count=mt.get("full_bullish_alignment_count", 0),
                full_bullish_alignment_ratio=mt.get("full_bullish_alignment_ratio", 0),
                partial_bullish_alignment_count=mt.get(
                    "partial_bullish_alignment_count", 0
                ),
                partial_bullish_alignment_ratio=mt.get(
                    "partial_bullish_alignment_ratio", 0
                ),
                selected_macd_golden_cross=mt.get("selected_macd_golden_cross", 0),
                selected_bullish_alignment=mt.get("selected_bullish_alignment", 0),
                rsi_oversold_count=mt.get("rsi_oversold_count", 0),
                rsi_overbought_count=mt.get("rsi_overbought_count", 0),
                rsi_neutral_count=mt.get("rsi_neutral_count", 0),
                trend_direction=mt.get("trend_direction", "震荡"),
                trend_strength=mt.get("trend_strength", "中"),
            )

        return StockSelectionTask(
            id=doc.get("_id", ""),
            strategy_type=doc.get("strategy_type", ""),
            strategy_params=doc.get("strategy_params", {}),
            plugin_id=doc.get("plugin_id"),
            stock_pool=StockPoolType(doc.get("stock_pool", "hs300")),
            status=SelectionStatus(doc.get("status", "pending")),
            created_at=doc.get("created_at", datetime.now()),
            completed_at=doc.get("completed_at"),
            results=results,
            ai_result=None,  # TODO: Parse if needed
            market_trend=market_trend,
            error=doc.get("error"),
            total_stocks=doc.get("total_stocks", 0),
            selected_count=doc.get("selected_count", 0),
        )


# Global engine instance
_engine: Optional[StockSelectionEngine] = None


def get_selection_engine() -> StockSelectionEngine:
    """Get or create StockSelectionEngine instance."""
    global _engine
    if _engine is None:
        logger.info(
            f"Creating new StockSelectionEngine with db: {settings.mongodb_database}"
        )
        _engine = StockSelectionEngine()
    return _engine
