import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../pages/index/index.vue'
import uniCompat from '../utils/uniCompat'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/login/index.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/register/index.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../pages/profile/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/questions',
    name: 'Questions',
    component: () => import('../pages/questions/list.vue')
  },
  {
    path: '/questions/add',
    name: 'AddQuestion',
    component: () => import('../pages/questions/add.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/questions/:id',
    name: 'QuestionDetail',
    component: () => import('../pages/questions/detail.vue')
  },
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('../pages/category/index.vue')
  },
  {
    path: '/categories/:id',
    name: 'CategoryDetail',
    component: () => import('../pages/category/detail.vue')
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../pages/search/index.vue')
  },
  {
    path: '/answers',
    name: 'Answers',
    component: () => import('../pages/profile/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/answers/:id',
    name: 'AnswerDetail',
    component: () => import('../pages/profile/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../pages/about/index.vue')
  },
  {
    path: '/feedback',
    name: 'Feedback',
    component: () => import('../pages/feedback/index.vue'),
    meta: { requiresAuth: true }
  }
]

const router = new VueRouter({
  mode: 'history',
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = uniCompat.storage.getStorageSync('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router