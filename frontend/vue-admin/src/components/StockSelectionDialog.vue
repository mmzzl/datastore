<template>
  <NModal
    v-model:show="visible"
    preset="dialog"
    title="策略选股"
    :positive-text="running ? '选股中...' : '开始选股'"
    :negative-text="'取消'"
    :positive-button-props="{ disabled: !canStart || running }"
    @positive-click="handleStart"
    @negative-click="handleCancel"
  >
    <NSpin :show="loading">
      <NForm ref="formRef" :model="form" label-placement="left" label-width="80">
        <!-- Strategy Selection -->
        <NFormItem label="策略类型" path="strategyType">
          <NSelect
            v-model:value="form.strategyType"
            :options="strategyOptions"
            placeholder="选择策略"
            @update:value="handleStrategyChange"
          />
        </NFormItem>

        <!-- Plugin Selection (when strategy type is 'plugin') -->
        <NFormItem v-if="form.strategyType === 'plugin'" label="选择插件" path="pluginId">
          <NSelect
            v-model:value="form.pluginId"
            :options="pluginOptions"
            placeholder="选择已上传的插件"
            :loading="loadingPlugins"
          />
        </NFormItem>

        <!-- Stock Pool Selection -->
        <NFormItem label="股票池" path="stockPool">
          <NRadioGroup v-model:value="form.stockPool">
            <NSpace>
              <NRadioButton
                v-for="pool in stockPools"
                :key="pool.id"
                :value="pool.id"
                :label="pool.name"
              >
                {{ pool.name }} ({{ pool.count }}只)
              </NRadioButton>
            </NSpace>
          </NRadioGroup>
        </NFormItem>

        <!-- Strategy Parameters (dynamic) -->
        <NDivider>策略参数</NDivider>

        <!-- MA Cross Parameters -->
        <template v-if="form.strategyType === 'ma_cross'">
          <NFormItem label="快线周期">
            <NInputNumber v-model:value="form.params.fast_period" :min="2" :max="100" />
          </NFormItem>
          <NFormItem label="慢线周期">
            <NInputNumber v-model:value="form.params.slow_period" :min="5" :max="200" />
          </NFormItem>
        </template>

        <!-- RSI Parameters -->
        <template v-if="form.strategyType === 'rsi'">
          <NFormItem label="RSI周期">
            <NInputNumber v-model:value="form.params.period" :min="5" :max="50" />
          </NFormItem>
          <NFormItem label="超卖阈值">
            <NInputNumber v-model:value="form.params.oversold" :min="10" :max="40" />
          </NFormItem>
          <NFormItem label="超买阈值">
            <NInputNumber v-model:value="form.params.overbought" :min="60" :max="90" />
          </NFormItem>
        </template>

        <!-- Bollinger Parameters -->
        <template v-if="form.strategyType === 'bollinger'">
          <NFormItem label="周期">
            <NInputNumber v-model:value="form.params.period" :min="5" :max="50" />
          </NFormItem>
          <NFormItem label="标准差倍数">
            <NInputNumber v-model:value="form.params.num_std" :min="1" :max="3" :step="0.5" />
          </NFormItem>
        </template>

        <!-- MACD Parameters -->
        <template v-if="form.strategyType === 'macd'">
          <NFormItem label="快线周期">
            <NInputNumber v-model:value="form.params.fast_period" :min="5" :max="30" />
          </NFormItem>
          <NFormItem label="慢线周期">
            <NInputNumber v-model:value="form.params.slow_period" :min="10" :max="50" />
          </NFormItem>
          <NFormItem label="信号线周期">
            <NInputNumber v-model:value="form.params.signal_period" :min="5" :max="20" />
          </NFormItem>
        </template>
      </NForm>
    </NSpin>

    <!-- Progress indicator when running -->
    <NProgress
      v-if="running"
      type="line"
      :percentage="100"
      :show-indicator="false"
      :height="4"
      processing
      class="mt-4"
    />
  </NModal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import {
  NModal, NForm, NFormItem, NSelect, NRadioGroup, NRadioButton, NSpace,
  NInputNumber, NDivider, NSpin, NProgress,
} from 'naive-ui';
import { apiPlugins } from '../services/api_plugins';

const props = defineProps<{
  show: boolean;
  running: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'start', request: any): void;
}>();

const visible = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v),
});

const formRef = ref();
const loading = ref(false);
const loadingPlugins = ref(false);
const plugins = ref<any[]>([]);

const form = ref({
  strategyType: 'ma_cross',
  stockPool: 'hs300',
  pluginId: null as string | null,
  params: {
    fast_period: 5,
    slow_period: 20,
    period: 14,
    oversold: 30,
    overbought: 70,
    num_std: 2,
    signal_period: 9,
  },
});

const stockPools = ref([
  { id: 'hs300', name: '沪深300', count: 300 },
  { id: 'zz500', name: '中证500', count: 500 },
  { id: 'all', name: '全市场', count: 800 },
]);

const strategyOptions = [
  { label: 'MA Cross (均线交叉)', value: 'ma_cross' },
  { label: 'RSI (相对强弱)', value: 'rsi' },
  { label: 'Bollinger (布林带)', value: 'bollinger' },
  { label: 'MACD', value: 'macd' },
  { label: '插件策略', value: 'plugin' },
];

const pluginOptions = computed(() => {
  return plugins.value
    .filter(p => p.status === 'active')
    .map(p => ({
      label: `${p.display_name || p.name} (v${p.version})`,
      value: p.id,
    }));
});

const canStart = computed(() => {
  if (form.value.strategyType === 'plugin' && !form.value.pluginId) {
    return false;
  }
  return true;
});

async function loadPlugins() {
  loadingPlugins.value = true;
  try {
    const res = await apiPlugins.getPlugins();
    plugins.value = res.items;
  } catch (e) {
    console.error('Failed to load plugins:', e);
  } finally {
    loadingPlugins.value = false;
  }
}

function handleStrategyChange(value: string) {
  if (value === 'plugin') {
    loadPlugins();
  }
}

function handleStart() {
  const request: any = {
    strategy_type: form.value.strategyType,
    stock_pool: form.value.stockPool,
    strategy_params: {},
  };

  // Add strategy-specific params
  if (form.value.strategyType === 'ma_cross') {
    request.strategy_params = {
      fast_period: form.value.params.fast_period,
      slow_period: form.value.params.slow_period,
    };
  } else if (form.value.strategyType === 'rsi') {
    request.strategy_params = {
      period: form.value.params.period,
      oversold: form.value.params.oversold,
      overbought: form.value.params.overbought,
    };
  } else if (form.value.strategyType === 'bollinger') {
    request.strategy_params = {
      period: form.value.params.period,
      num_std: form.value.params.num_std,
    };
  } else if (form.value.strategyType === 'macd') {
    request.strategy_params = {
      fast_period: form.value.params.fast_period,
      slow_period: form.value.params.slow_period,
      signal_period: form.value.params.signal_period,
    };
  } else if (form.value.strategyType === 'plugin') {
    request.plugin_id = form.value.pluginId;
  }

  emit('start', request);
}

function handleCancel() {
  visible.value = false;
}

// Load plugins when strategy type is plugin
watch(() => form.value.strategyType, (v) => {
  if (v === 'plugin') {
    loadPlugins();
  }
});
</script>

<style scoped>
.mt-4 {
  margin-top: 16px;
}
</style>
