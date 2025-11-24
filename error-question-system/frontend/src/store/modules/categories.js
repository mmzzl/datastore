import { getCategoryList, getCategoryDetail } from '../../api/category'

const state = {
  categoryList: [],
  currentCategory: null,
  loading: false
}

const mutations = {
  SET_CATEGORY_LIST(state, list) {
    state.categoryList = list
  },
  SET_CURRENT_CATEGORY(state, category) {
    state.currentCategory = category
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  }
}

const actions = {
  // 获取分类列表
  async getCategoryList({ commit }) {
    commit('SET_LOADING', true)
    try {
      const response = await getCategoryList()
      const list = response.data
      
      commit('SET_CATEGORY_LIST', list)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 获取分类详情
  async getCategoryDetail({ commit }, id) {
    commit('SET_LOADING', true)
    try {
      const response = await getCategoryDetail(id)
      const category = response.data
      
      commit('SET_CURRENT_CATEGORY', category)
      
      return Promise.resolve(category)
    } catch (error) {
      return Promise.reject(error)
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

const getters = {
  categoryList: state => state.categoryList,
  currentCategory: state => state.currentCategory,
  loading: state => state.loading
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}