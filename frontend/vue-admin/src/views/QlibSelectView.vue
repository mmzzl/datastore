<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useQlibStore } from '../stores/qlib'
import { NCard, NButton, NDataTable, NSelect, NDatePicker, NSpin, NAlert, NTag, NProgress, NEmpty } from 'naive-ui'
import type { DataTableColumns, DataTableProps } from 'naive-ui'
import type { Model } from '../services/api_qlib'

interface SelectionStock {
  rank: number
  code: string
  name: string
  score: number
}

const store = useQlibStore()

onMounted(async () => {
  await store.fetchModels()
})

const selectedModelId = ref<string | null>(null)
const selectedDate = ref(Date.now())
const tableLoading = ref(false)
const currentPage = ref(1)
const pageSize = 50

type SortOrder = 'ascend' | 'descend' | false
const sortKey = ref<keyof SelectionStock>('score')
const sortOrder = ref<SortOrder>('descend')

const modelOptions = computed(() => {
  const approvedModels = store.state.models.filter(m => m.status === 'active')
  return approvedModels.map((m: Model) => ({
    label: `${m.name} (${formatDate(m.created_at)}) - Sharpe: ${m.metrics?.sharpe_ratio?.toFixed(2) ?? 'N/A'})`,
    value: m.id
  }))
})

const defaultModelId = computed(() => {
  const approvedModels = store.state.models
    .filter(m => m.status === 'active')
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  return approvedModels.length > 0 ? approvedModels[0].id : null
})

const sortedAndPaginatedStocks = computed(() => {
  const stocks = store.state.selectionResults?.stocks || []
  if (!sortOrder.value || !sortKey.value) {
    return stocks
  }
  const sorted = [...stocks].sort((a, b) => {
    const aVal = a[sortKey.value as keyof SelectionStock]
    const bVal = b[sortKey.value as keyof SelectionStock]
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder.value === 'ascend' ? aVal - bVal : bVal - aVal
    }
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortOrder.value === 'ascend' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    }
    return 0
  })
  return sorted
})

const paginatedStocks = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return sortedAndPaginatedStocks.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(sortedAndPaginatedStocks.value.length / pageSize)
})

const totalCount = computed(() => {
  return sortedAndPaginatedStocks.value.length
})

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN')
}

function formatScore(score: number): string {
  return score.toFixed(4)
}

function handleSorterChange(sorter: { columnKey: string; order: 'ascend' | 'descend' | false }) {
  if (sorter.order) {
    sortKey.value = sorter.columnKey as keyof SelectionStock
    sortOrder.value = sorter.order
  } else {
    sortKey.value = 'score'
    sortOrder.value = 'descend'
  }
  currentPage.value = 1
}

const columns: DataTableColumns<SelectionStock> = [
  {
    title: '排名',
    key: 'rank',
    width: 80,
    sorter: (row1, row2) => row1.rank - row2.rank,
    defaultSortOrder: false
  },
  {
    title: '代码',
    key: 'code',
    width: 120,
    sorter: (row1, row2) => row1.code.localeCompare(row2.code),
    render: (row: SelectionStock) => row.code
  },
  {
    title: '名称',
    key: 'name',
    sorter: (row1, row2) => (row1.name || '').localeCompare(row2.name || ''),
    render: (row: SelectionStock) => row.name || row.code
  },
  {
    title: '得分',
    key: 'score',
    width: 120,
    defaultSortOrder: 'descend',
    sorter: (row1, row2) => row1.score - row2.score,
    render: (row: SelectionStock) => formatScore(row.score)
  }
]

const pagination = computed<DataTableProps['pagination']>(() => ({
  page: currentPage.value,
  pageSize: pageSize,
  itemCount: totalCount.value,
  showSizePicker: false,
  pageSlot: 5,
  onChange: (page: number) => {
    currentPage.value = page
  }
}))

function handlePageChange(page: number) {
  currentPage.value = page
}

async function runSelection() {
  if (!selectedModelId.value) {
    selectedModelId.value = defaultModelId.value
  }
  if (!selectedModelId.value) return
  
  const dateStr = new Date(selectedDate.value).toISOString().split('T')[0]
  
  tableLoading.value = true
  try {
    await store.runSelection({
      model_id: selectedModelId.value,
      date: dateStr,
      top_k: 100
    })
    currentPage.value = 1
    sortKey.value = 'score'
    sortOrder.value = 'descend'
  } finally {
    tableLoading.value = false
  }
}

function handleRowClick(row: SelectionStock) {
  console.log('Selected stock:', row)
}

function handleDateChange(value: number | null) {
  if (value !== null) {
    selectedDate.value = value
  }
}

const datePickerDisabledDate = (ts: number): boolean => {
  return ts > Date.now()
}
</script>

<template>
  <div class="qlib-select-view">
    <NCard title="Qlib 股票筛选">
      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <div class="selection-form mb-4">
        <NSelect
          v-model:value="selectedModelId"
          :options="modelOptions"
          :placeholder="defaultModelId ? '请选择模型' : '暂无可用模型'"
          :disabled="store.state.models.length === 0"
          style="width: 400px"
          clearable
        />
        <NDatePicker
          v-model:value="selectedDate"
          type="date"
          :is-date-disabled="datePickerDisabledDate"
          placeholder="选择预测日期"
          style="width: 200px"
        />
        <NButton
          type="primary"
          :loading="store.state.selecting || tableLoading"
          :disabled="!selectedModelId && !defaultModelId"
          @click="runSelection"
        >
          {{ store.state.selecting ? '筛选中...' : '运行筛选' }}
        </NButton>
      </div>

      <div v-if="store.state.selecting || tableLoading" class="progress-section mb-4">
        <NProgress 
          type="line" 
          :percentage="100" 
          :show-indicator="false"
          :height="4"
          processing
        />
        <NTag type="info" class="mt-2">正在筛选股票...</NTag>
      </div>

      <NSpin :show="store.state.selecting || tableLoading">
        <div v-if="store.state.selectionResults && store.state.selectionResults.stocks.length > 0" class="results">
          <div class="result-header mb-4">
            <NTag type="info">
              筛选日期: {{ store.state.selectionResults.date }}
            </NTag>
            <NTag type="success" class="ml-2">
              共 {{ totalCount }} 只股票
            </NTag>
          </div>
          
          <NDataTable
            :columns="columns"
            :data="paginatedStocks"
            :bordered="false"
            :pagination="pagination"
            :row-key="(row: SelectionStock) => row.code"
            striped
            @update:sorter="handleSorterChange"
            @update:page="handlePageChange"
          />
        </div>
        
        <NEmpty 
          v-else-if="!store.state.selecting && !tableLoading" 
          description="请选择模型和日期，点击运行筛选"
        />
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.qlib-select-view {
  padding: 20px;
}
.selection-form {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}
.mb-4 {
  margin-bottom: 16px;
}
.mt-2 {
  margin-top: 8px;
}
.ml-2 {
  margin-left: 8px;
}
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-section {
  padding: 16px 0;
}
</style>
