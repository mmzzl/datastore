import request from './request'

// 分类相关API
export const getCategoryList = () => {
  return request({
    url: '/api/categories',
    method: 'get'
  })
}

export const getCategoryDetail = (id) => {
  return request({
    url: `/api/categories/${id}`,
    method: 'get'
  })
}