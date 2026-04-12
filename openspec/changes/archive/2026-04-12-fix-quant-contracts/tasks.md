## 1. Symbol Normalization Layer

- [x] 1.1 Implement `Symbol` value object in a new utility module (e.g., `app/core/quant/symbol.py`)
- [x] 1.2 Implement `normalize()` method to convert various formats to the Golden Standard (`sh600000`)
- [x] 1.3 Implement `to_provider()` methods for Akshare, Baostock, and TDX formats
- [x] 1.4 Add comprehensive unit tests for symbol conversion covering all edge cases (A-shares,北交所, etc.)

## 2. Quant Data Contracts (Type Safety)

- [x] 2.1 Upgrade `StockIndicator` and `SelectionStockResult` in `app/schemas/stock_selection.py` from dataclasses to Pydantic `BaseModel`
- [x] 2.2 Define strong Pydantic models for K-lines and Signal outputs in a new `app/schemas/quant_base.py`
- [x] 2.3 Update `StockSelectionTask` to use Pydantic for all internal fields and MongoDB serialization
- [x] 2.4 Replace all `Dict[str, Any]` usages in the selection engine with these new strong models

## 3. Selection Engine Observability

- [x] 3.1 Add `filtration_logs: List[FiltrationLog]` to the `StockSelectionTask` model
- [x] 3.2 Refactor `_run_selection_task` in `engine.py` to replace `continue` statements with `log_filtration()` calls
- [x] 3.3 Implement the `log_filtration` method to record stock code, reason, and detail
- [x] 3.4 Update `get_selection_result` API endpoint to return the filtration logs to the frontend

## 4. Data Integrity & Guardrails

- [x] 4.1 Implement `validate_data_coverage()` check in `StockSelectionEngine` before processing the stock pool
- [x] 4.2 Add a "Pre-flight" status to the selection task that fails fast if data coverage is below a threshold
- [x] 4.3 Implement a similar data integrity check in the `BacktestEngine` before simulation starts

## 5. API & Frontend Integration

- [x] 5.1 Update all `/api/stock-selection` response models to use the new Pydantic contracts
- [x] 5.2 Verify that the `/api/stock-selection/{task_id}` endpoint now provides the `filtration_logs`
- [x] 5.3 Ensure `Backtest` results are serialized through Pydantic models to eliminate 500 errors
