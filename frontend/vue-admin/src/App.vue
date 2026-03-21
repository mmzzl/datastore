<template>
  <div class="app-layout" v-if="isAuthenticated">
    <aside class="sidebar">
      <h2 class="logo">Market Admin</h2>
      <nav>
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/holdings">持仓管理</router-link>
        <router-link to="/market-watch">市场监控</router-link>
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
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService, apiAuth } from './services/api'

const router = useRouter()
const route = useRoute()

const isAuthenticated = computed(() => authService.isAuthenticated())
const currentUser = computed(() => authService.getUser())

function logout() {
  apiAuth.logout()
  router.push('/login')
}

onMounted(async () => {
  if (isAuthenticated.value) {
    try {
      const token = authService.getToken()
      if (token) {
        currentUser.value = authService.getUser()
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