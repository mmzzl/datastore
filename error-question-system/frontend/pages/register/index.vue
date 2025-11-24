<template>
  <view class="register-page">
    <view class="register-container">
      <view class="register-header">
        <image class="logo" src="/static/images/logo.png" mode="aspectFit"></image>
        <text class="app-name">智能错题本</text>
        <text class="app-desc">高效学习，精准提升</text>
      </view>

      <view class="register-form">
        <view class="form-item">
          <input 
            class="form-input" 
            type="text" 
            placeholder="请输入用户名" 
            v-model="formData.username"
            :class="{ 'error': errors.username }"
          />
          <text class="error-text" v-if="errors.username">{{ errors.username }}</text>
        </view>

        <view class="form-item">
          <input 
            class="form-input" 
            type="text" 
            placeholder="请输入手机号" 
            v-model="formData.phone"
            :class="{ 'error': errors.phone }"
          />
          <text class="error-text" v-if="errors.phone">{{ errors.phone }}</text>
        </view>

        <view class="form-item">
          <input 
            class="form-input" 
            type="text" 
            placeholder="请输入验证码" 
            v-model="formData.verifyCode"
            :class="{ 'error': errors.verifyCode }"
          />
          <button 
            class="verify-btn" 
            @click="getVerifyCode" 
            :disabled="isCountingDown || !formData.phone"
          >
            {{ countDownText }}
          </button>
          <text class="error-text" v-if="errors.verifyCode">{{ errors.verifyCode }}</text>
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

        <view class="form-item">
          <input 
            class="form-input" 
            :type="showConfirmPassword ? 'text' : 'password'" 
            placeholder="请确认密码" 
            v-model="formData.confirmPassword"
            :class="{ 'error': errors.confirmPassword }"
          />
          <text class="toggle-password" @click="toggleConfirmPassword">
            {{ showConfirmPassword ? '隐藏' : '显示' }}
          </text>
          <text class="error-text" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</text>
        </view>

        <view class="form-item">
          <label class="checkbox-container">
            <checkbox :checked="formData.agreement" @change="handleAgreementChange" />
            <text class="checkbox-text">我已阅读并同意</text>
            <text class="link-text" @click="showUserAgreement">《用户协议》</text>
            <text class="checkbox-text">和</text>
            <text class="link-text" @click="showPrivacyPolicy">《隐私政策》</text>
          </label>
          <text class="error-text" v-if="errors.agreement">{{ errors.agreement }}</text>
        </view>

        <button class="register-btn" @click="handleRegister" :disabled="isLoading">
          {{ isLoading ? '注册中...' : '注册' }}
        </button>

        <view class="login-link">
          <text>已有账号？</text>
          <text class="link-text" @click="navigateToLogin">立即登录</text>
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
        phone: '',
        verifyCode: '',
        password: '',
        confirmPassword: '',
        agreement: false
      },
      errors: {
        username: '',
        phone: '',
        verifyCode: '',
        password: '',
        confirmPassword: '',
        agreement: ''
      },
      showPassword: false,
      showConfirmPassword: false,
      isLoading: false,
      isCountingDown: false,
      countDown: 60
    }
  },
  computed: {
    countDownText() {
      return this.isCountingDown ? `${this.countDown}秒后重试` : '获取验证码';
    }
  },
  methods: {
    ...mapActions(['register']),
    
    // 切换密码显示/隐藏
    togglePassword() {
      this.showPassword = !this.showPassword;
    },
    
    // 切换确认密码显示/隐藏
    toggleConfirmPassword() {
      this.showConfirmPassword = !this.showConfirmPassword;
    },
    
    // 处理协议同意变化
    handleAgreementChange(e) {
      this.formData.agreement = e.detail.value.length > 0;
    },
    
    // 获取验证码
    async getVerifyCode() {
      if (!this.formData.phone.trim()) {
        this.errors.phone = '请输入手机号';
        return;
      }
      
      if (!/^1[3-9]\d{9}$/.test(this.formData.phone)) {
        this.errors.phone = '请输入正确的手机号';
        return;
      }
      
      this.errors.phone = '';
      
      try {
        // 这里应该调用API获取验证码
        // 暂时使用模拟
        uni.showToast({
          title: '验证码已发送',
          icon: 'success'
        });
        
        // 开始倒计时
        this.isCountingDown = true;
        this.countDown = 60;
        
        const timer = setInterval(() => {
          this.countDown--;
          if (this.countDown <= 0) {
            clearInterval(timer);
            this.isCountingDown = false;
          }
        }, 1000);
      } catch (error) {
        console.error('获取验证码失败:', error);
        uni.showToast({
          title: '获取验证码失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 表单验证
    validateForm() {
      let isValid = true;
      this.errors = {
        username: '',
        phone: '',
        verifyCode: '',
        password: '',
        confirmPassword: '',
        agreement: ''
      };
      
      if (!this.formData.username.trim()) {
        this.errors.username = '请输入用户名';
        isValid = false;
      } else if (this.formData.username.length < 2 || this.formData.username.length > 20) {
        this.errors.username = '用户名长度应在2-20个字符之间';
        isValid = false;
      }
      
      if (!this.formData.phone.trim()) {
        this.errors.phone = '请输入手机号';
        isValid = false;
      } else if (!/^1[3-9]\d{9}$/.test(this.formData.phone)) {
        this.errors.phone = '请输入正确的手机号';
        isValid = false;
      }
      
      if (!this.formData.verifyCode.trim()) {
        this.errors.verifyCode = '请输入验证码';
        isValid = false;
      } else if (this.formData.verifyCode.length !== 6) {
        this.errors.verifyCode = '请输入6位验证码';
        isValid = false;
      }
      
      if (!this.formData.password.trim()) {
        this.errors.password = '请输入密码';
        isValid = false;
      } else if (this.formData.password.length < 6) {
        this.errors.password = '密码长度不能少于6位';
        isValid = false;
      }
      
      if (!this.formData.confirmPassword.trim()) {
        this.errors.confirmPassword = '请确认密码';
        isValid = false;
      } else if (this.formData.password !== this.formData.confirmPassword) {
        this.errors.confirmPassword = '两次输入的密码不一致';
        isValid = false;
      }
      
      if (!this.formData.agreement) {
        this.errors.agreement = '请阅读并同意用户协议和隐私政策';
        isValid = false;
      }
      
      return isValid;
    },
    
    // 处理注册
    async handleRegister() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isLoading = true;
      
      try {
        await this.register({
          username: this.formData.username,
          phone: this.formData.phone,
          verifyCode: this.formData.verifyCode,
          password: this.formData.password
        });
        
        uni.showToast({
          title: '注册成功',
          icon: 'success'
        });
        
        // 注册成功，跳转到登录页面
        setTimeout(() => {
          uni.redirectTo({
            url: '/pages/login/index'
          });
        }, 1500);
      } catch (error) {
        console.error('注册失败:', error);
        uni.showToast({
          title: error.message || '注册失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    // 跳转到登录页面
    navigateToLogin() {
      uni.redirectTo({
        url: '/pages/login/index'
      });
    },
    
    // 显示用户协议
    showUserAgreement() {
      uni.showModal({
        title: '用户协议',
        content: '这里是用户协议内容，实际应用中应该从服务器获取或使用单独页面展示',
        showCancel: false
      });
    },
    
    // 显示隐私政策
    showPrivacyPolicy() {
      uni.showModal({
        title: '隐私政策',
        content: '这里是隐私政策内容，实际应用中应该从服务器获取或使用单独页面展示',
        showCancel: false
      });
    }
  }
}
</script>

<style>
.register-page {
  height: 100vh;
  background-color: #f8f8f8;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx 0;
  box-sizing: border-box;
}

.register-container {
  width: 90%;
  max-width: 600rpx;
}

.register-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40rpx;
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

.register-form {
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

.verify-btn {
  position: absolute;
  right: 10rpx;
  top: 50%;
  transform: translateY(-50%);
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 20rpx;
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 6rpx;
  font-size: 24rpx;
}

.verify-btn:disabled {
  background-color: #a0cfff;
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

.checkbox-container {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.checkbox-text {
  font-size: 26rpx;
  color: #666;
  margin-left: 10rpx;
}

.link-text {
  color: #3c9cff;
  margin: 0 4rpx;
}

.register-btn {
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

.register-btn:disabled {
  background-color: #a0cfff;
}

.login-link {
  text-align: center;
  font-size: 26rpx;
  color: #666;
}
</style>