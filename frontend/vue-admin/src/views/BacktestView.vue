<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useBacktestStore } from '../stores/backtest'
import {
  NCard, NButton, NDataTable, NSpin, NAlert, NTag, NDatePicker,
  NInputNumber, NSpace, NSelect, NForm, NFormItem, NProgress,
  NGrid, NGi, NStatistic, NDivider
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DataZoomComponent
} from 'echarts/components'
import { apiPlugins } from '../services/api_plugins'

use([
  CanvasRenderer, LineChart, TitleComponent, TooltipComponent,
  LegendComponent, GridComponent, DataZoomComponent
])

const store = useBacktestStore()

const baseStrategyOptions = [
  { label: 'MA Cross', value: 'ma_cross' },
  { label: 'RSI', value: 'rsi' },
  { label: 'Bollinger', value: 'bollinger' },
  { label: 'MACD', value: 'macd' },
  { label: 'Qlib Model', value: 'qlib_model' },
  { label: 'Plugin', value: 'plugin' },
]

const strategyOptions = ref([...baseStrategyOptions])
const plugins = ref<any[]>([])
const selectedStrategy = ref('ma_cross')
const selectedPlugin = ref('')
const dateRange = ref<[number, number] | null>(null)
const initialCapital = ref(100000)

const strategyParams = ref<Record<string, any>>({
  ma_cross: { fast_period: 5, slow_period: 20 },
  rsi: { period: 14, oversold: 30, overbought: 70 },
  bollinger: { period: 20, num_std: 2 },
  macd: { fast_period: 12, slow_period: 26, signal_period: 9 },
  qlib_model: { model_id: '', topk: 50 },
  plugin: { plugin_id: '', custom_params: {} },
})

const currentParams = computed(() => strategyParams.value[selectedStrategy.value] || {})

const isRunning = computed(() => store.state.status === 'running' || store.state.status === 'pending')
const canStart = computed(() => {
  if (!dateRange.value) return false
  const [start, end] = dateRange.value
  if (start >= end) return false
  if (selectedStrategy.value === 'plugin' && !selectedPlugin.value) return false
  return true
})

const loadPlugins = async () => {
  try {
    const res = await apiPlugins.getPlugins()
    plugins.value = res.items
  } catch (e) {
    console.error('Failed to load plugins:', e)
  }
}

watch(selectedPlugin, (newPluginId) => {
  if (newPluginId) {
    strategyParams.value.plugin.plugin_id = newPluginId
  }
})

watch(selectedStrategy, async (newStrategy) => {
  if (newStrategy === 'plugin') {
    await loadPlugins()
  }
})

const returnChartOption = computed(() => {
  const result = store.state.currentBacktest
  if (!result || !result.trades?.length) {
    return {
      title: { text: '收益曲线', left: 'center' },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [] }],
    }
  }
  const trades = result.trades
  let portfolioValue = result.initial_capital
  const dates: string[] = [trades[0].date]
  const values: number[] = [portfolioValue]
  for (const trade of trades) {
    if (trade.action === 'buy') {
      portfolioValue -= trade.amount
    } else {
      portfolioValue += trade.amount
    }
    dates.push(trade.date)
    values.push(portfolioValue)
  }
  dates.push(result.end_date)
  values.push(result.final_capital)
  return {
    title: { text: '收益曲线', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value', name: '组合价值' },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      areaStyle: { opacity: 0.3 },
    }],
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
  }
})

const drawdownChartOption = computed(() => {
  const result = store.state.currentBacktest
  if (!result) {
    return {
      title: { text: '回撤曲线', left: 'center' },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [] }],
    }
  }
  const maxDrawdown = result.max_drawdown
  const dates = ['start', 'peak', 'trough', 'end']
  const values = [0, 0, -maxDrawdown * 100, -maxDrawdown * 100 * 0.5]
  return {
    title: { text: '回撤曲线', left: 'center' },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '回撤(%)', max: 0 },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      itemStyle: { color: '#ef4444' },
      areaStyle: { color: 'rgba(239, 68, 68, 0.3)' },
    }],
  }
})

