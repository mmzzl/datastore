// API基础配置
const config = {
  // 开发环境API地址
  dev: {
    baseUrl: 'http://localhost:8000'
  },
  // 生产环境API地址
  prod: {
    baseUrl: 'https://api.errorquestion.com'
  }
}

// 获取当前环境配置
const getConfig = () => {
  // #ifdef H5
  return process.env.NODE_ENV === 'production' ? config.prod : config.dev
  // #endif
  
  // #ifndef H5
  return config.dev
  // #endif
}

// 当前配置
const currentConfig = getConfig()

// 请求拦截器
const requestInterceptor = (options) => {
  // 添加基础URL
  if (!options.url.startsWith('http')) {
    options.url = currentConfig.baseUrl + options.url
  }
  
  // 添加请求头
  options.header = {
    'Content-Type': 'application/json',
    ...options.header
  }
  
  // 添加token
  const token = uni.getStorageSync('token')
  if (token) {
    options.header.Authorization = `Bearer ${token}`
  }
  
  // 显示加载中
  if (options.loading !== false) {
    uni.showLoading({
      title: options.loadingText || '请求中...',
      mask: true
    })
  }
  
  return options
}

// 响应拦截器
const responseInterceptor = (response, options) => {
  // 隐藏加载中
  if (options.loading !== false) {
    uni.hideLoading()
  }
  
  // 处理HTTP状态码
  if (response.statusCode === 200) {
    // 处理业务状态码
    if (response.data.code === 200) {
      return response.data
    } else if (response.data.code === 401) {
      // token过期，跳转到登录页
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
      uni.showToast({
        title: '登录已过期，请重新登录',
        icon: 'none'
      })
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/profile/login'
        })
      }, 1500)
      return Promise.reject(response.data)
    } else {
      // 业务错误
      uni.showToast({
        title: response.data.message || '请求失败',
        icon: 'none'
      })
      return Promise.reject(response.data)
    }
  } else {
    // HTTP错误
    uni.showToast({
      title: `请求失败: ${response.statusCode}`,
      icon: 'none'
    })
    return Promise.reject(response)
  }
}

// 请求错误处理
const errorHandler = (error, options) => {
  // 隐藏加载中
  if (options.loading !== false) {
    uni.hideLoading()
  }
  
  uni.showToast({
    title: '网络错误，请检查网络连接',
    icon: 'none'
  })
  
  return Promise.reject(error)
}

// 封装请求方法
const request = (options) => {
  // 请求拦截
  options = requestInterceptor(options)
  
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      success: (res) => {
        try {
          const result = responseInterceptor(res, options)
          resolve(result)
        } catch (error) {
          reject(error)
        }
      },
      fail: (error) => {
        errorHandler(error, options)
        reject(error)
      }
    })
  })
}

// 封装GET请求
const get = (url, data = {}, options = {}) => {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  })
}

// 封装POST请求
const post = (url, data = {}, options = {}) => {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

// 封装PUT请求
const put = (url, data = {}, options = {}) => {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

// 封装DELETE请求
const del = (url, data = {}, options = {}) => {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

// 封装文件上传
const uploadFile = (filePath, url, formData = {}, options = {}) => {
  // 添加基础URL
  if (!url.startsWith('http')) {
    url = currentConfig.baseUrl + url
  }
  
  // 添加token
  const token = uni.getStorageSync('token')
  const header = {
    'Authorization': token ? `Bearer ${token}` : '',
    ...options.header
  }
  
  // 显示加载中
  if (options.loading !== false) {
    uni.showLoading({
      title: options.loadingText || '上传中...',
      mask: true
    })
  }
  
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath,
      name: options.name || 'file',
      formData,
      header,
      success: (res) => {
        // 隐藏加载中
        if (options.loading !== false) {
          uni.hideLoading()
        }
        
        try {
          const data = JSON.parse(res.data)
          if (data.code === 200) {
            resolve(data)
          } else {
            uni.showToast({
              title: data.message || '上传失败',
              icon: 'none'
            })
            reject(data)
          }
        } catch (error) {
          uni.showToast({
            title: '上传失败',
            icon: 'none'
          })
          reject(error)
        }
      },
      fail: (error) => {
        // 隐藏加载中
        if (options.loading !== false) {
          uni.hideLoading()
        }
        
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        })
        reject(error)
      }
    })
  })
}

// 导出API方法
export default {
  request,
  get,
  post,
  put,
  delete: del,
  uploadFile,
  config: currentConfig
}