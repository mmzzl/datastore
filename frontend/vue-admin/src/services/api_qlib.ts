import api from './api'

interface TrainingRequest {
  model_type: string
  instruments?: string[]
  start_date?: string
  end_date?: string
  features?: string[]
  hyperparams?: Record<string, any>
}

interface TrainingStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
  started_at?: string
  completed_at?: string
  error?: string
}

interface Model {
  id: string
  name: string
  model_type: string
  created_at: string
  metrics?: Record<string, number>
  status: 'active' | 'inactive'
  path?: string
}

interface SelectionRequest {
  model_id: string
  instruments?: string[]
  top_k?: number
  date?: string
}

interface SelectionResult {
  id: string
  model_id: string
  date: string
  stocks: Array<{
    code: string
    name: string
    score: number
    rank: number
  }>
  created_at: string
}

interface Instrument {
  code: string
  name: string
}

interface Experiment {
  experiment_id: string
  tag: string | null
  config: Record<string, any>
  training_metrics: Record<string, any> | null
  backtest_result: Record<string, any> | null
  model_id: string | null
  status: string
  created_at: string | null
  error: string | null
}

interface ExperimentListResult {
  items: Experiment[]
  total: number
  page: number
  page_size: number
}

interface BestModel {
  experiment_id: string
  model_id: string | null
  tag: string | null
  config: Record<string, any>
  training_metrics: Record<string, any> | null
  backtest_result: Record<string, any> | null
  status: string
}

interface TopStockItem {
  rank: number
  code: string
  name: string | null
  score: number
}

interface TopStocksDay {
  date: string
  model_id: string
  model_type: string
  factor: string
  stocks: TopStockItem[]
  created_at: string | null
}

interface TopStocksListResponse {
  items: TopStocksDay[]
  total: number
  page: number
  page_size: number
}

interface TrainingTask {
  task_id: string
  job_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'revoked'
  progress: number
  message: string | null
  config: Record<string, any>
  result: Record<string, any> | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

interface TrainingTasksResponse {
  items: TrainingTask[]
  total: number
  page: number
  page_size: number
}

export const apiQlib = {
  async startTraining(request: TrainingRequest): Promise<{ task_id: string }> {
    const res = await api.post('/qlib/train', request)
    return res.data
  },

  async getTrainingStatus(id: string): Promise<TrainingStatus> {
    const res = await api.get(`/qlib/train/${id}`)
    return res.data
  },

  async getModels(): Promise<{ items: Model[]; total: number }> {
    const res = await api.get('/qlib/models')
    return res.data
  },

  async getModel(id: string): Promise<Model> {
    const res = await api.get(`/qlib/models/${id}`)
    return res.data
  },

  async runSelection(request: SelectionRequest): Promise<SelectionResult> {
    const res = await api.post('/qlib/select', request)
    return res.data
  },

  async getCSI300(): Promise<Instrument[]> {
    const res = await api.get('/qlib/instruments/csi300')
    return res.data
  },

  async getExperiments(page: number = 1, pageSize: number = 20, tag?: string, status?: string): Promise<ExperimentListResult> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (tag) params.tag = tag
    if (status) params.status = status
    const res = await api.get('/qlib/experiments', { params })
    return res.data
  },

  async compareExperiments(ids: string[]): Promise<Record<string, any>> {
    const res = await api.get('/qlib/experiments/compare', { params: { ids: ids.join(',') } })
    return res.data
  },

  async getBestModel(): Promise<BestModel> {
    const res = await api.get('/qlib/best-model')
    return res.data
  },

  async getTopStocks(startDate?: string, endDate?: string, modelId?: string, page: number = 1, pageSize: number = 20): Promise<TopStocksListResponse> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (modelId) params.model_id = modelId
    const res = await api.get('/qlib/top-stocks', { params })
    return res.data
  },

  async refreshTopStocks(): Promise<{ message: string; date: string; model_id: string; count: number }> {
    const res = await api.post('/qlib/top-stocks/refresh')
    return res.data
  },

  async getTrainingTasks(page: number = 1, pageSize: number = 20): Promise<TrainingTasksResponse> {
    const res = await api.get('/qlib/tasks', { params: { page, page_size: pageSize } })
    return res.data
  },

  async revokeTrainingTask(taskId: string): Promise<{ ok: boolean }> {
    const res = await api.post(`/qlib/train/${taskId}/revoke`)
    return res.data
  },

  async rerunTrainingTask(taskId: string): Promise<{ task_id: string }> {
    const res = await api.post(`/qlib/train/${taskId}/rerun`)
    return res.data
  }
}

export type { TrainingRequest, TrainingStatus, Model, SelectionRequest, SelectionResult, Instrument, Experiment, ExperimentListResult, BestModel, TopStockItem, TopStocksDay, TopStocksListResponse, TrainingTask, TrainingTasksResponse }
