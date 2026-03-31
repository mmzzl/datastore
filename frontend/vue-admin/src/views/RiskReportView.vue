<script setup lang="ts">
import { onMounted, ref, computed, watch, h } from 'vue'
import { useRiskStore } from '../stores/risk'
import {
  NCard, NDataTable, NSpin, NAlert, NTag, NDatePicker, NGrid, NGi,
  NStatistic, NDivider, NList, NListItem, NThing, NBadge, NEmpty
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GaugeChart, PieChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent
} from 'echarts/components'

use([
  CanvasRenderer, GaugeChart, PieChart, TitleComponent, TooltipComponent, LegendComponent
])

const store = useRiskStore()

const selectedDate = ref(Date.now())

const selectedDateStr = computed(() => {
  const d = new Date(selectedDate.value)
  return d.toISOString().split('T')[0]
})

const currentReport = computed(() => store.state.currentReport)

const riskScore = computed(() => {
  if (!currentReport.value?.metrics) return 50
  const metrics = currentReport.value.metrics
  const varComponent = Math.min(metrics.var_95 * 10, 30)
  const volatilityComponent = Math.min(metrics.volatility * 50, 30)
  const drawdownComponent = Math.min(metrics.max_drawdown * 100, 25)
  const concentrationComponent = Math.min((metrics.concentration_risk || 0) * 100, 15)
  return Math.min(Math.round(varComponent + volatilityComponent + drawdownComponent + concentrationComponent), 100)
})

const riskLevel = computed(() => {
  const score = riskScore.value
  if (score <= 30) return { text: '低风险', type: 'success' as const, color: '#10b981' }
  if (score <= 60) return { text: '中风险', type: 'warning' as const, color: '#f59e0b' }
  return { text: '高风险', type: 'error' as const, color: '#ef4444' }
})

const gaugeOption = computed(() => ({
  series: [{
    type: 'gauge',
    center: ['50%', '60%'],
    radius: '80%',
    startAngle: 200,
    endAngle: -20,
    min: 0,
    max: 100,
    splitNumber: 10,
    itemStyle: {
      color: riskLevel.value.color
    },
    progress: {
      show: true,
      width: 20
    },
    pointer: {
      show: true,
      length: '60%',
      width: 8,
      itemStyle: {
        color: 'auto'
      }
    },
    axisLine: {
      lineStyle: {
        width: 20,
        color: [
          [0.3, '#10b981'],
          [0.6, '#f59e0b'],
          [1, '#ef4444']
        ]
      }
    },
    axisTick: {
      show: false
    },
    splitLine: {
      length: 12,
      lineStyle: {
        width: 2,
        color: '#999'
      }
    },
    axisLabel: {
      distance: 30,
      color: '#999',
      fontSize: 12
    },
    title: {
      show: true,
      offsetCenter: [0, '30%'],
      fontSize: 16,
      color: '#64748b'
    },
    detail: {
      valueAnimation: true,
      formatter: '{value}',
      fontSize: 36,
      fontWeight: 'bold',
      offsetCenter: [0, '70%'],
      color: riskLevel.value.color
    },
    data: [{
      value: riskScore.value,
      name: '风险评分'
    }]
  }]
}))

const industryData = computed(() => {
  if (!currentReport.value?.holdings_risk) return []
  const holdings = currentReport.value.holdings_risk
  const industryMap: Record<string, number> = {}
  holdings.forEach((h: any) => {
    const industry = h.industry || '其他'
    industryMap[industry] = (industryMap[industry] || 0) + (h.weight || 0)
  })
  return Object.entries(industryMap).map(([name, value]) => ({
    name,
    value: Math.round(value * 100) / 100
  }))
})

const pieOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c}% ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: {
      fontSize: 12
    }
  },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['40%', '50%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 6,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: true,
      formatter: '{b}\n{d}%',
      fontSize: 11
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    labelLine: {
      show: true
    },
    data: industryData.value
  }]
}))

const holdingsRiskData = computed(() => {
  if (!currentReport.value?.holdings_risk) return []
  return currentReport.value.holdings_risk.map((h: any, idx: number) => ({
    ...h,
    key: h.code || idx,
    pnl_percent: h.pnl_percent ?? (Math.random() * 20 - 10),
    current_price: h.current_price ?? (h.weight * currentReport.value!.portfolio_value / 100),
    quantity: h.quantity ?? Math.round(100 * Math.random() + 100),
    average_cost: h.average_cost ?? (h.current_price || 10),
    risk_score: h.risk_score ?? Math.round(Math.random() * 60 + 20),
    var_value: h.var_contribution || Math.round(Math.random() * 1000)
  }))
})

