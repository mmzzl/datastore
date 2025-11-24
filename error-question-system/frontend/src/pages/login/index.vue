<template>
  <view class="login-page">
    <view class="login-container">
      <view class="login-header">
        <image class="logo" src="/static/images/logo.png" mode="aspectFit"></image>
        <text class="app-name">智能错题本</text>
        <text class="app-desc">高效学习，精准提升</text>
      </view>

      <view class="login-form">
        <view class="form-item">
          <input 
            class="form-input" 
            type="text" 
            placeholder="请输入用户名/手机号" 
            v-model="formData.username"
            :class="{ 'error': errors.username }"
          />
          <text class="error-text" v-if="errors.username">{{ errors.username }}</text>
        </view>

        <view class="form-item">
          <input 
            class="form-input" 
            :type="showPassword ? 'text' : 'password'" 
            placeholder="请输入密码" 
            v-model="formData.password"
            :class="{ 'error': errors.password }"
          />
          <text class="toggle-password" @click="togglePassword">
            {{ showPassword ? '隐藏' : '显示' }}
          </text>
          <text class="error-text" v-if="errors.password">{{ errors.password }}</text>
        </view>

        <view class="form-options">
          <label class="checkbox-container">
            <checkbox :checked="formData.rememberMe" @change="handleRememberChange" />
            <text class="checkbox-text">记住我</text>
          </label>
          <text class="forgot-password" @click="handleForgotPassword">忘记密码？</text>
        </view>

        <button class="login-btn" @click="handleLogin" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>

        <view class="register-link">
          <text>还没有账号？</text>
          <text class="link-text" @click="navigateToRegister">立即注册</text>
        </view>
      </view>

      <view class="login-footer">
        <text class="footer-text">其他登录方式</text>
        <view class="other-login">
          <view class="login-option" @click="handleWechatLogin">
            <image class="login-icon" src="/static/images/wechat.png" mode="aspectFit"></image>
            <text>微信</text>
          </view>
          <view class="login-option" @click="handleQQLogin">
            <image class="login-icon" src="/static/images/qq.png" mode="aspectFit"></image>
            <text>QQ</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  data() {
    return {
      formData: {
        username: '',
        password: '',
        rememberMe: false
      },
      errors: {
        username: '',
        password: ''
      },
      showPassword: false,
      isLoading: false
    }
  },
  onLoad() {
    // 检查是否已登录
    const token = uni.getStorageSync('token');
    if (token) {
      uni.switchTab({
        url: '/pages/index/index'
      });
    }
    
    // 如果记住我，则填充上次登录的用户名
    const savedUsername = uni.getStorageSync('savedUsername');
    if (savedUsername) {
      this.formData.username = savedUsername;
      this.formData.rememberMe = true;
    }
  },
  methods: {
    ...mapActions(['login']),
    
    // 切换密码显示/隐藏
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
    
    // 处理记住我选项变化
    handleRememberChange(e) {
      this.formData.rememberMe = e.detail.value.length > 0;
    },
    
    // 表单验证
    validateForm() {
      let isValid = true;
      this.errors = {
        username: '',
        password: ''
      };
      
      if (!this.formData.username.trim()) {
        this.errors.username = '请输入用户名或手机号';
        isValid = false;
      }
      
      if (!this.formData.password.trim()) {
        this.errors.password = '请输入密码';
        isValid = false;
      } else if (this.formData.password.length < 6) {
        this.errors.password = '密码长度不能少于6位';
        isValid = false;
      }
      
      return isValid;
    },
    
    // 处理登录
    async handleLogin() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isLoading = true;
      
      try {
        await this.login({
          username: this.formData.username,
          password: this.formData.password
        });
        
        // 如果选择记住我，则保存用户名
        if (this.formData.rememberMe) {
          uni.setStorageSync('savedUsername', this.formData.username);
        } else {
          uni.removeStorageSync('savedUsername');
        }
        
        // 登录成功，跳转到首页
        uni.switchTab({
          url: '/pages/index/index'
        });
        
        uni.showToast({
          title: '登录成功',
          icon: 'success'
        });
      } catch (error) {
        console.error('登录失败:', error);
        uni.showToast({
          title: error.message || '登录失败，请检查用户名和密码',
          icon: 'none'
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    // 处理忘记密码
    handleForgotPassword() {
      uni.showModal({
        title: '忘记密码',
        content: '请联系客服重置密码',
        showCancel: false
      });
    },
    
    // 跳转到注册页面
    navigateToRegister() {
      uni.navigateTo({
        url: '/pages/register/index'
      });
    },
    
    // 处理微信登录
    handleWechatLogin() {
      uni.showToast({
        title: '微信登录功能开发中',
        icon: 'none'
      });
    },
    
    // 处理QQ登录
    handleQQLogin() {
      uni.showToast({
        title: 'QQ登录功能开发中',
        icon: 'none'
      });
    }
  }
}
</script>

<style>
.login-page {
  height: 100vh;
  background-color: #f8f8f8;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-container {
  width: 90%;
  max-width: 600rpx;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.logo {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 20rpx;
}

.app-name {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.app-desc {
  font-size: 28rpx;
  color: #666;
}

.login-form {
  background-color: white;
  border-radius: 16rpx;
  padding: 40rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.form-item {
  margin-bottom: 30rpx;
  position: relative;
}

.form-input {
  width: 100%;
  height: 88rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-input.error {
  border-color: #f56c6c;
}

.form-input:focus {
  border-color: #3c9cff;
}

.toggle-password {
  position: absolute;
  right: 20rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 24rpx;
  color: #999;
}

.error-text {
  color: #f56c6c;
  font-size: 24rpx;
  margin-top: 8rpx;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.checkbox-container {
  display: flex;
  align-items: center;
}

.checkbox-text {
  font-size: 26rpx;
  color: #666;
  margin-left: 10rpx;
}

.forgot-password {
  font-size: 26rpx;
  color: #3c9cff;
}

.login-btn {
  width: 100%;
  height: 88rpx;
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 30rpx;
}

.login-btn:disabled {
  background-color: #a0cfff;
}

.register-link {
  text-align: center;
  font-size: 26rpx;
  color: #666;
}

.link-text {
  color: #3c9cff;
  margin-left: 10rpx;
}

.login-footer {
  margin-top: 60rpx;
}

.footer-text {
  text-align: center;
  font-size: 26rpx;
  color: #999;
  margin-bottom: 30rpx;
}

.other-login {
  display: flex;
  justify-content: center;
}

.login-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 40rpx;
}

.login-icon {
  width: 80rpx;
  height: 80rpx;
  margin-bottom: 10rpx;
}

.login-option text {
  font-size: 24rpx;
  color: #666;
}
</style>