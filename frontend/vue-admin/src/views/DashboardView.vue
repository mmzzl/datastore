<template>
  <div class="page dashboard">
    <h1>Dashboard</h1>
    <div class="grid">
      <div class="card">
        <div class="card-title">持仓概览</div>
        <div class="card-content">
          <div>持仓笔数：{{ dashboard.holdingsCount }}</div>
          <div>总成本：{{ dashboard.totalCost.toFixed(2) }}</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">市值与未实现盈亏</div>
        <div class="card-content">
          <div>市值：{{ dashboard.marketValue?.toFixed ? dashboard.marketValue.toFixed(2) : dashboard.marketValue }}</div>
          <div>未实现盈亏：{{ dashboard.unrealizedPnL?.toFixed ? dashboard.unrealizedPnL.toFixed(2) : dashboard.unrealizedPnL }}</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">信号状态</div>
        <div class="card-content">最近信号总数：{{ dashboard.signalCount }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()

onMounted(() => {
  dashboard.fetchSummary()
})
</script>

<style scoped>
.dashboard { padding: 16px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.card-title { font-weight: 600; margin-bottom: 8px; }
.card-content { font-size: 14px; color: #333; }
</style>
