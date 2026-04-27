<script setup lang="ts">
import { ref, onMounted, onActivated, onUnmounted, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NDivider, NProgress } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem, TrainingTask } from '../../services/api_qlib'

const store = useQlibStore()
const showHistory = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
  await store.fetchTrainingTasks()
  if (store.state.trainingTasks.some(t => t.status === 'running' || t.status === 'pending')) {
    showHistory.value = true
  }
  pollTimer = setInterval(() => store.fetchTrainingTasks(), 15000)
})

onActivated(async () => {
  await store.fetchTrainingTasks()
  if (!pollTimer) {
    pollTimer = setInterval(() => store.fetchTrainingTasks(), 15000)
  }
})

onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})

function formatDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0]
}

async function handleDateRangeChange(value: [number, number] | null) {
  if (value) {
    const start = formatDate(value[0])
    const end = formatDate(value[1])
    await store.fetchTopStocks(start, end)
  }
}

async function handleRefresh() {
  await store.refreshTopStocks()
}

async function handleTrainNow() {
  await apiQlib.startTraining({ model_type: 'lgbm' })
  showHistory.value = true
  await store.fetchTrainingTasks()
}

async function handleRevoke(taskId: string) {
  await store.revokeTask(taskId)
}

async function handleRerun(taskId: string) {
  await store.rerunTask(taskId)
}

const taskColumns: DataTableColumns<TrainingTask> = [
  { title: '时间', key: 'created_at', width: 150,
    render: (row) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-',
  },
  { title: '状态', key: 'status', width: 80,
    render: (row) => {
      const map: Record<string, [string, string]> = {
        pending: ['等待', 'default'],
        running: ['运行中', 'info'],
        success: ['完成', 'success'],
        failed: ['失败', 'error'],
        revoked: ['已取消', 'warning'],
      }
      const [label, type] = map[row.status] || [row.status, 'default']
      return h(NTag, { type, size: 'small' }, () => label)
    },
  },
  { title: '进度', key: 'progress', width: 150,
    render: (row) => {
      if (row.status === 'success') return h(NProgress, { type: 'success', percentage: 100, height: 16, indicatorPlacement: 'inside' })
      if (row.status === 'failed' || row.status === 'revoked') return '-'
      return h(NProgress, { percentage: row.progress || 0, height: 16, indicatorPlacement: 'inside' })
    },
  },
  { title: '消息', key: 'message', ellipsis: { tooltip: true },
    render: (row) => row.message || row.error_message || '-',
  },
  { title: '操作', key: 'actions', width: 120,
    render: (row) => {
      const btns = []
      if (row.status === 'running' || row.status === 'pending') {
        btns.push(h(NButton, { size: 'tiny', type: 'warning', onClick: () => handleRevoke(row.task_id) }, () => '取消'))
      }
      if (row.status === 'success' || row.status === 'failed' || row.status === 'revoked') {
        btns.push(h(NButton, { size: 'tiny', type: 'primary', onClick: () => handleRerun(row.task_id) }, () => '重跑'))
      }
      return h(NSpace, { size: 'small' }, () => btns)
    },
  },
  { title: '结果', key: 'result', ellipsis: { tooltip: true }, width: 150,
    render: (row) => {
      if (row.error_message) return row.error_message
      if (row.result) {
        const sr = (row.result as any)?.metrics?.sharpe_ratio
        return sr ? `Sharpe: ${sr.toFixed(3)}` : `模型: ${(row.result as any)?.model_id || ''}`
      }
      return '-'
    },
  },
]

const topColumns: DataTableColumns<TopStockItem> = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '代码', key: 'code', width: 120 },
  { title: '名称', key: 'name', render: (row) => row.name || row.code },
  { title: '评分', key: 'score', width: 100, render: (row) => row.score.toFixed(4) },
]
</script>

<template>
  <div class="top-stocks">
    <NSpace class="filter-bar" align="center">
      <NDatePicker type="daterange" clearable @update:value="handleDateRangeChange" style="width: 280px" />
      <NButton type="primary" :loading="store.state.refreshingTopStocks" @click="handleRefresh">刷新今日推荐</NButton>
      <NButton type="warning" @click="handleTrainNow">开始训练</NButton>
      <NButton size="small" quaternary @click="showHistory = !showHistory">
        {{ showHistory ? '隐藏训练记录' : '训练记录' }}
      </NButton>
    </NSpace>

    <div v-if="showHistory" style="margin-bottom: 16px">
      <NDivider>训练任务</NDivider>
      <NDataTable
        v-if="store.state.trainingTasks.length > 0"
        :columns="taskColumns"
        :data="store.state.trainingTasks"
        :bordered="false"
        size="small"
        :max-height="300"
        :scroll-x="800"
      />
      <NEmpty v-else description="暂无训练任务" />
    </div>

    <NAlert v-if="store.state.error" type="error" style="margin-bottom: 12px" closable>{{ store.state.error }}</NAlert>
    <NSpin :show="store.state.loading">
      <div v-if="store.state.topStocks.length > 0">
        <div v-for="day in store.state.topStocks" :key="day.date" style="margin-bottom: 20px">
          <NTag type="info" style="margin-bottom: 8px">{{ day.date }} | 模型: {{ day.model_id }} | {{ day.model_type }} | {{ day.factor }}</NTag>
          <NDataTable :columns="topColumns" :data="day.stocks" :bordered="false" size="small" striped :row-key="(row: TopStockItem) => row.code" />
        </div>
      </div>
      <NEmpty v-else-if="!store.state.loading" description="暂无推荐数据，点击刷新按钮生成" />
    </NSpin>
  </div>
</template>

<style scoped>
.top-stocks { padding: 0; }
.filter-bar { margin-bottom: 16px; }
</style>
