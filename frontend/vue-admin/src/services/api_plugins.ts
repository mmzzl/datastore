import api from './api'

export interface Plugin {
  id: string
  name: string
  version: string
  display_name: string
  description: string
  author: string
  status: 'active' | 'inactive'
  created_at: string
}

export interface PluginDetail extends Plugin {
  config: Record<string, any>
  readme?: string
}

export interface PaginatedPlugins {
  items: Plugin[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const apiPlugins = {
  async getPlugins(page: number = 1, pageSize: number = 20): Promise<PaginatedPlugins> {
    const res = await api.get('/plugins', {
      params: { page, page_size: pageSize }
    })
    return res.data
  },

  async getPlugin(pluginId: string): Promise<PluginDetail> {
    const res = await api.get(`/plugins/${pluginId}`)
    return res.data
  },

  async uploadPlugin(file: File, onProgress?: (percent: number) => void): Promise<Plugin> {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await api.post('/plugins/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
    return res.data
  },

  async deletePlugin(pluginId: string): Promise<void> {
    await api.delete(`/plugins/${pluginId}`)
  },

  async activatePlugin(pluginId: string): Promise<void> {
    await api.post(`/plugins/${pluginId}/activate`)
  },

  async deactivatePlugin(pluginId: string): Promise<void> {
    await api.post(`/plugins/${pluginId}/deactivate`)
  },

  async switchVersion(pluginId: string, version: string): Promise<void> {
    await api.post(`/plugins/${pluginId}/switch-version`, { version })
  },

  async getPluginVersions(pluginId: string): Promise<{ versions: string[] }> {
    const res = await api.get(`/plugins/${pluginId}/versions`)
    return res.data
  }
}
