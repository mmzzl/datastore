<template>
  <NCard class="stock-result-card" :class="{ expanded: isExpanded }">
    <!-- Header: Always visible -->
    <div class="card-header" @click="toggleExpand">
      <div class="header-left">
        <span class="rank">{{ rank }}</span>
        <span class="code">{{ stock.code }}</span>
        <span class="name">{{ stock.name }}</span>
      </div>
      <div class="header-right">
        <NTag :type="scoreColor" size="small">{{ scoreText }}</NTag>
        <NTag :type="signalColor" size="small">{{ stock.signal_strength }}买入</NTag>
        <NButton text size="small" class="expand-btn">
          <template #icon>
            <svg viewBox="0 0 24 24" width="16" height="16" :style="{ transform: isExpanded ? 'rotate(180deg)' : '' }">
              <path fill="currentColor" d="M7 10l5 5 5-5z" />
            </svg>
          </template>
        </NButton>
      </div>
    </div>

    <!-- Expanded Content -->
    <div v-if="isExpanded" class="card-content">
      <NDivider style="margin: 12px 0" />

      <!-- Technical Indicators -->
      <div class="section">
        <div class="section-title">技术指标</div>
        <div class="indicators-grid">
          <div class="indicator-item">
            <span class="label">MA5:</span>
            <span class="value">{{ formatNum(stock.indicators?.ma5) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">MA10:</span>
            <span class="value">{{ formatNum(stock.indicators?.ma10) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">MA20:</span>
            <span class="value">{{ formatNum(stock.indicators?.ma20) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">RSI:</span>
            <span class="value" :class="rsiClass">{{ formatNum(stock.indicators?.rsi) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">MACD:</span>
            <span class="value" :class="macdClass">{{ formatNum(stock.indicators?.macd) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">MACD柱:</span>
            <span class="value" :class="macdHistClass">{{ formatNum(stock.indicators?.macd_hist) }}</span>
          </div>
        </div>
      </div>

      <!-- AI Analysis -->
      <div v-if="stock.ai_analysis" class="section">
        <div class="section-title">AI分析</div>

        <div class="analysis-item">
          <span class="label">所属板块:</span>
          <NTag size="small">{{ stock.ai_analysis.sector }}</NTag>
          <span class="features">{{ stock.ai_analysis.sector_features }}</span>
        </div>

        <div class="analysis-item">
          <span class="label">技术分析:</span>
          <span class="content">{{ stock.ai_analysis.brief_analysis }}</span>
        </div>

        <div class="analysis-item">
          <span class="label">风险提示:</span>
          <div class="risk-list">
            <NTag v-for="(risk, i) in stock.ai_analysis.risk_factors" :key="i" type="warning" size="small" class="risk-tag">
              {{ risk }}
            </NTag>
          </div>
        </div>

        <div class="analysis-item">
          <span class="label">操作建议:</span>
          <span class="content suggestion">{{ stock.ai_analysis.operation_suggestion }}</span>
        </div>
      </div>

      <!-- Industry -->
      <div class="section">
        <span class="label">行业:</span>
        <NTag size="small">{{ stock.industry || '未知' }}</NTag>
      </div>
    </div>
  </NCard>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { NCard, NTag, NButton, NDivider } from 'naive-ui';
import type { StockResultItem } from '../services/api_stock_selection';

const props = defineProps<{
  stock: StockResultItem;
  rank: number;
}>();

const isExpanded = ref(false);

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
}

function formatNum(val: number | undefined | null): string {
  if (val === undefined || val === null) return '-';
  return val.toFixed(2);
}

const scoreText = computed(() => {
  return props.stock.score.toFixed(0) + '分';
});

const scoreColor = computed(() => {
  const score = props.stock.score;
  if (score >= 80) return 'success';
  if (score >= 60) return 'info';
  if (score >= 40) return 'warning';
  return 'error';
});

const signalColor = computed(() => {
  const strength = props.stock.signal_strength;
  if (strength === '强') return 'success';
  if (strength === '中') return 'info';
  return 'warning';
});

const rsiClass = computed(() => {
  const rsi = props.stock.indicators?.rsi;
  if (rsi === undefined) return '';
  if (rsi > 70) return 'overbought';
  if (rsi < 30) return 'oversold';
  return '';
});

const macdClass = computed(() => {
  const macd = props.stock.indicators?.macd;
  if (macd === undefined) return '';
  return macd > 0 ? 'positive' : 'negative';
});

const macdHistClass = computed(() => {
  const hist = props.stock.indicators?.macd_hist;
  if (hist === undefined) return '';
  return hist > 0 ? 'positive' : 'negative';
});
</script>

<style scoped>
.stock-result-card {
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.stock-result-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
}

.code {
  font-family: monospace;
  font-weight: bold;
}

.name {
  color: #666;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-btn {
  transition: transform 0.2s;
}

.card-content {
  padding-top: 8px;
}

.section {
  margin-bottom: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #333;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.indicator-item {
  display: flex;
  gap: 4px;
}

.indicator-item .label {
  color: #999;
  font-size: 12px;
}

.indicator-item .value {
  font-family: monospace;
  font-size: 13px;
}

.indicator-item .value.positive {
  color: #18a058;
}

.indicator-item .value.negative {
  color: #d03050;
}

.indicator-item .value.overbought {
  color: #d03050;
}

.indicator-item .value.oversold {
  color: #18a058;
}

.analysis-item {
  margin-bottom: 8px;
}

.analysis-item .label {
  color: #666;
  font-size: 13px;
  margin-right: 8px;
}

.analysis-item .content {
  font-size: 13px;
}

.analysis-item .features {
  font-size: 12px;
  color: #666;
  margin-left: 8px;
}

.analysis-item .suggestion {
  color: #2080f0;
}

.risk-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.risk-tag {
  font-size: 11px;
}
</style>
