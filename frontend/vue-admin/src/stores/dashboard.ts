import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings, apiSignals, authService } from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const state = reactive({
    holdingsCount: 0,
    totalCost: 0.0,
    marketValue: 0.0,
    unrealizedPnL: 0.0,
    profitRate: 0.0,
    signalCount: 0,
    lastUpdated: null as Date | null,
    loading: false,
    error: null as string | null,
  })

  async function fetchSummary(userId: string = 'default') {
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    state.loading = true
    state.error = null
    try {
      const [portfolio, signals] = await Promise.all([
        apiHoldings.getPortfolio(userId),
        apiSignals.getLatest(10).catch(() => []),
      ])
      
      state.holdingsCount = portfolio.holdings_count ?? portfolio.items?.length ?? 0
      state.totalCost = portfolio.total_cost ?? 0
      state.marketValue = portfolio.market_value ?? 0
      state.unrealizedPnL = portfolio.profit ?? portfolio.unrealized_pnl ?? 0
      state.profitRate = portfolio.profit_rate ?? 0
      state.signalCount = Array.isArray(signals) ? signals.length : 0
      state.lastUpdated = new Date()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取数据失败'
    } finally {
      state.loading = false
    }
  }

  return { state, fetchSummary }
})