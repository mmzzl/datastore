<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useBacktestStore } from '../stores/backtest'
import { NCard, NButton, NDataTable, NSpin, NAlert, NTag, NDatePicker, NInputNumber, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'

const store = useBacktestStore()

onMounted(async () => {
  await store.fetchResults()
})

onUnmounted(() => {
  store.disconnectWebSocket()
})

const columns: DataTableColumns = [
  { title: '策略', key: 'strategy' },
  { title: '开始日期', key: 'start_date' },
  { title: '结束日期', key: 'end_date' },
  { title: '初始资金', key: 'initial_capital' },
  { title: '最终资金', key: 'final_capital' },
  { title: '总收益', key: 'total_return' },
  { title: '夏普比率', key: 'sharpe_ratio' },
  { title: '最大回撤', key: 'max_drawdown' },
  { title: '状态', key: 'status' },
]

const dateRange = ref<[number, number] | null>(null)
const initialCapital = ref(1000000)
</script>

<template>
  <div class="backtest-view">
    <NCard title="回测管理">
      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <div class="backtest-form mb-4">
        <NDatePicker
          v-model:value="dateRange"
          type="daterange"
          placeholder="选择日期范围"
        />
        <NInputNumber
          v-model:value="initialCapital"
          :min="10000"
          placeholder="初始资金"
        />
        <NButton type="primary" :loading="store.state.status === 'running'">
          开始回测
        </NButton>
      </div>

      <div v-if="store.state.status === 'running'" class="progress-section mb-4">
        <NTag type="info">回测进度: {{ store.state.progress }}%</NTag>
      </div>

      <NSpin :show="store.state.loading">
        <NDataTable
          :columns="columns"
          :data="store.state.results"
          :bordered="false"
        />
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.backtest-view {
  padding: 20px;
}
.backtest-form {
  display: flex;
  gap: 16px;
  align-items: center;
}
.mb-4 {
  margin-bottom: 16px;
}
</style>
