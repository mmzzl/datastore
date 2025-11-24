// uni-app API 兼容性工具
// 在H5环境中提供uni API的替代实现

// 检查是否在uni-app环境中
const isUniApp = () => {
  return typeof uni !== 'undefined'
}

// 初始化uni对象，确保在H5环境中也能使用uni API
const initUniObject = () => {
  // 如果已经存在uni对象，则不需要初始化
  if (typeof uni !== 'undefined') {
    return
  }

  // 在H5环境中创建uni对象
  window.uni = {
    // 存储相关API
    getStorageSync(key) {
      try {
        return localStorage.getItem(key) || ''
      } catch (e) {
        console.error('getStorageSync error:', e)
        return ''
      }
    },
    setStorageSync(key, data) {
      try {
        localStorage.setItem(key, data)
      } catch (e) {
        console.error('setStorageSync error:', e)
      }
    },
    removeStorageSync(key) {
      try {
        localStorage.removeItem(key)
      } catch (e) {
        console.error('removeStorageSync error:', e)
      }
    },
    
    // 路由导航相关API
    navigateTo(options) {
      if (options && options.url) {
        window.location.href = options.url
      }
    },
    redirectTo(options) {
      if (options && options.url) {
        window.location.replace(options.url)
      }
    },
    switchTab(options) {
      if (options && options.url) {
        window.location.href = options.url
      }
    },
    navigateBack(options) {
      const delta = options && options.delta ? options.delta : 1
      window.history.go(-delta)
    },
    
    // 提示相关API
    showToast(options) {
      const title = options && options.title ? options.title : ''
      const duration = options && options.duration ? options.duration : 1500
      
      // 创建一个简单的toast提示
      const toast = document.createElement('div')
      toast.style.position = 'fixed'
      toast.style.top = '50%'
      toast.style.left = '50%'
      toast.style.transform = 'translate(-50%, -50%)'
      toast.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'
      toast.style.color = 'white'
      toast.style.padding = '10px 20px'
      toast.style.borderRadius = '4px'
      toast.style.zIndex = '9999'
      toast.textContent = title
      
      document.body.appendChild(toast)
      
      setTimeout(() => {
        document.body.removeChild(toast)
      }, duration)
    },
    showLoading(options) {
      const title = options && options.title ? options.title : '加载中'
      
      // 创建一个简单的loading提示
      const loading = document.createElement('div')
      loading.id = 'uni-loading'
      loading.style.position = 'fixed'
      loading.style.top = '0'
      loading.style.left = '0'
      loading.style.width = '100%'
      loading.style.height = '100%'
      loading.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'
      loading.style.display = 'flex'
      loading.style.justifyContent = 'center'
      loading.style.alignItems = 'center'
      loading.style.zIndex = '9999'
      
      const loadingContent = document.createElement('div')
      loadingContent.style.backgroundColor = 'white'
      loadingContent.style.padding = '20px'
      loadingContent.style.borderRadius = '4px'
      loadingContent.style.textAlign = 'center'
      loadingContent.innerHTML = `<div>${title}</div>`
      
      loading.appendChild(loadingContent)
      document.body.appendChild(loading)
    },
    hideLoading() {
      const loading = document.getElementById('uni-loading')
      if (loading) {
        document.body.removeChild(loading)
      }
    },
    showModal(options) {
      const title = options && options.title ? options.title : '提示'
      const content = options && options.content ? options.content : ''
      const showCancel = options && options.showCancel !== undefined ? options.showCancel : true
      const cancelText = options && options.cancelText ? options.cancelText : '取消'
      const confirmText = options && options.confirmText ? options.confirmText : '确定'
      const success = options && options.success ? options.success : () => {}
      
      // 创建一个简单的模态框
      const modal = document.createElement('div')
      modal.style.position = 'fixed'
      modal.style.top = '0'
      modal.style.left = '0'
      modal.style.width = '100%'
      modal.style.height = '100%'
      modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'
      modal.style.display = 'flex'
      modal.style.justifyContent = 'center'
      modal.style.alignItems = 'center'
      modal.style.zIndex = '9999'
      
      const modalContent = document.createElement('div')
      modalContent.style.backgroundColor = 'white'
      modalContent.style.padding = '20px'
      modalContent.style.borderRadius = '4px'
      modalContent.style.minWidth = '300px'
      modalContent.innerHTML = `
        <div style="margin-bottom: 15px; font-weight: bold;">${title}</div>
        <div style="margin-bottom: 20px;">${content}</div>
        <div style="display: flex; justify-content: flex-end;">
          ${showCancel ? `<button id="modal-cancel" style="margin-right: 10px; padding: 5px 10px;">${cancelText}</button>` : ''}
          <button id="modal-confirm" style="padding: 5px 10px;">${confirmText}</button>
        </div>
      `
      
      modal.appendChild(modalContent)
      document.body.appendChild(modal)
      
      const confirmBtn = document.getElementById('modal-confirm')
      confirmBtn.addEventListener('click', () => {
        document.body.removeChild(modal)
        success({ confirm: true, cancel: false })
      })
      
      if (showCancel) {
        const cancelBtn = document.getElementById('modal-cancel')
        cancelBtn.addEventListener('click', () => {
          document.body.removeChild(modal)
          success({ confirm: false, cancel: true })
        })
      }
    },
    
    // 网络请求API
    request(options) {
      const { url, method = 'GET', data = {}, header = {}, success, fail, complete } = options
      
      // 创建Promise对象
      return new Promise((resolve, reject) => {
        // 使用fetch API发送请求
        const fetchOptions = {
          method: method.toUpperCase(),
          headers: {
            'Content-Type': 'application/json',
            ...header
          }
        }
        
        // 如果是GET请求，将数据附加到URL
        let requestUrl = url
        if (method.toUpperCase() === 'GET' && Object.keys(data).length > 0) {
          const params = new URLSearchParams()
          for (const key in data) {
            params.append(key, data[key])
          }
          requestUrl = `${url}${url.includes('?') ? '&' : '?'}${params.toString()}`
        } else {
          // 如果是POST/PUT等请求，将数据放入请求体
          fetchOptions.body = JSON.stringify(data)
        }
        
        fetch(requestUrl, fetchOptions)
          .then(response => {
            return response.json().then(data => {
              const result = {
                statusCode: response.status,
                data: data
              }
              
              // 调用成功回调
              if (success) {
                success(result)
              }
              
              // 调用完成回调
              if (complete) {
                complete(result)
              }
              
              // 返回结果
              resolve(result)
            })
          })
          .catch(error => {
            console.error('Request error:', error)
            
            const errorResult = {
              statusCode: 0,
              data: null,
              errMsg: error.message
            }
            
            // 调用失败回调
            if (fail) {
              fail(errorResult)
            }
            
            // 调用完成回调
            if (complete) {
              complete(errorResult)
            }
            
            // 返回错误
            reject(errorResult)
          })
      })
    },
    
    // 其他API
    stopPullDownRefresh() {
      console.warn('uni.stopPullDownRefresh is not fully supported in H5 environment')
    },
    login(options) {
      console.warn('uni.login is not supported in H5 environment')
      const success = options && options.success ? options.success : () => {}
      const fail = options && options.fail ? options.fail : () => {}
      const complete = options && options.complete ? options.complete : () => {}
      
      // 模拟登录成功
      success({
        code: 'mock_code_' + Date.now()
      })
      complete()
    },
    getUserInfo(options) {
      console.warn('uni.getUserInfo is not supported in H5 environment')
      const success = options && options.success ? options.success : () => {}
      const fail = options && options.fail ? options.fail : () => {}
      const complete = options && options.complete ? options.complete : () => {}
      
      // 模拟获取用户信息
      success({
        userInfo: {
          nickName: 'H5用户',
          avatarUrl: '',
          gender: 0,
          city: '',
          province: '',
          country: '',
          language: 'zh_CN'
        }
      })
      complete()
    },
    scanCode(options) {
      console.warn('uni.scanCode is not supported in H5 environment')
      const fail = options && options.fail ? options.fail : () => {}
      
      // 模拟扫码失败
      fail({
        errMsg: 'uni.scanCode:fail scan code not supported in H5 environment'
      })
    }
  }
}

