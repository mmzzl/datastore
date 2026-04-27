<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, h } from 'vue'
import {
  NCard, NDataTable, NSpin, NTag, NSelect, NInput, NButton, NSpace, NEmpty, NIcon
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import api from '../services/api'

interface SignalItem {
  _id: string
  code: string
  symbol: string
  name: string
  signal: string
  confidence: number
  priority: string
  reasons: string[]
  message: string
  price: number
  alert_type: string
  timestamp: string
}

const items = ref<SignalItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const signalTypeFilter = ref<string | null>(null)
const codeFilter = ref('')
const daysFilter = ref(7)
let refreshTimer: ReturnType<typeof setInterval> | null = null

const signalTypeOptions = [
  { label: '全部', value: null },
  { label: '买入', value: 'buy' },
  { label: '卖出', value: 'sell' },
  { label: '观望', value: 'hold' },
]

const columns: DataTableColumns<SignalItem> = [
  { title: '时间', key: 'timestamp', width: 160,
    render: (row) => row.timestamp ? new Date(row.timestamp).toLocaleString('zh-CN') : '-',
    sorter: (a, b) => new Date(a.timestamp || 0).getTime() - new Date(b.timestamp || 0).getTime(),
  },
  { title: '代码', key: 'code', width: 100 },
  { title: '名称', key: 'name', width: 100 },
  { title: '信号', key: 'signal', width: 80,
    render: (row) => {
      const map: Record<string, [string, 'success' | 'warning' | 'error']> = {
        buy: ['买入', 'success'],
        sell: ['卖出', 'error'],
        hold: ['观望', 'warning'],
      }
      const [label, type] = map[row.signal] || [row.signal, 'warning']
      return h(NTag, { type, size: 'small' }, () => label)
    },
  },
  { title: '置信度', key: 'confidence', width: 80,
    render: (row) => row.confidence ? `${(row.confidence * 100).toFixed(0)}%` : '-',
  },
  { title: '价格', key: 'price', width: 80,
    render: (row) => row.price && row.price > 0 ? `¥${row.price.toFixed(2)}` : '-',
  },
  { title: '类型', key: 'alert_type', width: 80,
    render: (row) => {
      const map: Record<string, string> = { news: '新闻', technical: '技术', event: '事件' }
      return map[row.alert_type] || row.alert_type || '-'
    },
  },
  { title: '消息', key: 'message', ellipsis: { tooltip: true },
    render: (row) => row.reasons?.[0] || row.message || '-',
  },
]

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value, days: daysFilter.value }
    if (signalTypeFilter.value) params.signal_type = signalTypeFilter.value
    if (codeFilter.value.trim()) params.code = codeFilter.value.trim()
    const res = await api.get('/signals/latest', { params })
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  fetchData()
}

function onPageSizeChange(ps: number) {
  pageSize.value = ps
  page.value = 1
  fetchData()
}

function refresh() {
  page.value = 1
  fetchData()
}

onMounted(() => {
  fetchData()
  refreshTimer = setInterval(fetchData, 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="market-watch-view">
    <NCard title="市场信号">
      <template #header-extra>
        <NButton size="small" @click="refresh" :loading="loading">
          <template #icon><NIcon><RefreshOutline /></NIcon></template>
          刷新
        </NButton>
      </template>

      <NSpace vertical :size="12">
        <NSpace align="center" wrap>
          <NSelect
            v-model:value="signalTypeFilter"
            :options="signalTypeOptions"
            placeholder="信号类型"
            style="width: 120px"
            @update:value="refresh"
          />
          <NInput
            v-model:value="codeFilter"
            placeholder="股票代码"
            style="width: 140px"
            clearable
            @keyup.enter="refresh"
          />
          <NButton size="small" @click="refresh" :loading="loading">查询</NButton>
          <span style="font-size: 12px; color: #888;">每15秒自动刷新</span>
        </NSpace>

        <NSpin :show="loading">
          <NDataTable
            :columns="columns"
            :data="items"
            :bordered="false"
            :max-height="500"
            :scroll-x="900"
            :pagination="{
              page: page,
              pageSize: pageSize,
              itemCount: total,
              pageSizes: [10, 20, 50, 100],
              showSizePicker: true,
              onUpdatePage: onPageChange,
              onUpdatePageSize: onPageSizeChange,
            }"
          />
          <NEmpty v-if="!loading && items.length === 0" description="暂无信号数据" style="padding: 40px 0" />
        </NSpin>
      </NSpace>
    </NCard>
  </div>
</template>

<style scoped>
.market-watch-view {
  padding: 20px;
}
</style>
