<template>
  <div class="page">
    <div class="page-header">
      <h1>持仓管理</h1>
      <div class="header-actions">
        <button @click="refresh" :disabled="store.state.loading" class="btn btn-primary">
          {{ store.state.loading ? '刷新中...' : '刷新' }}
        </button>
        <button @click="fetchPortfolio" :disabled="store.state.loading" class="btn btn-secondary">
          查看组合
        </button>
      </div>
    </div>
    
    <div class="error-banner" v-if="store.state.error">
      {{ store.state.error }}
    </div>
    
    <div class="add-form-card">
      <h3>添加/更新持仓</h3>
      <form @submit.prevent="onAddHolding">
        <div class="form-row">
          <input 
            v-model="newHolding.code" 
            placeholder="代码，如 SH600000" 
            required 
            class="input-code"
          />
          <input 
            v-model.number="newHolding.quantity" 
            type="number" 
            placeholder="数量" 
            step="0.01" 
            required 
            class="input-quantity"
          />
          <input 
            v-model.number="newHolding.average_cost" 
            type="number" 
            placeholder="成本价" 
            step="0.01" 
            required 
            class="input-cost"
          />
          <button type="submit" :disabled="store.state.loading" class="btn btn-success">
            添加
          </button>
        </div>
      </form>
    </div>
    
    <div class="holdings-section" v-if="store.state.holdings.length">
      <h3>持仓列表 ({{ store.state.holdings.length }}条)</h3>
      <table class="holdings-table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th>数量</th>
            <th>成本价</th>
            <th>成本总额</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in store.state.holdings" :key="h.code">
            <td class="code-cell">{{ h.code }}</td>
            <td>{{ h.name || h.code }}</td>
            <td class="number-cell">{{ h.quantity }}</td>
            <td class="number-cell">¥{{ h.average_cost?.toFixed(2) }}</td>
            <td class="number-cell">¥{{ (h.quantity * h.average_cost).toFixed(2) }}</td>
            <td>
              <button @click="removeHolding(h.code)" class="btn btn-danger btn-sm">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="empty-state" v-else-if="!store.state.loading">
      <p>暂无持仓数据</p>
      <p class="hint">请添加持仓开始管理</p>
    </div>
    
    <div class="portfolio-section" v-if="portfolio">
      <h3>组合概览</h3>
      <div class="portfolio-stats">
        <div class="stat-item">
          <span class="label">总市值</span>
          <span class="value">¥{{ store.state.marketValue.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">总成本</span>
          <span class="value">¥{{ store.state.totalCost.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">总盈亏</span>
          <span class="value" :class="store.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
            {{ store.state.unrealizedPnL >= 0 ? '+' : '' }}¥{{ store.state.unrealizedPnL.toFixed(2) }}
          </span>
        </div>
        <div class="stat-item">
          <span class="label">盈亏比例</span>
          <span class="value" :class="store.state.profitRate >= 0 ? 'profit' : 'loss'">
            {{ (store.state.profitRate * 100).toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useHoldingsStore } from '../stores/holdings'

const store = useHoldingsStore()
const userId = ref('default')
const portfolio = ref(false)
const newHolding = ref({ code: '', quantity: 0, average_cost: 0 })

async function fetchHoldings() {
  await store.fetchHoldings(userId.value)
}

async function fetchPortfolio() {
  portfolio.value = true
  await store.refreshPortfolio(userId.value)
}

async function onAddHolding() {
  if (!newHolding.value.code || newHolding.value.quantity <= 0) {
    return
  }
  try {
    await store.saveHolding(
      userId.value,
      newHolding.value.code,
      newHolding.value.quantity,
      newHolding.value.average_cost
    )
    newHolding.value = { code: '', quantity: 0, average_cost: 0 }
  } catch (e: any) {
    alert(e.message || '添加失败')
  }
}

async function removeHolding(code: string) {
  if (!confirm(`确定删除 ${code}?`)) return
  try {
    await store.removeHolding(userId.value, code)
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

function refresh() {
  fetchHoldings()
  if (portfolio.value) {
    fetchPortfolio()
  }
}

onMounted(() => {
  fetchHoldings()
})
</script>

<style scoped>
.page { padding: 24px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-primary { background: #3b82f6; color: white; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-secondary:hover:not(:disabled) { background: #cbd5e1; }
.btn-success { background: #10b981; color: white; }
.btn-success:hover:not(:disabled) { background: #059669; }
.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.add-form-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.add-form-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1e293b;
}
.form-row {
  display: flex;
  gap: 12px;
  align-items: center;
}
.form-row input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.form-row input:focus {
  outline: none;
  border-color: #3b82f6;
}
.input-code { width: 160px; }
.input-quantity { width: 120px; }
.input-cost { width: 120px; }
.holdings-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.holdings-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1e293b;
}
.holdings-table {
  width: 100%;
  border-collapse: collapse;
}
.holdings-table th,
.holdings-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}
.holdings-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.holdings-table td {
  color: #1e293b;
}
.code-cell {
  font-family: monospace;
  font-weight: 600;
}
.number-cell {
  text-align: right;
  font-family: monospace;
}
.empty-state {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}
.empty-state p { margin: 0; }
.empty-state .hint {
  font-size: 14px;
  margin-top: 8px;
}
.portfolio-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.portfolio-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1e293b;
}
.portfolio-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-item .label {
  font-size: 13px;
  color: #64748b;
}
.stat-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}
.stat-item .value.profit { color: #059669; }
.stat-item .value.loss { color: #dc2626; }
</style>