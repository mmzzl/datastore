import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api', () => ({
  apiHoldings: {
    getPortfolio: vi.fn(),
  },
  apiSignals: {
    getLatest: vi.fn(),
  },
  apiStocks: {
    getRealtimePrices: vi.fn(),
  },
  authService: {
    getUser: vi.fn(() => 'admin'),
    isAuthenticated: vi.fn(() => true),
  },
}))

import { apiHoldings, apiSignals, apiStocks, authService } from '@/services/api'
import { useDashboardStore } from '@/stores/dashboard'

describe('Dashboard Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(authService.getUser).mockReturnValue('admin')
    vi.mocked(authService.isAuthenticated).mockReturnValue(true)
  })

  describe('Initial State', () => {
    it('should have initial zero values', () => {
      const store = useDashboardStore()
      expect(store.state.holdingsCount).toBe(0)
      expect(store.state.totalCost).toBe(0)
      expect(store.state.marketValue).toBe(0)
      expect(store.state.unrealizedPnL).toBe(0)
      expect(store.state.realizedPnL).toBe(0)
      expect(store.state.profitRate).toBe(0)
      expect(store.state.signalCount).toBe(0)
      expect(store.state.lastUpdated).toBeNull()
      expect(store.state.loading).toBe(false)
      expect(store.state.error).toBeNull()
      expect(store.state.holdings).toEqual([])
    })
  })

  describe('fetchSummary', () => {
    it('should set error when not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false)

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.error).toBe('未登录')
    })

    it('should fetch portfolio data successfully', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        holdings_count: 5,
        total_cost: 100000,
        realized_pnl: 5000,
        holdings: [
          { code: 'SH600000', quantity: 1000, average_cost: 100 },
        ],
      })
      vi.mocked(apiStocks.getRealtimePrices).mockResolvedValue({
        data: {
          SH600000: { price: 120, change: 20, change_pct: 0.2, name: '测试' },
        },
      })
      vi.mocked(apiSignals.getLatest).mockResolvedValue([{}, {}, {}])

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.holdingsCount).toBe(5)
      expect(store.state.totalCost).toBe(100000)
      expect(store.state.realizedPnL).toBe(5000)
      expect(store.state.marketValue).toBe(120000)
      expect(store.state.unrealizedPnL).toBe(20000)
      expect(store.state.signalCount).toBe(3)
      expect(store.state.lastUpdated).toBeInstanceOf(Date)
      expect(store.state.loading).toBe(false)
    })

    it('should handle empty holdings', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        holdings_count: 0,
        total_cost: 0,
        realized_pnl: 0,
        holdings: [],
        market_value: 0,
        profit_rate: 0,
      })
      vi.mocked(apiSignals.getLatest).mockResolvedValue([])

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.holdingsCount).toBe(0)
      expect(store.state.totalCost).toBe(0)
      expect(store.state.marketValue).toBe(0)
      expect(store.state.signalCount).toBe(0)
    })

    it('should calculate profit correctly', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        holdings_count: 1,
        total_cost: 10000,
        realized_pnl: 0,
        holdings: [{ code: 'SH600000', quantity: 100, average_cost: 100 }],
      })
      vi.mocked(apiStocks.getRealtimePrices).mockResolvedValue({
        data: { SH600000: { price: 110, name: 'test' } },
      })

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.marketValue).toBe(11000)
      expect(store.state.unrealizedPnL).toBe(1000)
      expect(store.state.profitRate).toBe(0.1)
    })

    it('should set error on API failure', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockRejectedValue({
        response: { data: { detail: 'API Error' } },
      })

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.error).toBe('API Error')
      expect(store.state.loading).toBe(false)
      expect(store.state.holdingsCount).toBe(0)
      expect(store.state.totalCost).toBe(0)
    })

    it('should handle price fetch failure gracefully', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        holdings_count: 1,
        total_cost: 10000,
        realized_pnl: 0,
        holdings: [{ code: 'SH600000', quantity: 100, average_cost: 100 }],
        market_value: 10500,
        profit: 500,
        profit_rate: 0.05,
      })
      vi.mocked(apiStocks.getRealtimePrices).mockRejectedValue(new Error('Network error'))

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.marketValue).toBe(10500)
      expect(store.state.unrealizedPnL).toBe(500)
    })

    it('should handle signal fetch failure gracefully', async () => {
      vi.mocked(apiHoldings.getPortfolio).mockResolvedValue({
        holdings_count: 0,
        total_cost: 0,
        realized_pnl: 0,
        holdings: [],
        market_value: 0,
        profit_rate: 0,
      })
      vi.mocked(apiSignals.getLatest).mockRejectedValue(new Error('Signal API error'))

      const store = useDashboardStore()
      await store.fetchSummary()

      expect(store.state.signalCount).toBe(0)
      expect(store.state.loading).toBe(false)
    })
  })
})
