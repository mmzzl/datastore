import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

let authToken: string | null = localStorage.getItem('auth_token')
let currentUser: string | null = localStorage.getItem('auth_user')

export const authService = {
  setToken(token: string) {
    authToken = token
    localStorage.setItem('auth_token', token)
  },
  getToken() {
    return authToken
  },
  setUser(user: string) {
    currentUser = user
    localStorage.setItem('auth_user', user)
  },
  getUser() {
    return currentUser || 'default'
  },
  clearToken() {
    authToken = null
    currentUser = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  },
  isAuthenticated() {
    return !!authToken
  }
}

api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail: string = error.response?.data?.detail || ''

    if (
      status === 401 ||
      status === 403 ||
      detail.includes('Invalid or expired token') ||
      detail.includes('Not authenticated') ||
      detail.includes('token')
    ) {
      authService.clearToken()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export const apiAuth = {
  async login(username: string, password: string) {
    const res = await api.post('/login', { username, password })
    if (res.data.token) {
      authService.setToken(res.data.token)
      authService.setUser(username)
    }
    return res.data
  },
  logout() {
    authService.clearToken()
  }
}

export const apiHoldings = {
  async getHoldings(userId: string, page: number = 1, pageSize: number = 10) {
    const res = await api.get(`/holdings/${userId}`, { params: { page, page_size: pageSize } })
    return res.data
  },
  async getHoldingsHistory(userId: string) {
    const res = await api.get(`/holdings/${userId}/history`)
    return res.data
  },
  async upsertHolding(userId: string, code: string, name: string | undefined, quantity: number, average_cost: number) {
    const payload = { code, quantity, average_cost }
    if (name) {
      payload.name = name
    }
    const res = await api.post(`/holdings/${userId}`, payload)
    return res.data
  },
  async removeHolding(userId: string, code: string) {
    const res = await api.delete(`/holdings/${userId}/${code}`)
    return res.data
  },
  async getPortfolio(userId: string) {
    const res = await api.get(`/portfolio/${userId}`)
    return res.data
  },
  async getTransactions(userId: string, code?: string, page: number = 1, pageSize: number = 10) {
    const params: any = { page, page_size: pageSize }
    if (code) params.code = code
    const res = await api.get(`/transactions/${userId}`, { params })
    return res.data
  },
  async deleteTransaction(userId: string, transactionId: string) {
    const res = await api.delete(`/transactions/${userId}/${transactionId}`)
    return res.data
  },
  async getRealizedPnL(userId: string, code?: string) {
    const params = code ? { params: { code } } : {}
    const res = await api.get(`/pnl/${userId}`, params)
    return res.data
  }
}

export const apiSignals = {
  async getLatest(n: number = 10) {
    const res = await api.get(`/signals/latest`, { params: { n } })
    return res.data
  },
  async push(signal: any) {
    const res = await api.post('/signals', signal)
    return res.data
  }
}

export const apiSettings = {
  async getSettings(userId: string) {
    const res = await api.get(`/settings/${userId}`)
    return res.data
  },
  async setSettings(userId: string, settings: { watchlist?: string[], interval_sec?: number, days?: number, cache_ttl?: number }) {
    const res = await api.post(`/settings/${userId}`, settings)
    return res.data
  }
}

export const apiStocks = {
  async searchStocks(keyword: string, limit: number = 20) {
    const res = await api.get('/stock/search', { params: { q: keyword, limit } })
    return res.data
  },
  async getStockList(params?: { keyword?: string; market?: string; type?: string; limit?: number }) {
    const res = await api.get('/stock/list', { params })
    return res.data
  },
  async getRealtimePrices(codes: string[]) {
    const res = await api.get('/stock/realtime', { params: { codes: codes.join(',') } })
    return res.data
  },
  async getRealtimePrice(code: string) {
    const res = await api.get(`/stock/realtime/${code}`)
    return res.data
  }
}

export const apiHealth = {
  async check() {
    const res = await api.get('/health')
    return res.data
  }
}

export default api