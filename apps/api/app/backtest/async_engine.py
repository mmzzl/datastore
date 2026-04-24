"""
Async Backtest Engine

Runs backtests asynchronously with progress updates.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from .strategies.base import BaseStrategy, Signal, SignalType
from .strategies.factory import StrategyFactory
from .risk_metrics import RiskMetrics, RiskMetricsCalculator
from ..core.quant.symbol import Symbol

logger = logging.getLogger(__name__)


class BacktestStatus(Enum):
    """Status of backtest task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Position:
    """Represents a stock position."""

    code: str
    quantity: float
    entry_price: float
    entry_date: str

    def value(self, current_price: float) -> float:
        return self.quantity * current_price

    def pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.quantity

    def pnl_pct(self, current_price: float) -> float:
        if self.entry_price == 0:
            return 0.0
        return (current_price - self.entry_price) / self.entry_price


@dataclass
class Trade:
    """Represents a trade execution."""

    code: str
    action: str
    quantity: float
    price: float
    date: str
    pnl: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest result."""

    task_id: str
    status: BacktestStatus
    config: Dict[str, Any]
    portfolio_values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    positions: Dict[str, Position] = field(default_factory=dict)
    metrics: Optional[RiskMetrics] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0


@dataclass
class BacktestConfig:
    """Configuration for backtest."""

    strategy_type: str
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 100000.0
    instruments: List[str] = field(default_factory=list)
    commission_rate: float = 0.0003
    slippage: float = 0.0001

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestConfig":
        return cls(
            strategy_type=data.get("strategy", "ma_cross"),
            strategy_params=data.get("params", {}),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            initial_capital=data.get("initial_capital", 100000.0),
            instruments=data.get("instruments", []),
            commission_rate=data.get("commission_rate", 0.0003),
            slippage=data.get("slippage", 0.0001),
        )


class AsyncBacktestEngine:
    """
    Asynchronous backtest engine.

    Runs backtests in background with:
    - Progress updates every 10 data points
    - Position tracking
    - Portfolio value calculation
    - Risk metrics computation

    Example:
    >>> engine = AsyncBacktestEngine()
    >>> task_id = await engine.run_backtest(config)
    >>> status = await engine.get_status(task_id)
    """

    PROGRESS_UPDATE_INTERVAL = 10

    def __init__(self):
        self._tasks: Dict[str, BacktestResult] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._storage = None
        self._total_data_points: Dict[str, int] = {}

    def _get_storage(self):
        """Get MongoDB storage lazily."""
        if self._storage is None:
            from app.storage import MongoStorage
            from app.core.config import settings

            self._storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self._storage.connect()
        return self._storage

    def _validate_data_coverage(self, config: BacktestConfig) -> bool:
        """
        Verify that the requested instruments have sufficient data coverage
        for the specified backtest period.
        """
        storage = self._get_storage()
        valid_count = 0
        total_instruments = len(config.instruments)

        if total_instruments == 0:
            return False

        for raw_code in config.instruments:
            code = Symbol(raw_code).to_provider("tdx")
            try:
                klines = storage.get_kline(
                    code=code,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    limit=1,
                )
                if klines and len(klines) >= 1:
                    valid_count += 1
            except Exception as e:
                logger.warning(f"Coverage check failed for {code}: {e}")

        coverage = valid_count / total_instruments
        logger.info(f"Backtest data coverage: {coverage:.2%}")

        # Threshold: at least 20% of the instruments must have data
        return coverage >= 0.2

    async def run_backtest(
        self,
        config: Dict[str, Any],
    ) -> str:
        """
        Start a backtest task.

        Args:
            config: Backtest configuration dictionary

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        bt_config = BacktestConfig.from_dict(config)

        result = BacktestResult(
            task_id=task_id,
            status=BacktestStatus.PENDING,
            config=config,
            start_time=datetime.now(),
        )
        self._tasks[task_id] = result

        task = asyncio.create_task(self._run_backtest_task(task_id, bt_config))
        self._running_tasks[task_id] = task

        return task_id

    async def _run_backtest_task(
        self,
        task_id: str,
        config: BacktestConfig,
    ) -> None:
        """
        Execute backtest task with data integrity guardrails.
        """
        result = self._tasks[task_id]
        result.status = BacktestStatus.RUNNING

        try:
            # --- DATA INTEGRITY GUARDRAIL ---
            if not self._validate_data_coverage(config):
                result.status = BacktestStatus.FAILED
                result.error = "Critical data coverage failure: Most instruments in the backtest pool have no historical data for the selected period."
                return
            # -------------------------------

            strategy = StrategyFactory.create(
                config.strategy_type, **config.strategy_params
            )

            data = await self._fetch_data(config)

            if data.empty:
                raise ValueError(f"No data found for instruments: {config.instruments}")

            total_data_points = (
                len(data.groupby("date")) if "date" in data.columns else 1
            )
            self._total_data_points[task_id] = total_data_points

            await self._execute_backtest(task_id, config, strategy, data)

            result.status = BacktestStatus.COMPLETED
            result.end_time = datetime.now()
            result.metrics = RiskMetricsCalculator.calculate(
                result.portfolio_values,
                trades=[t for t in result.trades],
            )

            logger.info(
                f"Backtest {task_id} completed with {len(result.trades)} trades"
            )

        except asyncio.CancelledError:
            result.status = BacktestStatus.CANCELLED
            result.end_time = datetime.now()
            logger.info(f"Backtest {task_id} cancelled")

        except Exception as e:
            result.status = BacktestStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            logger.error(f"Backtest {task_id} failed: {e}")

    async def _fetch_data(self, config: BacktestConfig) -> pd.DataFrame:
        """
        Fetch K-line data from MongoDB.

        Args:
            config: Backtest configuration

        Returns:
            DataFrame with OHLCV data
        """
        storage = self._get_storage()

        all_data = []

        for raw_code in config.instruments:
            code = Symbol(raw_code).to_provider("tdx")
            try:
                klines = storage.get_kline(
                    code=code,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    limit=10000,
                )

                for kline in klines:
                    kline["code"] = code
                    all_data.append(kline)

            except Exception as e:
                logger.warning(f"Failed to fetch data for {code}: {e}")

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        if "date" in df.columns:
            df = df.sort_values("date")

        return df

    async def _execute_backtest(
        self,
        task_id: str,
        config: BacktestConfig,
        strategy: BaseStrategy,
        data: pd.DataFrame,
    ) -> None:
        """
        Execute backtest logic.

        Dispatches to portfolio-level or per-stock execution based on
        strategy.is_portfolio_strategy.
        """
        if strategy.is_portfolio_strategy:
            await self._execute_portfolio_backtest(
                task_id, config, strategy, data
            )
        else:
            await self._execute_per_stock_backtest(
                task_id, config, strategy, data
            )

    async def _execute_portfolio_backtest(
        self,
        task_id: str,
        config: BacktestConfig,
        strategy: BaseStrategy,
        data: pd.DataFrame,
    ) -> None:
        """
        Execute backtest for portfolio-level strategies (e.g. QlibModelStrategy).

        On each rebalance date:
        1. Call strategy.predict_stocks(instruments, date) to get top-k
        2. Sell positions not in the current top-k
        3. Allocate capital equally across top-k stocks and buy
        """
        result = self._tasks[task_id]

        cash = config.initial_capital
        positions: Dict[str, Position] = {}
        portfolio_values: List[float] = []
        dates: List[str] = []
        trades: List[Dict[str, Any]] = []

        if "date" not in data.columns:
            result.status = BacktestStatus.FAILED
            result.error = "Portfolio backtest requires date column in data"
            return

        grouped = data.groupby("date")
        total_dates = len(grouped)
        processed_count = 0
        instruments = config.instruments

        for date, day_data in grouped:
            if self._tasks[task_id].status == BacktestStatus.CANCELLED:
                break

            date_str = str(date)

            price_map: Dict[str, float] = {}
            for _, row in day_data.iterrows():
                row_code = str(row.get("code", ""))
                close_price = row.get("close", 0)
                if row_code and close_price:
                    price_map[row_code] = float(close_price)

            daily_portfolio_value = cash
            for code, pos in positions.items():
                if code in price_map:
                    daily_portfolio_value += pos.value(price_map[code])

            predicted = strategy.predict_stocks(
                instruments=instruments, date=date_str
            )

            target_codes = set()
            for pred in predicted:
                pred_code = pred.get("code", "")
                if pred_code:
                    normalized = Symbol(pred_code).to_provider("tdx")
                    target_codes.add(normalized)

            current_codes = set(positions.keys())

            codes_to_sell = current_codes - target_codes
            for code in codes_to_sell:
                if code not in price_map:
                    continue
                pos = positions[code]
                price = price_map[code]
                quantity = pos.quantity
                if quantity > 0:
                    executed_price = price * (1 - config.slippage)
                    proceeds = quantity * executed_price
                    commission = proceeds * config.commission_rate
                    pnl = (executed_price - pos.entry_price) * quantity - commission
                    cash += proceeds - commission
                    trades.append({
                        "code": code,
                        "action": "sell",
                        "quantity": quantity,
                        "price": executed_price,
                        "date": date_str,
                        "commission": commission,
                        "pnl": pnl,
                        "cash_after": cash,
                    })
                    del positions[code]

            codes_to_buy = target_codes - set(positions.keys())
            buyable_codes = [c for c in codes_to_buy if c in price_map and price_map[c] > 0]

            if buyable_codes and cash > 0:
                per_stock_capital = cash / len(buyable_codes)
                for code in buyable_codes:
                    price = price_map[code]
                    executed_price = price * (1 + config.slippage)
                    quantity = int(per_stock_capital / executed_price / 100) * 100
                    if quantity <= 0:
                        continue
                    cost = quantity * executed_price
                    commission = cost * config.commission_rate
                    total_cost = cost + commission
                    if total_cost > cash:
                        quantity = int((cash - commission) / executed_price / 100) * 100
                        if quantity <= 0:
                            continue
                        cost = quantity * executed_price
                        commission = cost * config.commission_rate
                        total_cost = cost + commission
                    if total_cost <= cash and quantity > 0:
                        positions[code] = Position(
                            code=code,
                            quantity=quantity,
                            entry_price=executed_price,
                            entry_date=date_str,
                        )
                        cash -= total_cost
                        trades.append({
                            "code": code,
                            "action": "buy",
                            "quantity": quantity,
                            "price": executed_price,
                            "date": date_str,
                            "commission": commission,
                            "cash_after": cash,
                            "pnl": 0,
                        })

            portfolio_values.append(daily_portfolio_value)
            dates.append(date_str)

            processed_count += 1
            if processed_count % self.PROGRESS_UPDATE_INTERVAL == 0:
                result.progress = processed_count / max(total_dates, 1)
                await asyncio.sleep(0)

        result.portfolio_values = portfolio_values
        result.dates = dates
        result.trades = trades
        result.positions = {
            code: {
                "code": p.code,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
            }
            for code, p in positions.items()
        }

    async def _execute_per_stock_backtest(
        self,
        task_id: str,
        config: BacktestConfig,
        strategy: BaseStrategy,
        data: pd.DataFrame,
    ) -> None:
        """
        Execute backtest for per-stock strategies (e.g. MACross, RSI).

        Iterates over each instrument and date, calling
        strategy.generate_signals(code_data) for individual signals.
        """
        result = self._tasks[task_id]

        cash = config.initial_capital
        positions: Dict[str, Position] = {}
        portfolio_values: List[float] = []
        dates: List[str] = []
        trades: List[Dict[str, Any]] = []

        grouped = data.groupby("date") if "date" in data.columns else [(None, data)]

        min_points = strategy.get_required_data_points()
        historical_data = pd.DataFrame()

        processed_count = 0

        for date, day_data in grouped:
            if self._tasks[task_id].status == BacktestStatus.CANCELLED:
                break

            if "date" in day_data.columns:
                historical_data = pd.concat(
                    [historical_data, day_data], ignore_index=True
                )
            else:
                historical_data = day_data.copy()

            if len(historical_data) < min_points:
                continue

        daily_portfolio_value = cash

        for raw_code in config.instruments:
            code = Symbol(raw_code).to_provider("tdx")
            code_data = (
                historical_data[historical_data["code"] == code]
                if "code" in historical_data.columns
                else historical_data
            )

            if len(code_data) == 0:
                continue

            current_price = code_data.iloc[-1].get("close", 0)

            if code in positions:
                pos = positions[code]
                daily_portfolio_value += pos.value(current_price)

            signal = strategy.generate_signals(code_data)

            trade = self._process_signal(
                signal=signal,
                code=code,
                price=current_price,
                date=str(date) if date else "",
                cash=cash,
                positions=positions,
                config=config,
            )

            if trade:
                trades.append(trade)
                cash = trade.get("cash_after", cash)

            portfolio_values.append(daily_portfolio_value)
            dates.append(str(date) if date else "")

            result.portfolio_values = portfolio_values
            result.dates = dates
            result.trades = trades
            result.positions = {
                code: {
                    "code": p.code,
                    "quantity": p.quantity,
                    "entry_price": p.entry_price,
                }
                for code, p in positions.items()
            }

            processed_count += 1
            if processed_count % self.PROGRESS_UPDATE_INTERVAL == 0:
                result.progress = processed_count / max(len(grouped), 1)
                await asyncio.sleep(0)

        result.portfolio_values = portfolio_values
        result.dates = dates
        result.trades = trades

    def _process_signal(
        self,
        signal: Signal,
        code: str,
        price: float,
        date: str,
        cash: float,
        positions: Dict[str, Position],
        config: BacktestConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Process trading signal and execute trade if applicable.

        Args:
            signal: Trading signal
            code: Stock code
            price: Current price
            date: Trade date
            cash: Available cash
            positions: Current positions
            config: Backtest config

        Returns:
            Trade dictionary if executed, None otherwise
        """
        if signal.signal_type == SignalType.HOLD:
            return None

        executed_price = price * (1 + config.slippage)
        commission = 0.0
        trade = None

        if signal.signal_type == SignalType.BUY and code not in positions:
            position_size = cash * signal.confidence * 0.95
            quantity = position_size / executed_price if executed_price > 0 else 0
            quantity = int(quantity / 100) * 100

            if quantity > 0:
                cost = quantity * executed_price
                commission = cost * config.commission_rate
                total_cost = cost + commission

                if total_cost <= cash:
                    positions[code] = Position(
                        code=code,
                        quantity=quantity,
                        entry_price=executed_price,
                        entry_date=date,
                    )
                    cash -= total_cost

                    trade = {
                        "code": code,
                        "action": "buy",
                        "quantity": quantity,
                        "price": executed_price,
                        "date": date,
                        "commission": commission,
                        "cash_after": cash,
                        "pnl": 0,
                    }

        elif signal.signal_type == SignalType.SELL and code in positions:
            pos = positions[code]
            quantity = pos.quantity

            if quantity > 0:
                proceeds = quantity * executed_price
                commission = proceeds * config.commission_rate
                pnl = (executed_price - pos.entry_price) * quantity - commission

                cash += proceeds - commission

                trade = {
                    "code": code,
                    "action": "sell",
                    "quantity": quantity,
                    "price": executed_price,
                    "date": date,
                    "commission": commission,
                    "pnl": pnl,
                    "cash_after": cash,
                }

                del positions[code]

        return trade

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get backtest task status.

        Args:
            task_id: Task identifier

        Returns:
            Status dictionary
        """
        if task_id not in self._tasks:
            return {"error": "Task not found"}

        result = self._tasks[task_id]

        status = {
            "task_id": task_id,
            "status": result.status.value,
            "progress": result.progress,
            "start_time": result.start_time.isoformat() if result.start_time else None,
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "error": result.error,
            "total_data_points": self._total_data_points.get(task_id, 0),
        }

        if result.status == BacktestStatus.COMPLETED:
            status["total_trades"] = len(result.trades)
            status["portfolio_values_count"] = len(result.portfolio_values)

            if result.metrics:
                status["metrics"] = RiskMetricsCalculator.to_dict(result.metrics)

        return status

    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete backtest result.

        Args:
            task_id: Task identifier

        Returns:
            Result dictionary or None if not found
        """
        if task_id not in self._tasks:
            return None

        result = self._tasks[task_id]

        return {
            "task_id": task_id,
            "status": result.status.value,
            "config": result.config,
            "portfolio_values": result.portfolio_values,
            "dates": result.dates,
            "trades": result.trades,
            "metrics": RiskMetricsCalculator.to_dict(result.metrics)
            if result.metrics
            else None,
            "error": result.error,
        }

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a running backtest.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled successfully
        """
        if task_id not in self._tasks:
            return False

        result = self._tasks[task_id]

        if result.status in (
            BacktestStatus.COMPLETED,
            BacktestStatus.FAILED,
            BacktestStatus.CANCELLED,
        ):
            return False

        result.status = BacktestStatus.CANCELLED

        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()

        return True

    def get_task_result(self, task_id: str) -> Optional[BacktestResult]:
        """
        Get backtest result object for a task.

        Args:
            task_id: Task identifier

        Returns:
            BacktestResult or None if not found
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all task statuses.

        Returns:
            List of task status dictionaries
        """
        return [
            {"task_id": task_id, "status": result.status.value}
            for task_id, result in self._tasks.items()
        ]

    def clear_completed_tasks(self) -> int:
        """
        Remove completed, failed, and cancelled tasks.

        Returns:
            Number of tasks cleared
        """
        to_remove = [
            task_id
            for task_id, result in self._tasks.items()
            if result.status
            in (
                BacktestStatus.COMPLETED,
                BacktestStatus.FAILED,
                BacktestStatus.CANCELLED,
            )
        ]

        for task_id in to_remove:
            del self._tasks[task_id]
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

        return len(to_remove)
