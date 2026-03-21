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
  { path: '/dashboard', component: Dashboard },
  { path: '/holdings', component: Holdings },
  { path: '/market-watch', component: MarketWatch },
  { path: '/settings', component: Settings },
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

export default router