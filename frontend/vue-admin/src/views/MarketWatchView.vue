<template>
  <div class="page marketwatch">
    <h1>Market Watch</h1>
    <div class="signals" v-if="signals.length">
      <table class="wb-table">
        <thead><tr><th>股票</th><th>动作</th><th>置信度</th><th>目标价</th><th>理由</th></tr></thead>
        <tbody>
          <tr v-for="s in signals" :key="s.code">
            <td>{{ s.code }}</td>
            <td>{{ s.action }}</td>
            <td>{{ s.confidence.toFixed(2) }}</td>
            <td>{{ s.target_price }}</td>
            <td>{{ s.reasons?.join(', ') || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>信号数据尚未就绪，暂时为空。</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiSignals } from '../services/api'
const signals = ref([])
onMounted(async () => {
  try {
    const data = await apiSignals.getLatest()
    signals.value = data || []
  } catch {
    signals.value = []
  }
})
</script>

<style scoped>
.marketwatch { padding: 16px; }
.wb-table { width: 100%; border-collapse: collapse; }
.wb-table th, .wb-table td { border: 1px solid #e5e7eb; padding: 8px; }
</style>
