<script setup lang="ts">
import { onMounted, ref, h, computed } from 'vue'
import {
  NCard, NDataTable, NButton, NSpin, NAlert, NSpace, NModal, NForm, NFormItem,
  NInput, NSelect, NSwitch, NPopconfirm, NTag, NIcon, createDiscreteApi, NPagination,
  NCode, NDescriptions, NDescriptionsItem, NEmpty
} from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { apiScheduler, type SchedulerJob, type JobExecution } from '../services/api_scheduler'

const { message } = createDiscreteApi(['message'])

const jobs = ref<SchedulerJob[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pagination = ref({ page: 1, pageSize: 10, itemCount: 0, showSizePicker: true, pageSizes: [10, 20, 50] })
const sortKey = ref<string>('name')
const sortOrder = ref<'ascend' | 'descend'>('ascend')

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showHistoryModal = ref(false)
const showTriggerResultModal = ref(false)
const editingJob = ref<SchedulerJob | null>(null)
const triggerResult = ref<{ executionId: string; jobName: string } | null>(null)

const formRef = ref<FormInst | null>(null)
const formData = ref({
  name: '',
  task_type: '',
  schedule: '',
  enabled: true,
  config: '{}'
})

const taskTypes = [
  { label: '数据采集', value: 'data_collect' },
  { label: '信号生成', value: 'signal_generate' },
  { label: '定时报告', value: 'scheduled_report' },
  { label: '清理任务', value: 'cleanup' },
]

const executions = ref<JobExecution[]>([])
const executionsLoading = ref(false)
const executionsPagination = ref({ page: 1, pageSize: 10, itemCount: 0, totalPages: 0 })

const cronDescription = computed(() => {
  return getCronDescription(formData.value.schedule)
})

const editCronDescription = computed(() => {
  if (!editingJob.value) return ''
  return getCronDescription(editingJob.value.schedule)
})

function getCronDescription(cron: string): string {
  if (!cron) return ''
  const parts = cron.trim().split(/\s+/)
  if (parts.length !== 5) return '无效的 cron 表达式'
  
  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts
  
  const descriptions: string[] = []
  
  if (minute === '*' && hour === '*') {
    descriptions.push('每分钟')
  } else if (minute !== '*' && hour === '*') {
    descriptions.push(`每小时第 ${minute} 分钟`)
  } else if (minute !== '*' && hour !== '*') {
    if (minute === '0') {
      descriptions.push(`每天 ${hour}:00`)
    } else {
      descriptions.push(`每天 ${hour}:${minute.padStart(2, '0')}`)
    }
  }
  
  if (dayOfMonth !== '*' && month === '*') {
    descriptions.push(`每月 ${dayOfMonth} 号`)
  }
  
  if (dayOfWeek !== '*') {
    const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const days = dayOfWeek.split(',').map(d => dayNames[parseInt(d)] || d).join('、')
    descriptions.push(`每${days}`)
  }
  
  if (month !== '*') {
    descriptions.push(`${month} 月`)
  }
  
  return descriptions.length > 0 ? descriptions.join('，') : '自定义时间'
}

function validateCron(cron: string): boolean {
  if (!cron) return false
  const parts = cron.trim().split(/\s+/)
  if (parts.length !== 5) return false
  
  const validatePart = (part: string, min: number, max: number): boolean => {
    if (part === '*') return true
    if (part.includes('/')) {
      const [, step] = part.split('/')
      const stepNum = parseInt(step)
      return !isNaN(stepNum) && stepNum > 0
    }
    if (part.includes('-')) {
      const [start, end] = part.split('-').map(Number)
      return !isNaN(start) && !isNaN(end) && start >= min && end <= max && start <= end
    }
    if (part.includes(',')) {
      return part.split(',').every(p => {
        const n = parseInt(p)
        return !isNaN(n) && n >= min && n <= max
      })
    }
    const num = parseInt(part)
    return !isNaN(num) && num >= min && num <= max
  }
  
  return validatePart(parts[0], 0, 59) &&
         validatePart(parts[1], 0, 23) &&
         validatePart(parts[2], 1, 31) &&
         validatePart(parts[3], 1, 12) &&
         validatePart(parts[4], 0, 6)
}

const formRules: FormRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  schedule: [
    { required: true, message: '请输入 cron 表达式', trigger: 'blur' },
    {
      validator: (_rule, value) => {
        return validateCron(value) ? Promise.resolve() : Promise.reject('无效的 cron 表达式，格式应为: 分 时 日 月 周')
      },
      trigger: 'blur'
    }
  ],
  config: [
    {
      validator: (_rule, value) => {
        try {
          if (value && value.trim()) {
            JSON.parse(value)
          }
          return Promise.resolve()
        } catch {
          return Promise.reject('配置必须是有效的 JSON 格式')
        }
      },
      trigger: 'blur'
    }
  ]
}

