<template>
  <div class="page settings">
    <h1>Settings</h1>
    <div class="config-grid">
      <div class="config-item">
        <label>Watchlist</label>
        <textarea rows="6" placeholder="用逗号分隔的股票代码，例如 SH600000, SH600519"></textarea>
      </div>
      <div class="config-item">
        <label>轮询间隔 (秒)</label>
        <input type="number" value="60" />
      </div>
      <div class="config-item">
        <label>缓存 TTL (秒)</label>
        <input type="number" value="60" />
      </div>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.settings { padding: 16px; }
.config-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.config-item { background: #fff; padding: 12px; border-radius: 8px; border: 1px solid #eee; }
.config-item label { display: block; font-weight: 600; margin-bottom: 6px; }
.config-item textarea { width: 100%; resize: vertical; }
.config-item input { width: 100%; padding: 6px 8px; }
</style>
