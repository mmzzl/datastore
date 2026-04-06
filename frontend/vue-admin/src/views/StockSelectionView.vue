<template>
  <div class="stock-selection-view">
    <NCard title="策略选股">
      <template #header-extra>
        <NSpace>
          <NButton type="primary" @click="showDialog = true">
            开始选股
          </NButton>
          <NButton @click="loadHistory">
            刷新历史
          </NButton>
        </NSpace>
      </template>

      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <!-- Current Result -->
      <template v-if="store.state.currentResult && store.state.currentResult.status === 'completed'">
        <!-- Market Trend Section -->
        <div v-if="store.state.currentResult.market_trend" class="market-trend-section mb-4">
          <div class="section-title">
            <span>📊 市场趋势分析</span>
          </div>
          <NCard size="small" :bordered="false" class="trend-card">
            <div class="trend-header">
              <span class="trend-direction">
                趋势方向: <NTag :type="trendColor">{{ trendData?.trend_direction }}</NTag>
              </span>
              <span class="trend-strength">
                强度: <NTag :type="strengthColor">{{ trendData?.trend_strength }}</NTag>
              </span>
            </div>

            <div class="trend-stats">
              <div class="stat-group">
                <span class="stat-label">金叉统计:</span>
                <span class="stat-value">
                  MACD金叉: {{ trendData?.macd_golden_cross_count }}只 ({{ trendData?.macd_golden_cross_ratio }}%)
                </span>
                <span class="stat-value">
                  均线金叉: {{ trendData?.ma_golden_cross_count }}只 ({{ trendData?.ma_golden_cross_ratio }}%)
                </span>
              </div>

              <div class="stat-group">
                <span class="stat-label">多头排列:</span>
                <span class="stat-value">
                  完整多头: {{ trendData?.full_bullish_alignment_count }}只 ({{ trendData?.full_bullish_alignment_ratio }}%)
                </span>
              </div>

              <div class="stat-group">
                <span class="stat-label">RSI分布:</span>
                <span class="stat-value">
                  超卖 {{ trendData?.rsi_oversold_count }}只 |
                  中性 {{ trendData?.rsi_neutral_count }}只 |
                  超买 {{ trendData?.rsi_overbought_count }}只
                </span>
              </div>
            </div>
          </NCard>
        </div>

        <!-- Sector Overview -->
        <div v-if="store.state.currentResult.sector_overview" class="section mb-4">
          <div class="section-title">🏭 板块概览</div>
          <NCard size="small" :bordered="false">
            {{ store.state.currentResult.sector_overview }}
          </NCard>
        </div>

        <!-- Market Risk -->
        <div v-if="store.state.currentResult.market_risk" class="section mb-4">
          <div class="section-title">⚠️ 市场风险提示</div>
          <NCard size="small" :bordered="false">
            {{ store.state.currentResult.market_risk }}
          </NCard>
        </div>

        <!-- AI Summary -->
        <div v-if="store.state.currentResult.ai_summary" class="section mb-4">
          <div class="section-title">📝 选股总结</div>
          <NCard size="small" :bordered="false">
            {{ store.state.currentResult.ai_summary }}
          </NCard>
        </div>

        <!-- Results List -->
        <div class="section">
          <div class="section-title">
            📋 选股结果 (共 {{ store.state.currentResult.selected_count }} 只)
          </div>
          <div class="results-list">
            <StockResultCard
              v-for="(stock, index) in store.state.currentResult.results"
              :key="stock.code"
              :stock="stock"
              :rank="index + 1"
            />
          </div>
        </div>
      </template>

      <!-- Running State -->
      <div v-else-if="store.state.running" class="loading-section">
        <NSpin size="large" />
        <p>正在选股，请稍候...</p>
        <NProgress
          type="line"
          :percentage="100"
          :show-indicator="false"
          :height="4"
          processing
        />
      </div>

      <!-- Empty State -->
      <NEmpty v-else-if="!store.state.currentResult" description="点击'开始选股'启动策略选股" />

      <!-- History Section -->
      <NDivider>历史记录</NDivider>
      <NSpin :show="store.state.loadingHistory">
        <NDataTable
          :columns="historyColumns"
          :data="store.state.history"
          :pagination="historyPagination"
          :row-key="(row: any) => row.task_id"
          size="small"
          @update:page="handleHistoryPageChange"
        />
      </NSpin>
    </NCard>

    <!-- Selection Dialog -->
    <StockSelectionDialog
      v-model:show="showDialog"
      :running="store.state.running"
      @start="handleStartSelection"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import {
  NCard, NButton, NSpace, NAlert, NTag, NProgress, NSpin, NEmpty,
  NDivider, NDataTable, useMessage,
} from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { useStockSelectionStore } from '../stores/stockSelection';
import StockSelectionDialog from '../components/StockSelectionDialog.vue';
import type { RunSelectionRequest } from '../services/api_stock_selection';

const store = useStockSelectionStore();
const message = useMessage();

const showDialog = ref(false);

const trendData = computed(() => store.state.currentResult?.market_trend);
const trendColor = computed(() => {
  const dir = trendData.value?.trend_direction;
  if (dir === '看多') return 'success';
  if (dir === '看空') return 'error';
  return 'warning';
});
const strengthColor = computed(() => {
  const str = trendData.value?.trend_strength;
  if (str === '强') return 'success';
  if (str === '中') return 'warning';
  return 'error';
});

const historyColumns: DataTableColumns<any> = [
  { title: '时间', key: 'created_at', width: 160 },
  { title: '策略', key: 'strategy_type', width: 100 },
  { title: '股票池', key: 'stock_pool', width: 100 },
  { title: '选股数量', key: 'selected_count', width: 100 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => h(NTag, {
      type: row.status === 'completed' ? 'success' : row.status === 'failed' ? 'error' : 'warning',
      size: 'small',
    }, { default: () => row.status }),
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row: any) => h(NButton, {
      text: true,
      type: 'primary',
      onClick: () => viewHistory(row.task_id),
    }, { default: () => '查看' }),
  },
];

const historyPagination = computed(() => ({
  page: store.state.historyPage,
  pageSize: store.state.historyPageSize,
  itemCount: store.state.historyTotal,
}));

async function handleStartSelection(request: RunSelectionRequest) {
  try {
    showDialog.value = false;
    await store.runSelection(request);
    message.success('选股完成');
  } catch (e) {
    message.error('选股失败');
  }
}

async function loadHistory() {
  await store.fetchHistory();
}

function handleHistoryPageChange(page: number) {
  store.fetchHistory(page);
}

async function viewHistory(taskId: string) {
  await store.fetchResult(taskId);
}

onMounted(async () => {
  await store.fetchStockPools();
  await store.fetchHistory();
});
</script>

<style scoped>
.stock-selection-view {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 16px;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
  color: #333;
}

.market-trend-section {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
}

.trend-card {
  background: transparent;
}

.trend-header {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.trend-direction, .trend-strength {
  font-size: 14px;
}

.trend-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-label {
  font-weight: bold;
  color: #666;
  width: 80px;
}

.stat-value {
  font-size: 13px;
}

.results-list {
  max-height: 600px;
  overflow-y: auto;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 16px;
}
</style>
