<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NModal, NCard } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem } from '../../services/api_qlib'

const store = useQlibStore()

const showTrainModal = ref(false)
const training = ref(false)
const trainStatus = ref('')

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
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

async function handleStartTraining() {
  training.value = true
  trainStatus.value = '训练中...'
  try {
    const res = await apiQlib.startTraining({
      model_type: 'lgbm',
    })
    const taskId = res.id
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 5000))
      const status = await apiQlib.getTrainingStatus(taskId)
      if (status.status === 'completed') {
        trainStatus.value = '训练完成，正在刷新推荐...'
        await store.refreshTopStocks()
        trainStatus.value = '训练完成！'
        break
      } else if (status.status === 'failed') {
        trainStatus.value = `训练失败: ${status.error || '未知错误'}`
        break
      } else {
        trainStatus.value = `训练中 (${i * 5}s)...`
      }
    }
  } catch (e: any) {
    trainStatus.value = e.response?.data?.detail || e.message || '启动训练失败'
  } finally {
    training.value = false
  }
}

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
      <NButton type="warning" @click="showTrainModal = true">开始训练</NButton>
    </NSpace>

    <NModal v-model:show="showTrainModal" :mask-closable="false" preset="card" title="模型训练" style="width: 400px">
      <p>将使用默认参数（lgbm / alpha158 / CSI300）训练新模型。</p>
      <p style="margin-top: 8px; color: #888; font-size: 13px;">训练完成后会自动刷新今日推荐。</p>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showTrainModal = false" :disabled="training">取消</NButton>
          <NButton type="primary" :loading="training" @click="handleStartTraining">开始训练</NButton>
        </NSpace>
      </template>
      <div v-if="trainStatus" style="margin-top: 12px">
        <NAlert :type="trainStatus.includes('失败') ? 'error' : 'info'" closable>{{ trainStatus }}</NAlert>
      </div>
    </NModal>

    <NAlert v-if="store.state.error" type="error" style="margin-bottom: 12px">{{ store.state.error }}</NAlert>
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
