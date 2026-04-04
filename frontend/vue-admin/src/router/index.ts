import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Dashboard from '../views/DashboardView.vue'
import Holdings from '../views/HoldingsView.vue'
import MarketWatch from '../views/MarketWatchView.vue'
import Settings from '../views/SettingsView.vue'
import Login from '../views/LoginView.vue'
import QlibSelectView from '../views/QlibSelectView.vue'
import BacktestView from '../views/BacktestView.vue'
import RiskReportView from '../views/RiskReportView.vue'
import SchedulerView from '../views/SchedulerView.vue'
import DingtalkConfigView from '../views/DingtalkConfigView.vue'
import PluginManagementView from '../views/PluginManagementView.vue'
import UserManagementView from '../views/UserManagementView.vue'
import RoleManagementView from '../views/RoleManagementView.vue'
import { authService } from '../services/api'

const routes: Array<RouteRecordRaw> = [
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard, name: 'dashboard' },
  { path: '/holdings', component: Holdings, name: 'holdings' },
  { path: '/market-watch', component: MarketWatch, name: 'market-watch' },
  { path: '/settings', component: Settings, name: 'settings' },
  { path: '/qlib/select', component: QlibSelectView, name: 'qlib-select' },
  { path: '/backtest', component: BacktestView, name: 'backtest' },
  { path: '/risk-report', component: RiskReportView, name: 'risk-report' },
  { path: '/scheduler', component: SchedulerView, name: 'scheduler' },
  { path: '/dingtalk-config', component: DingtalkConfigView, name: 'dingtalk-config' },
  { path: '/plugins', component: PluginManagementView, name: 'plugins' },
  { path: '/admin/users', component: UserManagementView, name: 'admin-users' },
  { path: '/admin/roles', component: RoleManagementView, name: 'admin-roles' },
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

router.afterEach((to) => {
  if (to.name === 'dashboard') {
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  }
})

export default router
