import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings, authService } from '../services/api'

interface Holding {
  code: string
  name?: string
  quantity: number
  average_cost: number
}

export const useHoldingsStore = defineStore('holdings', () => {
  const state = reactive({
    userId: 'default',
    holdings: [] as Holding[],
    totalCost: 0 as number,
    marketValue: 0 as number,
    unrealizedPnL: 0 as number,
    profitRate: 0 as number,
    loading: false,
    error: null as string | null,
  })

  async function fetchHoldings(userId?: string) {
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    const id = userId || state.userId
    state.loading = true
    state.error = null
    try {
      const res = await apiHoldings.getHoldings(id)
      state.holdings = res || []
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取持仓失败'
    } finally {
      state.loading = false
    }
  }

  async function saveHolding(userId: string, code: string, quantity: number, avgCost: number) {
    if (!authService.isAuthenticated()) {
      throw new Error('未登录')
    }
    await apiHoldings.upsertHolding(userId, code, quantity, avgCost)
    await fetchHoldings(userId)
  }

  async function removeHolding(userId: string, code: string) {
    if (!authService.isAuthenticated()) {
      throw new Error('未登录')
    }
    await apiHoldings.removeHolding(userId, code)
    await fetchHoldings(userId)
  }

  async function refreshPortfolio(userId: string) {
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    state.loading = true
    try {
      const summary = await apiHoldings.getPortfolio(userId)
      state.totalCost = summary.total_cost ?? 0
      state.marketValue = summary.market_value ?? 0
      state.unrealizedPnL = summary.profit ?? summary.unrealized_pnl ?? 0
      state.profitRate = summary.profit_rate ?? 0
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取组合失败'
    } finally {
      state.loading = false
    }
  }

  return { 
    state, 
    fetchHoldings, 
    saveHolding, 
    removeHolding,
    refreshPortfolio 
  }
})