onMounted(async () => {
  await fetchJobs()
})

async function fetchJobs() {
  loading.value = true
  error.value = null
  try {
    const res = await apiScheduler.getJobs()
    jobs.value = (res.items || []).map(item => ({
      id: item.job_id,
      name: item.name,
      task_type: item.job_type,
      schedule: item.cron_expression,
      enabled: item.enabled,
      last_run: item.last_run,
      next_run: item.next_run,
      config: item.config,
      created_at: item.created_at,
      updated_at: item.updated_at
    }))
    pagination.value.itemCount = jobs.value.length
  } catch (e: any) {
    error.value = e.response?.data?.detail || '获取任务列表失败'
  } finally {
    loading.value = false
  }
}

const sortedJobs = computed(() => {
  const sorted = [...jobs.value]
  const key = sortKey.value
  const order = sortOrder.value === 'ascend' ? 1 : -1
  
  return sorted.sort((a, b) => {
    let valA: any = a[key as keyof SchedulerJob]
    let valB: any = b[key as keyof SchedulerJob]
    
    if (typeof valA === 'boolean') {
      valA = valA ? 1 : 0
      valB = valB ? 1 : 0
    }
    if (valA === undefined || valA === null) return order * -1
    if (valB === undefined || valB === null) return order * 1
    
    if (typeof valA === 'string') {
      return order * valA.localeCompare(valB)
    }
    return order * (valA > valB ? 1 : valA < valB ? -1 : 0)
  })
})

const paginatedJobs = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return sortedJobs.value.slice(start, end)
})

function handleSorterChange(sorter: { columnKey: string; order: 'ascend' | 'descend' | false }) {
  if (sorter.order) {
    sortKey.value = sorter.columnKey
    sortOrder.value = sorter.order
  }
}

function handlePageChange(page: number) {
  pagination.value.page = page
}

function handlePageSizeChange(pageSize: number) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
}

function openCreateModal() {
  formData.value = { name: '', task_type: '', schedule: '', enabled: true, config: '{}' }
  showCreateModal.value = true
}

function openEditModal(job: SchedulerJob) {
  editingJob.value = { ...job }
  showEditModal.value = true
}

async function handleCreate() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  
  try {
    const config = formData.value.config.trim() ? JSON.parse(formData.value.config) : undefined
    await apiScheduler.createJob({
      name: formData.value.name,
      task_type: formData.value.task_type,
      schedule: formData.value.schedule,
      enabled: formData.value.enabled,
      config
    })
    message.success('任务创建成功')
    showCreateModal.value = false
    await fetchJobs()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建任务失败')
  }
}

async function handleEdit() {
  if (!editingJob.value) return
  
  try {
    await apiScheduler.updateJob(editingJob.value.id, {
      name: editingJob.value.name,
      schedule: editingJob.value.schedule,
      enabled: editingJob.value.enabled,
      config: editingJob.value.config
    })
    message.success('任务更新成功')
    showEditModal.value = false
    await fetchJobs()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新任务失败')
  }
}

async function handleDelete(id: string) {
  try {
    await apiScheduler.deleteJob(id)
    message.success('任务已删除')
    await fetchJobs()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除任务失败')
  }
}

async function toggleEnabled(job: SchedulerJob) {
  try {
    await apiScheduler.updateJob(job.id, { enabled: !job.enabled })
    message.success(job.enabled ? '任务已禁用' : '任务已启用')
    await fetchJobs()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新状态失败')
  }
}

async function triggerJob(job: SchedulerJob) {
  try {
    const result = await apiScheduler.triggerJob(job.id)
    triggerResult.value = { executionId: result.execution_id, jobName: job.name }
    showTriggerResultModal.value = true
    await fetchJobs()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '触发任务失败')
  }
}

async function openHistoryModal(job: SchedulerJob) {
  editingJob.value = job
  executionsPagination.value.page = 1
  await loadExecutions(job.id)
  showHistoryModal.value = true
}

