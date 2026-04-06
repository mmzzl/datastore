<template>
  <n-message-provider>
    <div class="app-layout" v-if="isAuthenticated">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <h2 class="logo" v-if="!sidebarCollapsed">Market Admin</h2>
          <h2 class="logo-mini" v-else>MA</h2>
          <button class="toggle-btn" @click="toggleSidebar">
            <svg
              :class="{ rotated: sidebarCollapsed }"
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
        </div>
        <nav>
          <router-link to="/dashboard">
            <span class="nav-icon">📊</span>
            <span class="nav-text" v-if="!sidebarCollapsed">Dashboard</span>
          </router-link>
          <router-link to="/holdings">
            <span class="nav-icon">📈</span>
            <span class="nav-text" v-if="!sidebarCollapsed">持仓管理</span>
          </router-link>
          <router-link to="/market-watch">
            <span class="nav-icon">👀</span>
            <span class="nav-text" v-if="!sidebarCollapsed">市场监控</span>
          </router-link>
          <router-link to="/qlib/select">
            <span class="nav-icon">🤖</span>
            <span class="nav-text" v-if="!sidebarCollapsed">Qlib模型</span>
          </router-link>
          <router-link to="/backtest">
            <span class="nav-icon">🔄</span>
            <span class="nav-text" v-if="!sidebarCollapsed">回测</span>
          </router-link>
    <router-link to="/stock-selection">
      <span class="nav-icon">🎯</span>
      <span class="nav-text" v-if="!sidebarCollapsed">策略选股</span>
    </router-link>
          <router-link to="/risk-report">
            <span class="nav-icon">⚠️</span>
            <span class="nav-text" v-if="!sidebarCollapsed">风险报告</span>
          </router-link>
          <router-link to="/scheduler">
            <span class="nav-icon">⏰</span>
            <span class="nav-text" v-if="!sidebarCollapsed">定时任务</span>
          </router-link>
          <router-link to="/dingtalk-config">
            <span class="nav-icon">📱</span>
            <span class="nav-text" v-if="!sidebarCollapsed">钉钉配置</span>
          </router-link>

          <div v-if="canManagePlugins" class="menu-divider">
            <span class="divider-text" v-if="!sidebarCollapsed">插件</span>
          </div>
          <router-link v-if="canManagePlugins" to="/plugins">
            <span class="nav-icon">🧩</span>
            <span class="nav-text" v-if="!sidebarCollapsed">插件管理</span>
          </router-link>

          <div v-if="canManageUsers" class="menu-divider">
            <span class="divider-text" v-if="!sidebarCollapsed">系统管理</span>
          </div>
          <router-link v-if="canManageUsers" to="/admin/users">
            <span class="nav-icon">👥</span>
            <span class="nav-text" v-if="!sidebarCollapsed">用户管理</span>
          </router-link>
          <router-link v-if="canManageRoles" to="/admin/roles">
            <span class="nav-icon">🔑</span>
            <span class="nav-text" v-if="!sidebarCollapsed">角色管理</span>
          </router-link>

          <router-link to="/settings">
            <span class="nav-icon">⚙️</span>
            <span class="nav-text" v-if="!sidebarCollapsed">设置</span>
          </router-link>
        </nav>
        <div class="user-section">
          <span class="user-info" v-if="!sidebarCollapsed">用户: {{ currentUser }}</span>
          <button @click="logout" class="logout-btn">
            <span v-if="!sidebarCollapsed">退出登录</span>
            <span v-else>🚪</span>
          </button>
        </div>
      </aside>
      <main class="content">
        <router-view />
      </main>
    </div>
    <router-view v-else />
  </n-message-provider>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMessageProvider } from 'naive-ui'
import { authService, apiAuth } from './services/api'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)

const isAuthenticated = computed(() => authService.isAuthenticated())
const currentUser = computed(() => authService.getUser())

const canManageUsers = computed(() => {
  return authStore.hasAnyPermission(['user:read', 'user:manage']) || authStore.state.is_superuser
})

const canManageRoles = computed(() => {
  return authStore.hasAnyPermission(['role:read', 'role:manage']) || authStore.state.is_superuser
})

const canManagePlugins = computed(() => {
  return authStore.hasAnyPermission(['plugin:read', 'plugin:manage']) || authStore.state.is_superuser
})

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function logout() {
  apiAuth.logout()
  router.push('/login')
}

onMounted(async () => {
  if (isAuthenticated.value) {
    try {
      authStore.setAuthFromStorage()
      // 获取用户信息和权限
      await authStore.fetchCurrentUser()
    } catch (e) {
      console.error('Failed to get user info', e)
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: Inter, system-ui, Arial, sans-serif;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #fff;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: relative;
  min-height: 100vh;
  height: 100vh;
}

.sidebar.collapsed {
  width: 64px;
  padding: 12px 8px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #334155;
}

.sidebar.collapsed .sidebar-header {
  flex-direction: column;
  gap: 8px;
}

.sidebar .logo {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
  white-space: nowrap;
}

.sidebar .logo-mini {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #334155;
  color: #f1f5f9;
}

.toggle-btn svg {
  transition: transform 0.3s ease;
}

.toggle-btn svg.rotated {
  transform: rotate(180deg);
}

.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar a {
  color: #94a3b8;
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar.collapsed a {
  padding: 12px 8px;
  justify-content: center;
}

.sidebar a:hover {
  background: #1e293b;
  color: #f1f5f9;
}

.sidebar a.router-link-active {
  background: #3b82f6;
  color: #fff;
}

.nav-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.nav-text {
  white-space: nowrap;
}

.menu-divider {
  margin: 12px 0;
  padding: 8px 16px;
  background: transparent;
}

.sidebar.collapsed .menu-divider {
  padding: 8px 0;
  margin: 8px 0;
}

.menu-divider .divider-text {
  font-size: 11px;
  color: #64748b !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
  padding-top: 8px;
  border-top: 1px solid #334155;
}

.user-section {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #334155;
}

.sidebar.collapsed .user-section {
  padding-top: 8px;
}

.user-info {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  width: 100%;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #475569;
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.sidebar.collapsed .logout-btn {
  padding: 8px;
  font-size: 16px;
}

.logout-btn:hover {
  background: #475569;
  color: #fff;
}

.content {
  flex: 1;
  background: #f1f5f9;
  overflow-y: auto;
}
</style>
