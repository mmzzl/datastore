import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings, apiSignals, authService } from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const state = reactive({
    holdingsCount: 0,
    totalCost: 0.0,
    marketValue: 0.0,
    unrealizedPnL: 0.0,
    realizedPnL: 0.0,
    profitRate: 0.0,
    signalCount: 0,
    lastUpdated: null as Date | null,
    loading: false,
    error: null as string | null,
  })

  async function fetchSummary() {
    const userId = authService.getUser()
    
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    
    state.loading = true
    state.error = null
    
    try {
      // 使用正确的用户ID获取持仓数据
      const portfolio = await apiHoldings.getPortfolio(userId)
      
      // 更新持仓数量
      state.holdingsCount = portfolio?.holdings_count ?? portfolio?.holdings?.length ?? 0
      state.totalCost = portfolio?.total_cost ?? 0
      state.marketValue = portfolio?.market_value ?? 0
      state.unrealizedPnL = portfolio?.profit ?? portfolio?.unrealized_pnl ?? 0
      state.realizedPnL = portfolio?.realized_pnl ?? 0
      state.profitRate = portfolio?.profit_rate ?? 0
      
      // 获取信号数据
      try {
        const signals = await apiSignals.getLatest(10)
        state.signalCount = Array.isArray(signals) ? signals.length : 0
      } catch {
        state.signalCount = 0
      }
      
      state.lastUpdated = new Date()
    } catch (e: any) {
      console.error('获取Dashboard数据失败:', e)
      state.error = e.response?.data?.detail || '获取数据失败'
      state.holdingsCount = 0
      state.totalCost = 0
    } finally {
      state.loading = false
    }
  }

  return { state, fetchSummary }
})