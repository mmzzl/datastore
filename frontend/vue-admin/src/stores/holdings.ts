import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiHoldings } from '../services/api'

interface Holding {
  code: string
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
  })

  async function fetchHoldings(userId?: string) {
    const id = userId || state.userId
    const res = await apiHoldings.getHoldings(id)
    state.holdings = res as any
  }

  async function saveHolding(userId: string, code: string, quantity: number, avgCost: number) {
    await apiHoldings.upsertHolding(userId, code, quantity, avgCost)
  }

  async function refreshPortfolio(userId: string, priceFetcher?: (code: string) => number) {
    const summary = await apiHoldings.getPortfolio(userId, priceFetcher)
    state.totalCost = summary.total_cost ?? 0
    state.marketValue = summary.market_value ?? 0
    state.unrealizedPnL = summary.unrealized_pnl ?? 0
  }

  async function addHolding(userId: string, code: string, quantity: number, averageCost: number) {
    await apiHoldings.upsertHolding(userId, code, quantity, averageCost)
  }

  return { state, fetchHoldings, saveHolding, refreshPortfolio, addHolding }
})