const riskMetrics = computed(() => {
  const result = store.state.currentBacktest
  if (!result) return null
  return {
    totalReturn: result.total_return,
    annualReturn: result.annual_return,
    sharpeRatio: result.sharpe_ratio,
    maxDrawdown: result.max_drawdown,
    winRate: result.win_rate,
    numTrades: result.trades?.length || 0,
  }
})

async function handleStartBacktest() {
  if (!canStart.value || !dateRange.value) return
  const [start, end] = dateRange.value
  const params = { ...currentParams.value }
  if (selectedStrategy.value === 'qlib_model') {
    params.model_id = params.model_id || ''
  }
  try {
    const backtestId = await store.startBacktest({
      strategy: selectedStrategy.value,
      ...params,
      start_date: new Date(start).toISOString().split('T')[0],
      end_date: new Date(end).toISOString().split('T')[0],
      initial_capital: initialCapital.value,
    })
    store.connectWebSocket(backtestId)
  } catch (e) {
    console.error('Failed to start backtest:', e)
  }
}

const columns: DataTableColumns = [
  { title: '策略', key: 'strategy' },
  { title: '开始日期', key: 'start_date' },
  { title: '结束日期', key: 'end_date' },
  { title: '初始资金', key: 'initial_capital' },
  { title: '最终资金', key: 'final_capital' },
  { title: '总收益', key: 'total_return' },
  { title: '夏普比率', key: 'sharpe_ratio' },
  { title: '最大回撤', key: 'max_drawdown' },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => {
      const statusMap: Record<string, { type: 'success' | 'warning' | 'error' | 'info', text: string }> = {
        pending: { type: 'warning', text: '等待中' },
        running: { type: 'info', text: '运行中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' },
      }
      const s = statusMap[row.status] || { type: 'info', text: row.status }
      return h(NTag, { type: s.type }, () => s.text)
    }
  },
]

import { h } from 'vue'

onMounted(async () => {
  await store.fetchResults()
})

onUnmounted(() => {
  store.disconnectWebSocket()
})
</script>

