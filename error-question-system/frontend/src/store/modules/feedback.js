import api from '../api';

export default {
  namespaced: true,
  state: {
    feedbackList: [],
    currentFeedback: null,
    total: 0,
    loading: false,
    feedbackTypes: [
      { id: 1, name: '功能建议' },
      { id: 2, name: '问题反馈' },
      { id: 3, name: '内容错误' },
      { id: 4, name: '其他' }
    ]
  },
  getters: {
    feedbackList: state => state.feedbackList,
    currentFeedback: state => state.currentFeedback,
    total: state => state.total,
    loading: state => state.loading,
    feedbackTypes: state => state.feedbackTypes
  },
  mutations: {
    SET_FEEDBACK_LIST(state, feedbackList) {
      state.feedbackList = feedbackList;
    },
    SET_CURRENT_FEEDBACK(state, feedback) {
      state.currentFeedback = feedback;
    },
    SET_TOTAL(state, total) {
      state.total = total;
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    ADD_FEEDBACK(state, feedback) {
      state.feedbackList.unshift(feedback);
      state.total += 1;
    },
    UPDATE_FEEDBACK(state, updatedFeedback) {
      const index = state.feedbackList.findIndex(f => f.id === updatedFeedback.id);
      if (index !== -1) {
        state.feedbackList.splice(index, 1, updatedFeedback);
      }
      
      if (state.currentFeedback && state.currentFeedback.id === updatedFeedback.id) {
        state.currentFeedback = updatedFeedback;
      }
    }
  },
  actions: {
    // 获取反馈列表
    async fetchFeedbackList({ commit }, params = {}) {
      commit('SET_LOADING', true);
      try {
        const response = await api.get('/feedback', { params });
        const { feedbackList, total } = response.data;
        
        commit('SET_FEEDBACK_LIST', feedbackList);
        commit('SET_TOTAL', total);
        
        return { feedbackList, total };
      } catch (error) {
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // 提交反馈
    async submitFeedback({ commit }, feedbackData) {
      try {
        const response = await api.post('/feedback', feedbackData);
        const feedback = response.data;
        
        commit('ADD_FEEDBACK', feedback);
        
        return feedback;
      } catch (error) {
        throw error;
      }
    },
    
    // 获取反馈详情
    async fetchFeedbackById({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        const response = await api.get(`/feedback/${id}`);
        const feedback = response.data;
        
        commit('SET_CURRENT_FEEDBACK', feedback);
        
        return feedback;
      } catch (error) {
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    }
  }
};