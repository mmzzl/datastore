import { getQuestionList, getQuestionDetail, addQuestion, updateQuestion, deleteQuestion } from '../../api/question'

const state = {
  questionList: [],
  currentQuestion: null,
  loading: false,
  pagination: {
    current: 1,
    pageSize: 10,
    total: 0
  }
}

const mutations = {
  SET_QUESTION_LIST(state, list) {
    state.questionList = list
  },
  SET_CURRENT_QUESTION(state, question) {
    state.currentQuestion = question
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination }
  },
  ADD_QUESTION(state, question) {
    state.questionList.unshift(question)
  },
  UPDATE_QUESTION(state, updatedQuestion) {
    const index = state.questionList.findIndex(item => item.id === updatedQuestion.id)
    if (index !== -1) {
      state.questionList.splice(index, 1, updatedQuestion)
    }
  },
  DELETE_QUESTION(state, questionId) {
    state.questionList = state.questionList.filter(item => item.id !== questionId)
  }
}

const actions = {
  // 获取错题列表
  async getQuestionList({ commit }, params) {
    commit('SET_LOADING', true)
    try {
      const response = await getQuestionList(params)
      const { list, pagination } = response.data
      
      commit('SET_QUESTION_LIST', list)
      commit('SET_PAGINATION', pagination)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 获取错题详情
  async getQuestionDetail({ commit }, id) {
    commit('SET_LOADING', true)
    try {
      const response = await getQuestionDetail(id)
      const question = response.data
      
      commit('SET_CURRENT_QUESTION', question)
      
      return Promise.resolve(question)
    } catch (error) {
      return Promise.reject(error)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 添加错题
  async addQuestion({ commit }, questionData) {
    try {
      const response = await addQuestion(questionData)
      const question = response.data
      
      commit('ADD_QUESTION', question)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    }
  },
  
  // 更新错题
  async updateQuestion({ commit }, { id, questionData }) {
    try {
      const response = await updateQuestion(id, questionData)
      const updatedQuestion = response.data
      
      commit('UPDATE_QUESTION', updatedQuestion)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    }
  },
  
  // 删除错题
  async deleteQuestion({ commit }, id) {
    try {
      const response = await deleteQuestion(id)
      
      commit('DELETE_QUESTION', id)
      
      return Promise.resolve(response)
    } catch (error) {
      return Promise.reject(error)
    }
  }
}

const getters = {
  questionList: state => state.questionList,
  currentQuestion: state => state.currentQuestion,
  loading: state => state.loading,
  pagination: state => state.pagination
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}