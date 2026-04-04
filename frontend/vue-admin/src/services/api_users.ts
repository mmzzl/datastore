import api from './api'
import type { User } from './api_auth'

export interface CreateUserRequest {
  username: string
  password: string
  display_name: string
  email?: string
  role_id: string
  is_superuser?: boolean
}

export interface UpdateUserRequest {
  display_name?: string
  email?: string
  role_id?: string
  status?: 'active' | 'disabled' | 'locked'
  is_superuser?: boolean
}

export interface ResetPasswordRequest {
  new_password: string
}

export interface PaginatedUsers {
  items: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const apiUsers = {
  async getUsers(page: number = 1, pageSize: number = 10): Promise<PaginatedUsers> {
    const res = await api.get('/users', {
      params: { page, page_size: pageSize }
    })
    return res.data
  },

  async getUser(userId: string): Promise<User> {
    const res = await api.get(`/users/${userId}`)
    return res.data
  },

  async createUser(data: CreateUserRequest): Promise<User> {
    const res = await api.post('/users', data)
    return res.data
  },

  async updateUser(userId: string, data: UpdateUserRequest): Promise<User> {
    const res = await api.put(`/users/${userId}`, data)
    return res.data
  },

  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/users/${userId}`)
  },

  async resetPassword(userId: string, data: ResetPasswordRequest): Promise<void> {
    await api.post(`/users/${userId}/reset-password`, data)
  },

  async unlockUser(userId: string): Promise<void> {
    await api.post(`/users/${userId}/unlock`)
  }
}
