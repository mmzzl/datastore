<template>
  <div class="page dashboard">
    <div class="page-header">
      <h1>仪表盘</h1>
      <button @click="refresh" :disabled="dashboard.state.loading" class="refresh-btn">
        {{ dashboard.state.loading ? '刷新中...' : '刷新数据' }}
      </button>
    </div>
    
    <div class="error-banner" v-if="dashboard.state.error">
      {{ dashboard.state.error }}
    </div>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon holdings">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">持仓数量</div>
          <div class="stat-value">{{ dashboard.state.holdingsCount }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon cost">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">总成本</div>
          <div class="stat-value">¥{{ dashboard.state.totalCost.toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon value">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">市值</div>
          <div class="stat-value">¥{{ dashboard.state.marketValue.toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" :class="dashboard.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">未实现盈亏</div>
          <div class="stat-value" :class="dashboard.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
            {{ dashboard.state.unrealizedPnL >= 0 ? '+' : '' }}¥{{ dashboard.state.unrealizedPnL.toFixed(2) }}
            <span class="stat-rate">({{ (dashboard.state.profitRate * 100).toFixed(2) }}%)</span>
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" :class="dashboard.state.realizedPnL >= 0 ? 'profit' : 'loss'">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">已实现盈亏</div>
          <div class="stat-value" :class="dashboard.state.realizedPnL >= 0 ? 'profit' : 'loss'">
            {{ dashboard.state.realizedPnL >= 0 ? '+' : '' }}¥{{ dashboard.state.realizedPnL.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>

    <div class="section" v-if="dashboard.state.holdings.length > 0">
      <div class="section-header">
        <h2>持仓明细</h2>
      </div>
      <table class="holdings-table">
      <thead>
        <tr>
          <th>名称</th>
          <th>数量</th>
          <th>成本价</th>
          <th>现价</th>
          <th>市值</th>
          <th>盈亏</th>
          <th>盈亏%</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in dashboard.state.holdings" :key="h.code">
          <td class="name-cell link-cell" @click="showKline(h.code)">{{ h.name || h.code }}</td>
          <td class="number-cell">{{ h.quantity }}</td>
          <td class="number-cell">¥{{ h.average_cost?.toFixed(2) }}</td>
          <td class="number-cell" :class="h.change >= 0 ? 'profit' : 'loss'">
            {{ h.current_price?.toFixed(2) || '-' }}
            <span v-if="h.change !== undefined" class="change-badge">
              {{ h.change >= 0 ? '+' : '' }}{{ h.change_pct?.toFixed(2) }}%
            </span>
          </td>
          <td class="number-cell">¥{{ h.market_value?.toFixed(2) || '-' }}</td>
          <td class="number-cell" :class="h.profit >= 0 ? 'profit' : 'loss'">
            {{ h.profit !== undefined ? (h.profit >= 0 ? '+' : '') + '¥' + h.profit?.toFixed(2) : '-' }}
          </td>
          <td class="number-cell" :class="h.profit_pct >= 0 ? 'profit' : 'loss'">
            {{ h.profit_pct !== undefined ? (h.profit_pct >= 0 ? '+' : '') + h.profit_pct?.toFixed(2) + '%' : '-' }}
          </td>
          <td>
            <button @click="showKline(h.code)" class="btn-kline">K线</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-header">
        <h2>最近信号</h2>
        <router-link to="/market-watch" class="link">查看全部</router-link>
      </div>
      <div class="signal-count">
        <span class="count">{{ dashboard.state.signalCount }}</span>
        <span class="label">条信号</span>
      </div>
    </div>
    
    <div class="section">
      <div class="section-header">
        <h2>快速操作</h2>
      </div>
      <div class="quick-actions">
        <router-link to="/holdings" class="action-btn">
          <span class="icon">📝</span>
          <span>管理持仓</span>
        </router-link>
        <router-link to="/settings" class="action-btn">
          <span class="icon">⚙️</span>
          <span>系统设置</span>
        </router-link>
      </div>
    </div>
    
<div class="last-update" v-if="dashboard.state.lastUpdated">
    最后更新: {{ dashboard.state.lastUpdated.toLocaleString() }}
  </div>

  <div class="kline-modal" v-if="showKlineModal" @click.self="closeKlineModal">
    <div class="kline-modal-content">
      <div class="kline-modal-header">
        <h3>{{ klineCode }}</h3>
        <button @click="closeKlineModal" class="btn-close">关闭</button>
      </div>
        <div class="kline-modal-body">
          <div v-if="loadingKline" class="loading-state">加载中...</div>
          <div v-else-if="klineData.length === 0" class="empty-state">暂无K线数据</div>
          <div v-else class="kline-chart-container">
            <div ref="klineChartRef" class="kline-chart" style="width: 100%; height: 450px;"></div>
          </div>
        </div>
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { onMounted, onActivated, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'
import * as echarts from 'echarts'

const dashboard = useDashboardStore()
const route = useRoute()

let refreshTimer: number | null = null
const showKlineModal = ref(false)
const klineCode = ref('')
const klineData = ref<any[]>([])
const loadingKline = ref(false)
const klineChartRef = ref<HTMLElement | null>(null)
let klineChart: echarts.ECharts | null = null

function refresh() {
  dashboard.fetchSummary()
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = window.setInterval(() => {
    dashboard.fetchSummary()
  }, 5 * 60 * 1000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

async function showKline(code: string) {
  klineCode.value = code
  showKlineModal.value = true
  loadingKline.value = true
  klineData.value = []
  
  try {
    const pureCode = code.replace(/^(SH|SZ|sh|sz)/, '')
    const res = await fetch(`/api/stock/kline/${pureCode}?limit=120`)
    const data = await res.json()
    if (data.success && data.data) {
      klineData.value = data.data.reverse()
      loadingKline.value = false
      await nextTick()
      setTimeout(() => renderKlineChart(), 100)
    }
  } catch (e) {
    console.error('获取K线数据失败:', e)
    loadingKline.value = false
  }
}

function renderKlineChart() {
  if (!klineChartRef.value || klineData.value.length === 0) return
  
  if (klineChart) {
    klineChart.dispose()
  }
  
  klineChart = echarts.init(klineChartRef.value)
  
  const dates = klineData.value.map(d => d.date)
  const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = klineData.value.map(d => d.volume)
  const closes = klineData.value.map(d => d.close)
  
  const ma5 = calculateMA(5, closes)
  const ma10 = calculateMA(10, closes)
  const ma20 = calculateMA(20, closes)
  
  const option = {
    title: {
      text: klineCode.value,
      left: 'center',
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: function(params: any) {
        const data = klineData.value[params[0].dataIndex]
        const vol = params.find((p: any) => p.seriesType === 'bar')
        let result = `日期: ${data.date}<br/>`
        result += `开盘: ${data.open?.toFixed(2)}<br/>`
        result += `收盘: ${data.close?.toFixed(2)}<br/>`
        result += `最高: ${data.high?.toFixed(2)}<br/>`
        result += `最低: ${data.low?.toFixed(2)}<br/>`
        if (vol) result += `成交量: ${(vol.data / 10000).toFixed(2)}万<br/>`
        result += `MA5: ${ma5[params[0].dataIndex]?.toFixed(2) || '-'}<br/>`
        result += `MA10: ${ma10[params[0].dataIndex]?.toFixed(2) || '-'}<br/>`
        result += `MA20: ${ma20[params[0].dataIndex]?.toFixed(2) || '-'}`
        return result
      }
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', '成交量'],
      bottom: 10
    },
    grid: [
      { left: '10%', right: '8%', top: '15%', height: '50%' },
      { left: '10%', right: '8%', top: '70%', height: '15%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', fontSize: 10 }
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666' },
        splitLine: { lineStyle: { color: '#eee' } }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLine: { lineStyle: { color: '#ccc' } },
        axisLabel: { color: '#666', formatter: (val: number) => (val / 10000).toFixed(0) + '万' },
        splitLine: { lineStyle: { color: '#eee' } }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 40, start: 50, end: 100 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        smooth: true,
        lineStyle: { width: 1 },
        symbol: 'none',
        itemStyle: { color: '#f5a623' }
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10,
        smooth: true,
        lineStyle: { width: 1 },
        symbol: 'none',
        itemStyle: { color: '#7b68ee' }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        smooth: true,
        lineStyle: { width: 1 },
        symbol: 'none',
        itemStyle: { color: '#16a085' }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params: any) {
            const idx = params.dataIndex
            if (idx === 0) return '#ccc'
            const prev = klineData.value[idx - 1]
            const curr = klineData.value[idx]
            return curr.close >= prev.close ? '#ef5350' : '#26a69a'
          }
        }
      }
    ]
  }
  
  klineChart.setOption(option)
}

function calculateMA(dayCount: number, data: number[]) {
  const result: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < dayCount; j++) {
        sum += data[i - j]
      }
      result.push(sum / dayCount)
    }
  }
  return result
}

function closeKlineModal() {
  showKlineModal.value = false
  klineData.value = []
  if (klineChart) {
    klineChart.dispose()
    klineChart = null
  }
}

onMounted(() => {
  dashboard.fetchSummary()
  startAutoRefresh()
  window.addEventListener('dashboard-refresh', handleRefresh)
})

onActivated(() => {
  dashboard.fetchSummary()
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('dashboard-refresh', handleRefresh)
})

function handleRefresh() {
  dashboard.fetchSummary()
}
</script>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1200px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
}
.refresh-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.refresh-btn:hover:not(:disabled) {
  background: #2563eb;
}
.refresh-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.stat-icon.holdings { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.stat-icon.cost { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
.stat-icon.value { background: linear-gradient(135deg, #06b6d4, #0891b2); }
.stat-icon.profit { background: linear-gradient(135deg, #10b981, #059669); }
.stat-icon.loss { background: linear-gradient(135deg, #ef4444, #dc2626); }
.stat-content {
  flex: 1;
}
.stat-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}
.stat-value.profit { color: #059669; }
.stat-value.loss { color: #dc2626; }
.stat-rate {
  font-size: 14px;
  font-weight: 400;
}
.section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 14px;
}
.link:hover {
  text-decoration: underline;
}
.signal-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.signal-count .count {
  font-size: 36px;
  font-weight: 700;
  color: #1e293b;
}
.signal-count .label {
  font-size: 16px;
  color: #64748b;
}
.quick-actions {
  display: flex;
  gap: 12px;
}
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f1f5f9;
  border-radius: 8px;
  text-decoration: none;
  color: #1e293b;
  font-weight: 500;
  transition: all 0.2s;
}
.action-btn:hover {
  background: #e2e8f0;
}
.action-btn .icon {
  font-size: 20px;
}
.last-update {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 16px;
}
.holdings-table {
  width: 100%;
  border-collapse: collapse;
}
.holdings-table th,
.holdings-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}
.holdings-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.holdings-table td {
  color: #1e293b;
}
.code-cell {
  font-family: monospace;
  font-weight: 600;
}
.number-cell {
  text-align: right;
  font-family: monospace;
}
.number-cell.profit {
  color: #059669;
}
.number-cell.loss {
  color: #dc2626;
}
.change-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 4px;
  background: #f1f5f9;
}
.number-cell.profit .change-badge {
  background: #dcfce7;
  color: #059669;
}
.number-cell.loss .change-badge {
  background: #fee2e2;
  color: #dc2626;
}
.link-cell {
  cursor: pointer;
  color: #3b82f6;
}
.link-cell:hover {
  text-decoration: underline;
}
.btn-kline {
  padding: 4px 10px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-kline:hover {
  background: #2563eb;
}
.kline-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.kline-modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.kline-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.kline-modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}
.btn-close {
  padding: 6px 12px;
  background: #e2e8f0;
  color: #475569;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.btn-close:hover {
  background: #cbd5e1;
}
.kline-modal-body {
  padding: 20px;
  overflow-y: auto;
}
.loading-state {
  text-align: center;
  padding: 40px;
  color: #64748b;
}
.kline-chart-container {
  width: 100%;
  height: 450px;
}
.kline-chart {
  width: 100%;
  height: 100%;
}
</style>