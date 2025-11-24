import store from '../store'
import uniCompat from '../utils/uniCompat'

// 创建请求实例
const service = {
  baseURL: process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8080'  // 开发环境API地址
    : 'https://api.example.com', // 生产环境API地址
  timeout: 10000 // 请求超时时间
}

// 请求拦截器
const requestInterceptor = (config) => {
  // 在发送请求之前做些什么
  
  // 添加token到请求头
  const token = store.getters['user/token']
  if (token) {
    config.header = config.header || {}
    config.header['Authorization'] = `Bearer ${token}`
  }
  
  return config
}

// 响应拦截器
const responseInterceptor = (res, resolve, reject) => {
  // 对响应数据做点什么
  const data = res.data || res
  
  // 如果返回的状态码不是200，说明接口出错了
  if (data.code !== 200) {
    uniCompat.toast.showToast({
      title: data.message || '服务器错误',
      icon: 'none',
      duration: 2000
    })
    
    // 401: 未登录或token过期
    // 403: 权限不足
    if (data.code === 401 || data.code === 403) {
      // 重新登录
      store.dispatch('user/logout').then(() => {
        // 跳转到登录页
        uniCompat.navigation.navigateTo({
          url: '/pages/login/index'
        })
      })
    }
    
    return reject(new Error(data.message || '服务器错误'))
  } else {
    return resolve(data)
  }
}

// 错误处理
const errorHandler = (error, reject) => {
  // 对响应错误做点什么
  console.log('err' + error)
  
  let message = '网络错误'
  
  if (error.statusCode) {
    switch (error.statusCode) {
      case 400:
        message = '请求参数错误'
        break
      case 401:
        message = '未授权，请登录'
        break
      case 403:
        message = '拒绝访问'
        break
      case 404:
        message = '请求地址出错'
        break
      case 408:
        message = '请求超时'
        break
      case 500:
        message = '服务器内部错误'
        break
      case 501:
        message = '服务未实现'
        break
      case 502:
        message = '网关错误'
        break
      case 503:
        message = '服务不可用'
        break
      case 504:
        message = '网关超时'
        break
      case 505:
        message = 'HTTP版本不受支持'
        break
      default:
        message = `连接出错(${error.statusCode})!`
    }
  } else if (error.errMsg && error.errMsg.includes('timeout')) {
    message = '请求超时'
  } else if (error.errMsg && error.errMsg.includes('fail')) {
    message = '网络连接异常'
  }
  
  uniCompat.toast.showToast({
    title: message,
    icon: 'none',
    duration: 2000
  })
  
  return reject(error)
}

// 封装请求方法
const request = (config) => {
  return new Promise((resolve, reject) => {
    // 应用请求拦截器
    config = requestInterceptor(config)
    
    // 设置完整URL
    if (config.url && !config.url.startsWith('http')) {
      config.url = service.baseURL + config.url
    }
    
    // 发起请求
    uniCompat.request({
      url: config.url,
      method: config.method || 'GET',
      data: config.data,
      header: config.header,
      timeout: config.timeout || service.timeout,
      success: (res) => {
        responseInterceptor(res, resolve, reject)
      },
      fail: (error) => {
        errorHandler(error, reject)
      }
    })
  })
}

// 导出各种请求方法
export const get = (url, params = {}, config = {}) => {
  return request({
    url,
    method: 'GET',
    data: params,
    ...config
  })
}

export const post = (url, data = {}, config = {}) => {
  return request({
    url,
    method: 'POST',
    data,
    ...config
  })
}

export const put = (url, data = {}, config = {}) => {
  return request({
    url,
    method: 'PUT',
    data,
    ...config
  })
}

export const del = (url, data = {}, config = {}) => {
  return request({
    url,
    method: 'DELETE',
    data,
    ...config
  })
}

export default request