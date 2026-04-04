<template>
  <n-message-provider>
    <div class="app-layout" v-if="isAuthenticated">
      <aside class="sidebar">
        <h2 class="logo">Market Admin</h2>
        <nav>
          <router-link to="/dashboard">Dashboard</router-link>
          <router-link to="/holdings">持仓管理</router-link>
          <router-link to="/market-watch">市场监控</router-link>
          <router-link to="/qlib/select">Qlib模型</router-link>
          <router-link to="/backtest">回测</router-link>
          <router-link to="/risk-report">风险报告</router-link>
          <router-link to="/scheduler">定时任务</router-link>
          <router-link to="/dingtalk-config">钉钉配置</router-link>
          
          <div v-if="canManagePlugins" class="menu-divider">
            <span class="divider-text">插件</span>
          </div>
          <router-link v-if="canManagePlugins" to="/plugins">插件管理</router-link>
          
          <div v-if="canManageUsers" class="menu-divider">
            <span class="divider-text">系统管理</span>
          </div>
          <router-link v-if="canManageUsers" to="/admin/users">用户管理</router-link>
          <router-link v-if="canManageRoles" to="/admin/roles">角色管理</router-link>
          
          <router-link to="/settings">设置</router-link>
        </nav>
        <div class="user-section">
          <span class="user-info">用户: {{ currentUser }}</span>
          <button @click="logout" class="logout-btn">退出登录</button>
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

function logout() {
  apiAuth.logout()
  router.push('/login')
}

onMounted(async () => {
  if (isAuthenticated.value) {
    try {
      const token = authService.getToken()
      if (token) {
        authStore.setAuthFromStorage()
      }
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
}
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #fff;
  padding: 20px;
  display: flex;
  flex-direction: column;
}
.sidebar .logo {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 600;
  color: #f1f5f9;
  padding-bottom: 16px;
  border-bottom: 1px solid #334155;
}
.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.sidebar a {
  color: #94a3b8;
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.sidebar a:hover {
  background: #1e293b;
  color: #f1f5f9;
}
.sidebar a.router-link-active {
  background: #3b82f6;
  color: #fff;
}
.menu-divider {
  margin: 12px 0;
  padding: 0 16px;
  border-top: 1px solid #334155;
  padding-top: 12px;
}
.menu-divider .divider-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.user-section {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #334155;
}
.user-info {
  display: block;
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 8px;
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
