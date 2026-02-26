<template>
  <div class="list-page">
    <el-card>
      <template #header>
        <div class="header">
          <h2>📊 盘后信息列表</h2>
          <el-button type="primary" @click="triggerJob" :loading="loading">
            <el-icon><Refresh /></el-icon>
            手动采集
          </el-button>
        </div>
      </template>
      
      <el-table :data="list" stripe v-loading="tableLoading">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="大盘指数">
          <template #default="{ row }">
            {{ row.market_overview?.indices?.length || 0 }}个
          </template>
        </el-table-column>
        <el-table-column label="涨停" width="80">
          <template #default="{ row }">
            <el-tag type="success">{{ row.market_overview?.stats?.limit_up || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="跌停" width="80">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.market_overview?.stats?.limit_down || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="板块数" width="80">
          <template #default="{ row }">
            {{ row.sectors?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="新闻数" width="80">
          <template #default="{ row }">
            {{ row.news?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.date)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const tableLoading = ref(false)

const fetchList = async () => {
  tableLoading.value = true
  try {
    const res = await axios.get('/api/after-market')
    list.value = res.data || []
  } catch (e) {
    ElMessage.error('获取列表失败')
  } finally {
    tableLoading.value = false
  }
}

const triggerJob = async () => {
  loading.value = true
  try {
    await axios.post('/api/after-market/trigger')
    ElMessage.success('采集任务已触发')
    setTimeout(fetchList, 2000)
  } catch (e) {
    ElMessage.error('触发失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const viewDetail = (date) => {
  router.push(`/detail/${date}`)
}

onMounted(fetchList)
</script>

<style scoped>
.list-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h2 {
  margin: 0;
}
</style>
