<script setup lang="ts">
import { onMounted } from 'vue'
import { useRiskStore } from '../stores/risk'
import { NCard, NDataTable, NSpin, NAlert, NTag, NPagination } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'

const store = useRiskStore()

onMounted(async () => {
  await store.fetchReports()
})

const columns: DataTableColumns = [
  { title: '报告名称', key: 'name' },
  { title: '类型', key: 'type' },
  { title: '日期', key: 'date' },
  { title: '组合价值', key: 'portfolio_value' },
  { title: 'VaR(95%)', key: 'metrics.var_95' },
  { title: '最大回撤', key: 'metrics.max_drawdown' },
  {
    title: '状态',
    key: 'status',
    render: () => '已生成'
  },
]
</script>

<template>
  <div class="risk-report-view">
    <NCard title="风险报告">
      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <NSpin :show="store.state.loading">
        <NDataTable
          :columns="columns"
          :data="store.state.reports"
          :bordered="false"
        />
      </NSpin>

      <div class="pagination-wrapper mt-4">
        <NPagination
          v-model:page="store.state.currentPage"
          :page-count="store.state.totalPages"
          @update:page="store.fetchReports"
        />
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.risk-report-view {
  padding: 20px;
}
.mb-4 {
  margin-bottom: 16px;
}
.mt-4 {
  margin-top: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
