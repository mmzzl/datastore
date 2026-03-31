<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useQlibStore } from '../stores/qlib'
import { NCard, NButton, NSpin, NDataTable, NSelect, NInputNumber, NAlert, NTag } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'

const store = useQlibStore()

onMounted(async () => {
  await store.fetchModels()
  await store.fetchCSI300()
})

const selectedModel = ref<string | null>(null)
const topK = ref(10)

const modelOptions = computed(() =>
  store.state.models.map(m => ({
    label: m.name,
    value: m.id
  }))
)

async function runSelection() {
  if (!selectedModel.value) return
  await store.runSelection({
    model_id: selectedModel.value,
    top_k: topK.value
  })
}

const columns: DataTableColumns = [
  { title: '排名', key: 'rank', width: 80 },
  { title: '代码', key: 'code', width: 120 },
  { title: '名称', key: 'name' },
  { title: '得分', key: 'score', width: 100 },
]
</script>

<template>
  <div class="qlib-select-view">
    <NCard title="Qlib 股票筛选">
      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <div class="selection-form">
        <NSelect
          v-model:value="selectedModel"
          :options="modelOptions"
          placeholder="选择模型"
          style="width: 200px"
        />
        <NInputNumber
          v-model:value="topK"
          :min="1"
          :max="100"
          placeholder="Top K"
        />
        <NButton
          type="primary"
          :loading="store.state.selecting"
          :disabled="!selectedModel"
          @click="runSelection"
        >
          运行筛选
        </NButton>
      </div>

      <NSpin :show="store.state.selecting">
        <div v-if="store.state.selectionResults" class="results mt-4">
          <div class="result-header mb-2">
            <NTag type="info">
              筛选日期: {{ store.state.selectionResults.date }}
            </NTag>
          </div>
          <NDataTable
            :columns="columns"
            :data="store.state.selectionResults.stocks"
            :bordered="false"
          />
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.qlib-select-view {
  padding: 20px;
}
.selection-form {
  display: flex;
  gap: 16px;
  align-items: center;
}
.mb-4 {
  margin-bottom: 16px;
}
.mt-4 {
  margin-top: 16px;
}
.mb-2 {
  margin-bottom: 8px;
}
</style>
