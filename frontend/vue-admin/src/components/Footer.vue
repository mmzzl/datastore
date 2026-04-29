<template>
  <footer class="site-footer">
    <div class="footer-content">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" class="icp-link">
        蜀ICP备2025144552号-1
      </a>
    </div>
  </footer>
</template>

<script setup lang="ts">
</script>

<style scoped>
.site-footer {
  width: 100%;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  text-align: center;
  margin-top: auto;
}

.footer-content {
  font-size: 14px;
  color: #64748b;
}

.icp-link {
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s;
}

.icp-link:hover {
  color: #3b82f6;
}
</style>
