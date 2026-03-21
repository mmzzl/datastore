<template>
  <div class="page dashboard">
    <div class="page-header">
      <h1>仪表盘</h1>
      <button @click="refresh" :disabled="dashboard.state.loading" class="refresh-btn">
        {{ dashboard.state.loading ? '刷新中...' : '刷新数据' }}
      </button>
    </div>
    
    <div class="error-banner" v-if="dashboard.state.error">
      {{ dashboard.state.error }}
    </div>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon holdings">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">持仓数量</div>
          <div class="stat-value">{{ dashboard.state.holdingsCount }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon cost">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">总成本</div>
          <div class="stat-value">¥{{ dashboard.state.totalCost.toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon value">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">市值</div>
          <div class="stat-value">¥{{ dashboard.state.marketValue.toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" :class="dashboard.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">未实现盈亏</div>
          <div class="stat-value" :class="dashboard.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
            {{ dashboard.state.unrealizedPnL >= 0 ? '+' : '' }}¥{{ dashboard.state.unrealizedPnL.toFixed(2) }}
            <span class="stat-rate">({{ (dashboard.state.profitRate * 100).toFixed(2) }}%)</span>
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" :class="dashboard.state.realizedPnL >= 0 ? 'profit' : 'loss'">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">已实现盈亏</div>
          <div class="stat-value" :class="dashboard.state.realizedPnL >= 0 ? 'profit' : 'loss'">
            {{ dashboard.state.realizedPnL >= 0 ? '+' : '' }}¥{{ dashboard.state.realizedPnL.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
    
    <div class="section">
      <div class="section-header">
        <h2>最近信号</h2>
        <router-link to="/market-watch" class="link">查看全部</router-link>
      </div>
      <div class="signal-count">
        <span class="count">{{ dashboard.state.signalCount }}</span>
        <span class="label">条信号</span>
      </div>
    </div>
    
    <div class="section">
      <div class="section-header">
        <h2>快速操作</h2>
      </div>
      <div class="quick-actions">
        <router-link to="/holdings" class="action-btn">
          <span class="icon">📝</span>
          <span>管理持仓</span>
        </router-link>
        <router-link to="/settings" class="action-btn">
          <span class="icon">⚙️</span>
          <span>系统设置</span>
        </router-link>
      </div>
    </div>
    
    <div class="last-update" v-if="dashboard.state.lastUpdated">
      最后更新: {{ dashboard.state.lastUpdated.toLocaleString() }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onActivated, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()
const route = useRoute()

function refresh() {
  dashboard.fetchSummary()
}

// 组件挂载时获取数据
onMounted(() => {
  dashboard.fetchSummary()
  
  // 监听全局刷新事件
  window.addEventListener('dashboard-refresh', handleRefresh)
})

// 组件激活时（从其他页面返回时）刷新数据
onActivated(() => {
  dashboard.fetchSummary()
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('dashboard-refresh', handleRefresh)
})

// 处理刷新事件
function handleRefresh() {
  dashboard.fetchSummary()
}
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1200px;
}
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
.refresh-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.refresh-btn:hover:not(:disabled) {
  background: #2563eb;
}
.refresh-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.stat-icon.holdings { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.stat-icon.cost { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
.stat-icon.value { background: linear-gradient(135deg, #06b6d4, #0891b2); }
.stat-icon.profit { background: linear-gradient(135deg, #10b981, #059669); }
.stat-icon.loss { background: linear-gradient(135deg, #ef4444, #dc2626); }
.stat-content {
  flex: 1;
}
.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}
.stat-value.profit { color: #059669; }
.stat-value.loss { color: #dc2626; }
.stat-rate {
  font-size: 14px;
  font-weight: 400;
}
.section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 14px;
}
.link:hover {
  text-decoration: underline;
}
.signal-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.signal-count .count {
  font-size: 36px;
  font-weight: 700;
  color: #1e293b;
}
.signal-count .label {
  font-size: 16px;
  color: #64748b;
}
.quick-actions {
  display: flex;
  gap: 12px;
}
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f1f5f9;
  border-radius: 8px;
  text-decoration: none;
  color: #1e293b;
  font-weight: 500;
  transition: all 0.2s;
}
.action-btn:hover {
  background: #e2e8f0;
}
.action-btn .icon {
  font-size: 20px;
}
.last-update {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 16px;
}
</style>