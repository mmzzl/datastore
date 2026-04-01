<template>
  <div class="page">
    <div class="page-header">
      <h1>持仓管理</h1>
      <div class="header-actions">
        <button @click="showTransactions" :disabled="loadingHistory" class="btn btn-info">
          {{ loadingHistory ? '加载中...' : '交易记录' }}
        </button>
        <button v-if="showingTransactions" @click="hideTransactions" class="btn btn-secondary">
          返回当前持仓
        </button>
        <button @click="refresh" :disabled="store.state.loading" class="btn btn-primary">
          {{ store.state.loading ? '刷新中...' : '刷新' }}
        </button>
        <button @click="fetchPortfolio" :disabled="store.state.loading" class="btn btn-secondary">
          查看组合
        </button>
      </div>
    </div>
    
    <div class="error-banner" v-if="store.state.error">
      {{ store.state.error }}
    </div>
    
    <div class="add-form-card">
      <h3>买入</h3>
      <form @submit.prevent="onAddHolding">
        <div class="form-row">
              <div class="input-group">
                <label>代码 (股票/指数/ETF)</label>
                <input
                  v-model="newHolding.code"
                  placeholder="输入6位数字，如 600000、159930"
                  required
                  class="input-code"
                />
              </div>
          <div class="input-group">
            <label>股票名称</label>
            <input 
              v-model="newHolding.name" 
              placeholder="自动获取（可选）" 
              class="input-name"
            />
          </div>
          <div class="input-group">
            <label>买入数量 (100的整数倍)</label>
            <input 
              v-model.number="newHolding.quantity" 
              type="number" 
              placeholder="最低100" 
              min="100"
              step="100"
              required 
              class="input-quantity"
            />
          </div>
          <div class="input-group">
            <label>买入价格</label>
            <input 
              v-model.number="newHolding.average_cost" 
              type="number" 
              placeholder="元" 
              min="0.01"
              step="0.01"
              required 
              class="input-cost"
            />
          </div>
          <button type="submit" :disabled="store.state.loading" class="btn btn-success">
            买入
          </button>
          <button 
            type="button" 
            @click="queryStockName" 
            class="btn btn-secondary query-btn"
            :disabled="queryingName"
            title="查询股票名称"
          >
            {{ queryingName ? '查询中...' : '查名称' }}
          </button>
        </div>