<template>
  <div class="backtest-view">
    <NCard title="回测配置" class="config-card">
      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <NForm label-placement="left" label-width="80">
        <NFormItem label="策略选择">
          <NSelect
            v-model:value="selectedStrategy"
            :options="strategyOptions"
            style="width: 200px"
            :disabled="isRunning"
          />
        </NFormItem>

        <NFormItem label="参数配置">
          <div class="params-form">
            <template v-if="selectedStrategy === 'ma_cross'">
              <NInputNumber
                v-model:value="strategyParams.ma_cross.fast_period"
                :min="1"
                placeholder="快线周期"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.ma_cross.slow_period"
                :min="1"
                placeholder="慢线周期"
                :disabled="isRunning"
              />
            </template>
            <template v-else-if="selectedStrategy === 'rsi'">
              <NInputNumber
                v-model:value="strategyParams.rsi.period"
                :min="1"
                placeholder="周期"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.rsi.oversold"
                :min="0"
                :max="50"
                placeholder="超卖阈值"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.rsi.overbought"
                :min="50"
                :max="100"
                placeholder="超买阈值"
                :disabled="isRunning"
              />
            </template>
            <template v-else-if="selectedStrategy === 'bollinger'">
              <NInputNumber
                v-model:value="strategyParams.bollinger.period"
                :min="1"
                placeholder="周期"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.bollinger.num_std"
                :min="0.5"
                :step="0.5"
                placeholder="标准差倍数"
                :disabled="isRunning"
              />
            </template>
            <template v-else-if="selectedStrategy === 'macd'">
              <NInputNumber
                v-model:value="strategyParams.macd.fast_period"
                :min="1"
                placeholder="快线周期"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.macd.slow_period"
                :min="1"
                placeholder="慢线周期"
                :disabled="isRunning"
              />
              <NInputNumber
                v-model:value="strategyParams.macd.signal_period"
                :min="1"
                placeholder="信号线周期"
                :disabled="isRunning"
              />
            </template>
            <template v-else-if="selectedStrategy === 'qlib_model'">
              <NInputNumber
                v-model:value="strategyParams.qlib_model.topk"
                :min="1"
                placeholder="TopK"
                :disabled="isRunning"
              />
            </template>
            <template v-else-if="selectedStrategy === 'plugin'">
              <NSelect
                v-model:value="selectedPlugin"
                :options="plugins.map(p => ({ label: p.name, value: p.id }))"
                placeholder="选择插件"
                style="width: 200px"
                :disabled="isRunning"
              />
            </template>
          </div>
        </NFormItem>

        <NFormItem label="日期范围">
          <NDatePicker
            v-model:value="dateRange"
            type="daterange"
            placeholder="选择日期范围"
            :disabled="isRunning"
          />
        </NFormItem>

        <NFormItem label="初始资金">
          <NInputNumber
            v-model:value="initialCapital"
            :min="1000"
            :step="10000"
            placeholder="初始资金"
            :disabled="isRunning"
          >
            <template #prefix>¥</template>
          </NInputNumber>
        </NFormItem>

        <NFormItem label=" ">
          <NButton
            type="primary"
            :loading="isRunning"
            :disabled="!canStart"
            @click="handleStartBacktest"
          >
            开始回测
          </NButton>
          <NButton
            v-if="isRunning"
            type="warning"
            @click="store.disconnectWebSocket"
            class="ml-2"
          >
            取消
          </NButton>
        </NFormItem>
      </NForm>

      <div v-if="isRunning" class="progress-section">
        <NProgress
          type="line"
          :percentage="store.state.progress"
          :indicator-placement="'inside'"
          processing
        />
        <div class="progress-info">
          <NTag :type="store.state.wsConnected ? 'success' : 'warning'">
            {{ store.state.wsConnected ? 'WebSocket 已连接' : 'WebSocket 断开' }}
          </NTag>
        </div>
      </div>
    </NCard>

    <NCard v-if="store.state.currentBacktest" title="回测结果" class="results-card">
      <NGrid :cols="6" :x-gap="16">
        <NGi>
          <NStatistic label="总收益" :value="riskMetrics?.totalReturn ?? 0">
            <template #suffix>%</template>
          </NStatistic>
        </NGi>
        <NGi>
          <NStatistic label="年化收益" :value="riskMetrics?.annualReturn ?? 0">
            <template #suffix>%</template>
          </NStatistic>
        </NGi>
        <NGi>
          <NStatistic label="夏普比率" :value="riskMetrics?.sharpeRatio ?? 0" />
        </NGi>
        <NGi>
          <NStatistic label="最大回撤" :value="riskMetrics?.maxDrawdown ?? 0">
            <template #suffix>%</template>
          </NStatistic>
        </NGi>
        <NGi>
          <NStatistic label="胜率" :value="riskMetrics?.winRate ?? 0">
            <template #suffix>%</template>
          </NStatistic>
        </NGi>
        <NGi>
          <NStatistic label="交易次数" :value="riskMetrics?.numTrades ?? 0" />
        </NGi>
      </NGrid>

      <NDivider />

      <NGrid :cols="2" :x-gap="16">
        <NGi>
          <VChart :option="returnChartOption" autoresize style="height: 300px" />
        </NGi>
        <NGi>
          <VChart :option="drawdownChartOption" autoresize style="height: 300px" />
        </NGi>
      </NGrid>
    </NCard>

    <NCard title="历史回测" class="history-card">
      <NSpin :show="store.state.loading">
        <NDataTable
          :columns="columns"
          :data="store.state.results"
          :bordered="false"
          :row-key="(row: any) => row.id"
        />
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.backtest-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.config-card, .results-card, .history-card {
  margin-bottom: 0;
}
.params-form {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.progress-section {
  margin-top: 16px;
}
.progress-info {
  margin-top: 8px;
}
.mb-4 {
  margin-bottom: 16px;
}
.ml-2 {
  margin-left: 8px;
}
</style>
