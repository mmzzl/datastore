## 1. Backend - Data Models and Schemas

- [x] 1.1 Create `apps/api/app/schemas/stock_selection.py` with data models:
  - StockPoolType enum (hs300, zz500, all)
  - SelectionStatus enum (pending, running, analyzing, completed, failed)
  - StockIndicator dataclass (ma5, ma10, ma20, rsi, macd, macd_hist, boll_upper, boll_mid, boll_lower)
  - StockAIAnalysis dataclass (code, name, sector, sector_features, risk_factors, operation_suggestion, brief_analysis)
  - SelectionStockResult dataclass (code, name, score, signal_type, signal_strength, confidence, indicators, industry, ai_analysis)
  - MarketTrendData dataclass (golden cross counts/ratios, bullish alignment counts/ratios, RSI distribution, trend_direction, trend_strength)
  - SelectionAIResult dataclass (stock_analyses, summary, sector_overview, market_risk)
  - StockSelectionTask dataclass (full task model)

## 2. Backend - Stock Pool Service

- [x] 2.1 Create `apps/api/app/stock_selection/__init__.py` module initialization
- [x] 2.2 Create `apps/api/app/stock_selection/stock_pool.py` with StockPoolService:
  - Load stock lists from CSV files (hs300_stocks.csv, zz500_stocks.csv)
  - Memory cache with 1-hour TTL
  - get_codes(pool_type) method
  - load_industry_map() method (code -> industry mapping from stock_industry.csv)
  - get_stock_name(code) method

## 3. Backend - Technical Indicator Calculator

- [x] 3.1 Create indicator calculation functions in engine:
  - _calc_ma(df, periods) - Moving Averages
  - _calc_rsi(df, period=14) - Relative Strength Index
  - _calc_macd(df) - MACD, Signal, Histogram
  - _calc_bollinger(df, period=20, std=2) - Bollinger Bands
- [x] 3.2 Create _calculate_indicators(df) -> StockIndicator method
- [x] 3.3 Create _calculate_score(signal, indicators) -> float method
- [x] 3.4 Create _get_strength(confidence) -> str method

## 4. Backend - Market Trend Analyzer

- [x] 4.1 Create `apps/api/app/stock_selection/market_trend.py`:
  - calculate_market_trend(all_indicators: Dict[str, StockIndicator]) -> MarketTrendData
  - Count MACD golden crosses (macd_hist > 0)
  - Count MA golden crosses (ma5 > ma10)
  - Count full bullish alignment (ma5 > ma10 > ma20)
  - Count partial bullish alignment (ma5 > ma10)
  - Calculate RSI distribution (oversold < 30, overbought > 70)
  - Determine trend_direction and trend_strength

## 5. Backend - AI Analyzer

- [x] 5.1 Create `apps/api/app/stock_selection/ai_analyzer.py`:
  - AIAnalyzer class wrapping LLMClient
  - build_analysis_prompt(task, market_trend, stocks_detail) method
  - analyze_selection(task, market_trend_data) -> SelectionAIResult method
  - Parse LLM JSON response

## 6. Backend - Selection Engine

- [x] 6.1 Create `apps/api/app/stock_selection/engine.py` with StockSelectionEngine:
  - __init__(storage, llm_client)
  - run_selection(strategy_type, strategy_params, stock_pool, plugin_id) -> task_id
  - _create_strategy(strategy_type, strategy_params, plugin_id)
  - _process_stock(code, strategy) -> SelectionStockResult
  - _run_ai_analysis(task) -> SelectionAIResult
- [x] 6.2 Implement task status management (pending -> running -> analyzing -> completed)
- [x] 6.3 Implement MongoDB persistence for tasks
- [x] 6.4 Implement get_task(task_id) method
- [x] 6.5 Implement get_history(page, page_size, filters) method

## 7. Backend - API Endpoints

- [x] 7.1 Create `apps/api/app/api/endpoints/stock_selection.py`:
  - POST /api/stock-selection/run - Start selection task
  - GET /api/stock-selection/{task_id} - Get selection result
  - GET /api/stock-selection/history - Get selection history with pagination
  - GET /api/stock-selection/pools - Get available stock pools
- [x] 7.2 Add permission checks (selection:run, selection:view)
- [x] 7.3 Register router in main app
- [x] 7.4 Create request/response Pydantic models for API

## 8. Backend - Permission Configuration

- [x] 8.1 Add selection:run permission to permission list
- [x] 8.2 Add selection:view permission to permission list
- [x] 8.3 Update default role permissions if needed

## 9. Frontend - API Service

- [x] 9.1 Create `frontend/vue-admin/src/services/api_stock_selection.ts`:
  - runSelection(request) API call
  - getSelectionResult(task_id) API call
  - getSelectionHistory(page, page_size) API call
  - getStockPools() API call
- [x] 9.2 Define TypeScript interfaces for request/response types

## 10. Frontend - State Management

- [x] 10.1 Create `frontend/vue-admin/src/stores/stockSelection.ts`:
  - State: currentTask, taskHistory, stockPools, loading, error
  - Actions: runSelection, fetchResult, fetchHistory, fetchStockPools
  - Getters: sortedResults, hasResults

## 11. Frontend - Components

- [x] 11.1 Create `frontend/vue-admin/src/components/StockSelectionDialog.vue`:
  - Strategy type selector (built-in + plugin strategies)
  - Stock pool selector (hs300, zz500, all)
  - Dynamic parameter form based on strategy type
  - Plugin selector (when strategy type is "plugin")
  - Submit/Cancel buttons
- [x] 11.2 Create `frontend/vue-admin/src/components/StockResultCard.vue`:
  - Collapsible card showing stock info
  - Header: rank, code, name, score, signal strength
  - Expanded content: indicators, industry, AI analysis (sector_features, risk_factors, operation_suggestion)

## 12. Frontend - Main View

- [x] 12.1 Create `frontend/vue-admin/src/views/StockSelectionView.vue`:
  - "Run Selection" button that opens dialog
  - Market Trend section (golden cross ratios, bullish alignment ratios, RSI distribution, trend judgment)
  - Sector Overview section
  - Market Risk section
  - Results table with expandable rows
  - History panel with pagination
- [x] 12.2 Implement loading states and progress indicators
- [x] 12.3 Implement error handling and display

## 13. Frontend - Router Configuration

- [x] 13.1 Add route for /stock-selection in router
- [x] 13.2 Add menu item for stock selection page

## 14. Testing

- [x] 14.1 Create unit tests for StockPoolService
- [x] 14.2 Create unit tests for indicator calculations
- [x] 14.3 Create unit tests for MarketTrendData calculation
- [x] 14.4 Create unit tests for AIAnalyzer prompt building
- [x] 14.5 Create integration tests for API endpoints
- [ ] 14.6 Manual end-to-end testing

## 15. Documentation

- [x] 15.1 Update API documentation with new endpoints
- [x] 15.2 Add user guide for strategy selection feature
