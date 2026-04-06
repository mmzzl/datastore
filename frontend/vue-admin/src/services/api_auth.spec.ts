import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiAuthNew, type LoginResponse, type User } from '@/services/api_auth'

vi.mock('./api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import api from './api'

const mockedApi = vi.mocked(api)

describe('apiAuthNew', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should call POST /auth/token with credentials', async () => {
      mockedApi.post.mockResolvedValue({
        data: {
          access_token: 'test-token-123',
          user_id: '1',
          username: 'admin',
          display_name: 'Admin',
          role_id: 'admin',
          role_name: 'Administrator',
          is_superuser: true,
          permissions: ['holdings:view', 'users:edit']
        }
      })

      await apiAuthNew.login('admin', 'password123')

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/token', {
        username: 'admin',
        password: 'password123'
      })
    })

    it('should return LoginResponse with mapped fields', async () => {
      mockedApi.post.mockResolvedValue({
        data: {
          access_token: 'token-abc',
          user_id: '5',
          username: 'testuser',
          display_name: 'Test User',
          role_id: 'user',
          role_name: 'User',
          is_superuser: false,
          permissions: ['holdings:view']
        }
      })

      const result = await apiAuthNew.login('testuser', 'pass')

      expect(result).toEqual({
        token: 'token-abc',
        user: {
          id: '5',
          username: 'testuser',
          display_name: 'Test User',
          role_id: 'user',
          role_name: 'User',
          is_superuser: false,
          status: 'active',
          created_at: expect.any(String)
        },
        permissions: ['holdings:view'],
        is_superuser: false
      })
    })

    it('should handle missing optional fields gracefully', async () => {
      mockedApi.post.mockResolvedValue({
        data: {
          access_token: 'token',
          user_id: '1',
          username: 'admin',
          display_name: 'Admin'
        }
      })

      const result = await apiAuthNew.login('admin', 'pass')

      expect(result.user.role_id).toBeUndefined()
      expect(result.user.is_superuser).toBeFalsy()
      expect(result.permissions).toEqual([])
    })
  })

  describe('logout', () => {
    it('should call POST /auth/logout', async () => {
      mockedApi.post.mockResolvedValue({ data: null })

      await apiAuthNew.logout()

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/logout')
    })
  })

  describe('getCurrentUser', () => {
    it('should call GET /auth/me', async () => {
      const mockUser = { id: '1', username: 'admin' }
      mockedApi.get.mockResolvedValue({ data: mockUser })

      const result = await apiAuthNew.getCurrentUser()

      expect(mockedApi.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual(mockUser)
    })
  })

  describe('changePassword', () => {
    it('should call POST /auth/change-password with old and new password', async () => {
      mockedApi.post.mockResolvedValue({ data: { success: true } })

      await apiAuthNew.changePassword('oldpass', 'newpass')

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/change-password', {
        old_password: 'oldpass',
        new_password: 'newpass'
      })
    })
  })
})
