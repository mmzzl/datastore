import request from './request'

// 用户相关API
export const login = (data) => {
  return request({
    url: '/api/user/login',
    method: 'post',
    data
  })
}

export const register = (data) => {
  return request({
    url: '/api/user/register',
    method: 'post',
    data
  })
}

export const logout = () => {
  return request({
    url: '/api/user/logout',
    method: 'post'
  })
}

export const getUserInfo = () => {
  return request({
    url: '/api/user/info',
    method: 'get'
  })
}

export const updateUserInfo = (data) => {
  return request({
    url: '/api/user/info',
    method: 'put',
    data
  })
}

export const changePassword = (data) => {
  return request({
    url: '/api/user/password',
    method: 'put',
    data
  })
}