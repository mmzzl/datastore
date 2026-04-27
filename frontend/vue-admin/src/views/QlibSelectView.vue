<script setup lang="ts">
import { NTabs, NTabPane } from 'naive-ui'
import QlibTrainHistory from './qlib/QlibTrainHistory.vue'
import QlibBestModel from './qlib/QlibBestModel.vue'
import QlibTopStocks from './qlib/QlibTopStocks.vue'
</script>

<template>
  <div class="qlib-select-view">
    <NTabs type="line" animated>
      <NTabPane name="top-stocks" tab="Top10推荐">
        <QlibTopStocks />
      </NTabPane>
      <NTabPane name="best-model" tab="最优模型">
        <QlibBestModel />
      </NTabPane>
      <NTabPane name="history" tab="训练历史">
        <QlibTrainHistory />
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.qlib-select-view { padding: 20px; }
</style>
