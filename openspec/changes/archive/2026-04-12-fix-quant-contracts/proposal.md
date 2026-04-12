## Why

The current quantitative stock selection and backtesting systems suffer from "silent failures" (tasks completing successfully but returning empty results) and frequent API 500 errors due to a lack of strict data contracts and inconsistent symbol formatting across different data providers. This change establishes a rigorous type-safe foundation and a unified symbol normalization layer to ensure reliability and observability.

## What Changes

- **Introduce `Symbol` Value Object**: A unified system to normalize stock codes (e.g., `600000` $\leftrightarrow$ `sh600000` $\leftrightarrow$ `600000.SH`) across the entire pipeline. **BREAKING**
- **Strict Pydantic Contract**: Replace all `Dataclasses` and `Dict` usage in the selection and backtest engines with strict Pydantic models to eliminate serialization errors. **BREAKING**
- **Observability Layer**: Replace silent `continue` statements in the selection engine with a structured `TaskEventLog` to track why specific stocks were filtered out.
- **Data Integrity Guardrails**: Implement pre-flight checks for K-line data coverage before starting selection or backtest tasks.
- **Unified Response Models**: Standardize API responses to ensure frontend consistency and prevent 422/500 errors.

## Capabilities

### New Capabilities
- `symbol-normalization`: A core utility for converting and validating stock symbols across different market providers (Akshare, Baostock, TDX).
- `selection-observability`: A mechanism to log and report the exact reason for stock filtration during a selection task.
- `quant-data-contracts`: Strong type definitions for K-lines, indicators, and signals used across all quant modules.

### Modified Capabilities
- `stock-selection`: Requirements change from "return results" to "return results with detailed filtration logs".
- `backtesting`: Requirements change to include mandatory data integrity verification before execution.

## Impact

- **Code**: `apps/api/app/stock_selection/`, `apps/api/app/backtest/`, `apps/api/app/schemas/`.
- **APIs**: All `/api/stock-selection/*` and `/api/backtest/*` endpoints will have updated request/response schemas.
- **Database**: MongoDB `stock_selections` and `backtest` collections will store data using the new normalized symbol format.
- **Frontend**: The Vue frontend will need to handle the new `TaskEventLog` to display filtration reasons.
