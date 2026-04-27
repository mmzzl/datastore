<script setup lang="ts">
import { ref, onMounted, onActivated, onUnmounted, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NDivider, NProgress } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem, TrainingStatus, Experiment } from '../../services/api_qlib'

const store = useQlibStore()

const showHistory = ref(false)
const historyItems = ref<Experiment[]>([])
const loadingHistory = ref(false)
let activePollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
  await fetchHistory()
})

onActivated(async () => {
  await fetchHistory()
  if (store.state.activeTaskId) {
    activePollTimer = setInterval(() => pollProgress(store.state.activeTaskId), 3000)
  }
})

onUnmounted(() => {
  stopPolling()
})

async function fetchHistory() {
  loadingHistory.value = true
  try {
    await store.fetchExperiments(1, 20, undefined, undefined)
    historyItems.value = store.state.experiments
  } catch {
    // ignore
  } finally {
    loadingHistory.value = false
  }
}

async function findTrainJob() {
  try {
    const res = await apiScheduler.getJobs()
    const job = res.items.find((j: any) => j.job_type === 'qlib_train')
    if (job) {
      trainJobId.value = job.job_id
      await fetchExecutions()
      return
    }
  } catch {
    // ignore
  }
  try {
    const created = await apiScheduler.createJob({
      name: 'Qlib模型训练',
      task_type: 'qlib_train',
      schedule: '0 2 * * 0',
      enabled: true,
      config: { model_type: 'lgbm', instruments: 'csi300', factor_type: 'alpha158' },
    })
    trainJobId.value = (created as any).id || (created as any).job_id
  } catch {
    // ignore
  }
}

async function fetchExecutions() {
  if (!trainJobId.value) return
  loadingExecutions.value = true
  try {
    const res = await apiScheduler.getExecutions(trainJobId.value, 1, 20)
    executions.value = res.items || []
  } catch {
    // ignore
  } finally {
    loadingExecutions.value = false
  }
}

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

function stopPolling() {
  if (activePollTimer) {
    clearInterval(activePollTimer)
    activePollTimer = null
  }
}

async function pollProgress(taskId: string) {
  try {
    const status: TrainingStatus = await apiQlib.getTrainingStatus(taskId)
    store.state.activeProgress = status.progress || 0
    store.state.activeStatus = status.message || status.status
    if (status.status === 'completed') {
      stopPolling()
      store.state.activeTaskId = null
      await store.refreshTopStocks()
      await fetchHistory()
    } else if (status.status === 'failed') {
      stopPolling()
      store.state.activeTaskId = null
      store.state.activeStatus = `失败: ${status.error || '未知错误'}`
      await fetchHistory()
    }
  } catch {
    stopPolling()
    store.state.activeTaskId = null
  }
}

async function handleTrainNow() {
  try {
    const res = await apiQlib.startTraining({ model_type: 'lgbm' })
    store.state.activeTaskId = res.task_id
    store.state.activeProgress = 0
    store.state.activeStatus = '提交成功'
    showHistory.value = true
    activePollTimer = setInterval(() => pollProgress(res.task_id), 3000)
    setTimeout(() => pollProgress(res.task_id), 1000)
  } catch (e: any) {
    store.state.error = e.response?.data?.detail || '启动训练失败'
  }
}

const execColumns: DataTableColumns<Experiment> = [
  { title: '开始时间', key: 'created_at', width: 160,
    render: (row) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' },
  { title: '模型', key: 'model_type', width: 80 },
  { title: '因子', key: 'factor_type', width: 80 },
  { title: '状态', key: 'status', width: 70,
    render: (row) => {
      const map: Record<string, [string, string]> = {
        completed: ['成功', 'success'],
        running: ['运行中', 'info'],
        failed: ['失败', 'error'],
        skipped_low_ic: ['IC过低', 'warning'],
      }
      const [label, type] = map[row.status] || [row.status, 'default']
      return h(NTag, { type, size: 'small' }, () => label)
    },
  },
  { title: 'Sharpe', key: 'sharpe_ratio', width: 80,
    render: (row) => {
      const sr = (row as any).backtest_result?.sharpe_ratio || (row as any).training_metrics?.sharpe_ratio
      return sr ? sr.toFixed(3) : '-'
    },
  },
  { title: 'IC', key: 'rank_ic', width: 80,
    render: (row) => {
      const ic = (row as any).training_metrics?.rank_ic
      return ic ? ic.toFixed(4) : '-'
    },
  },
  { title: '结果', key: 'error_message', ellipsis: { tooltip: true },
    render: (row) => row.error_message || (row.model_id ? row.model_id : '-') },
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
      <NButton type="warning" :disabled="!!store.state.activeTaskId" @click="handleTrainNow">开始训练</NButton>
      <NButton v-if="historyItems.length > 0 || store.state.activeTaskId" size="small" quaternary @click="showHistory = !showHistory">
        {{ showHistory ? '隐藏训练记录' : '训练记录' }}
      </NButton>
    </NSpace>

    <NAlert v-if="!store.state.loading && !store.state.activeTaskId" type="info" style="margin-bottom: 12px" closable>
      点击"开始训练"使用 lgbm/alpha158/CSI300 训练新模型
    </NAlert>

    <div v-if="store.state.activeTaskId" style="margin-bottom: 16px; padding: 12px; background: #f5f7fa; border-radius: 6px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span style="font-weight: 500;">训练进度</span>
        <span style="color: #888; font-size: 13px;">{{ store.state.activeProgress }}%</span>
      </div>
      <NProgress :percentage="store.state.activeProgress" :height="10" :indicator-placement="'inside'" />
      <div style="margin-top: 4px; color: #666; font-size: 13px;">{{ store.state.activeStatus }}</div>
    </div>

    <div v-if="showHistory" style="margin-bottom: 16px">
      <NDivider>训练历史</NDivider>
      <NSpin :show="loadingHistory">
        <NDataTable
          v-if="historyItems.length > 0"
          :columns="execColumns"
          :data="historyItems"
          :bordered="false"
          size="small"
          :max-height="200"
        />
        <NEmpty v-else description="暂无训练记录" />
      </NSpin>
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