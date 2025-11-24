import request from './request'

// 认证相关API
export const authApi = {
  // 用户登录
  login: (data) => request.post('/api/authentication/login/', data),
  
  // 用户注册
  register: (data) => request.post('/api/authentication/register/', data),
  
  // 验证token
  verify: () => request.post('/api/authentication/verify/'),
  
  // 刷新token
  refresh: (data) => request.post('/api/authentication/refresh/', data),
  
  // 退出登录
  logout: () => request.post('/api/authentication/logout/'),
  
  // 获取用户信息
  getUserInfo: () => request.get('/api/authentication/user/'),
  
  // 更新用户信息
  updateUserInfo: (data) => request.put('/api/authentication/user/', data),
  
  // 修改密码
  changePassword: (data) => request.post('/api/authentication/change-password/', data),
  
  // 重置密码
  resetPassword: (data) => request.post('/api/authentication/reset-password/', data)
}

// 题目相关API
export const questionApi = {
  // 获取题目列表
  getQuestions: (params) => request.get('/api/questions/', params),
  
  // 获取题目详情
  getQuestionDetail: (id) => request.get(`/api/questions/${id}/`),
  
  // 创建题目
  createQuestion: (data) => request.post('/api/questions/', data),
  
  // 更新题目
  updateQuestion: (id, data) => request.put(`/api/questions/${id}/`, data),
  
  // 删除题目
  deleteQuestion: (id) => request.delete(`/api/questions/${id}/`),
  
  // 上传题目图片
  uploadQuestionImage: (filePath, formData) => request.uploadFile(filePath, '/api/questions/upload-image/', formData),
  
  // 获取错题统计
  getQuestionStats: () => request.get('/api/questions/stats/'),
  
  // 批量操作题目
  batchOperateQuestions: (data) => request.post('/api/questions/batch/', data)
}

// 答案相关API
export const answerApi = {
  // 获取答案列表
  getAnswers: (params) => request.get('/api/answers/', params),
  
  // 获取答案详情
  getAnswerDetail: (id) => request.get(`/api/answers/${id}/`),
  
  // 创建答案
  createAnswer: (data) => request.post('/api/answers/', data),
  
  // 更新答案
  updateAnswer: (id, data) => request.put(`/api/answers/${id}/`, data),
  
  // 删除答案
  deleteAnswer: (id) => request.delete(`/api/answers/${id}/`),
  
  // 获取题目答案
  getQuestionAnswers: (questionId) => request.get(`/api/answers/question/${questionId}/`),
  
  // 请求AI解答
  requestAIAnswer: (data) => request.post('/api/answers/ai-answer/', data),
  
  // 评价答案
  rateAnswer: (id, data) => request.post(`/api/answers/${id}/rate/`, data)
}

// 分类相关API
export const categoryApi = {
  // 获取分类列表
  getCategories: (params) => request.get('/api/categories/', params),
  
  // 获取分类详情
  getCategoryDetail: (id) => request.get(`/api/categories/${id}/`),
  
  // 创建分类
  createCategory: (data) => request.post('/api/categories/', data),
  
  // 更新分类
  updateCategory: (id, data) => request.put(`/api/categories/${id}/`, data),
  
  // 删除分类
  deleteCategory: (id) => request.delete(`/api/categories/${id}/`),
  
  // 获取分类统计
  getCategoryStats: () => request.get('/api/categories/stats/'),
  
  // 获取分类树
  getCategoryTree: () => request.get('/api/categories/tree/')
}

// 搜索相关API
export const searchApi = {
  // 搜索题目
  searchQuestions: (params) => request.get('/api/search/questions/', params),
  
  // 搜索答案
  searchAnswers: (params) => request.get('/api/search/answers/', params),
  
  // 获取搜索建议
  getSearchSuggestions: (params) => request.get('/api/search/suggestions/', params),
  
  // 获取热门搜索
  getHotSearches: () => request.get('/api/search/hot/'),
  
  // 记录搜索历史
  recordSearchHistory: (data) => request.post('/api/search/history/', data),
  
  // 获取搜索历史
  getSearchHistory: (params) => request.get('/api/search/history/', params),
  
  // 清除搜索历史
  clearSearchHistory: () => request.delete('/api/search/history/')
}

// 文件上传相关API
export const uploadApi = {
  // 上传图片
  uploadImage: (filePath, formData) => request.uploadFile(filePath, '/api/upload/image/', formData),
  
  // 上传文件
  uploadFile: (filePath, formData) => request.uploadFile(filePath, '/api/upload/file/', formData),
  
  // 获取上传凭证
  getUploadToken: (data) => request.post('/api/upload/token/', data)
}

// 系统相关API
export const systemApi = {
  // 获取系统配置
  getSystemConfig: () => request.get('/api/system/config/'),
  
  // 获取版本信息
  getVersionInfo: () => request.get('/api/system/version/'),
  
  // 检查更新
  checkUpdate: () => request.get('/api/system/check-update/'),
  
  // 提交反馈
  submitFeedback: (data) => request.post('/api/system/feedback/', data),
  
  // 获取公告列表
  getAnnouncements: (params) => request.get('/api/system/announcements/', params),
  
  // 获取公告详情
  getAnnouncementDetail: (id) => request.get(`/api/system/announcements/${id}/`)
}

// 导出所有API
export default {
  authApi,
  questionApi,
  answerApi,
  categoryApi,
  searchApi,
  uploadApi,
  systemApi
}