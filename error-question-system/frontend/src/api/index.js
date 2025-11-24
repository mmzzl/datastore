import axios from 'axios';
import store from '../store';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000/api',
  timeout: 10000
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 添加token到请求头
    const token = store.getters['user/token'];
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    // 处理401未授权错误
    if (error.response && error.response.status === 401) {
      // 清除用户信息并跳转到登录页
      store.dispatch('user/logout');
      uni.navigateTo({
        url: '/pages/login/index'
      });
    }
    
    return Promise.reject(error);
  }
);

export default api;