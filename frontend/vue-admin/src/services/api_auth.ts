import api from './api'

export interface User {
  id: string
  username: string
  display_name: string
  email?: string
  role_id: string
  role_name?: string
  status: 'active' | 'disabled' | 'locked'
  is_superuser: boolean
  last_login?: string
  created_at: string
}

export interface Role {
  id: string
  role_id: string
  name: string
  description: string
  permissions: string[]
  is_system: boolean
  user_count?: number
}

export interface LoginResponse {
  token: string
  user: User
  permissions: string[]
  is_superuser: boolean
}

export interface AuthState {
  user: User | null
  token: string | null
  permissions: string[]
  is_superuser: boolean
}

export const apiAuthNew = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const res = await api.post('/auth/token', { username, password })
    const data = res.data
    return {
      token: data.access_token,
      user: {
        id: data.user_id,
        username: data.username,
        display_name: data.display_name,
        role_id: data.role_id,
        role_name: data.role_name,
        is_superuser: data.is_superuser,
        status: 'active',
        created_at: new Date().toISOString()
      },
      permissions: data.permissions || [],
      is_superuser: data.is_superuser || false
    }
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async getCurrentUser(): Promise<User> {
    const res = await api.get('/auth/me')
    return res.data
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
  }
}
