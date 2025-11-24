import request from './request'

// 错题相关API
export const getQuestionList = (params) => {
  return request({
    url: '/api/questions',
    method: 'get',
    params
  })
}

export const getQuestionDetail = (id) => {
  return request({
    url: `/api/questions/${id}`,
    method: 'get'
  })
}

export const addQuestion = (data) => {
  return request({
    url: '/api/questions',
    method: 'post',
    data
  })
}

export const updateQuestion = (id, data) => {
  return request({
    url: `/api/questions/${id}`,
    method: 'put',
    data
  })
}

export const deleteQuestion = (id) => {
  return request({
    url: `/api/questions/${id}`,
    method: 'delete'
  })
}

export const uploadQuestionImage = (data) => {
  return request({
    url: '/api/questions/upload',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}