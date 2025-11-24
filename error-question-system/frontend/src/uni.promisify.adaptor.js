// uni.promisify.adaptor.js
// 此文件用于在H5环境下将uni-app的API转换为Promise形式

let promisifyFunction

// #ifdef H5
promisifyFunction = function(api) {
  return (options = {}) => {
    return new Promise((resolve, reject) => {
      api({
        ...options,
        success: (res) => {
          resolve(res)
        },
        fail: (err) => {
          reject(err)
        }
      })
    })
  }
}
// #endif

// #ifndef H5
// 非H5环境不需要适配器
promisifyFunction = function(api) {
  return api
}
// #endif

export default promisifyFunction