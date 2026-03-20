<template>
  <div class="page">
    <h1>Holdings</h1>
    <div class="toolbar" style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:12px;">
      <button @click="refresh">刷新</button>
      <form @submit.prevent="onAddHolding" class="add-form" style="display:flex;gap:8px;align-items:center;">
        <input v-model="newHolding.code" placeholder="代码，如 SH600000" />
        <input v-model.number="newHolding.quantity" type="number" placeholder="数量" step="0.01" />
        <input v-model.number="newHolding.average_cost" type="number" placeholder="成本价" step="0.01" />
        <button type="submit">添加持仓</button>
      </form>
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
  const newHolding = reactive({ code: '', quantity: 0, average_cost: 0 })
  async function onAddHolding() {
    if (!newHolding.code || newHolding.quantity <= 0) return
    try {
      await fetch(`/api/holdings/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: newHolding.code, quantity: newHolding.quantity, average_cost: newHolding.average_cost })
      })
      newHolding.code = ''
      newHolding.quantity = 0
      newHolding.average_cost = 0
      fetchHoldings()
    } catch (e) {
      console.error('添加持仓失败', e)
    }
  }
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
