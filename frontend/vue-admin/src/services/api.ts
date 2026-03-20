import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export const apiHoldings = {
  async getHoldings(userId: string) {
    const res = await api.get(`/holdings/${userId}`)
    return res.data
  },
  async upsertHolding(userId: string, code: string, quantity: number, average_cost: number) {
    const payload = { code, quantity, average_cost }
    const res = await api.post(`/holdings/${userId}`, payload)
    return res.data
  },
  async getPortfolio(userId: string, priceFetcher?: (code: string) => number) {
    // priceFetcher 为前端回填的价格，例如用于计算市值；此处简化为后端提供
    const res = await api.get(`/portfolio/${userId}`)
    return res.data
  }
}

export const apiSignals = {
  async getLatest() {
    const res = await (await fetch('/api/signals/latest')).json()
    return res
  },
  async push(signal: any) {
    const resp = await fetch('/api/signals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal)
    })
    return resp.json()
  }
}
