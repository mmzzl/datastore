const BASE_URL = 'http://127.0.0.1:8000/api/';

let isRefreshing = false;
let requests = [];

const logout = () => {
  uni.removeStorageSync('token');
  uni.removeStorageSync('refresh_token');
  uni.removeStorageSync('user');
  uni.showToast({
    title: '登录已过期，请重新登录',
    icon: 'none'
  });
  setTimeout(() => {
    uni.reLaunch({
      url: '/pages/login/login'
    });
  }, 1500);
};

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token');
    const header = {
      'Content-Type': 'application/json',
      ...options.header,
    };

    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: header,
      success: async (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          // If the failed request was to the refresh endpoint itself, logout
          if (options.url.includes('auth/token/refresh/')) {
            logout();
            reject(res);
            return;
          }

          const refreshToken = uni.getStorageSync('refresh_token');
          if (!refreshToken) {
            logout();
            reject(res);
            return;
          }

          if (!isRefreshing) {
            isRefreshing = true;
            try {
              const refreshRes = await new Promise((refResolve, refReject) => {
                uni.request({
                  url: BASE_URL + 'auth/token/refresh/',
                  method: 'POST',
                  data: { refresh: refreshToken },
                  header: { 'Content-Type': 'application/json' },
                  success: (r) => {
                    if (r.statusCode === 200) {
                      refResolve(r.data);
                    } else {
                      refReject(r);
                    }
                  },
                  fail: refReject
                });
              });

              if (refreshRes.access) {
                uni.setStorageSync('token', refreshRes.access);
                if (refreshRes.refresh) {
                  uni.setStorageSync('refresh_token', refreshRes.refresh);
                }
                
                // Execute all queued requests
                requests.forEach((cb) => cb(refreshRes.access));
                requests = [];
                
                // Retry the current request
                resolve(request(options));
              } else {
                 throw new Error('No access token received');
              }
            } catch (e) {
              console.error('Token refresh failed:', e);
              requests.forEach((cb) => cb(null)); // Cancel queued requests? Or just fail them.
              requests = [];
              logout();
              reject(res);
            } finally {
              isRefreshing = false;
            }
          } else {
            // If refreshing, queue the request
            return new Promise((resolve) => {
              requests.push((newToken) => {
                if (newToken) {
                    resolve(request(options));
                } else {
                    reject(res);
                }
              });
            }).then(resolve).catch(reject);
          }
        } else {
          uni.showToast({
            title: res.data.error?.message || '请求失败',
            icon: 'none'
          });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络错误',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};

export default request;
