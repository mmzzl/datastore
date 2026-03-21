import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

let authToken: string | null = localStorage.getItem('auth_token')

export const authService = {
  setToken(token: string) {
    authToken = token
    localStorage.setItem('auth_token', token)
  },
  getToken() {
    return authToken
  },
  clearToken() {
    authToken = null
    localStorage.removeItem('auth_token')
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
    if (error.response?.status === 401) {
      authService.clearToken()
    }
    return Promise.reject(error)
  }
)

export const apiAuth = {
  async login(userId: string, password: string) {
    const res = await api.post('/login', { user_id: userId, password })
    if (res.data.token) {
      authService.setToken(res.data.token)
    }
    return res.data
  },
  logout() {
    authService.clearToken()
  }
}

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
  async removeHolding(userId: string, code: string) {
    const res = await api.delete(`/holdings/${userId}/${code}`)
    return res.data
  },
  async getPortfolio(userId: string) {
    const res = await api.get(`/portfolio/${userId}`)
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

export const apiHealth = {
  async check() {
    const res = await api.get('/health')
    return res.data
  }
}

export default api