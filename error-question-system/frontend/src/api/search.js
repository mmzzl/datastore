import request from './request'

// 搜索相关API
export const searchQuestions = (params) => {
  return request({
    url: '/api/search/questions',
    method: 'get',
    params
  })
}

export const getSearchHistory = () => {
  return request({
    url: '/api/search/history',
    method: 'get'
  })
}

export const clearSearchHistory = () => {
  return request({
    url: '/api/search/history',
    method: 'delete'
  })
}