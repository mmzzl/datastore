/**
 * Stock Selection Store
 *
 * Manages state for strategy-based stock selection.
 */

import { defineStore } from 'pinia';
import { reactive } from 'vue';
import apiStockSelection, {
  type SelectionResult,
  type HistoryItem,
  type StockPoolItem,
  type RunSelectionRequest,
} from '../services/api_stock_selection';

export const useStockSelectionStore = defineStore('stockSelection', () => {
  const state = reactive({
    // Current selection result
    currentResult: null as SelectionResult | null,

    // History
    history: [] as HistoryItem[],
    historyTotal: 0,
    historyPage: 1,
    historyPageSize: 20,

    // Stock pools
    stockPools: [] as StockPoolItem[],

    // Loading states
    loading: false,
    running: false,
    loadingHistory: false,

    // Error
    error: null as string | null,
  });

  /**
   * Run a new selection task
   */
  async function runSelection(request: RunSelectionRequest): Promise<string> {
    state.running = true;
    state.error = null;

    try {
      const response = await apiStockSelection.runSelection(request);
      const taskId = response.task_id;

      // Poll for result
      await pollForResult(taskId);

      return taskId;
    } catch (e: any) {
      state.error = e.response?.data?.detail || '选股任务启动失败';
      throw e;
    } finally {
      state.running = false;
    }
  }

  /**
   * Poll for selection result
   */
  async function pollForResult(taskId: string, maxAttempts: number = 120): Promise<void> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const result = await apiStockSelection.getResult(taskId);

        if (result.status === 'completed' || result.status === 'failed') {
          state.currentResult = result;
          return;
        }

        // Wait 1 second before next poll
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
      } catch (e) {
        console.error('Poll error:', e);
        attempts++;
      }
    }

    state.error = '选股任务超时';
  }

  /**
   * Get selection result by task ID
   */
  async function fetchResult(taskId: string): Promise<void> {
    state.loading = true;
    state.error = null;

    try {
      state.currentResult = await apiStockSelection.getResult(taskId);
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取选股结果失败';
      throw e;
    } finally {
      state.loading = false;
    }
  }

  /**
   * Fetch history with pagination
   */
  async function fetchHistory(page: number = 1, filters?: { status?: string; stock_pool?: string }): Promise<void> {
    state.loadingHistory = true;
    state.error = null;

    try {
      const response = await apiStockSelection.getHistory(page, state.historyPageSize, filters);
      state.history = response.items;
      state.historyTotal = response.total;
      state.historyPage = page;
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取选股历史失败';
      throw e;
    } finally {
      state.loadingHistory = false;
    }
  }

  /**
   * Fetch available stock pools
   */
  async function fetchStockPools(): Promise<void> {
    try {
      const response = await apiStockSelection.getStockPools();
      state.stockPools = response.pools;
    } catch (e: any) {
      console.error('Failed to fetch stock pools:', e);
    }
  }

  /**
   * Clear current result
   */
  function clearResult(): void {
    state.currentResult = null;
  }

  /**
   * Clear error
   */
  function clearError(): void {
    state.error = null;
  }

  return {
    state,
    runSelection,
    fetchResult,
    fetchHistory,
    fetchStockPools,
    clearResult,
    clearError,
  };
});
