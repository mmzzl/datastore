<template>
  <div class="page settings">
    <div class="page-header">
      <h1>系统设置</h1>
      <div class="user-info">
        <span>用户: {{ authService.getUser() }}</span>
      </div>
    </div>
    
    <div class="error-banner" v-if="error">{{ error }}</div>
    <div class="success-banner" v-if="successMessage">{{ successMessage }}</div>
    
    <div class="toast-overlay" v-if="showToast">
      <div :class="['toast', toastType]">
        {{ toastMessage }}
      </div>
    </div>
    
    <div class="config-grid">
      <div class="config-item">
        <label>Watchlist</label>
        <textarea 
          v-model="settings.watchlist" 
          rows="6" 
          placeholder="用逗号分隔的股票代码，例如 SH600000, SH600519"
        ></textarea>
      </div>
      <div class="config-item">
        <label>轮询间隔 (秒)</label>
        <input v-model.number="settings.interval_sec" type="number" min="1" />
      </div>
      <div class="config-item">
        <label>显示天数</label>
        <input v-model.number="settings.days" type="number" min="1" />
      </div>
      <div class="config-item">
        <label>缓存 TTL (秒)</label>
        <input v-model.number="settings.cache_ttl" type="number" min="1" />
      </div>
    </div>
    
    <div class="action-bar">
      <button @click="saveSettings" :disabled="loading" class="btn btn-primary">
        {{ loading ? '保存中...' : '保存设置' }}
      </button>
      <button @click="resetSettings" :disabled="loading" class="btn btn-secondary">
        重置
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiSettings, authService } from '../services/api'

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')

function displayToast(message: string, type: 'success' | 'error') {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}
const settings = ref({
  watchlist: '',
  interval_sec: 60,
  days: 5,
  cache_ttl: 60
})

async function loadSettings() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiSettings.getSettings(authService.getUser())
    settings.value = {
      watchlist: data.watchlist?.join(', ') || '',
      interval_sec: data.interval_sec || 60,
      days: data.days || 5,
      cache_ttl: data.cache_ttl || 60
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载设置失败'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const watchlistArray = settings.value.watchlist
      .split(',')
      .map(s => s.trim())
      .filter(s => s)
    
    await apiSettings.setSettings(authService.getUser(), {
      watchlist: watchlistArray,
      interval_sec: settings.value.interval_sec,
      days: settings.value.days,
      cache_ttl: settings.value.cache_ttl
    })
    successMessage.value = '设置保存成功！'
    displayToast('设置保存成功！', 'success')
  } catch (e: any) {
    const errorMsg = e.response?.data?.detail || e.message || '保存设置失败，请重试'
    error.value = errorMsg
    displayToast('保存设置失败：' + errorMsg, 'error')
  } finally {
    loading.value = false
  }
}

function resetSettings() {
  settings.value = {
    watchlist: '',
    interval_sec: 60,
    days: 5,
    cache_ttl: 60
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings { padding: 24px; max-width: 1200px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
}
.user-info {
  background: #f1f5f9;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  color: #64748b;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-weight: 500;
}
.config-grid { 
  display: grid; 
  grid-template-columns: repeat(2, 1fr); 
  gap: 16px; 
  margin-bottom: 24px;
}
.config-item { 
  background: #fff; 
  padding: 16px; 
  border-radius: 8px; 
  border: 1px solid #e2e8f0; 
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.config-item label { 
  display: block; 
  font-weight: 600; 
  margin-bottom: 8px; 
  color: #374151;
}
.config-item textarea { 
  width: 100%; 
  padding: 8px; 
  border: 1px solid #d1d5db;
  border-radius: 6px;
  resize: vertical;
  font-family: monospace;
}
.config-item input { 
  width: 100%; 
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}
.action-bar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-primary {
  background: #3b82f6;
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}
.btn-secondary {
  background: #64748b;
  color: white;
}
.btn-secondary:hover:not(:disabled) {
  background: #475569;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.toast-overlay {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 9999;
  animation: slideIn 0.3s ease-out;
}
.toast {
  padding: 16px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
}
.toast.success {
  background: #10b981;
  color: white;
}
.toast.error {
  background: #ef4444;
  color: white;
}
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
