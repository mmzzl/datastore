<template>
  <div class="plugin-management">
    <n-card title="策略插件管理" size="large">
      <div class="plugin-actions">
        <n-upload
          :default-upload="false"
          @before-upload="handleUpload"
          accept=".zip"
        >
          <n-button type="primary">
            <template #icon>
              <n-icon><upload /></n-icon>
            </template>
            上传插件
          </n-button>
        </n-upload>
      </div>

      <n-divider />

      <n-data-table
        v-if="plugins.length > 0"
        :columns="columns"
        :data="plugins"
        :bordered="true"
        :loading="loading"
      >
        <template #cell(actions)="{ row }">
          <div class="action-buttons">
            <n-button size="small" @click="deletePlugin(row.id)">
              <template #icon>
                <n-icon><trash /></n-icon>
              </template>
              删除
            </n-button>
          </div>
        </template>
      </n-data-table>

      <div v-else-if="!loading" class="no-plugins">
        <n-empty description="暂无插件" />
      </div>

      <n-spin v-if="loading" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NUpload, NButton, NIcon, NDivider, NDataTable, NEmpty, NSpin, useMessage } from 'naive-ui'
import { upload, Trash, Upload } from '@vicons/ionicons5'
import { pluginService } from '../services/api'

const message = useMessage()
const plugins = ref<any[]>([])
const loading = ref(false)

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 240
  },
  {
    title: '名称',
    key: 'name',
    width: 150
  },
  {
    title: '描述',
    key: 'description'
  },
  {
    title: '作者',
    key: 'author',
    width: 120
  },
  {
    title: '版本',
    key: 'version',
    width: 80
  },
  {
    title: '上传时间',
    key: 'upload_time',
    width: 180
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right'
  }
]

const loadPlugins = async () => {
  loading.value = true
  try {
    const res = await pluginService.getPlugins()
    plugins.value = res.items
  } catch (e: any) {
    message.error(`加载插件失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

const handleUpload = async (file: File) => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await pluginService.uploadPlugin(formData)
    message.success('插件上传成功')
    await loadPlugins()
  } catch (e: any) {
    message.error(`上传失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
  return false
}

const deletePlugin = async (id: string) => {
  try {
    await pluginService.deletePlugin(id)
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

.plugin-actions {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.no-plugins {
  text-align: center;
  padding: 40px 0;
}
</style>