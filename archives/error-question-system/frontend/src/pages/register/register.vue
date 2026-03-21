<template>
  <view class="register-container">
    <view class="logo-box">
      <image class="logo" src="/static/logo.png" mode="widthFix"></image>
      <text class="title">注册新账号</text>
    </view>
    
    <view class="form-box">
      <u--form labelPosition="left" :model="form" :rules="rules" ref="uForm">
        <u-form-item label="用户名" prop="username" borderBottom>
          <u--input v-model="form.username" placeholder="请输入用户名" border="none"></u--input>
        </u-form-item>
        <u-form-item label="邮箱" prop="email" borderBottom>
          <u--input v-model="form.email" placeholder="请输入邮箱" border="none"></u--input>
        </u-form-item>
        <u-form-item label="密码" prop="password" borderBottom>
          <u--input v-model="form.password" type="password" placeholder="请输入密码" border="none"></u--input>
        </u-form-item>
        <u-form-item label="确认密码" prop="password_confirm" borderBottom>
          <u--input v-model="form.password_confirm" type="password" placeholder="请再次输入密码" border="none"></u--input>
        </u-form-item>
      </u--form>
      
      <view class="btn-group">
        <u-button type="primary" text="注册" customStyle="margin-top: 40rpx" @click="submit"></u-button>
        <u-button type="info" text="返回登录" plain customStyle="margin-top: 20rpx" @click="toLogin"></u-button>
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
        username: '',
        email: '',
        password: '',
        password_confirm: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: ['blur', 'change'] }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: ['blur', 'change'] },
          { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: ['blur', 'change'] },
          { min: 6, message: '密码长度不能少于6位', trigger: ['blur', 'change'] }
        ],
        password_confirm: [
          { required: true, message: '请再次输入密码', trigger: ['blur', 'change'] },
          {
            validator: (rule, value, callback) => {
              return value === this.form.password;
            },
            message: '两次输入的密码不一致',
            trigger: ['blur', 'change']
          }
        ]
      }
    };
  },
  methods: {
    submit() {
      this.$refs.uForm.validate().then(res => {
        this.register();
      }).catch(errors => {
        console.log(errors)
      })
    },
    async register() {
      try {
        const res = await request({
          url: 'auth/register/',
          method: 'POST',
          data: this.form
        });
        
        uni.showToast({
          title: '注册成功',
          icon: 'success'
        });
        
        // Redirect to login
        setTimeout(() => {
          uni.navigateTo({
            url: '/pages/login/login'
          });
        }, 1500);
      } catch (e) {
        console.error(e);
      }
    },
    toLogin() {
      uni.navigateBack();
    }
  }
};
</script>

<style lang="scss" scoped>
.register-container {
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
