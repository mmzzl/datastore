<template>
  <div class="page marketwatch">
    <h1>Market Watch</h1>
    <div class="signals" v-if="signals.length">
      <table class="wb-table">
        <thead><tr><th>股票代码</th><th>股票名称</th><th>信号类型</th><th>价格</th><th>消息</th><th>时间</th></tr></thead>
        <tbody>
          <tr v-for="s in signals" :key="s.symbol">
            <td>{{ s.symbol }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.signal }}</td>
            <td>{{ s.price }}</td>
            <td>{{ s.message }}</td>
            <td>{{ formatTime(s.timestamp) }}</td>
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

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

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
