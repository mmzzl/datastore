import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import uView from 'uview-ui'
import uniCompat from './utils/uniCompat'
import './uni.promisify.adaptor'

// 初始化uni兼容层
uniCompat.initUniObject()

Vue.config.productionTip = false
App.mpType = 'app'

// 使用插件
Vue.use(router)
Vue.use(store)
Vue.use(uView)

const app = new Vue({
  router,
  store,
  ...App
})
app.$mount()