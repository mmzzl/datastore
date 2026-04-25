<script setup lang="ts">
import { onMounted } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { NCard, NDescriptions, NDescriptionsItem, NTag, NEmpty, NSpin } from 'naive-ui'

const store = useQlibStore()

onMounted(async () => {
  await store.fetchBestModel()
})

function formatValue(val: any, digits: number = 4): string {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'number') return val.toFixed(digits)
  return String(val)
}
</script>

<template>
  <div class="best-model">
    <NSpin :show="store.state.loading">
      <template v-if="store.state.bestModel">
        <NCard title="最优模型 (Sharpe最高)" size="small">
          <NDescriptions label-placement="left" bordered :column="2">
            <NDescriptionsItem label="实验ID">{{ store.state.bestModel.experiment_id }}</NDescriptionsItem>
            <NDescriptionsItem label="模型ID">{{ store.state.bestModel.model_id || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="模型类型">{{ store.state.bestModel.config?.model_type || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="因子配置">{{ store.state.bestModel.config?.factor_type || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="Tag">{{ store.state.bestModel.tag || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="状态">
              <NTag :type="store.state.bestModel.status === 'completed' ? 'success' : 'default'" size="small">{{ store.state.bestModel.status }}</NTag>
            </NDescriptionsItem>
          </NDescriptions>
          <NCard title="训练指标" size="small" style="margin-top: 16px">
            <NDescriptions label-placement="left" bordered :column="2">
              <NDescriptionsItem label="IC">{{ formatValue(store.state.bestModel.training_metrics?.ic) }}</NDescriptionsItem>
              <NDescriptionsItem label="Rank IC">{{ formatValue(store.state.bestModel.training_metrics?.rank_ic) }}</NDescriptionsItem>
              <NDescriptionsItem label="ICIR">{{ formatValue(store.state.bestModel.training_metrics?.icir) }}</NDescriptionsItem>
              <NDescriptionsItem label="预测数量">{{ store.state.bestModel.training_metrics?.num_predictions ?? '-' }}</NDescriptionsItem>
            </NDescriptions>
          </NCard>
          <NCard title="回测指标" size="small" style="margin-top: 16px">
            <NDescriptions label-placement="left" bordered :column="2">
              <NDescriptionsItem label="Sharpe Ratio">{{ formatValue(store.state.bestModel.backtest_result?.sharpe_ratio, 2) }}</NDescriptionsItem>
              <NDescriptionsItem label="多空收益">{{ formatValue(store.state.bestModel.backtest_result?.long_short_return) }}</NDescriptionsItem>
            </NDescriptions>
          </NCard>
        </NCard>
      </template>
      <NEmpty v-else-if="!store.state.loading" description="暂无已完成的训练实验" />
    </NSpin>
  </div>
</template>

<style scoped>
.best-model { padding: 0; }
</style>
