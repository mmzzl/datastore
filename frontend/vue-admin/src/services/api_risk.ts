import api from './api'

interface RiskReport {
  id: string
  name: string
  type: 'daily' | 'weekly' | 'monthly'
  date: string
  portfolio_value: number
  metrics: {
    var_95: number
    var_99: number
    expected_shortfall: number
    beta: number
    volatility: number
    max_drawdown: number
    sharpe_ratio: number
    concentration_risk: number
    concentration_score: number
  }
  holdings_risk?: Array<{
    code: string
    name: string
    weight: number
    contribution_to_risk: number
    var_contribution: number
    var_95: number
    var_99: number
    expected_shortfall: number
    volatility: number
    max_drawdown: number
    sharpe_ratio: number
    beta: number
    liquidity_days: number
    pnl_percent: number
    current_price: number
    quantity: number
    average_cost: number
    risk_score: number
    industry?: string
  }>
  stress_test?: {
    scenarios: StressScenario[]
    industry_shock: StressScenario[]
    liquidity_crisis: StressScenario | null
  } | null
  high_correlation_pairs?: Array<{
    code_1: string
    code_2: string
    correlation: number
  }> | null
  created_at: string
}

interface StressScenario {
  name: string
  description: string
  market_shock: number
  estimated_loss: number
  estimated_loss_pct: number
}

interface RiskTrend {
  dates: string[]
  risk_score: number[]
  var_95: number[]
  var_99: number[]
  max_drawdown: number[]
  sharpe_ratio: number[]
  concentration_score: number[]
}

interface PaginatedReports {
  items: RiskReport[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const apiRisk = {
  async getReports(page: number = 1, pageSize: number = 10, type?: string): Promise<PaginatedReports> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (type) params.type = type
    const res = await api.get('/risk/reports', { params })
    return res.data
  },

  async getReport(id: string): Promise<RiskReport> {
    const res = await api.get(`/risk/reports/${id}`)
    return res.data
  },

  async getTrend(userId: string, days: number = 30): Promise<RiskTrend> {
    const res = await api.get(`/risk/reports/trend/${userId}`, { params: { days } })
    return res.data
  }
}

export type { RiskReport, RiskTrend, PaginatedReports, StressScenario }
