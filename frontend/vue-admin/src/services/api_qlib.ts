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
  id: string
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

export const apiQlib = {
  async startTraining(request: TrainingRequest): Promise<{ id: string }> {
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
  }
}

export type { TrainingRequest, TrainingStatus, Model, SelectionRequest, SelectionResult, Instrument }
