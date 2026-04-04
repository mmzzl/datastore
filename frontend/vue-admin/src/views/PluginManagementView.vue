<template>
  <div class="plugin-management">
    <n-card title="策略插件管理" size="large">
      <template #header-extra>
        <n-upload
          :custom-request="handleUpload"
          accept=".zip"
          :show-file-list="false"
        >
          <n-button type="primary" :loading="uploading">
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            上传插件
          </n-button>
        </n-upload>
      </template>

      <n-progress
        v-if="uploading && uploadProgress > 0"
        type="line"
        :percentage="uploadProgress"
        :show-indicator="true"
        :height="24"
        style="margin-bottom: 16px"
      />

      <n-divider />

      <n-data-table
        v-if="plugins.length > 0"
        :columns="columns"
        :data="plugins"
        :bordered="true"
        :loading="loading"
        :row-key="(row: Plugin) => row.id"
      />

      <div v-else-if="!loading" class="no-plugins">
        <n-empty description="暂无插件" />
      </div>
    </n-card>

    <n-modal v-model:show="showDetailModal" preset="card" title="插件详情" :style="{ width: '600px' }">
      <n-descriptions label-placement="left" :column="1" bordered>
        <n-descriptions-item label="名称">{{ currentPlugin?.display_name }}</n-descriptions-item>
        <n-descriptions-item label="版本">{{ currentPlugin?.version }}</n-descriptions-item>
        <n-descriptions-item label="作者">{{ currentPlugin?.author }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="currentPlugin?.status === 'active' ? 'success' : 'warning'">
            {{ currentPlugin?.status === 'active' ? '已启用' : '已禁用' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="描述">{{ currentPlugin?.description }}</n-descriptions-item>
        <n-descriptions-item label="创建时间">{{ formatDateTime(currentPlugin?.created_at) }}</n-descriptions-item>
      </n-descriptions>
      
      <n-divider v-if="currentPlugin?.readme" />
      
      <div v-if="currentPlugin?.readme" class="readme-section">
        <h4>说明文档</h4>
        <pre class="readme-content">{{ currentPlugin.readme }}</pre>
      </div>
    </n-modal>

    <n-modal v-model:show="showVersionModal" preset="card" title="切换版本" :style="{ width: '400px' }">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="插件名称">
          <span>{{ currentPlugin?.name }}</span>
        </n-form-item>
        <n-form-item label="当前版本">
          <n-tag type="info">{{ currentPlugin?.version }}</n-tag>
        </n-form-item>
        <n-form-item label="选择版本">
          <n-select
            v-model:value="selectedVersion"
            :options="versionOptions"
            placeholder="请选择版本"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showVersionModal = false">取消</n-button>
          <n-button type="primary" :loading="switchingVersion" :disabled="!selectedVersion" @click="handleSwitchVersion">
            切换
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { NCard, NUpload, NButton, NIcon, NDivider, NDataTable, NEmpty, NTag, NModal, NDescriptions, NDescriptionsItem, NSelect, NForm, NFormItem, NProgress, NSpace, useMessage } from 'naive-ui'
import { CloudUploadOutline, EyeOutline, TrashOutline, PlayOutline, PauseOutline, GitBranchOutline } from '@vicons/ionicons5'
import { apiPlugins, type Plugin, type PluginDetail } from '../services/api_plugins'

const message = useMessage()
const plugins = ref<Plugin[]>([])
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const switchingVersion = ref(false)

const showDetailModal = ref(false)
const showVersionModal = ref(false)
const currentPlugin = ref<PluginDetail | null>(null)
const pluginVersions = ref<string[]>([])
const selectedVersion = ref('')

const versionOptions = computed(() => {
  return pluginVersions.value.map(v => ({
    label: v,
    value: v,
  }))
})

const columns = [
  { title: 'ID', key: 'id', width: 240, ellipsis: { tooltip: true } },
  { title: '名称', key: 'display_name', width: 150 },
  { title: '版本', key: 'version', width: 80 },
  { title: '作者', key: 'author', width: 120 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: Plugin) => {
      return h(NTag, {
        type: row.status === 'active' ? 'success' : 'warning',
        size: 'small'
      }, () => row.status === 'active' ? '已启用' : '已禁用')
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row: Plugin) => formatDateTime(row.created_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    fixed: 'right',
    render: (row: Plugin) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => showPluginDetail(row.id),
        }, { icon: () => h(NIcon, null, () => h(EyeOutline)), default: () => '详情' }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          type: row.status === 'active' ? 'warning' : 'success',
          onClick: () => togglePluginStatus(row),
        }, { icon: () => h(NIcon, null, () => h(row.status === 'active' ? PauseOutline : PlayOutline)), default: () => row.status === 'active' ? '禁用' : '启用' }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openVersionModal(row),
        }, { icon: () => h(NIcon, null, () => h(GitBranchOutline)), default: () => '版本' }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          type: 'error',
          onClick: () => handleDelete(row),
        }, { icon: () => h(NIcon, null, () => h(TrashOutline)), default: () => '删除' }),
      ])
    },
  },
]

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadPlugins() {
  loading.value = true
  try {
    const res = await apiPlugins.getPlugins()
    plugins.value = res.items
  } catch (e: any) {
    message.error(`加载插件失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

async function handleUpload({ file }: { file: { file: File } }) {
  uploading.value = true
  uploadProgress.value = 0
  try {
    await apiPlugins.uploadPlugin(file.file, (percent) => {
      uploadProgress.value = percent
    })
    message.success('插件上传成功')
    await loadPlugins()
  } catch (e: any) {
    message.error(`上传失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function showPluginDetail(pluginId: string) {
  loading.value = true
  try {
    currentPlugin.value = await apiPlugins.getPlugin(pluginId)
    showDetailModal.value = true
  } catch (e: any) {
    message.error(`获取详情失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

async function togglePluginStatus(plugin: Plugin) {
  try {
    if (plugin.status === 'active') {
      await apiPlugins.deactivatePlugin(plugin.id)
      message.success('插件已禁用')
    } else {
      await apiPlugins.activatePlugin(plugin.id)
      message.success('插件已启用')
    }
    await loadPlugins()
  } catch (e: any) {
    message.error(`操作失败: ${e.response?.data?.detail || e.message}`)
  }
}

async function openVersionModal(plugin: Plugin) {
  loading.value = true
  try {
    const res = await apiPlugins.getPluginVersions(plugin.id)
    pluginVersions.value = res.versions
    currentPlugin.value = plugin as PluginDetail
    selectedVersion.value = ''
    showVersionModal.value = true
  } catch (e: any) {
    message.error(`获取版本列表失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

async function handleSwitchVersion() {
  if (!currentPlugin.value || !selectedVersion.value) return
  switchingVersion.value = true
  try {
    await apiPlugins.switchVersion(currentPlugin.value.id, selectedVersion.value)
    message.success('版本切换成功')
    showVersionModal.value = false
    await loadPlugins()
  } catch (e: any) {
    message.error(`切换版本失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    switchingVersion.value = false
  }
}

async function handleDelete(plugin: Plugin) {
  const confirmed = window.confirm(`确定删除插件 "${plugin.display_name}" 吗？`)
  if (!confirmed) return
  try {
    await apiPlugins.deletePlugin(plugin.id)
    message.success('插件删除成功')
    await loadPlugins()
  } catch (e: any) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
.plugin-management {
  padding: 20px;
}

.no-plugins {
  text-align: center;
  padding: 40px 0;
}

.readme-section {
  margin-top: 16px;
}

.readme-section h4 {
  margin-bottom: 8px;
  color: #333;
}

.readme-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  max-height: 300px;
  overflow-y: auto;
}
</style>
