import { login, logout, getUserInfo } from '../../api/user'
import uniCompat from '../../utils/uniCompat'

const state = {
  token: uniCompat.storage.getStorageSync('token'),
  userInfo: (() => {
    try {
      const userInfoStr = uniCompat.storage.getStorageSync('userInfo', '{}')
      return userInfoStr ? JSON.parse(userInfoStr) : {}
    } catch (e) {
      console.error('Failed to parse userInfo from storage:', e)
      return {}
    }
  })(),
  isLoggedIn: !!uniCompat.storage.getStorageSync('token')
}

const mutations = {
  SET_TOKEN(state, token) {
    state.token = token
    state.isLoggedIn = !!token
    uniCompat.storage.setStorageSync('token', token)
  },
  SET_USER_INFO(state, userInfo) {
    state.userInfo = userInfo
    uniCompat.storage.setStorageSync('userInfo', JSON.stringify(userInfo))
  },
  CLEAR_USER(state) {
    state.token = ''
    state.userInfo = {}
    state.isLoggedIn = false
    uniCompat.storage.removeStorageSync('token')
    uniCompat.storage.removeStorageSync('userInfo')
  }
}

const actions = {
  // 登录
  async login({ commit }, loginForm) {
    try {
      const response = await login(loginForm)
      const { token, userInfo } = response.data
      
      commit('SET_TOKEN', token)
      commit('SET_USER_INFO', userInfo)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    }
  },
  
  // 登出
  async logout({ commit }) {
    try {
      await logout()
      commit('CLEAR_USER')
      return Promise.resolve()
    } catch (error) {
      commit('CLEAR_USER')
      return Promise.reject(error)
    }
  },
  
  // 获取用户信息
  async getUserInfo({ commit }) {
    try {
      const response = await getUserInfo()
      const userInfo = response.data
      
      commit('SET_USER_INFO', userInfo)
      return Promise.resolve(userInfo)
    } catch (error) {
      return Promise.reject(error)
    }
  },
  
  // 更新用户信息
  updateUserInfo({ commit }, userInfo) {
    commit('SET_USER_INFO', userInfo)
  }
}

const getters = {
  token: state => state.token,
  userInfo: state => state.userInfo,
  isLoggedIn: state => state.isLoggedIn,
  userId: state => state.userInfo.id || '',
  username: state => state.userInfo.username || '',
  avatar: state => state.userInfo.avatar || '/static/images/default-avatar.png'
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}