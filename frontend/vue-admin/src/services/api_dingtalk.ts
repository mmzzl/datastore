import api from './api'

interface DingtalkConfig {
  id?: string
  user_id?: string
  name?: string
  webhook: string
  secret: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

interface CreateConfigRequest {
  user_id: string
  name: string
  webhook: string
  secret: string
}

interface UpdateConfigRequest {
  name?: string
  webhook?: string
  secret?: string
}

interface TestNotificationResponse {
  success: boolean
  message: string
}

export const apiDingtalk = {
  async getConfigs(userId: string): Promise<{ items: DingtalkConfig[]; total: number }> {
    const res = await api.get(`/dingtalk/configs/${userId}`)
    return res.data
  },

  async createConfig(data: CreateConfigRequest): Promise<DingtalkConfig> {
    const res = await api.post('/dingtalk/configs/on_save', data)
    return res.data
  },

  async updateConfig(configId: string, data: UpdateConfigRequest): Promise<DingtalkConfig> {
    const res = await api.put(`/dingtalk/configs/${configId}`, data)
    return res.data
  },

  async deleteConfig(configId: string): Promise<void> {
    await api.delete(`/dingtalk/configs/${configId}`)
  },

  async testNotification(configId: string): Promise<TestNotificationResponse> {
    const res = await api.post(`/dingtalk/configs/test/${configId}`, {
      message: 'Test notification from trading system'
    })
    return res.data
  }
}

export type { DingtalkConfig, CreateConfigRequest, UpdateConfigRequest, TestNotificationResponse }