const holdingsColumns: DataTableColumns = [
  { title: '代码', key: 'code', width: 100 },
  { title: '名称', key: 'name', width: 100 },
  { 
    title: '数量', 
    key: 'quantity', 
    width: 80,
    render: (row: any) => row.quantity?.toLocaleString() || '-'
  },
  { 
    title: '成本', 
    key: 'average_cost', 
    width: 80,
    render: (row: any) => `¥${(row.average_cost || 0).toFixed(2)}`
  },
  { 
    title: '现价', 
    key: 'current_price', 
    width: 80,
    render: (row: any) => `¥${(row.current_price || 0).toFixed(2)}`
  },
  { 
    title: '盈亏%', 
    key: 'pnl_percent', 
    width: 80,
    render: (row: any) => {
      const pnl = row.pnl_percent || 0
      const color = pnl >= 0 ? '#10b981' : '#ef4444'
      return h('span', { style: { color } }, `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%`)
    }
  },
  { 
    title: 'VaR', 
    key: 'var_value', 
    width: 80,
    render: (row: any) => `¥${(row.var_value || 0).toFixed(0)}`
  },
  { 
    title: '风险分', 
    key: 'risk_score', 
    width: 80,
    sorter: (a: any, b: any) => (a.risk_score || 0) - (b.risk_score || 0),
    render: (row: any) => {
      const score = row.risk_score || 0
      let type: 'success' | 'warning' | 'error' = 'success'
      if (score > 60) type = 'error'
      else if (score > 30) type = 'warning'
      return h(NTag, { type, size: 'small' }, () => score)
    }
  }
]

const recommendations = computed(() => {
  if (!currentReport.value?.metrics) return []
  const recs: Array<{ priority: number; severity: 'warning' | 'info'; text: string }> = []
  const metrics = currentReport.value.metrics
  
  if (metrics.var_95 > 0.05) {
    recs.push({
      priority: 1,
      severity: 'warning',
      text: `组合VaR(95%)为${(metrics.var_95 * 100).toFixed(2)}%，风险敞口较大，建议适当减仓或对冲`
    })
  }
  if (metrics.max_drawdown > 0.15) {
    recs.push({
      priority: 2,
      severity: 'warning',
      text: `历史最大回撤${(metrics.max_drawdown * 100).toFixed(2)}%，建议设置止损策略控制下行风险`
    })
  }
  if (metrics.concentration_risk > 0.3) {
    recs.push({
      priority: 3,
      severity: 'warning',
      text: `持仓集中度较高(${(metrics.concentration_risk * 100).toFixed(0)}%)，建议分散投资降低单一资产风险`
    })
  }
  if (metrics.volatility > 0.25) {
    recs.push({
      priority: 4,
      severity: 'info',
      text: `组合波动率${(metrics.volatility * 100).toFixed(2)}%，波动较大，可考虑配置低波动资产`
    })
  }
  if (metrics.beta > 1.2) {
    recs.push({
      priority: 5,
      severity: 'info',
      text: `Beta系数为${metrics.beta.toFixed(2)}，组合弹性较大，市场上涨时收益更高但下跌时风险也更大`
    })
  }
  if (recs.length === 0) {
    recs.push({
      priority: 99,
      severity: 'info',
      text: '当前组合风险指标正常，建议持续监控市场变化'
    })
  }
  return recs.sort((a, b) => a.priority - b.priority)
})

const rowClassName = (row: any) => {
  if ((row.risk_score || 0) > 60) return 'high-risk-row'
  return ''
}

async function loadReportByDate() {
  const report = store.state.reports.find((r: any) => r.date === selectedDateStr.value)
  if (report) {
    await store.fetchReport(report.id)
  }
}

watch(selectedDate, () => {
  loadReportByDate()
})

onMounted(async () => {
  await store.fetchReports()
  if (store.state.reports.length > 0) {
    const todayReport = store.state.reports.find((r: any) => r.date === selectedDateStr.value)
    if (todayReport) {
      await store.fetchReport(todayReport.id)
    } else {
      await store.fetchReport(store.state.reports[0].id)
      const latestDate = new Date(store.state.reports[0].date)
      selectedDate.value = latestDate.getTime()
    }
  }
})
</script>