async function loadExecutions(jobId: string) {
  executionsLoading.value = true
  try {
    const res = await apiScheduler.getExecutions(jobId, executionsPagination.value.page, executionsPagination.value.pageSize)
    executions.value = (res.executions || []).map(item => ({
      id: item.execution_id,
      job_id: item.job_id,
      status: item.status,
      started_at: item.started_at,
      completed_at: item.completed_at,
      duration: item.completed_at && item.started_at ? 
        Math.floor((new Date(item.completed_at).getTime() - new Date(item.started_at).getTime()) / 1000) * 1000 : 
        undefined,
      result: item.result,
      error: item.error_message
    }))
    executionsPagination.value.itemCount = res.total
    executionsPagination.value.totalPages = res.total_pages
  } catch (e: any) {
    message.error(e.response?.data?.detail || '加载执行历史失败')
  } finally {
    executionsLoading.value = false
  }
}

function handleExecutionsPageChange(page: number) {
  executionsPagination.value.page = page
  if (editingJob.value) {
    loadExecutions(editingJob.value.id)
  }
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusTag(status: string) {
  const statusMap: Record<string, { type: 'success' | 'error' | 'warning' | 'default'; text: string }> = {
    pending: { type: 'default', text: '待执行' },
    running: { type: 'warning', text: '执行中' },
    success: { type: 'success', text: '成功' },
    failed: { type: 'error', text: '失败' }
  }
  return statusMap[status] || { type: 'default', text: status }
}

const columns: DataTableColumns<SchedulerJob> = [
  { title: '名称', key: 'name', sorter: true },
  { title: '类型', key: 'task_type', sorter: true },
  { title: '调度表达式', key: 'schedule' },
  { title: '启用', key: 'enabled', sorter: true,
    render: (row) => h(NSwitch, {
      value: row.enabled,
      onUpdateValue: () => toggleEnabled(row)
    })
  },
  { title: '上次执行', key: 'last_run', sorter: true,
    render: (row) => formatDate(row.last_run)
  },
  { title: '下次执行', key: 'next_run', sorter: true,
    render: (row) => formatDate(row.next_run)
  },
  { title: '状态', key: 'status',
    render: (row) => {
      if (!row.enabled) return h(NTag, { type: 'default' }, () => '已禁用')
      if (row.next_run) return h(NTag, { type: 'success' }, () => '运行中')
      return h(NTag, { type: 'warning' }, () => '待启动')
    }
  },
  { title: '操作', key: 'actions', width: 280,
    render: (row) => h(NSpace, { size: 'small' }, () => [
      h(NButton, { size: 'small', type: 'primary', onClick: () => triggerJob(row) }, () => '立即执行'),
      h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => '编辑'),
      h(NButton, { size: 'small', onClick: () => openHistoryModal(row) }, () => '历史'),
      h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
        trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'),
        default: () => '确定删除此任务吗？'
      })
    ])
  }
]

const executionColumns: DataTableColumns<JobExecution> = [
  { title: '开始时间', key: 'started_at', render: (row) => formatDate(row.started_at) },
  { title: '完成时间', key: 'completed_at', render: (row) => formatDate(row.completed_at) },
  { title: '状态', key: 'status',
    render: (row) => {
      const { type, text } = getStatusTag(row.status)
      return h(NTag, { type }, () => text)
    }
  },
  { title: '耗时', key: 'duration',
    render: (row) => row.duration ? `${row.duration}ms` : '-'
  },
  { title: '结果/错误', key: 'result',
    render: (row) => {
      if (row.error) {
        return h(NTag, { type: 'error' }, () => row.error?.substring(0, 50) + (row.error.length > 50 ? '...' : ''))
      }
      if (row.result) {
        return h('span', { class: 'result-link', onClick: () => message.info(JSON.stringify(row.result, null, 2)) }, '查看结果')
      }
      return '-'
    }
  }
]
</script>

