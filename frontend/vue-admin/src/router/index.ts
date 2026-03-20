import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Dashboard from '../views/DashboardView.vue'
import Holdings from '../views/HoldingsView.vue'
import MarketWatch from '../views/MarketWatchView.vue'
import Settings from '../views/SettingsView.vue'

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard },
  { path: '/holdings', component: Holdings },
  { path: '/market-watch', component: MarketWatch },
  { path: '/settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