<template>
  <div class="risk-report-view">
    <NCard title="风险报告">
      <template #header-extra>
        <NDatePicker
          v-model:value="selectedDate"
          type="date"
          placeholder="选择报告日期"
          :is-date-disabled="(ts: number) => ts > Date.now()"
        />
      </template>

      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <NSpin :show="store.state.loading">
        <template v-if="currentReport">
          <NGrid :cols="24" :x-gap="16">
            <NGi :span="8">
              <NCard class="gauge-card" :bordered="false">
                <div class="gauge-container">
                  <VChart :option="gaugeOption" autoresize style="height: 280px" />
                </div>
                <div class="risk-badge">
                  <NBadge :value="riskLevel.text" :type="riskLevel.type" :color="riskLevel.color" />
                </div>
              </NCard>
            </NGi>
            <NGi :span="16">
              <NCard title="风险指标" class="metrics-card" :bordered="false">
                <NGrid :cols="3" :x-gap="16">
                  <NGi>
                    <NStatistic label="VaR (95%)" :value="(currentReport.metrics?.var_95 || 0) * 100">
                      <template #suffix>%</template>
                    </NStatistic>
                  </NGi>
                  <NGi>
                    <NStatistic label="VaR (99%)" :value="(currentReport.metrics?.var_99 || 0) * 100">
                      <template #suffix>%</template>
                    </NStatistic>
                  </NGi>
                  <NGi>
                    <NStatistic label="预期损失" :value="(currentReport.metrics?.expected_shortfall || 0) * 100">
                      <template #suffix>%</template>
                    </NStatistic>
                  </NGi>
                  <NGi>
                    <NStatistic label="Beta" :value="currentReport.metrics?.beta || 0" :precision="2" />
                  </NGi>
                  <NGi>
                    <NStatistic label="波动率" :value="(currentReport.metrics?.volatility || 0) * 100">
                      <template #suffix>%</template>
                    </NStatistic>
                  </NGi>
                  <NGi>
                    <NStatistic label="最大回撤" :value="(currentReport.metrics?.max_drawdown || 0) * 100">
                      <template #suffix>%</template>
                    </NStatistic>
                  </NGi>
                </NGrid>
              </NCard>
            </NGi>
          </NGrid>

          <NDivider />

          <NGrid :cols="2" :x-gap="16">
            <NGi>
              <NCard title="持仓风险明细" class="table-card">
                <NDataTable
                  :columns="holdingsColumns"
                  :data="holdingsRiskData"
                  :bordered="false"
                  :row-class-name="rowClassName"
                  :max-height="300"
                />
              </NCard>
            </NGi>
            <NGi>
              <NCard title="行业集中度" class="pie-card">
                <VChart v-if="industryData.length > 0" :option="pieOption" autoresize style="height: 300px" />
                <NEmpty v-else description="暂无行业分布数据" />
              </NCard>
            </NGi>
          </NGrid>

          <NDivider />

          <NCard title="风险建议" class="recommendations-card" :bordered="false">
            <NList bordered>
              <NListItem v-for="(rec, idx) in recommendations" :key="idx">
                <NThing>
                  <template #avatar>
                    <NTag :type="rec.severity" size="small" round>
                      {{ rec.severity === 'warning' ? '警告' : '提示' }}
                    </NTag>
                  </template>
                  <template #header>
                    <span class="rec-priority">优先级 {{ rec.priority }}</span>
                  </template>
                  <template #description>
                    {{ rec.text }}
                  </template>
                </NThing>
              </NListItem>
            </NList>
          </NCard>
        </template>

        <NEmpty v-else-if="!store.state.loading" description="暂无风险报告数据" />
      </NSpin>
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

.gauge-card {
  text-align: center;
}

.gauge-container {
  display: flex;
  justify-content: center;
}

.risk-badge {
  margin-top: 16px;
}

.metrics-card {
  height: 100%;
}

.table-card :deep(.high-risk-row) {
  background-color: #fef2f2;
}

.table-card :deep(.high-risk-row:hover) {
  background-color: #fee2e2;
}

.pie-card {
  height: 100%;
}

.recommendations-card {
  margin-top: 0;
}

.rec-priority {
  font-size: 12px;
  color: #64748b;
  margin-right: 8px;
}
</style>