// 存储相关API
const storage = {
  getStorageSync(key) {
    if (isUniApp()) {
      return uni.getStorageSync(key)
    } else if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(key)
    }
    return ''
  },
  
  setStorageSync(key, value) {
    if (isUniApp()) {
      uni.setStorageSync(key, value)
    } else if (typeof localStorage !== 'undefined') {
      localStorage.setItem(key, value)
    }
  },
  
  removeStorageSync(key) {
    if (isUniApp()) {
      uni.removeStorageSync(key)
    } else if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(key)
    }
  }
}

// 路由导航API
const navigation = {
  navigateTo(options) {
    if (isUniApp()) {
      uni.navigateTo(options)
    } else if (typeof window !== 'undefined') {
      // H5环境下使用window.location
      window.location.href = options.url
    }
  },
  
  navigateBack(delta = 1) {
    if (isUniApp()) {
      uni.navigateBack({ delta })
    } else if (typeof window !== 'undefined' && window.history) {
      window.history.go(-delta)
    }
  },
  
  redirectTo(options) {
    if (isUniApp()) {
      uni.redirectTo(options)
    } else if (typeof window !== 'undefined') {
      window.location.replace(options.url)
    }
  },
  
  switchTab(options) {
    if (isUniApp()) {
      uni.switchTab(options)
    } else if (typeof window !== 'undefined') {
      window.location.href = options.url
    }
  }
}

