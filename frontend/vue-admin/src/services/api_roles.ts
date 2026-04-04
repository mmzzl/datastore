import api from './api'
import type { Role } from './api_auth'

export interface CreateRoleRequest {
  role_id: string
  name: string
  description: string
  permissions: string[]
}

export interface UpdateRoleRequest {
  name?: string
  description?: string
  permissions?: string[]
}

export interface Permission {
  code: string
  name: string
  category: string
}

export const apiRoles = {
  async getRoles(): Promise<{ items: Role[] }> {
    const res = await api.get('/roles')
    return res.data
  },

  async getRole(roleId: string): Promise<Role> {
    const res = await api.get(`/roles/${roleId}`)
    return res.data
  },

  async createRole(data: CreateRoleRequest): Promise<Role> {
    const res = await api.post('/roles', data)
    return res.data
  },

  async updateRole(roleId: string, data: UpdateRoleRequest): Promise<Role> {
    const res = await api.put(`/roles/${roleId}`, data)
    return res.data
  },

  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/roles/${roleId}`)
  },

  async getPermissions(): Promise<{ items: Permission[] }> {
    const res = await api.get('/roles/permissions')
    return res.data
  }
}
