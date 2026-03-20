<template>
  <div class="app-layout">
    <aside class="sidebar">
      <h2 class="logo">Market Admin</h2>
      <nav>
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/holdings">Holdings</router-link>
        <router-link to="/market-watch">Market Watch</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
  </template>

<script setup>
// simple layout wrapper
</script>

<style scoped>
.app-layout { display: flex; min-height: 100vh; font-family: Inter, system-ui, Arial; }
.sidebar { width: 260px; background: #1f2937; color: #fff; padding: 20px; }
.sidebar .logo { margin: 0 0 16px; font-size: 18px; }
.sidebar nav { display: flex; flex-direction: column; gap: 8px; }
.sidebar a { color: #cbd5e1; text-decoration: none; padding: 6px 8px; border-radius: 4px; }
.sidebar a.router-link-active { background: #374151; color: #fff; }
.content { flex: 1; padding: 20px; background: #f5f7fa; }
</style>
