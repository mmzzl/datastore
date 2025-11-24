import { createStore } from 'vuex'

const store = createStore({
  state: {
    // 用户信息
    userInfo: null,
    isLogin: false,
    token: '',
    
    // 系统信息
    systemInfo: {},
    
    // API基础URL
    apiBaseUrl: 'http://localhost:8000',
    
    // 题目分类
    categories: [],
    
    // 难度级别
    difficultyLevels: [
      { id: 1, name: '简单', color: '#52c41a' },
      { id: 2, name: '中等', color: '#faad14' },
      { id: 3, name: '困难', color: '#f5222d' }
    ],
    
    // 学科列表
    subjects: [
      { id: 1, name: '语文', icon: 'book' },
      { id: 2, name: '数学', icon: 'calculator' },
      { id: 3, name: '英语', icon: 'global' },
      { id: 4, name: '物理', icon: 'flash' },
      { id: 5, name: '化学', icon: 'flask' },
      { id: 6, name: '生物', icon: 'leaf' },
      { id: 7, name: '历史', icon: 'time' },
      { id: 8, name: '地理', icon: 'map' },
      { id: 9, name: '政治', icon: 'flag' }
    ]
  },
  
  getters: {
    // 获取用户信息
    getUserInfo: state => state.userInfo,
    
    // 检查是否登录
    isLoggedIn: state => state.isLogin,
    
    // 获取API基础URL
    getApiBaseUrl: state => state.apiBaseUrl,
    
    // 获取系统信息
    getSystemInfo: state => state.systemInfo,
    
    // 获取分类列表
    getCategories: state => state.categories,
    
    // 根据ID获取分类名称
    getCategoryNameById: state => id => {
      const category = state.categories.find(item => item.id === id)
      return category ? category.name : '未分类'
    },
    
    // 获取难度级别
    getDifficultyLevels: state => state.difficultyLevels,
    
    // 根据ID获取难度级别
    getDifficultyLevelById: state => id => {
      const level = state.difficultyLevels.find(item => item.id === id)
      return level || { id: 0, name: '未知', color: '#999' }
    },
    
    // 获取学科列表
    getSubjects: state => state.subjects,
    
    // 根据ID获取学科名称
    getSubjectNameById: state => id => {
      const subject = state.subjects.find(item => item.id === id)
      return subject ? subject.name : '未知学科'
    }
  },
  
  mutations: {
    // 设置用户信息
    setUserInfo(state, userInfo) {
      state.userInfo = userInfo
    },
    
    // 设置登录状态
    setLoginStatus(state, isLogin) {
      state.isLogin = isLogin
    },
    
    // 设置token
    setToken(state, token) {
      state.token = token
      if (token) {
        uni.setStorageSync('token', token)
      } else {
        uni.removeStorageSync('token')
      }
    },
    
    // 设置系统信息
    setSystemInfo(state, systemInfo) {
      state.systemInfo = systemInfo
    },
    
    // 设置API基础URL
    setApiBaseUrl(state, url) {
      state.apiBaseUrl = url
    },
    
    // 设置分类列表
    setCategories(state, categories) {
      state.categories = categories
    },
    
    // 添加分类
    addCategory(state, category) {
      state.categories.push(category)
    },
    
    // 更新分类
    updateCategory(state, updatedCategory) {
      const index = state.categories.findIndex(item => item.id === updatedCategory.id)
      if (index !== -1) {
        state.categories.splice(index, 1, updatedCategory)
      }
    },
    
    // 删除分类
    deleteCategory(state, categoryId) {
      const index = state.categories.findIndex(item => item.id === categoryId)
      if (index !== -1) {
        state.categories.splice(index, 1)
      }
    },
    
    // 清除用户信息
    clearUserInfo(state) {
      state.userInfo = null
      state.isLogin = false
      state.token = ''
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
    }
  },
  
  actions: {
    // 登录
    async login({ commit }, { username, password }) {
      try {
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + '/api/authentication/login/',
          method: 'POST',
          data: { username, password }
        })
        
        if (res.data.code === 200) {
          const { token, user } = res.data.data
          commit('setToken', token)
          commit('setUserInfo', user)
          commit('setLoginStatus', true)
          
          // 保存用户信息到本地存储
          uni.setStorageSync('userInfo', user)
          
          return { success: true, data: res.data.data }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    },
    
    // 注册
    async register({ commit }, { username, password, email }) {
      try {
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + '/api/authentication/register/',
          method: 'POST',
          data: { username, password, email }
        })
        
        if (res.data.code === 200) {
          return { success: true, data: res.data.data }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    },
    
    // 退出登录
    logout({ commit }) {
      commit('clearUserInfo')
      uni.switchTab({
        url: '/pages/index/index'
      })
    },
    
    // 获取分类列表
    async fetchCategories({ commit }) {
      try {
        const token = uni.getStorageSync('token')
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + '/api/categories/',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.data.code === 200) {
          commit('setCategories', res.data.data.results)
          return { success: true, data: res.data.data.results }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    },
    
    // 创建分类
    async createCategory({ commit }, categoryData) {
      try {
        const token = uni.getStorageSync('token')
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + '/api/categories/',
          method: 'POST',
          data: categoryData,
          header: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.data.code === 200) {
          commit('addCategory', res.data.data)
          return { success: true, data: res.data.data }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    },
    
    // 更新分类
    async updateCategory({ commit }, { id, categoryData }) {
      try {
        const token = uni.getStorageSync('token')
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + `/api/categories/${id}/`,
          method: 'PUT',
          data: categoryData,
          header: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.data.code === 200) {
          commit('updateCategory', res.data.data)
          return { success: true, data: res.data.data }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    },
    
    // 删除分类
    async deleteCategory({ commit }, id) {
      try {
        const token = uni.getStorageSync('token')
        const res = await uni.request({
          url: this.getters.getApiBaseUrl + `/api/categories/${id}/`,
          method: 'DELETE',
          header: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.data.code === 200) {
          commit('deleteCategory', id)
          return { success: true }
        } else {
          return { success: false, message: res.data.message }
        }
      } catch (error) {
        return { success: false, message: '网络错误，请检查网络连接' }
      }
    }
  }
})

export default store