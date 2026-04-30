import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings, apiStocks, authService } from '../services/api'

interface Holding {
  code: string
  name?: string
  quantity: number
  average_cost: number
}

interface PaginatedHoldings {
  items: Holding[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const useHoldingsStore = defineStore('holdings', () => {
  const state = reactive({
    userId: authService.getUser(),
    holdings: [] as Holding[],
    totalCost: 0 as number,
    marketValue: 0 as number,
    unrealizedPnL: 0 as number,
    profitRate: 0 as number,
    loading: false,
    error: null as string | null,
    // 分页
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    totalCount: 0,
  })

  async function fetchHoldings(userId?: string, page: number = 1) {
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    const id = userId || state.userId
    state.loading = true
    state.error = null
    try {
      const res: PaginatedHoldings = await apiHoldings.getHoldings(id, page, state.pageSize)
      let holdings = res.items || []
      
      // 获取股票名称
      if (holdings.length > 0) {
        const codes = holdings.map((h: Holding) => h.code)
        try {
          const priceRes = await apiStocks.getRealtimePrices(codes)
          if (priceRes?.data) {
            holdings = holdings.map((h: Holding) => {
              const priceData = priceRes.data[h.code]
              if (priceData && priceData.name) {
                return { ...h, name: priceData.name }
              }
              return h
            })
          }
        } catch (e) {
          console.warn('获取股票名称失败:', e)
        }
      }
      
      state.holdings = holdings
      state.currentPage = res.page || 1
      state.totalPages = res.total_pages || 0
      state.totalCount = res.total || 0
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取持仓失败'
    } finally {
      state.loading = false
    }
  }

  async function saveHolding(userId: string, code: string, name: string | undefined, quantity: number, avgCost: number) {
    if (!authService.isAuthenticated()) {
      throw new Error('未登录')
    }
    await apiHoldings.upsertHolding(userId, code, name, quantity, avgCost)
    await fetchHoldings(userId, state.currentPage)
  }

  async function sellHolding(userId: string, code: string, quantity: number, price: number) {
    if (!authService.isAuthenticated()) {
      throw new Error('未登录')
    }
    await apiHoldings.sellHolding(userId, code, quantity, price)
    await fetchHoldings(userId, state.currentPage)
  }

  async function removeHolding(userId: string, code: string) {
    if (!authService.isAuthenticated()) {
      throw new Error('未登录')
    }
    await apiHoldings.removeHolding(userId, code)
    await fetchHoldings(userId, state.currentPage)
  }

  async function refreshPortfolio(userId: string) {
    if (!authService.isAuthenticated()) {
      state.error = '未登录'
      return
    }
    state.loading = true
    try {
      const summary = await apiHoldings.getPortfolio(userId)
      const unrealized = summary.profit ?? summary.unrealized_pnl ?? 0
      const realized = summary.realized_pnl ?? 0
      state.totalCost = summary.total_cost ?? 0
      state.marketValue = summary.market_value ?? 0
      state.unrealizedPnL = unrealized + realized
      state.profitRate = summary.profit_rate ?? 0
      return summary
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取组合失败'
      throw e
    } finally {
      state.loading = false
    }
  }

  return {
    state,
    fetchHoldings,
    saveHolding,
    sellHolding,
    removeHolding,
    refreshPortfolio
  }
})