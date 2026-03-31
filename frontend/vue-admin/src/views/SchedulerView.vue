<script setup lang="ts">
import { onMounted, ref, h } from 'vue'
import { NCard, NDataTable, NButton, NSpin, NAlert, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useRouter } from 'vue-router'
import { apiScheduler } from '../services/api_scheduler'

const router = useRouter()

const jobs = ref<any[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  await fetchJobs()
})

async function fetchJobs() {
  loading.value = true
  error.value = null
  try {
    const res = await apiScheduler.getJobs()
    jobs.value = res.items || []
  } catch (e: any) {
    error.value = e.response?.data?.detail || '获取任务列表失败'
  } finally {
    loading.value = false
  }
}

async function triggerJob(id: string) {
  try {
    await apiScheduler.triggerJob(id)
    await fetchJobs()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '触发任务失败'
  }
}

function viewExecutions(id: string) {
  router.push({ path: '/scheduler', query: { jobId: id } })
}

const columns: DataTableColumns = [
  { title: '任务名称', key: 'name' },
  { title: '任务类型', key: 'task_type' },
  { title: '调度表达式', key: 'schedule' },
  { title: '上次执行', key: 'last_run' },
  { title: '下次执行', key: 'next_run' },
  {
    title: '状态',
    key: 'enabled',
    render: (row: any) => row.enabled ? '启用' : '禁用'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(NSpace, () => [
      h(NButton, { size: 'small', onClick: () => triggerJob(row.id) }, () => '执行'),
      h(NButton, { size: 'small', onClick: () => viewExecutions(row.id) }, () => '历史'),
    ])
  }
]
</script>

<template>
  <div class="scheduler-view">
    <NCard title="调度任务">
      <NAlert v-if="error" type="error" class="mb-4">
        {{ error }}
      </NAlert>

      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="jobs"
          :bordered="false"
        />
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.scheduler-view {
  padding: 20px;
}
.mb-4 {
  margin-bottom: 16px;
}
</style>