// 提示相关API
const toast = {
  showToast(options) {
    const { title, icon = 'none', duration = 2000 } = options
    
    if (isUniApp()) {
      uni.showToast({
        title,
        icon,
        duration
      })
    } else {
      // H5环境下的替代方案
      console.log(title)
      if (typeof alert !== 'undefined') {
        alert(title)
      }
    }
  },
  
  showLoading(options = {}) {
    const { title = '加载中' } = options
    
    if (isUniApp()) {
      uni.showLoading({ title })
    } else {
      console.log(title)
    }
  },
  
  hideLoading() {
    if (isUniApp()) {
      uni.hideLoading()
    } else {
      console.log('隐藏加载提示')
    }
  },
  
  showModal(options) {
    if (isUniApp()) {
      return uni.showModal(options)
    } else {
      // H5环境下的替代方案
      const { title = '提示', content = '' } = options
      const result = confirm(`${title}\n${content}`)
      return Promise.resolve({
        confirm: result,
        cancel: !result
      })
    }
  },
  
  showActionSheet(options) {
    if (isUniApp()) {
      return uni.showActionSheet(options)
    } else {
      // H5环境下的替代方案
      const { itemList = [] } = options
      const result = prompt(`请选择:\n${itemList.map((item, index) => `${index + 1}. ${item}`).join('\n')}`)
      const tapIndex = parseInt(result) - 1
      
      if (!isNaN(tapIndex) && tapIndex >= 0 && tapIndex < itemList.length) {
        return Promise.resolve({ tapIndex, errMsg: 'showActionSheet:ok' })
      } else {
        return Promise.resolve({ tapIndex: -1, errMsg: 'showActionSheet:fail cancel' })
      }
    }
  }
}

// 其他API
const others = {
  stopPullDownRefresh() {
    if (isUniApp()) {
      uni.stopPullDownRefresh()
    }
  },
  
  chooseImage(options) {
    if (isUniApp()) {
      return uni.chooseImage(options)
    } else {
      // H5环境下的替代方案
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      
      return new Promise((resolve, reject) => {
        input.onchange = (event) => {
          const file = event.target.files[0]
          if (file) {
            const reader = new FileReader()
            reader.onload = (e) => {
              resolve({
                tempFilePaths: [e.target.result],
                tempFiles: [{ path: e.target.result, size: file.size }]
              })
            }
            reader.onerror = reject
            reader.readAsDataURL(file)
          } else {
            reject(new Error('未选择文件'))
          }
        }
        input.click()
      })
    }
  },
  
  previewImage(options) {
    if (isUniApp()) {
      uni.previewImage(options)
    } else {
      // H5环境下的替代方案
      const { urls = [], current = 0 } = options
      if (urls.length > 0) {
        const index = typeof current === 'number' ? current : urls.indexOf(current)
        if (index >= 0 && index < urls.length) {
          window.open(urls[index], '_blank')
        }
      }
    }
  },
  
  setClipboardData(options) {
    if (isUniApp()) {
      uni.setClipboardData(options)
    } else if (typeof navigator !== 'undefined' && navigator.clipboard) {
      const { data = '' } = options
      navigator.clipboard.writeText(data).then(() => {
        if (options.success) options.success()
      }).catch(() => {
        if (options.fail) options.fail()
      })
    }
  },
  
  makePhoneCall(options) {
    if (isUniApp()) {
      uni.makePhoneCall(options)
    } else if (typeof window !== 'undefined') {
      const { phoneNumber = '' } = options
      window.location.href = `tel:${phoneNumber}`
    }
  },
  
  share(options) {
    if (isUniApp()) {
      uni.share(options)
    } else {
      // H5环境下的替代方案
      console.log('分享功能:', options)
    }
  }
}

// 导出所有API
export default {
  isUniApp,
  initUniObject,
  storage,
  navigation,
  toast,
  others
}