import api from './index';

// 用户相关API
export const userApi = {
  // 登录
  login(data) {
    return api.post('/auth/login', data);
  },
  
  // 注册
  register(data) {
    return api.post('/auth/register', data);
  },
  
  // 获取用户信息
  getUserInfo() {
    return api.get('/user/profile');
  },
  
  // 更新用户信息
  updateUserInfo(data) {
    return api.put('/user/profile', data);
  },
  
  // 修改密码
  changePassword(data) {
    return api.put('/user/password', data);
  }
};

// 错题相关API
export const questionApi = {
  // 获取错题列表
  getQuestions(params) {
    return api.get('/questions', { params });
  },
  
  // 获取错题详情
  getQuestionById(id) {
    return api.get(`/questions/${id}`);
  },
  
  // 添加错题
  addQuestion(data) {
    return api.post('/questions', data);
  },
  
  // 更新错题
  updateQuestion(id, data) {
    return api.put(`/questions/${id}`, data);
  },
  
  // 删除错题
  deleteQuestion(id) {
    return api.delete(`/questions/${id}`);
  },
  
  // 添加解答
  addAnswer(questionId, data) {
    return api.post(`/questions/${questionId}/answers`, data);
  },
  
  // 搜索错题
  searchQuestions(params) {
    return api.get('/questions/search', { params });
  }
};

// 分类相关API
export const categoryApi = {
  // 获取分类列表
  getCategories(params) {
    return api.get('/categories', { params });
  },
  
  // 获取分类详情
  getCategoryById(id) {
    return api.get(`/categories/${id}`);
  },
  
  // 添加分类
  addCategory(data) {
    return api.post('/categories', data);
  },
  
  // 更新分类
  updateCategory(id, data) {
    return api.put(`/categories/${id}`, data);
  },
  
  // 删除分类
  deleteCategory(id) {
    return api.delete(`/categories/${id}`);
  }
};

// 反馈相关API
export const feedbackApi = {
  // 获取反馈列表
  getFeedbackList(params) {
    return api.get('/feedback', { params });
  },
  
  // 提交反馈
  submitFeedback(data) {
    return api.post('/feedback', data);
  },
  
  // 获取反馈详情
  getFeedbackById(id) {
    return api.get(`/feedback/${id}`);
  }
};

// 文件上传API
export const uploadApi = {
  // 上传图片
  uploadImage(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    return api.post('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};

export default {
  userApi,
  questionApi,
  categoryApi,
  feedbackApi,
  uploadApi
};