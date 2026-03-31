import api from './api'

interface BacktestRequest {
  strategy: string
  model_id?: string
  instruments?: string[]
  start_date: string
  end_date: string
  initial_capital?: number
  commission_rate?: number
}

interface BacktestResult {
  id: string
  strategy: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  trades?: BacktestTrade[]
}

interface BacktestTrade {
  date: string
  code: string
  action: 'buy' | 'sell'
  quantity: number
  price: number
  amount: number
}

interface PaginatedResults {
  items: BacktestResult[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const apiBacktest = {
  async startBacktest(request: BacktestRequest): Promise<{ id: string }> {
    const res = await api.post('/backtest/run', request)
    return res.data
  },

  async getResults(page: number = 1, pageSize: number = 10): Promise<PaginatedResults> {
    const res = await api.get('/backtest/results', {
      params: { page, page_size: pageSize }
    })
    return res.data
  },

  async getResult(id: string): Promise<BacktestResult> {
    const res = await api.get(`/backtest/results/${id}`)
    return res.data
  }
}

export type { BacktestRequest, BacktestResult, BacktestTrade, PaginatedResults }
