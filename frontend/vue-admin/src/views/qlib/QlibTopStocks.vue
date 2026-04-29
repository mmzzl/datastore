<script setup lang="ts">
import { ref, onMounted, onActivated, onUnmounted, nextTick, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NDivider, NProgress, NPagination } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem, TrainingTask } from '../../services/api_qlib'
import * as echarts from 'echarts'

const store = useQlibStore()
const showHistory = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

// date range
const dateRange = ref<[number, number] | null>(null)

// pagination
const currentPage = ref(1)
const pageSize = ref(20)

// K-line
const showKlineModal = ref(false)
const klineCode = ref('')
const klineName = ref('')
const klineData = ref<any[]>([])
const loadingKline = ref(false)
const klineChartRef = ref<HTMLElement | null>(null)
let klineChart: echarts.ECharts | null = null

onMounted(async () => {
  await loadTopStocks()
  await store.fetchTrainingTasks()
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
  if (klineChart) { klineChart.dispose(); klineChart = null }
})

function formatDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0]
}

async function loadTopStocks() {
  let start: string | undefined
  let end: string | undefined
  if (dateRange.value) {
    start = formatDate(dateRange.value[0])
    end = formatDate(dateRange.value[1])
  }
  await store.fetchTopStocks(start, end, undefined, currentPage.value, pageSize.value)
}

async function handleDateRangeChange(value: [number, number] | null) {
  dateRange.value = value
  currentPage.value = 1
  await loadTopStocks()
}

async function handlePageChange(page: number) {
  currentPage.value = page
  await loadTopStocks()
}

