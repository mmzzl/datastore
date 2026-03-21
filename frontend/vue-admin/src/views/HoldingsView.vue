<template>
  <div class="page">
    <h1>持仓管理</h1>
    <div class="toolbar">
      <button @click="refresh">刷新</button>
      <button @click="fetchPortfolio">查看组合</button>
    </div>
    <div class="add-form">
      <h3>添加持仓</h3>
      <form @submit.prevent="onAddHolding">
        <input v-model="newHolding.code" placeholder="代码，如 SH600000" required />
        <input v-model.number="newHolding.quantity" type="number" placeholder="数量" step="0.01" required />
        <input v-model.number="newHolding.average_cost" type="number" placeholder="成本价" step="0.01" required />
        <button type="submit">添加</button>
      </form>
    </div>
    <div class="holdings-section" v-if="holdings.length">
      <h3>持仓列表</h3>
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
          <tr v-for="h in holdings" :key="h.code">
            <td>{{ h.code }}</td>
            <td>{{ h.name || h.code }}</td>
            <td>{{ h.quantity }}</td>
            <td>{{ h.average_cost?.toFixed(2) }}</td>
            <td>{{ (h.quantity * h.average_cost).toFixed(2) }}</td>
            <td><button @click="removeHolding(h.code)" class="btn-danger">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="empty-msg">暂无持仓数据</p>
    <div class="portfolio-section" v-if="portfolio">
      <h3>组合概览</h3>
      <div class="portfolio-stats">
        <div class="stat-item">
          <span class="label">总市值:</span>
          <span class="value">{{ portfolio.total_value?.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">总成本:</span>
          <span class="value">{{ portfolio.total_cost?.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">总盈亏:</span>
          <span class="value" :class="portfolio.profit >= 0 ? 'profit' : 'loss'">
            {{ portfolio.profit?.toFixed(2) }}
          </span>
        </div>
        <div class="stat-item">
          <span class="label">盈亏比例:</span>
          <span class="value" :class="portfolio.profit_rate >= 0 ? 'profit' : 'loss'">
            {{ (portfolio.profit_rate * 100)?.toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiHoldings, authService } from '../services/api'

const userId = ref('default')
const holdings = ref<any[]>([])
const portfolio = ref<any>(null)
const newHolding = ref({ code: '', quantity: 0, average_cost: 0 })

async function fetchHoldings() {
  if (!authService.isAuthenticated()) {
    console.warn('未登录')
    return
  }
  try {
    holdings.value = await apiHoldings.getHoldings(userId.value) || []
  } catch (e) {
    console.error('获取持仓失败', e)
  }
}

async function fetchPortfolio() {
  if (!authService.isAuthenticated()) {
    console.warn('未登录')
    return
  }
  try {
    portfolio.value = await apiHoldings.getPortfolio(userId.value)
  } catch (e) {
    console.error('获取组合失败', e)
  }
}

async function onAddHolding() {
  if (!newHolding.value.code || newHolding.value.quantity <= 0) {
    return
  }
  try {
    await apiHoldings.upsertHolding(
      userId.value,
      newHolding.value.code,
      newHolding.value.quantity,
      newHolding.value.average_cost
    )
    newHolding.value = { code: '', quantity: 0, average_cost: 0 }
    fetchHoldings()
  } catch (e) {
    console.error('添加持仓失败', e)
  }
}

async function removeHolding(code: string) {
  if (!confirm(`确定删除 ${code}?`)) return
  try {
    await apiHoldings.removeHolding(userId.value, code)
    fetchHoldings()
  } catch (e) {
    console.error('删除持仓失败', e)
  }
}

function refresh() {
  fetchHoldings()
  fetchPortfolio()
}

onMounted(() => {
  fetchHoldings()
})
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.add-form { margin-bottom: 20px; padding: 16px; background: #f9fafb; border-radius: 8px; }
.add-form h3 { margin: 0 0 12px 0; }
.add-form form { display: flex; gap: 8px; flex-wrap: wrap; }
.add-form input { padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; }
.add-form button { padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; }
.add-form button:hover { background: #2563eb; }
.holdings-section { margin-bottom: 20px; }
.holdings-table { width: 100%; border-collapse: collapse; background: white; }
.holdings-table th, .holdings-table td { border: 1px solid #e5e7eb; padding: 12px; text-align: left; }
.holdings-table th { background: #f3f4f6; }
.btn-danger { padding: 4px 12px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-danger:hover { background: #dc2626; }
.empty-msg { color: #6b7280; }
.portfolio-section { padding: 16px; background: #f0fdf4; border-radius: 8px; }
.portfolio-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat-item { display: flex; flex-direction: column; }
.stat-item .label { font-size: 12px; color: #6b7280; }
.stat-item .value { font-size: 18px; font-weight: 600; }
.profit { color: #059669; }
.loss { color: #dc2626; }
</style>