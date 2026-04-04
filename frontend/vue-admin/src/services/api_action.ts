import api from './api'

export interface ActionLog {
  id: string
  user_id: string
  username: string
  action: string
  resource_type: string
  resource_id?: string
  details?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface PaginatedActionLogs {
  items: ActionLog[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ActionLogFilter {
  user_id?: string
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export const apiAction = {
  async getActionLogs(filter: ActionLogFilter = {}): Promise<PaginatedActionLogs> {
    const res = await api.get('/action-logs', {
      params: {
        page: filter.page || 1,
        page_size: filter.page_size || 20,
        ...filter
      }
    })
    return res.data
  },

  async getActionTypes(): Promise<{ items: string[] }> {
    const res = await api.get('/action-logs/actions')
    return res.data
  },

  async getResourceTypes(): Promise<{ items: string[] }> {
    const res = await api.get('/action-logs/resource-types')
    return res.data
  }
}
