import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api_stock_selection', () => ({
  default: {
    runSelection: vi.fn(),
    getResult: vi.fn(),
    getHistory: vi.fn(),
    getStockPools: vi.fn(),
  },
}))

import apiStockSelection from '@/services/api_stock_selection'
import { useStockSelectionStore } from '@/stores/stockSelection'

describe('StockSelection Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have initial state', () => {
      const store = useStockSelectionStore()
      expect(store.state.currentResult).toBeNull()
      expect(store.state.history).toEqual([])
      expect(store.state.stockPools).toEqual([])
      expect(store.state.loading).toBe(false)
      expect(store.state.running).toBe(false)
      expect(store.state.error).toBeNull()
    })
  })

  describe('runSelection', () => {
    it('should run selection and return task id', async () => {
      vi.mocked(apiStockSelection.runSelection).mockResolvedValue({ task_id: 'task-123' })
      vi.mocked(apiStockSelection.getResult).mockResolvedValue({ task_id: 'task-123', status: 'completed' })

      const store = useStockSelectionStore()
      const result = await store.runSelection({ strategy: 'test' } as any)

      expect(store.state.running).toBe(false)
      expect(result).toBe('task-123')
    })

    it('should handle error on runSelection', async () => {
      vi.mocked(apiStockSelection.runSelection).mockRejectedValue({
        response: { data: { detail: 'Failed' } },
      })

      const store = useStockSelectionStore()
      await expect(store.runSelection({} as any)).rejects.toThrow()

      expect(store.state.error).toBe('Failed')
    })
  })

  describe('fetchHistory', () => {
    it('should fetch history and update state', async () => {
      vi.mocked(apiStockSelection.getHistory).mockResolvedValue({
        items: [{ id: '1' }],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      })

      const store = useStockSelectionStore()
      await store.fetchHistory()

      expect(store.state.history).toHaveLength(1)
      expect(store.state.loadingHistory).toBe(false)
    })

    it('should throw error on fetchHistory failure', async () => {
      vi.mocked(apiStockSelection.getHistory).mockRejectedValue({
        response: { data: { detail: 'Error' } },
      })

      const store = useStockSelectionStore()
      await expect(store.fetchHistory()).rejects.toThrow()
    })
  })

  describe('fetchStockPools', () => {
    it('should fetch stock pools', async () => {
      vi.mocked(apiStockSelection.getStockPools).mockResolvedValue({
        pools: [{ id: '1', name: 'Pool1' }],
      })

      const store = useStockSelectionStore()
      await store.fetchStockPools()

      expect(store.state.stockPools).toHaveLength(1)
    })
  })

  describe('clearError', () => {
    it('should clear error', () => {
      const store = useStockSelectionStore()
      store.state.error = 'test error'

      store.clearError()

      expect(store.state.error).toBeNull()
    })
  })
})
