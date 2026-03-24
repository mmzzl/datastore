import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings, apiSignals, apiStocks, authService } from '../services/api'

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
    holdings: [] as any[],
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
      const portfolio = await apiHoldings.getPortfolio(userId)

      state.holdingsCount = portfolio?.holdings_count ?? portfolio?.holdings?.length ?? 0
      state.totalCost = portfolio?.total_cost ?? 0
      state.realizedPnL = portfolio?.realized_pnl ?? 0
      state.holdings = portfolio?.holdings ?? []

    if (state.holdings.length > 0) {
      const codes = state.holdings.map((h: any) => h.code)
      try {
        const priceRes = await apiStocks.getRealtimePrices(codes)
        if (priceRes?.data) {
          let totalMarketValue = 0
          for (const h of state.holdings) {
            const priceData = priceRes.data[h.code]
            if (priceData) {
              h.current_price = priceData.price
              h.change = priceData.change
              h.change_pct = priceData.change_pct
              h.market_value = h.quantity * priceData.price
              h.profit = h.market_value - h.quantity * h.average_cost
              h.profit_pct = h.average_cost > 0 ? (h.profit / (h.quantity * h.average_cost)) * 100 : 0
              if (priceData.name) {
                h.name = priceData.name
              }
              totalMarketValue += h.market_value
            }
          }
          state.marketValue = totalMarketValue
          state.unrealizedPnL = totalMarketValue - state.totalCost
          state.profitRate = state.totalCost > 0 ? state.unrealizedPnL / state.totalCost : 0
        }
      } catch (e) {
        console.warn('获取实时价格失败:', e)
        state.marketValue = portfolio?.market_value ?? 0
        state.unrealizedPnL = portfolio?.profit ?? portfolio?.unrealized_pnl ?? 0
        state.profitRate = portfolio?.profit_rate ?? 0
      }
    } else {
        state.marketValue = portfolio?.market_value ?? 0
        state.unrealizedPnL = portfolio?.profit ?? portfolio?.unrealized_pnl ?? 0
        state.profitRate = portfolio?.profit_rate ?? 0
      }

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