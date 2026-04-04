import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import { apiAuthNew, type User, type LoginResponse } from '../services/api_auth'
import { authService } from '../services/api'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const state = reactive({
    user: null as User | null,
    token: authService.getToken(),
    permissions: [] as string[],
    is_superuser: false,
    loading: false,
    error: null as string | null,
  })

  const isLoggedIn = computed(() => !!state.token && !!state.user)
  const username = computed(() => state.user?.username || authService.getUser() || '')

  function hasPermission(permission: string): boolean {
    if (state.is_superuser) return true
    return state.permissions.includes(permission)
  }

  function hasAnyPermission(permissions: string[]): boolean {
    if (state.is_superuser) return true
    return permissions.some(p => state.permissions.includes(p))
  }

  function hasAllPermissions(permissions: string[]): boolean {
    if (state.is_superuser) return true
    return permissions.every(p => state.permissions.includes(p))
  }

  async function login(username: string, password: string): Promise<boolean> {
    state.loading = true
    state.error = null
    try {
      const response: LoginResponse = await apiAuthNew.login(username, password)
      state.token = response.token
      state.user = response.user
      state.permissions = response.permissions || []
      state.is_superuser = response.is_superuser || false
      
      authService.setToken(response.token)
      if (state.user) {
        authService.setUser(state.user.username)
      }
      
      return true
    } catch (e: any) {
      state.error = e.response?.data?.detail || '登录失败'
      return false
    } finally {
      state.loading = false
    }
  }

  async function logout() {
    try {
      await apiAuthNew.logout()
    } catch (e) {
      console.warn('Logout API call failed:', e)
    }
    state.user = null
    state.token = null
    state.permissions = []
    state.is_superuser = false
    authService.clearToken()
    router.push('/login')
  }

  async function fetchCurrentUser() {
    if (!state.token) return null
    state.loading = true
    try {
      const user = await apiAuthNew.getCurrentUser()
      state.user = user
      return user
    } catch (e) {
      console.error('Failed to fetch current user:', e)
      return null
    } finally {
      state.loading = false
    }
  }

  function setAuthFromStorage() {
    const token = authService.getToken()
    if (token) {
      state.token = token
    }
  }

  return {
    state,
    isLoggedIn,
    username,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    login,
    logout,
    fetchCurrentUser,
    setAuthFromStorage,
  }
})
