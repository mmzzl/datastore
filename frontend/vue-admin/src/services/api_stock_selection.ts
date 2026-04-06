/**
 * Stock Selection API Service
 *
 * Provides API calls for strategy-based stock selection.
 */

import api from './api';

// Type definitions

export interface RunSelectionRequest {
  strategy_type: string;
  strategy_params?: Record<string, any>;
  stock_pool?: string;
  plugin_id?: string;
}

export interface StockResultItem {
  code: string;
  name: string;
  score: number;
  signal_type: string;
  signal_strength: string;
  confidence: number;
  industry: string;
  indicators: {
    ma5?: number;
    ma10?: number;
    ma20?: number;
    rsi?: number;
    macd?: number;
    macd_hist?: number;
  };
  ai_analysis?: {
    sector: string;
    sector_features: string;
    risk_factors: string[];
    operation_suggestion: string;
    brief_analysis: string;
  };
}

export interface MarketTrendData {
  total_stocks: number;
  macd_golden_cross_count: number;
  macd_golden_cross_ratio: number;
  ma_golden_cross_count: number;
  ma_golden_cross_ratio: number;
  full_bullish_alignment_count: number;
  full_bullish_alignment_ratio: number;
  trend_direction: string;
  trend_strength: string;
  rsi_oversold_count: number;
  rsi_overbought_count: number;
  rsi_neutral_count: number;
}

export interface SelectionResult {
  id: string;
  task_id: string;
  strategy_type: string;
  stock_pool: string;
  status: 'pending' | 'running' | 'analyzing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  total_stocks: number;
  selected_count: number;
  results: StockResultItem[];
  market_trend?: MarketTrendData;
  ai_summary?: string;
  sector_overview?: string;
  market_risk?: string;
  error?: string;
}

export interface HistoryItem {
  id: string;
  task_id: string;
  strategy_type: string;
  stock_pool: string;
  created_at: string;
  selected_count: number;
  status: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface StockPoolItem {
  id: string;
  name: string;
  count: number;
  description: string;
}

export interface StockPoolsResponse {
  pools: StockPoolItem[];
}

// API functions

export const apiStockSelection = {
  /**
   * Start a new selection task
   */
  async runSelection(request: RunSelectionRequest): Promise<{ task_id: string; status: string; message: string }> {
    const response = await api.post('/stock-selection/run', request);
    return response.data;
  },

  /**
   * Get selection result by task ID
   */
  async getResult(taskId: string): Promise<SelectionResult> {
    const response = await api.get(`/stock-selection/${taskId}`);
    return response.data;
  },

  /**
   * Get selection history with pagination
   */
  async getHistory(page: number = 1, pageSize: number = 20, filters?: { status?: string; stock_pool?: string }): Promise<HistoryResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (filters?.status) params.append('status', filters.status);
    if (filters?.stock_pool) params.append('stock_pool', filters.stock_pool);

    const response = await api.get(`/stock-selection/history?${params.toString()}`);
    return response.data;
  },

  /**
   * Get available stock pools
   */
  async getStockPools(): Promise<StockPoolsResponse> {
    const response = await api.get('/stock-selection/pools');
    return response.data;
  },
};

export default apiStockSelection;
