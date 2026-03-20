import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings } from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const state = reactive({
    holdingsCount: 0,
    totalCost: 0.0,
    marketValue: 0.0,
    unrealizedPnL: 0.0,
    signalCount: 0,
    lastUpdated: null as Date | null,
  })

  async function fetchSummary(userId: string = 'default') {
    try {
      const res = await fetch(`/api/portfolio/${userId}`)
      const data = await res.json()
      state.holdingsCount = data.holdings_count ?? 0
      state.totalCost = data.total_cost ?? 0
      state.marketValue = data.market_value ?? 0
      state.unrealizedPnL = data.unrealized_pnl ?? 0
      // 信号数量示意，后续接入真实信号源
      state.signalCount = (data.data_points ?? 0) + 0
      state.lastUpdated = new Date()
    } catch {
      // ignore
    }
  }

  return { state, fetchSummary }
})
