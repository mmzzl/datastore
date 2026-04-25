<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { NDataTable, NButton, NSelect, NTag, NDrawer, NDrawerContent, NEmpty, NSpin } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { Experiment } from '../../services/api_qlib'

const store = useQlibStore()

onMounted(async () => {
  await store.fetchExperiments()
})

const currentPage = ref(1)
const pageSize = 20
const selectedIds = ref<string[]>([])
const showCompare = ref(false)
const statusFilter = ref<string | null>(null)
const compareData = ref<Record<string, any>>({})

const statusOptions = [
  { label: '全部', value: '' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: 'IC过低跳过', value: 'skipped_low_ic' },
]

const columns: DataTableColumns<Experiment> = [
  { type: 'selection' },
  { title: '实验ID', key: 'experiment_id', width: 180, ellipsis: { tooltip: true } },
  { title: '模型类型', key: 'model_type', width: 100, render: (row: Experiment) => row.config?.model_type || '-' },
  { title: '因子', key: 'factor', width: 100, render: (row: Experiment) => row.config?.factor_type || '-' },
  { title: 'IC', key: 'ic', width: 80, render: (row: Experiment) => row.training_metrics?.ic?.toFixed(4) ?? '-' },
  { title: 'Rank IC', key: 'rank_ic', width: 80, render: (row: Experiment) => row.training_metrics?.rank_ic?.toFixed(4) ?? '-' },
  { title: 'Sharpe', key: 'sharpe', width: 80, render: (row: Experiment) => row.backtest_result?.sharpe_ratio?.toFixed(2) ?? '-' },
  {
    title: '状态', key: 'status', width: 100,
    render: (row: Experiment) => {
      const map: Record<string, string> = { completed: 'success', failed: 'error', skipped_low_ic: 'warning' }
      return h(NTag, { type: map[row.status] || 'default', size: 'small' }, { default: () => row.status })
    },
  },
  { title: '创建时间', key: 'created_at', width: 160, render: (row: Experiment) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' },
]

const pagination = computed(() => ({
  page: currentPage.value,
  pageSize,
  itemCount: store.state.experimentsTotal,
  onChange: (page: number) => {
    currentPage.value = page
    store.fetchExperiments(page, pageSize, undefined, statusFilter.value || undefined)
  },
}))

function handleCheckedRowKeys(keys: string[]) {
  selectedIds.value = keys
}

async function openCompare() {
  if (selectedIds.value.length < 2) return
  const { apiQlib } = await import('../../services/api_qlib')
  compareData.value = await apiQlib.compareExperiments(selectedIds.value)
  showCompare.value = true
}

async function applyFilter() {
  currentPage.value = 1
  await store.fetchExperiments(1, pageSize, undefined, statusFilter.value || undefined)
}
</script>

<template>
  <div class="train-history">
    <div class="filter-bar">
      <NSelect v-model:value="statusFilter" :options="statusOptions" placeholder="状态筛选" style="width: 140px" clearable @update:value="applyFilter" />
      <NButton type="primary" :disabled="selectedIds.length < 2" @click="openCompare">对比 ({{ selectedIds.length }})</NButton>
    </div>
    <NSpin :show="store.state.loading">
      <NDataTable :columns="columns" :data="store.state.experiments" :pagination="pagination" :row-key="(row: Experiment) => row.experiment_id" :bordered="false" striped @update:checked-row-keys="handleCheckedRowKeys" />
      <NEmpty v-if="store.state.experiments.length === 0 && !store.state.loading" description="暂无训练记录，请先运行训练" />
    </NSpin>
    <NDrawer v-model:show="showCompare" :width="600" placement="right">
      <NDrawerContent title="实验对比">
        <div v-for="(data, id) in compareData" :key="id" class="compare-item">
          <h3>{{ id }}</h3>
          <p>模型: {{ data.config?.model_type }} | 因子: {{ data.config?.factor_type }}</p>
          <p>IC: {{ data.training_metrics?.ic?.toFixed(4) ?? '-' }} | Rank IC: {{ data.training_metrics?.rank_ic?.toFixed(4) ?? '-' }}</p>
          <p>Sharpe: {{ data.backtest_result?.sharpe_ratio?.toFixed(2) ?? '-' }} | 状态: {{ data.status }}</p>
        </div>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.train-history { padding: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.compare-item { margin-bottom: 16px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 4px; }
</style>
