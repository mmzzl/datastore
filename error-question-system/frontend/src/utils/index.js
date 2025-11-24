// 格式化日期
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '';
  
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

// 相对时间
export function timeAgo(date) {
  if (!date) return '';
  
  const now = new Date();
  const past = new Date(date);
  const diff = now - past;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return `${days}天前`;
  } else if (hours > 0) {
    return `${hours}小时前`;
  } else if (minutes > 0) {
    return `${minutes}分钟前`;
  } else {
    return '刚刚';
  }
}

// 防抖函数
export function debounce(func, wait) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func.apply(context, args);
    }, wait);
  };
}

// 节流函数
export function throttle(func, wait) {
  let lastTime = 0;
  return function(...args) {
    const context = this;
    const now = Date.now();
    if (now - lastTime >= wait) {
      func.apply(context, args);
      lastTime = now;
    }
  };
}

// 深拷贝
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  
  const clone = Array.isArray(obj) ? [] : {};
  
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      clone[key] = deepClone(obj[key]);
    }
  }
  
  return clone;
}

// 生成唯一ID
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// 获取文件扩展名
export function getFileExtension(filename) {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

// 检查是否为图片文件
export function isImageFile(filename) {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'];
  const extension = getFileExtension(filename).toLowerCase();
  return imageExtensions.includes(extension);
}

// 格式化文件大小
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 验证手机号
export function validatePhoneNumber(phone) {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
}

// 验证邮箱
export function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// 验证密码强度
export function validatePassword(password) {
  // 至少8位，包含大小写字母和数字
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
}

// 获取难度等级文本
export function getDifficultyText(level) {
  const levels = {
    1: '简单',
    2: '中等',
    3: '困难',
    4: '非常困难'
  };
  
  return levels[level] || '未知';
}

// 获取难度等级颜色
export function getDifficultyColor(level) {
  const colors = {
    1: '#67C23A', // 绿色
    2: '#E6A23C', // 橙色
    3: '#F56C6C', // 红色
    4: '#909399'  // 灰色
  };
  
  return colors[level] || '#909399';
}

// 获取状态文本
export function getStatusText(status) {
  const statuses = {
    0: '未解决',
    1: '已解决',
    2: '已掌握'
  };
  
  return statuses[status] || '未知';
}

// 获取状态颜色
export function getStatusColor(status) {
  const colors = {
    0: '#F56C6C', // 红色
    1: '#E6A23C', // 橙色
    2: '#67C23A'  // 绿色
  };
  
  return colors[status] || '#909399';
}

// 复制到剪贴板
export function copyToClipboard(text) {
  return new Promise((resolve, reject) => {
    try {
      // #ifdef H5
      navigator.clipboard.writeText(text).then(() => {
        resolve();
      }).catch(() => {
        reject(new Error('复制失败'));
      });
      // #endif
      
      // #ifndef H5
      uni.setClipboardData({
        data: text,
        success: () => {
          resolve();
        },
        fail: () => {
          reject(new Error('复制失败'));
        }
      });
      // #endif
    } catch (error) {
      reject(error);
    }
  });
}

// 打电话
export function makePhoneCall(phoneNumber) {
  return new Promise((resolve, reject) => {
    uni.makePhoneCall({
      phoneNumber,
      success: () => {
        resolve();
      },
      fail: () => {
        reject(new Error('拨打电话失败'));
      }
    });
  });
}

// 打开网页
export function openWebpage(url) {
  return new Promise((resolve, reject) => {
    // #ifdef H5
    window.open(url, '_blank');
    resolve();
    // #endif
    
    // #ifndef H5
    uni.navigateTo({
      url: `/pages/webview/index?url=${encodeURIComponent(url)}`,
      success: () => {
        resolve();
      },
      fail: () => {
        reject(new Error('打开网页失败'));
      }
    });
    // #endif
  });
}

// 显示提示消息
export function showToast(title, icon = 'none', duration = 2000) {
  uni.showToast({
    title,
    icon,
    duration
  });
}

// 显示加载中
export function showLoading(title = '加载中...') {
  uni.showLoading({
    title
  });
}

// 隐藏加载中
export function hideLoading() {
  uni.hideLoading();
}

// 显示确认对话框
export function showModal(title, content) {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      success: (res) => {
        resolve(res.confirm);
      }
    });
  });
}

// 显示操作菜单
export function showActionSheet(itemList) {
  return new Promise((resolve, reject) => {
    uni.showActionSheet({
      itemList,
      success: (res) => {
        resolve(res.tapIndex);
      },
      fail: () => {
        reject(new Error('取消选择'));
      }
    });
  });
}