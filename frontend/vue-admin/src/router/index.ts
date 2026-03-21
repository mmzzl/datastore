import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Dashboard from '../views/DashboardView.vue'
import Holdings from '../views/HoldingsView.vue'
import MarketWatch from '../views/MarketWatchView.vue'
import Settings from '../views/SettingsView.vue'
import Login from '../views/LoginView.vue'
import { authService } from '../services/api'

const routes: Array<RouteRecordRaw> = [
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, name: 'dashboard' },
  { path: '/holdings', component: Holdings, name: 'holdings' },
  { path: '/market-watch', component: MarketWatch, name: 'market-watch' },
  { path: '/settings', component: Settings, name: 'settings' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public || authService.isAuthenticated()) {
    next()
  } else {
    next('/login')
  }
})

// 导航后刷新Dashboard数据
router.afterEach((to) => {
  if (to.name === 'dashboard') {
    // 触发一个全局事件，让Dashboard组件刷新数据
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  }
})

export default router