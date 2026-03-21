<template>
  <div class="chart-card" :style="{ height: (height || '180px') }">
    <div class="title">{{ title }}</div>
    <div class="body"><slot>数据</slot></div>
  </div>
</template>

<script setup>
defineProps<{ title: string; height?: string }>()
</script>

<style scoped>
.chart-card { background: #fff; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; }
.title { font-weight: 600; margin-bottom: 6px; }
.body { flex: 1; display: flex; align-items: center; justify-content: center; color: #555; }
</style>
