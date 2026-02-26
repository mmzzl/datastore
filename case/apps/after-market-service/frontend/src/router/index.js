import { createRouter, createWebHistory } from 'vue-router'
import List from '../views/List.vue'
import Detail from '../views/Detail.vue'

const routes = [
  { path: '/', name: 'List', component: List },
  { path: '/detail/:date', name: 'Detail', component: Detail }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
