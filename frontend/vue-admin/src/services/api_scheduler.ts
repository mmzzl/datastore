import api from './api'

interface SchedulerJob {
  id: string
  name: string
  task_type: string
  schedule: string
  enabled: boolean
  last_run?: string
  next_run?: string
  config?: Record<string, any>
  created_at: string
  updated_at: string
}

interface CreateJobRequest {
  name: string
  task_type: string
  schedule: string
  enabled?: boolean
  config?: Record<string, any>
}

interface UpdateJobRequest {
  name?: string
  schedule?: string
  enabled?: boolean
  config?: Record<string, any>
}

interface JobExecution {
  id: string
  job_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  started_at: string
  completed_at?: string
  duration?: number
  result?: Record<string, any>
  error?: string
}

interface PaginatedExecutions {
  items: JobExecution[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const apiScheduler = {
  async getJobs(): Promise<{ items: SchedulerJob[]; total: number }> {
    const res = await api.get('/scheduler/jobs')
    return res.data
  },

  async createJob(request: CreateJobRequest): Promise<SchedulerJob> {
    const res = await api.post('/scheduler/jobs', {
      name: request.name,
      job_type: request.task_type,
      cron_expression: request.schedule,
      enabled: request.enabled,
      config: request.config
    })
    return res.data
  },

  async updateJob(id: string, request: UpdateJobRequest): Promise<SchedulerJob> {
    const res = await api.put(`/scheduler/jobs/${id}`, request)
    return res.data
  },

  async deleteJob(id: string): Promise<void> {
    await api.delete(`/scheduler/jobs/${id}`)
  },

  async triggerJob(id: string): Promise<{ execution_id: string }> {
    const res = await api.post(`/scheduler/jobs/${id}/trigger`)
    return res.data
  },

  async getExecutions(jobId: string, page: number = 1, pageSize: number = 10): Promise<PaginatedExecutions> {
    const res = await api.get(`/scheduler/jobs/${jobId}/executions`, {
      params: { page, page_size: pageSize }
    })
    const totalPages = Math.ceil(res.data.total / pageSize)
    return { ...res.data, total_pages: totalPages }
  }
}

export type { SchedulerJob, CreateJobRequest, UpdateJobRequest, JobExecution, PaginatedExecutions }