async function handleRefresh() {
  await store.refreshTopStocks()
  currentPage.value = 1
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

// K-line
async function showKline(code: string, name: string) {
  klineCode.value = code
  klineName.value = name || code
  showKlineModal.value = true
  loadingKline.value = true
  klineData.value = []

  try {
    const pureCode = code.replace(/^(SH|SZ|sh|sz)/, '')
    const res = await fetch(`/api/stock/kline/${pureCode}?limit=120`)
    const data = await res.json()
    if (data.success && data.data) {
      klineData.value = data.data.reverse()
      loadingKline.value = false
      await nextTick()
      setTimeout(() => renderKlineChart(), 100)
    } else {
      loadingKline.value = false
    }
  } catch {
    loadingKline.value = false
  }
}

function renderKlineChart() {
  if (!klineChartRef.value || klineData.value.length === 0) return

  if (klineChart) klineChart.dispose()
  klineChart = echarts.init(klineChartRef.value)

  const dates = klineData.value.map(d => d.date)
  const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = klineData.value.map(d => d.volume)
  const closes = klineData.value.map(d => d.close)

  const ma5 = calculateMA(5, closes)
  const ma10 = calculateMA(10, closes)
  const ma20 = calculateMA(20, closes)

  const option = {
    title: {
      text: `${klineName.value} (${klineCode.value})`,
      left: 'center', top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      borderWidth: 1, textStyle: { color: '#333' },
      formatter(params: any) {
        const data = klineData.value[params[0].dataIndex]
        const vol = params.find((p: any) => p.seriesType === 'bar')
        let result = `日期: ${data.date}<br/>`
        result += `开盘: ${data.open?.toFixed(2)}<br/>`
        result += `收盘: ${data.close?.toFixed(2)}<br/>`
        result += `最高: ${data.high?.toFixed(2)}<br/>`
        result += `最低: ${data.low?.toFixed(2)}<br/>`
        if (vol) result += `成交量: ${(vol.data / 10000).toFixed(2)}万手<br/>`
        return result
      }
    },
    legend: { data: ['K线', 'MA5', 'MA10', 'MA20'], top: 40 },
    grid: [{ left: '10%', right: '10%', top: '20%', height: '50%' }, { left: '10%', right: '10%', top: '75%', height: '15%' }],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { onZero: false }, splitLine: { show: false } },
      { type: 'category', data: dates, gridIndex: 1, axisLine: { onZero: false }, splitLine: { show: false } }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true }, gridIndex: 0 },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { show: false } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
      { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '2%', start: 70, end: 100 }
    ],
    series: [
      { name: 'K线', type: 'candlestick', data: ohlc, itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' }, xAxisIndex: 0, yAxisIndex: 0 },
      { name: 'MA5', type: 'line', data: ma5, smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
      { name: 'MA10', type: 'line', data: ma10, smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
      { name: 'MA20', type: 'line', data: ma20, smooth: true, lineStyle: { width: 1, color: '#8b5cf6' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
      {
        name: '成交量', type: 'bar', data: volumes.map((v: number, idx: number) => ({
          value: v,
          itemStyle: { color: idx > 0 && klineData.value[idx].close >= klineData.value[idx - 1].close ? '#ef5350' : '#26a69a' }
        })), xAxisIndex: 1, yAxisIndex: 1
      }
    ]
  }

  klineChart.setOption(option)
}

function calculateMA(dayCount: number, data: number[]) {
  return data.map((_: number, i: number) => {
    if (i < dayCount - 1) return '-'
    let sum = 0
    for (let j = 0; j < dayCount; j++) sum += data[i - j]
    return +(sum / dayCount).toFixed(2)
  })
}

function closeKlineModal() {
  showKlineModal.value = false
  klineData.value = []
  if (klineChart) { klineChart.dispose(); klineChart = null }
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
          <NDataTable
            :columns="[
              { title: '排名', key: 'rank', width: 60 },
              { title: '代码', key: 'code', width: 120 },
              { title: '名称', key: 'name', render: (row) => row.name || row.code },
              { title: '评分', key: 'score', width: 100, render: (row) => row.score.toFixed(4) },
              { title: '操作', key: 'actions', width: 80,
                render: (row) => h(NButton, { size: 'tiny', type: 'primary', onClick: () => showKline(row.code, row.name || row.code) }, () => 'K线')
              },
            ]"
            :data="day.stocks"
            :bordered="false"
            size="small"
            striped
            :row-key="(row: TopStockItem) => row.code"
          />
        </div>

        <div style="display: flex; justify-content: flex-end; margin-top: 12px">
          <NPagination
            :page="currentPage"
            :page-size="pageSize"
            :item-count="store.state.topStocksTotal"
            :page-slot="7"
            show-quick-jumper
            @update:page="handlePageChange"
          />
        </div>
      </div>
      <NEmpty v-else-if="!store.state.loading" description="暂无推荐数据，点击刷新按钮生成" />
    </NSpin>

    <!-- K-line Modal -->
    <div class="kline-modal" v-if="showKlineModal" @click.self="closeKlineModal">
      <div class="kline-modal-content">
        <div class="kline-modal-header">
          <h3>{{ klineName }} ({{ klineCode }})</h3>
          <NButton size="small" @click="closeKlineModal">关闭</NButton>
        </div>
        <div class="kline-modal-body">
          <div v-if="loadingKline" class="loading-state">加载中...</div>
          <div v-else-if="klineData.length === 0" class="empty-state">暂无K线数据</div>
          <div v-else class="kline-chart-container">
            <div ref="klineChartRef" class="kline-chart" style="width: 100%; height: 450px;"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-stocks { padding: 0; }
.filter-bar { margin-bottom: 16px; }
.kline-modal {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5); display: flex;
  align-items: center; justify-content: center; z-index: 1000;
}
.kline-modal-content {
  background: white; border-radius: 12px; width: 90%;
  max-width: 1000px; max-height: 90vh; display: flex; flex-direction: column;
}
.kline-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #e5e7eb;
}
.kline-modal-header h3 { margin: 0; font-size: 18px; color: #1e293b; }
.kline-modal-body { padding: 20px; overflow-y: auto; }
.loading-state, .empty-state { text-align: center; padding: 40px; color: #64748b; }
.kline-chart-container { width: 100%; height: 450px; }
.kline-chart { width: 100%; height: 100%; }
</style>
