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
    concentration_risk: number
  }
  holdings_risk?: Array<{
    code: string
    name: string
    weight: number
    contribution_to_risk: number
    var_contribution: number
  }>
  created_at: string
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
  }
}

export type { RiskReport, PaginatedReports }
