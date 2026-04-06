import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/services/api_auth', () => ({
  apiAuthNew: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}))

vi.mock('@/services/api', () => ({
  authService: {
    getToken: vi.fn(() => null),
    getUser: vi.fn(() => null),
    setToken: vi.fn(),
    setUser: vi.fn(),
    clearToken: vi.fn(),
  },
}))

vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
  },
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have initial state with null user and empty permissions', () => {
      const store = useAuthStore()
      expect(store.state.user).toBeNull()
      expect(store.state.token).toBeNull()
      expect(store.state.permissions).toEqual([])
      expect(store.state.is_superuser).toBe(false)
      expect(store.state.loading).toBe(false)
      expect(store.state.error).toBeNull()
    })

    it('should compute isLoggedIn correctly when no token', () => {
      const store = useAuthStore()
      expect(store.isLoggedIn).toBe(false)
    })

    it('should compute isLoggedIn correctly when has token but no user', () => {
      const store = useAuthStore()
      store.state.token = 'some-token'
      expect(store.isLoggedIn).toBe(false)
    })

    it('should compute isLoggedIn correctly when has both token and user', () => {
      const store = useAuthStore()
      store.state.token = 'some-token'
      store.state.user = { id: 1, username: 'admin' }
      expect(store.isLoggedIn).toBe(true)
    })
  })

  describe('hasPermission', () => {
    it('should return true for superuser', () => {
      const store = useAuthStore()
      store.state.is_superuser = true
      expect(store.hasPermission('any_permission')).toBe(true)
    })

    it('should return true when user has the permission', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view', 'users:edit']
      expect(store.hasPermission('holdings:view')).toBe(true)
    })

    it('should return false when user lacks the permission', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view']
      expect(store.hasPermission('users:edit')).toBe(false)
    })
  })

  describe('hasAnyPermission', () => {
    it('should return true for superuser', () => {
      const store = useAuthStore()
      store.state.is_superuser = true
      expect(store.hasAnyPermission(['a', 'b'])).toBe(true)
    })

    it('should return true when user has any of the permissions', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view']
      expect(store.hasAnyPermission(['holdings:view', 'users:edit'])).toBe(true)
    })

    it('should return false when user has none of the permissions', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view']
      expect(store.hasAnyPermission(['users:edit', 'roles:delete'])).toBe(false)
    })
  })

  describe('hasAllPermissions', () => {
    it('should return true for superuser', () => {
      const store = useAuthStore()
      store.state.is_superuser = true
      expect(store.hasAllPermissions(['a', 'b'])).toBe(true)
    })

    it('should return true when user has all permissions', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view', 'users:edit']
      expect(store.hasAllPermissions(['holdings:view', 'users:edit'])).toBe(true)
    })

    it('should return false when user lacks some permissions', () => {
      const store = useAuthStore()
      store.state.permissions = ['holdings:view']
      expect(store.hasAllPermissions(['holdings:view', 'users:edit'])).toBe(false)
    })
  })

  describe('login', () => {
    it('should set loading state during login', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.login).mockResolvedValue({
        token: 'test-token',
        user: { id: 1, username: 'admin' },
        permissions: [],
        is_superuser: false,
      } as any)

      const store = useAuthStore()
      const loginPromise = store.login('admin', 'password')

      expect(store.state.loading).toBe(true)

      await loginPromise
      expect(store.state.loading).toBe(false)
    })

    it('should set error on login failure', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.login).mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } },
      })

      const store = useAuthStore()
      const result = await store.login('admin', 'wrong-password')

      expect(result).toBe(false)
      expect(store.state.error).toBe('Invalid credentials')
    })
  })

  describe('logout', () => {
    it('should clear all state on logout', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.logout).mockResolvedValue(undefined)

      const store = useAuthStore()
      store.state.user = { id: 1, username: 'admin' }
      store.state.token = 'test-token'
      store.state.permissions = ['holdings:view']
      store.state.is_superuser = true

      await store.logout()

      expect(store.state.user).toBeNull()
      expect(store.state.token).toBeNull()
      expect(store.state.permissions).toEqual([])
      expect(store.state.is_superuser).toBe(false)
    })

    it('should handle logout API error gracefully', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.logout).mockRejectedValue(new Error('Network error'))

      const store = useAuthStore()
      store.state.user = { id: 1, username: 'admin' }
      store.state.token = 'test-token'

      await store.logout()

      expect(store.state.user).toBeNull()
      expect(store.state.token).toBeNull()
    })
  })

  describe('fetchCurrentUser', () => {
    it('should return null when no token', async () => {
      const store = useAuthStore()
      store.state.token = null

      const result = await store.fetchCurrentUser()

      expect(result).toBeNull()
    })

    it('should fetch and set current user', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.getCurrentUser).mockResolvedValue({
        id: '1',
        username: 'admin',
        display_name: 'Admin',
        role_id: 'admin',
        is_superuser: true,
        status: 'active',
        created_at: '2024-01-01',
      })

      const store = useAuthStore()
      store.state.token = 'test-token'

      const result = await store.fetchCurrentUser()

      expect(result).not.toBeNull()
      expect(store.state.user).not.toBeNull()
    })

    it('should handle fetchCurrentUser error gracefully', async () => {
      const { apiAuthNew } = await import('@/services/api_auth')
      vi.mocked(apiAuthNew.getCurrentUser).mockRejectedValue(new Error('API error'))

      const store = useAuthStore()
      store.state.token = 'test-token'

      const result = await store.fetchCurrentUser()

      expect(result).toBeNull()
    })
  })

  describe('setAuthFromStorage', () => {
    it('should load auth when token exists', async () => {
      const { authService } = await import('@/services/api')
      vi.mocked(authService.getToken).mockReturnValue('stored-token')

      const store = useAuthStore()
      store.setAuthFromStorage()

      expect(store.state.token).toBe('stored-token')
    })

    it('should not load auth when token does not exist', async () => {
      const { authService } = await import('@/services/api')
      vi.mocked(authService.getToken).mockReturnValue(null)

      const store = useAuthStore()
      store.setAuthFromStorage()

      expect(store.state.token).toBeNull()
    })
  })
})