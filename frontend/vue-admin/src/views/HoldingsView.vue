<template>
  <div class="page">
    <h1>Holdings</h1>
    <div class="toolbar">
      <button @click="refresh">刷新</button>
    </div>
    <table class="holdings-table" v-if="holdings.length">
      <thead>
        <tr>
          <th>代码</th>
          <th>名称</th>
          <th>数量</th>
          <th>成本价</th>
          <th>成本总额</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in holdings" :key="h.code">
          <td>{{ h.code }}</td>
          <td>{{ h.name || h.code }}</td>
          <td>{{ h.quantity }}</td>
          <td>{{ h.average_cost }}</td>
          <td>{{ (h.quantity * h.average_cost).toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>暂无持仓数据</p>
  </div>
  </template>

<script setup>
import { onMounted, reactive } from 'vue'

const userId = 'default'
const state = reactive({ holdings: [] as any[] })

async function fetchHoldings() {
  try {
    const res = await fetch(`/api/holdings/${userId}`)
    const json = await res.json()
    state.holdings = json || []
  } catch (e) {
    console.error('Failed to fetch holdings', e)
  }
}

function refresh() {
  fetchHoldings()
}

onMounted(() => {
  fetchHoldings()
})
</script>

<style scoped>
.page { padding: 16px; }
.holdings-table { width: 100%; border-collapse: collapse; }
.holdings-table th, .holdings-table td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
.toolbar { margin-bottom: 12px; }
</style>
