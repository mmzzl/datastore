import Vue from 'vue'
import Vuex from 'vuex'
import user from './modules/user'
import questions from './modules/questions'
import categories from './modules/categories'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    user,
    questions,
    categories
  }
})