<template>
  <div class="detail-page">
    <el-page-header @back="goBack" :content="'盘后信息 ' + date" />
    
    <el-tabs v-model="activeTab" class="tabs" v-loading="loading">
      <el-tab-pane label="大盘概况" name="market">
        <el-card v-if="data.market_overview">
          <template #header>三大指数</template>
          <el-row :gutter="20">
            <el-col :span="8" v-for="idx in data.market_overview.indices" :key="idx.code">
              <el-statistic :title="idx.name">
                <template #default>{{ idx.close?.toFixed(2) }}</template>
                <template #suffix :class="idx.pct_chg >= 0 ? 'up' : 'down'">
                  {{ idx.pct_chg >= 0 ? '↑' : '↓' }} {{ idx.pct_chg?.toFixed(2) }}%
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </el-card>
        
        <el-card class="mt-16" v-if="data.market_overview?.stats">
          <template #header>市场统计</template>
          <el-descriptions :column="4" border>
            <el-descriptions-item label="上涨家数">
              <el-tag type="success">{{ data.market_overview.stats.up_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="下跌家数">
              <el-tag type="danger">{{ data.market_overview.stats.down_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="涨停数">
              <el-tag type="success">{{ data.market_overview.stats.limit_up }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="跌停数">
              <el-tag type="danger">{{ data.market_overview.stats.limit_down }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="操作建议" name="recommend">
        <el-card v-if="data.recommendations">
          <template #header>📈 明日操作建议</template>
          
          <el-divider content-position="left">大盘层面</el-divider>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="趋势">
              <el-tag :type="getTrendType(data.recommendations.market?.trend)">
                {{ data.recommendations.market?.trend }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="仓位建议">
              <el-tag>{{ data.recommendations.market?.position }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="风险提示">
              <el-tag type="warning">{{ data.recommendations.market?.risk }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider content-position="left">板块层面</el-divider>
          <el-space wrap>
            <el-tag type="success" v-for="s in data.recommendations.sectors?.main" :key="s">
              👍 {{ s }}
            </el-tag>
            <el-tag type="danger" v-for="s in data.recommendations.sectors?.avoid" :key="s">
              👎 {{ s }}
            </el-tag>
          </el-space>
          <p v-if="data.recommendations.sectors?.rotation">
            🔄 {{ data.recommendations.sectors.rotation }}
          </p>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="板块热点" name="sectors">
        <el-table :data="data.sectors || []" stripe>
          <el-table-column prop="name" label="板块名称" />
          <el-table-column prop="pct_chg" label="涨跌幅">
            <template #default="{ row }">
              <span :class="row.pct_chg >= 0 ? 'up' : 'down'">
                {{ row.pct_chg >= 0 ? '↑' : '↓' }} {{ Math.abs(row.pct_chg).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="新闻" name="news">
        <el-table :data="data.news || []" stripe>
          <el-table-column prop="title" label="标题" show-overflow-tooltip />
          <el-table-column prop="show_time" label="时间" width="180" />
          <el-table-column prop="stock_list" label="关联股票" width="200">
            <template #default="{ row }">
              <el-tag v-for="s in (row.stock_list || []).slice(0, 3)" :key="s" size="small" class="mr-4">
                {{ s }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const date = route.params.date
const activeTab = ref('market')
const data = ref({})
const loading = ref(false)

const getTrendType = (trend) => {
  if (trend === '上行') return 'success'
  if (trend === '下行') return 'danger'
  return 'warning'
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/after-market/${date}`)
    data.value = res.data || {}
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const goBack = () => router.push('/')

onMounted(fetchDetail)
</script>

<style scoped>
.detail-page {
  padding: 20px;
}
.tabs {
  margin-top: 20px;
}
.mt-16 {
  margin-top: 16px;
}
.mr-4 {
  margin-right: 4px;
}
.up {
  color: #f56c6c;
}
.down {
  color: #67c23a;
}
</style>
