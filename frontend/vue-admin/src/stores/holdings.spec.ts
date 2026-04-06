import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api', () => ({
  apiHoldings: {
    getHoldings: vi.fn(),
    upsertHolding: vi.fn(),
    removeHolding: vi.fn(),
    getPortfolio: vi.fn(),
  },
  apiStocks: {
    getRealtimePrices: vi.fn(),
  },
  authService: {
    getUser: vi.fn(() => 'admin'),
    isAuthenticated: vi.fn(() => true),
  },
}))

import { apiHoldings, apiStocks, authService } from '@/services/api'
import { useHoldingsStore } from '@/stores/holdings'

describe('Holdings Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(authService.getUser).mockReturnValue('admin')
    vi.mocked(authService.isAuthenticated).mockReturnValue(true)
  })

  describe('Initial State', () => {
    it('should have empty holdings array', () => {
      const store = useHoldingsStore()
      expect(store.state.holdings).toEqual([])
      expect(store.state.totalCost).toBe(0)
      expect(store.state.marketValue).toBe(0)
      expect(store.state.unrealizedPnL).toBe(0)
      expect(store.state.profitRate).toBe(0)
      expect(store.state.loading).toBe(false)
      expect(store.state.error).toBeNull()
    })

    it('should have default pagination values', () => {
      const store = useHoldingsStore()
      expect(store.state.currentPage).toBe(1)
      expect(store.state.pageSize).toBe(10)
      expect(store.state.totalPages).toBe(0)
      expect(store.state.totalCount).toBe(0)
    })
  })

  describe('fetchHoldings', () => {
    it('should set error when not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false)

      const store = useHoldingsStore()
      await store.fetchHoldings('admin')

      expect(store.state.error).toBe('未登录')
    })

    it('should fetch holdings and update state', async () => {
      vi.mocked(apiHoldings.getHoldings).mockResolvedValue({
        items: [
          { code: 'SH600000', quantity: 100, average_cost: 10.0 },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })
      vi.mocked(apiStocks.getRealtimePrices).mockResolvedValue({
        data: { SH600000: { name: '测试股票' } },
      })

      const store = useHoldingsStore()
      await store.fetchHoldings('admin')

      expect(store.state.holdings).toHaveLength(1)
      expect(store.state.holdings[0].code).toBe('SH600000')
      expect(store.state.holdings[0].name).toBe('测试股票')
      expect(store.state.totalCount).toBe(1)
      expect(store.state.currentPage).toBe(1)
      expect(store.state.loading).toBe(false)
    })

    it('should set error on API failure', async () => {
      vi.mocked(apiHoldings.getHoldings).mockRejectedValue({
        response: { data: { detail: 'API Error' } },
      })

      const store = useHoldingsStore()
      await store.fetchHoldings('admin')

      expect(store.state.error).toBe('API Error')
      expect(store.state.loading).toBe(false)
    })

    it('should handle price fetch failure in fetchHoldings', async () => {
      vi.mocked(apiHoldings.getHoldings).mockResolvedValue({
        items: [
          { code: 'SH600000', quantity: 100, average_cost: 10.0 },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })
      vi.mocked(apiStocks.getRealtimePrices).mockRejectedValue(new Error('Price API error'))

      const store = useHoldingsStore()
      await store.fetchHoldings('admin')

      expect(store.state.holdings).toHaveLength(1)
      expect(store.state.holdings[0].code).toBe('SH600000')
      expect(store.state.loading).toBe(false)
    })
  })

  describe('saveHolding', () => {
    it('should throw error when not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false)

      const store = useHoldingsStore()
      await expect(store.saveHolding('admin', 'SH600000', 'test', 100, 10)).rejects.toThrow('未登录')
    })

    it('should call API to save holding', async () => {
      vi.mocked(apiHoldings.upsertHolding).mockResolvedValue({ success: true })
      vi.mocked(apiHoldings.getHoldings).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0,
      })

      const store = useHoldingsStore()
      await store.saveHolding('admin', 'SH600000', 'test', 100, 10)

      expect(apiHoldings.upsertHolding).toHaveBeenCalledWith('admin', 'SH600000', 'test', 100, 10)
    })

    it('should handle API error on save holding', async () => {
      vi.mocked(apiHoldings.upsertHolding).mockRejectedValue({
        response: { data: { detail: 'Save failed' } },
      })

      const store = useHoldingsStore()
      await expect(store.saveHolding('admin', 'SH600000', 'test', 100, 10)).rejects.toThrow()
    })
  })

  describe('removeHolding', () => {
    it('should throw error when not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false)

      const store = useHoldingsStore()
      await expect(store.removeHolding('admin', 'SH600000')).rejects.toThrow('未登录')
    })

    it('should call API to remove holding', async () => {
      vi.mocked(apiHoldings.removeHolding).mockResolvedValue({ success: true })
      vi.mocked(apiHoldings.getHoldings).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0,
      })

      const store = useHoldingsStore()
      await store.removeHolding('admin', 'SH600000')

      expect(apiHoldings.removeHolding).toHaveBeenCalledWith('admin', 'SH600000')
    })

    it('should handle API error on remove holding', async () => {
      vi.mocked(apiHoldings.removeHolding).mockRejectedValue({
        response: { data: { detail: 'Remove failed' } },
      })

      const store = useHoldingsStore()
      await expect(store.removeHolding('admin', 'SH600000')).rejects.toThrow()
    })
  })

  describe('refreshPortfolio', () => {
    it('should set error when not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false)

      const store = useHoldingsStore()
      await store.refreshPortfolio('admin')

      expect(store.state.error).toBe('未登录')
    })

    it('should fetch portfolio and update state', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        total_cost: 10000,
        market_value: 15000,
        unrealized_pnl: 5000,
        profit_rate: 0.5,
        realized_pnl: 0,
      })

      const store = useHoldingsStore()
      const result = await store.refreshPortfolio('admin')

      expect(store.state.totalCost).toBe(10000)
      expect(store.state.marketValue).toBe(15000)
      expect(store.state.unrealizedPnL).toBe(5000)
      expect(store.state.profitRate).toBe(0.5)
      expect(result).toHaveProperty('total_cost')
    })

    it('should handle missing profit_rate with profit field', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        total_cost: 10000,
        market_value: 12000,
        profit: 2000,
        realized_pnl: 500,
        profit_rate: 0,
      })

      const store = useHoldingsStore()
      await store.refreshPortfolio('admin')

      expect(store.state.unrealizedPnL).toBe(2500)
    })
  })
})
