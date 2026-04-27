<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { apiScheduler, type JobExecution } from '../../services/api_scheduler'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NModal, NDivider } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem } from '../../services/api_qlib'

const store = useQlibStore()

const trainJobId = ref<string | null>(null)
const executions = ref<JobExecution[]>([])
const loadingExecutions = ref(false)
const showHistory = ref(false)

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
  await findTrainJob()
})

async function findTrainJob() {
  try {
    const res = await apiScheduler.getJobs()
    const job = res.items.find((j: any) => j.task_type === 'qlib_train' || j.job_type === 'qlib_train')
    if (job) {
      trainJobId.value = job.id
      await fetchExecutions()
    }
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

async function handleTrainNow() {
  if (!trainJobId.value) return
  try {
    await apiScheduler.triggerJob(trainJobId.value)
    showHistory.value = true
    setTimeout(fetchExecutions, 2000)
  } catch (e: any) {
    store.state.error = e.response?.data?.detail || '启动训练失败'
  }
}

const execColumns: DataTableColumns<JobExecution> = [
  { title: '开始时间', key: 'started_at', width: 160,
    render: (row) => row.started_at ? new Date(row.started_at).toLocaleString('zh-CN') : '-' },
  { title: '状态', key: 'status', width: 80,
    render: (row) => {
      const map: Record<string, [string, string]> = {
        pending: ['等待中', 'default'],
        running: ['运行中', 'info'],
        success: ['成功', 'success'],
        failed: ['失败', 'error'],
      }
      const [label, type] = map[row.status] || [row.status, 'default']
      return h(NTag, { type, size: 'small' }, () => label)
    },
  },
  { title: '耗时', key: 'duration', width: 80,
    render: (row) => row.duration ? `${row.duration.toFixed(1)}s` : '-' },
  { title: '结果', key: 'result', ellipsis: { tooltip: true },
    render: (row) => row.error || (row.result ? JSON.stringify(row.result).slice(0, 80) : '-') },
]

const columns: DataTableColumns<TopStockItem> = [
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
      <NButton v-if="trainJobId" type="warning" @click="handleTrainNow">开始训练</NButton>
      <NButton v-if="trainJobId" size="small" quaternary @click="showHistory = !showHistory">
        {{ showHistory ? '隐藏训练记录' : '训练记录' }}
      </NButton>
    </NSpace>

    <NAlert v-if="!trainJobId && !store.state.loading" type="warning" style="margin-bottom: 12px">
      未找到 Qlib 模型训练任务，请先在调度页面创建 job_type 为 qlib_train 的任务
    </NAlert>

    <div v-if="showHistory && trainJobId" style="margin-bottom: 16px">
      <NDivider>训练任务执行记录</NDivider>
      <NSpin :show="loadingExecutions">
        <NDataTable
          v-if="executions.length > 0"
          :columns="execColumns"
          :data="executions"
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
          <NDataTable :columns="columns" :data="day.stocks" :bordered="false" size="small" striped :row-key="(row: TopStockItem) => row.code" />
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