<div class="form-hints">
      <span class="hint-item">💡 输入6位数字后点击"查名称"自动补全代码和名称</span>
      <span class="hint-item">📈 支持股票(600000)、指数(000001)、ETF(510300、159930)</span>
    </div>
      </form>
    </div>
    
    <div class="sell-form-card" v-if="showSellForm">
      <h3>卖出 - {{ sellHolding.code }} {{ sellHolding.name }}</h3>
      <form @submit.prevent="onSellHolding">
        <div class="form-row">
          <div class="input-group">
            <label>可卖数量</label>
            <input :value="sellHolding.availableQty + ' 股'" readonly />
          </div>
          <div class="input-group">
            <label>卖出数量 (100的整数倍)</label>
            <input 
              v-model.number="sellHolding.quantity" 
              type="number" 
              :max="sellHolding.availableQty"
              min="100"
              step="100"
              required 
              class="input-quantity"
            />
          </div>
          <div class="input-group">
            <label>卖出价格 (元)</label>
            <input 
              v-model.number="sellHolding.price" 
              type="number" 
              min="0.01"
              step="0.01"
              required 
              class="input-cost"
            />
          </div>
          <button type="submit" :disabled="store.state.loading" class="btn btn-warning">
            确认卖出
          </button>
          <button type="button" @click="showSellForm = false" class="btn btn-secondary">
            取消
          </button>
        </div>
      </form>
    </div>
    
    <div class="transactions-section" v-if="showingTransactions">
      <div class="section-header">
        <h3>交易记录 ({{ txTotalCount }}条)</h3>
        <div class="header-right">
          <span v-if="realizedPnL !== 0" :class="['pnl-badge', realizedPnL >= 0 ? 'profit' : 'loss']">
            已实现盈亏: {{ realizedPnL >= 0 ? '+' : '' }}¥{{ realizedPnL.toFixed(2) }}
          </span>
          <div class="pagination" v-if="txTotalPages > 1">
            <button @click="goToTxPage(1)" :disabled="txCurrentPage === 1" class="btn btn-sm">首页</button>
            <button @click="goToTxPage(txCurrentPage - 1)" :disabled="txCurrentPage === 1" class="btn btn-sm">上一页</button>
            <span class="page-info">{{ txCurrentPage }} / {{ txTotalPages }}</span>
            <button @click="goToTxPage(txCurrentPage + 1)" :disabled="txCurrentPage >= txTotalPages" class="btn btn-sm">下一页</button>
            <button @click="goToTxPage(txTotalPages)" :disabled="txCurrentPage >= txTotalPages" class="btn btn-sm">末页</button>
          </div>
        </div>
      </div>
      <table class="holdings-table" v-if="transactions.length">
        <thead>
          <tr>
            <th>时间</th>
            <th>代码</th>
            <th>名称</th>
            <th>类型</th>
            <th>数量</th>
            <th>价格</th>
            <th>金额</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tx in transactions" :key="tx._id">
            <td>{{ formatDate(tx.created_at) }}</td>
            <td class="code-cell">{{ tx.code }}</td>
            <td>{{ tx.name || tx.code }}</td>
            <td>
              <span :class="tx.type === 'buy' ? 'type-buy' : 'type-sell'">
                {{ tx.type === 'buy' ? '买入' : '卖出' }}
              </span>
            </td>
            <td class="number-cell">{{ tx.quantity }}</td>
            <td class="number-cell">¥{{ tx.price?.toFixed(2) }}</td>
            <td class="number-cell">¥{{ (tx.quantity * tx.price).toFixed(2) }}</td>
            <td>
              <button @click="deleteTransaction(tx._id)" class="btn btn-danger btn-sm">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <p>暂无交易记录</p>
        <p class="hint">买入股票后会在这里显示</p>
      </div>
    </div>
    
    <div class="holdings-section" v-if="!showingTransactions && store.state.holdings.length">
      <div class="section-header">
        <h3>当前持仓 ({{ store.state.totalCount }}条)</h3>
        <div class="pagination" v-if="store.state.totalPages > 1">
          <button @click="goToPage(1)" :disabled="store.state.currentPage === 1" class="btn btn-sm">首页</button>
          <button @click="goToPage(store.state.currentPage - 1)" :disabled="store.state.currentPage === 1" class="btn btn-sm">上一页</button>
          <span class="page-info">{{ store.state.currentPage }} / {{ store.state.totalPages }}</span>
          <button @click="goToPage(store.state.currentPage + 1)" :disabled="store.state.currentPage >= store.state.totalPages" class="btn btn-sm">下一页</button>
          <button @click="goToPage(store.state.totalPages)" :disabled="store.state.currentPage >= store.state.totalPages" class="btn btn-sm">末页</button>
        </div>
      </div>
      <table class="holdings-table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th>数量</th>
            <th>成本价</th>
            <th>成本总额</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in store.state.holdings" :key="h.code">
            <td class="code-cell link-cell" @click="showKline(h.code, h.name)">{{ h.code }}</td>
            <td>{{ h.name || h.code }}</td>
            <td class="number-cell">{{ h.quantity }}</td>
            <td class="number-cell">¥{{ h.average_cost?.toFixed(2) }}</td>
            <td class="number-cell">¥{{ (h.quantity * h.average_cost).toFixed(2) }}</td>
            <td>
              <button @click="showKline(h.code, h.name)" class="btn btn-primary btn-sm">
                K线
              </button>
              <button @click="openSellForm(h)" class="btn btn-warning btn-sm">
                卖出
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="empty-state" v-else-if="!store.state.loading && !showingTransactions">
      <p>暂无持仓数据</p>
      <p class="hint">请在上方买入股票</p>
    </div>
    
    <div class="empty-state" v-else-if="showingTransactions && !transactions.length && !loadingHistory">
      <p>暂无交易记录</p>
    </div>
    
    <div class="portfolio-section" v-if="portfolio">
      <h3>组合概览</h3>
      <div class="portfolio-stats">
        <div class="stat-item">
          <span class="label">总市值</span>
          <span class="value">¥{{ store.state.marketValue.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">总成本</span>
          <span class="value">¥{{ store.state.totalCost.toFixed(2) }}</span>
        </div>
        <div class="stat-item">
          <span class="label">已实现盈亏</span>
          <span class="value" :class="realizedPnL >= 0 ? 'profit' : 'loss'">
            {{ realizedPnL >= 0 ? '+' : '' }}¥{{ realizedPnL.toFixed(2) }}
          </span>
        </div>
        <div class="stat-item">
          <span class="label">总盈亏</span>
          <span class="value" :class="store.state.unrealizedPnL >= 0 ? 'profit' : 'loss'">
            {{ store.state.unrealizedPnL >= 0 ? '+' : '' }}¥{{ store.state.unrealizedPnL.toFixed(2) }}
          </span>
        </div>
        <div class="stat-item">
          <span class="label">盈亏比例</span>
          <span class="value" :class="store.state.profitRate >= 0 ? 'profit' : 'loss'">
            {{ (store.state.profitRate * 100).toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
  </div>

  <div class="kline-modal" v-if="showKlineModal" @click.self="closeKlineModal">
    <div class="kline-modal-content">
      <div class="kline-modal-header">
        <h3>{{ klineName }} ({{ klineCode }})</h3>
        <button @click="closeKlineModal" class="btn btn-secondary btn-sm">关闭</button>
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
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useHoldingsStore } from '../stores/holdings'
import { authService, apiHoldings, apiSignals, apiStocks } from '../services/api'
import * as echarts from 'echarts'

const store = useHoldingsStore()
const userId = ref(authService.getUser())
const portfolio = ref(false)
const newHolding = ref({ code: '', name: '', quantity: 0, average_cost: 0 })
const queryingName = ref(false)
const showingTransactions = ref(false)
const transactions = ref<any[]>([])
const loadingHistory = ref(false)
const showSellForm = ref(false)
const sellHolding = ref({ code: '', name: '', availableQty: 0, quantity: 0, price: 0 })
const realizedPnL = ref(0)
const showKlineModal = ref(false)
const klineCode = ref('')
const klineName = ref('')
const klineData = ref<any[]>([])
const loadingKline = ref(false)
const klineChartRef = ref<HTMLElement | null>(null)
let klineChart: echarts.ECharts | null = null
const txCurrentPage = ref(1)
const txTotalPages = ref(0)
const txTotalCount = ref(0)
const txPageSize = 10

async function showKline(code: string, name: string) {
  klineCode.value = code
  klineName.value = name || code
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
      text: `${klineName.value} (${klineCode.value})`,
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

async function queryStockName() {
  const code = newHolding.value.code.trim()
  if (!code) {
    alert('请先输入代码')
    return
  }

  queryingName.value = true
  try {
    const res = await apiStocks.searchStocks(code, 10)
    if (res.success && res.data && res.data.length > 0) {
      const firstMatch = res.data[0]
      newHolding.value.name = firstMatch.name
      newHolding.value.code = firstMatch.code
      alert(`查询成功：${firstMatch.code} - ${firstMatch.name}`)
    } else {
      alert(`未找到代码 ${code} 的信息，请手动输入名称`)
    }
  } catch (e: any) {
    console.error('查询名称失败:', e)
    alert('查询名称失败，请手动输入')
  } finally {
    queryingName.value = false
  }
}

async function fetchHoldings() {
  await store.fetchHoldings(userId.value)
}

async function fetchPortfolio() {
  await store.refreshPortfolio(userId.value)
}

async function goToPage(page: number) {
  if (page < 1 || page > store.state.totalPages) return
  await store.fetchHoldings(userId.value, page)
}

async function showTransactions() {
  txCurrentPage.value = 1
  loadingHistory.value = true
  showingTransactions.value = true
  try {
    const res = await apiHoldings.getTransactions(userId.value, undefined, 1, txPageSize)
    transactions.value = res.items || []
    txTotalPages.value = res.total_pages || 0
    txTotalCount.value = res.total || 0
    // 获取已实现盈亏
    const pnl = await apiHoldings.getRealizedPnL(userId.value)
    realizedPnL.value = pnl?.realized_pnl || 0
  } catch (e: any) {
    alert('加载交易记录失败')
  } finally {
    loadingHistory.value = false
  }
}

async function goToTxPage(page: number) {
  if (page < 1 || page > txTotalPages.value) return
  txCurrentPage.value = page
  loadingHistory.value = true
  try {
    const res = await apiHoldings.getTransactions(userId.value, undefined, page, txPageSize)
    transactions.value = res.items || []
    txTotalPages.value = res.total_pages || 0
  } catch (e: any) {
    alert('加载交易记录失败')
  } finally {
    loadingHistory.value = false
  }
}

async function deleteTransaction(transactionId: string) {
  if (!confirm('确定删除这条交易记录？\n注意：这会影响成本和盈亏计算')) return
  try {
    await apiHoldings.deleteTransaction(userId.value, transactionId)
    await showTransactions()
    await fetchHoldings()
    alert('删除成功')
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function hideTransactions() {
  showingTransactions.value = false
  transactions.value = []
}

async function onAddHolding() {
  if (!newHolding.value.code) {
    alert('请输入代码')
    return
  }
  if (!newHolding.value.quantity || newHolding.value.quantity < 100) {
    alert('买入数量不能少于100股')
    return
  }
  if (newHolding.value.quantity % 100 !== 0) {
    alert('买入数量必须是100的整数倍')
    return
  }
  if (!newHolding.value.average_cost || newHolding.value.average_cost <= 0) {
    alert('请输入有效的买入价格')
    return
  }
  
  try {
    await store.saveHolding(
      userId.value,
      newHolding.value.code,
      newHolding.value.name,
      newHolding.value.quantity,
      newHolding.value.average_cost
    )
    alert('买入成功')
    newHolding.value = { code: '', name: '', quantity: 0, average_cost: 0 }
    await fetchHoldings()
    await fetchPortfolio()
  } catch (e: any) {
    alert(e.message || '买入失败')
  }
}

function openSellForm(holding: any) {
  sellHolding.value = {
    code: holding.code,
    name: holding.name || holding.code,
    availableQty: holding.quantity,
    quantity: holding.quantity,
    price: holding.average_cost
  }
  showSellForm.value = true
}

async function onSellHolding() {
  // 校验数量（A股最低100股，且必须是100的整数倍）
  if (sellHolding.value.quantity < 100) {
    alert('卖出数量不能少于100股！\nA股买卖最低为100股')
    return
  }
  if (sellHolding.value.quantity % 100 !== 0) {
    alert('卖出数量必须是100的整数倍！')
    return
  }
  if (sellHolding.value.quantity > sellHolding.value.availableQty) {
    alert('卖出数量不能超过可卖数量')
    return
  }
  try {
    await store.saveHolding(
      userId.value,
      sellHolding.value.code,
      sellHolding.value.name,
      -sellHolding.value.quantity,
      sellHolding.value.price
    )
    showSellForm.value = false
    alert('卖出成功')
    await fetchHoldings()
    await fetchPortfolio()
  } catch (e: any) {
    alert(e.message || '卖出失败')
  }
}

function refresh() {
  if (showingTransactions.value) {
    showTransactions()
  } else {
    fetchHoldings()
  }
  if (portfolio.value) {
    fetchPortfolio()
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

onMounted(() => {
  portfolio.value = true
  fetchHoldings()
  fetchPortfolio()
})
</script>

<style scoped>
.page { padding: 24px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-primary { background: #3b82f6; color: white; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-secondary:hover:not(:disabled) { background: #cbd5e1; }
.btn-success { background: #10b981; color: white; }
.btn-success:hover:not(:disabled) { background: #059669; }
.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
.add-form-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.add-form-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1e293b;
}
.form-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.input-group label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}
.form-row input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.form-row input:focus {
  outline: none;
  border-color: #3b82f6;
}
.query-btn {
  padding: 8px 16px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.2s;
}
.query-btn:hover:not(:disabled) {
  background: #4f46e5;
}
.query-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.input-code {
  width: 220px;
  font-family: monospace;
}
.input-name {
  width: 200px;
}
.input-quantity { width: 120px; }
.input-cost { width: 120px; }
.form-hints {
  margin-top: 16px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.hint-item {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}
.hint-item:last-child {
  margin-bottom: 0;
}
.holdings-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.holdings-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.holdings-section h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pagination .btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}
.pagination .page-info {
  padding: 6px 12px;
  font-size: 14px;
  color: #64748b;
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
.status-holding {
  color: #059669;
  font-weight: 600;
}
.status-sold {
  color: #dc2626;
  font-weight: 600;
}
.empty-state {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}
.empty-state p { margin: 0; }
.empty-state .hint {
  font-size: 14px;
  margin-top: 8px;
}
.portfolio-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.portfolio-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1e293b;
}
.portfolio-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-item .label {
  font-size: 13px;
  color: #64748b;
}
.stat-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}
.stat-item .value.profit { color: #059669; }
.stat-item .value.loss { color: #dc2626; }
.btn-info {
  background: #8b5cf6;
  color: white;
}
.btn-info:hover:not(:disabled) {
  background: #7c3aed;
}
.btn-warning {
  background: #f59e0b;
  color: white;
}
.btn-warning:hover:not(:disabled) {
  background: #d97706;
}
.sell-form-card {
  background: #fef3c7;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.sell-form-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #92400e;
}
.transactions-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}
.section-header .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.pnl-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}
.pnl-badge.profit {
  background: #dcfce7;
  color: #16a34a;
}
.pnl-badge.loss {
  background: #fee2e2;
  color: #dc2626;
}
.type-buy {
  color: #059669;
  font-weight: 600;
}
.type-sell {
  color: #dc2626;
  font-weight: 600;
}
.link-cell {
  cursor: pointer;
  color: #3b82f6;
}
.link-cell:hover {
  text-decoration: underline;
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