<template>
  <div class="scheduler-view">
    <NCard title="调度任务管理">
      <template #header-extra>
        <NButton type="primary" @click="openCreateModal">新建任务</NButton>
      </template>
      
      <NAlert v-if="error" type="error" class="mb-4">
        {{ error }}
      </NAlert>
      
      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="paginatedJobs"
          :bordered="false"
          :row-key="(row: SchedulerJob) => row.id"
          @update:sorter="handleSorterChange"
        />
        <div class="pagination-wrapper">
          <NPagination
            v-model:page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :item-count="pagination.itemCount"
            :page-sizes="pagination.pageSizes"
            show-size-picker
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </NSpin>
    </NCard>
    
    <NModal v-model:show="showCreateModal" preset="card" title="新建任务" style="width: 600px">
      <NForm ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="100px">
        <NFormItem label="任务名称" path="name">
          <NInput v-model:value="formData.name" placeholder="请输入任务名称" />
        </NFormItem>
        <NFormItem label="任务类型" path="task_type">
          <NSelect v-model:value="formData.task_type" :options="taskTypes" placeholder="请选择任务类型" />
        </NFormItem>
        <NFormItem label="Cron 表达式" path="schedule">
          <NInput v-model:value="formData.schedule" placeholder="例如: 0 9 * * 1-5 (工作日早上9点)" />
          <template #feedback>
            <span v-if="cronDescription" class="cron-hint">{{ cronDescription }}</span>
          </template>
        </NFormItem>
        <NFormItem label="配置" path="config">
          <NInput v-model:value="formData.config" type="textarea" :rows="5" placeholder="JSON 格式配置，可选" />
        </NFormItem>
        <NFormItem label="启用">
          <NSwitch v-model:value="formData.enabled" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showCreateModal = false">取消</NButton>
          <NButton type="primary" @click="handleCreate">创建</NButton>
        </NSpace>
      </template>
    </NModal>
    
    <NModal v-model:show="showEditModal" preset="card" title="编辑任务" style="width: 600px">
      <NForm v-if="editingJob" :model="editingJob" label-placement="left" label-width="100px">
        <NFormItem label="任务名称">
          <NInput v-model:value="editingJob.name" />
        </NFormItem>
        <NFormItem label="任务类型">
          <NInput :value="editingJob.task_type" disabled />
        </NFormItem>
        <NFormItem label="Cron 表达式">
          <NInput v-model:value="editingJob.schedule" />
          <template #feedback>
            <span v-if="editCronDescription" class="cron-hint">{{ editCronDescription }}</span>
          </template>
        </NFormItem>
        <NFormItem label="配置">
          <NInput
            :value="JSON.stringify(editingJob.config || {}, null, 2)"
            @update:value="(val: string) => { try { editingJob.config = JSON.parse(val) } catch {} }"
            type="textarea"
            :rows="5"
          />
        </NFormItem>
        <NFormItem label="启用">
          <NSwitch v-model:value="editingJob.enabled" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="showEditModal = false">取消</NButton>
          <NButton type="primary" @click="handleEdit">保存</NButton>
        </NSpace>
      </template>
    </NModal>
    
    <NModal v-model:show="showTriggerResultModal" preset="card" title="任务已触发" style="width: 400px">
      <NDescriptions label-placement="left" :column="1">
        <NDescriptionsItem label="任务名称">{{ triggerResult?.jobName }}</NDescriptionsItem>
        <NDescriptionsItem label="执行ID">
          <NCode>{{ triggerResult?.executionId }}</NCode>
        </NDescriptionsItem>
      </NDescriptions>
      <template #footer>
        <NButton @click="showTriggerResultModal = false">关闭</NButton>
      </template>
    </NModal>
    
    <NModal v-model:show="showHistoryModal" preset="card" title="执行历史" style="width: 900px">
      <NSpin :show="executionsLoading">
        <NDataTable
          v-if="executions.length > 0"
          :columns="executionColumns"
          :data="executions"
          :bordered="false"
          :row-key="(row: JobExecution) => row.id"
        />
        <NEmpty v-else description="暂无执行记录" />
        <div v-if="executionsPagination.totalPages > 1" class="pagination-wrapper">
          <NPagination
            v-model:page="executionsPagination.page"
            :page-count="executionsPagination.totalPages"
            @update:page="handleExecutionsPageChange"
          />
        </div>
      </NSpin>
      <template #footer>
        <NButton @click="showHistoryModal = false">关闭</NButton>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.scheduler-view {
  padding: 20px;
}
.mb-4 {
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.cron-hint {
  color: #18a058;
  font-size: 12px;
}
.result-link {
  color: #2080f0;
  cursor: pointer;
}
.result-link:hover {
  text-decoration: underline;
}
</style>
