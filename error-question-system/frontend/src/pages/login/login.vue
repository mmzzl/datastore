<template>
  <view class="login-container">
    <view class="logo-box">
      <image class="logo" src="/static/logo.png" mode="widthFix"></image>
      <text class="title">错题本系统</text>
    </view>
    
    <view class="form-box">
      <u--form labelPosition="left" :model="form" :rules="rules" ref="uForm">
        <u-form-item label="邮箱" prop="email" borderBottom>
          <u--input v-model="form.email" placeholder="请输入邮箱" border="none"></u--input>
        </u-form-item>
        <u-form-item label="密码" prop="password" borderBottom>
          <u--input v-model="form.password" type="password" placeholder="请输入密码" border="none"></u--input>
        </u-form-item>
      </u--form>
      
      <view class="btn-group">
        <u-button type="primary" text="登录" customStyle="margin-top: 40rpx" @click="submit"></u-button>
        <u-button type="info" text="注册账号" plain customStyle="margin-top: 20rpx" @click="toRegister"></u-button>
      </view>
    </view>
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      rules: {
        email: [
          { required: true, message: '请输入邮箱', trigger: ['blur', 'change'] },
          { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: ['blur', 'change'] }
        ]
      }
    };
  },
  methods: {
    submit() {
      this.$refs.uForm.validate().then(res => {
        this.login();
      }).catch(errors => {
        // uni.$u.toast('校验失败')
      })
    },
    async login() {
      try {
        const res = await request({
          url: 'auth/token/',
          method: 'POST',
          data: this.form
        });
        
        // Save token
        uni.setStorageSync('token', res.access);
        uni.setStorageSync('refresh_token', res.refresh);
        if (res.user) {
          uni.setStorageSync('user', res.user);
        } else {
          // Fetch user profile if not provided in login response
          try {
             const profileRes = await request({
                url: 'auth/profile/',
                method: 'GET',
                header: {
                   'Authorization': `Bearer ${res.access}`
                }
             });
             if (profileRes) {
                uni.setStorageSync('user', profileRes);
             }
          } catch (err) {
             console.error('Failed to fetch profile', err);
          }
        }
        
        uni.showToast({
          title: '登录成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/index/index'
          });
        }, 1500);
      } catch (e) {
        console.error(e);
      }
    },
    toRegister() {
      uni.navigateTo({
        url: '/pages/register/register'
      });
    }
  }
};
</script>

<style lang="scss" scoped>
.login-container {
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
  background-color: #fff;
  
  .logo-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 60rpx;
    
    .logo {
      width: 160rpx;
      height: 160rpx;
      margin-bottom: 20rpx;
    }
    
    .title {
      font-size: 36rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .form-box {
    padding: 0 20rpx;
  }
}
</style>
