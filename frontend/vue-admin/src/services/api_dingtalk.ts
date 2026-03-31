import api from './api'

interface DingtalkConfig {
  id?: string
  user_id?: string
  webhook_url: string
  secret: string
  enabled: boolean
  keywords?: string
  at_mobiles?: string
  created_at?: string
  updated_at?: string
}

interface CreateConfigRequest {
  webhook_url: string
  secret: string
  enabled?: boolean
  keywords?: string
  at_mobiles?: string
}

interface UpdateConfigRequest {
  webhook_url?: string
  secret?: string
  enabled?: boolean
  keywords?: string
  at_mobiles?: string
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
    const res = await api.post('/dingtalk/configs', data)
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
    const res = await api.post(`/dingtalk/configs/${configId}/test`)
    return res.data
  }
}

export type { DingtalkConfig, CreateConfigRequest, UpdateConfigRequest, TestNotificationResponse }
