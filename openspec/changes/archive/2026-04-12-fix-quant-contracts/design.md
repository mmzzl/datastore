## Context

The current quantitative system (stock selection and backtesting) relies on inconsistent string-based stock symbols (e.g., "600000", "sh600000", "600000.SH") and a mix of `Dataclasses` and `Dicts`. This leads to "silent failures" where data is missing but the system reports success, and API 500 errors during JSON serialization in FastAPI.

## Goals / Non-Goals

**Goals:**
- Establish a **Single Source of Truth** for stock symbols using a `Symbol` value object.
- Implement **Strong Type Safety** across the entire pipeline using Pydantic v2.
- Transform "Silent Failures" into **Observable Events** via a structured filtration log.
- Ensure **Data Integrity** by validating K-line coverage before executing quant tasks.

**Non-Goals:**
- Rewriting the actual strategy logic (the mathematical formulas of the strategies).
- Adding new stock data providers (focus is on fixing the current pipeline).
- Full frontend UI redesign (only adding support for the new logs).

## Decisions

### 1. The `Symbol` Value Object Pattern
**Decision**: Implement a `Symbol` class that handles internal normalization to a "Golden Standard" (e.g., `sh600000`).
- **Rationale**: Avoids `if code.startswith('sh')` checks throughout the codebase.
- **Alternatives**: Using simple strings with a naming convention. (Rejected: Too prone to human error).
- **Mechanism**: `Symbol.normalize(raw_code)` $\rightarrow$ Internal Standard $\rightarrow$ `Symbol.to_provider(provider_name)`.

### 2. Total Pydantic Migration
**Decision**: Replace all `dataclasses` in `app/schemas/stock_selection.py` and `app/backtest/` with Pydantic `BaseModel`.
- **Rationale**: Pydantic provides automatic validation, coerced types, and seamless integration with FastAPI's serialization.
- **Alternatives**: Keeping Dataclasses and adding manual validation layers. (Rejected: High maintenance overhead).

### 3. Structured Filtration Logging (`TaskEventLog`)
**Decision**: Introduce a `filtration_logs` list in the `StockSelectionTask` model.
- **Rationale**: Instead of `continue`, the engine will record: `{ "code": "600000", "reason": "INSUFFICIENT_DATA", "detail": "Only 15/30 candles found" }`.
- **Alternatives**: Standard application logs. (Rejected: Hard for users to see via API).

### 4. Pre-flight Data Integrity Check
**Decision**: Add a `validate_data_coverage` step before the main loop in `run_selection`.
- **Rationale**: Fails the task immediately if the stock pool is largely missing data, rather than iterating through thousands of stocks and returning an empty list.

## Risks / Trade-offs

- **[Risk]** Breaking existing MongoDB documents. $\rightarrow$ **Mitigation**: Implement a migration utility or a lenient `_doc_to_task` converter that normalizes old data on read.
- **[Risk]** Performance hit due to Pydantic validation in tight loops. $\rightarrow$ **Mitigation**: Use Pydantic's `.model_construct()` for high-volume internal data if profiling shows a bottleneck.
- **[Risk]** Symbol collision in edge cases (e.g., different markets using same code). $\rightarrow$ **Mitigation**: Use a strict `market_prefix` in the internal standard.
