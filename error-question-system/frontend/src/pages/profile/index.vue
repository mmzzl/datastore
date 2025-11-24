<template>
  <view class="profile-page">
    <!-- 用户信息区域 -->
    <view class="user-info-section">
      <view class="user-avatar">
        <image class="avatar" :src="userInfo.avatar || '/static/images/default-avatar.png'" mode="aspectFill"></image>
        <text class="username">{{ userInfo.username || '未登录' }}</text>
      </view>
      <view class="user-stats">
        <view class="stat-item">
          <text class="stat-number">{{ stats.totalQuestions }}</text>
          <text class="stat-label">总错题</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ stats.solvedQuestions }}</text>
          <text class="stat-label">已解决</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ stats.correctRate }}%</text>
          <text class="stat-label">正确率</text>
        </view>
      </view>
    </view>

    <!-- 功能列表 -->
    <view class="function-list">
      <view class="function-item" @click="navigateTo('/pages/answers/list')">
        <view class="function-left">
          <text class="function-icon">📝</text>
          <text class="function-title">我的解答</text>
        </view>
        <text class="function-arrow">></text>
      </view>
      
      <view class="function-item" @click="navigateTo('/pages/categories/list')">
        <view class="function-left">
          <text class="function-icon">📚</text>
          <text class="function-title">错题分类</text>
        </view>
        <text class="function-arrow">></text>
      </view>
      
      <view class="function-item" @click="navigateTo('/pages/statistics/index')">
        <view class="function-left">
          <text class="function-icon">📊</text>
          <text class="function-title">学习统计</text>
        </view>
        <text class="function-arrow">></text>
      </view>
      
      <view class="function-item" @click="navigateTo('/pages/settings/index')">
        <view class="function-left">
          <text class="function-icon">⚙️</text>
          <text class="function-title">设置</text>
        </view>
        <text class="function-arrow">></text>
      </view>
    </view>

    <!-- 其他功能 -->
    <view class="other-list">
      <view class="function-item" @click="showAbout">
        <view class="function-left">
          <text class="function-icon">ℹ️</text>
          <text class="function-title">关于我们</text>
        </view>
        <text class="function-arrow">></text>
      </view>
      
      <view class="function-item" @click="showFeedback">
        <view class="function-left">
          <text class="function-icon">💬</text>
          <text class="function-title">意见反馈</text>
        </view>
        <text class="function-arrow">></text>
      </view>
      
      <view class="function-item" @click="shareApp">
        <view class="function-left">
          <text class="function-icon">🔗</text>
          <text class="function-title">分享应用</text>
        </view>
        <text class="function-arrow">></text>
      </view>
    </view>

    <!-- 退出登录按钮 -->
    <view class="logout-section" v-if="isLoggedIn">
      <button class="logout-btn" @click="handleLogout">退出登录</button>
    </view>

    <!-- 登录按钮 -->
    <view class="login-section" v-else>
      <button class="login-btn" @click="navigateToLogin">立即登录</button>
    </view>
  </view>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  data() {
    return {
      stats: {
        totalQuestions: 0,
        solvedQuestions: 0,
        correctRate: 0
      }
    }
  },
  computed: {
    ...mapState('user', ['userInfo', 'token']),
    
    isLoggedIn() {
      return !!this.token;
    }
  },
  onLoad() {
    this.loadUserInfo();
    this.loadStats();
  },
  onShow() {
    // 每次显示页面时刷新数据
    this.loadUserInfo();
    this.loadStats();
  },
  methods: {
    ...mapActions('user', ['getUserInfo', 'logout']),
    
    // 加载用户信息
    async loadUserInfo() {
      if (!this.isLoggedIn) {
        return;
      }
      
      try {
        await this.getUserInfo();
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    },
    
    // 加载统计数据
    async loadStats() {
      if (!this.isLoggedIn) {
        return;
      }
      
      try {
        // 这里应该调用API获取统计数据
        // 暂时使用模拟数据
        this.stats = {
          totalQuestions: 25,
          solvedQuestions: 18,
          correctRate: 72
        };
      } catch (error) {
        console.error('加载统计数据失败:', error);
      }
    },
    
    // 处理退出登录
    async handleLogout() {
      uni.showModal({
        title: '提示',
        content: '确定要退出登录吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              await this.logout();
              uni.showToast({
                title: '已退出登录',
                icon: 'success'
              });
              
              // 退出登录后刷新页面数据
              this.loadStats();
            } catch (error) {
              console.error('退出登录失败:', error);
              uni.showToast({
                title: '退出登录失败',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    // 跳转到登录页面
    navigateToLogin() {
      uni.navigateTo({
        url: '/pages/login/index'
      });
    },
    
    // 页面导航
    navigateTo(url) {
      if (!this.isLoggedIn) {
        uni.showToast({
          title: '请先登录',
          icon: 'none'
        });
        setTimeout(() => {
          this.navigateToLogin();
        }, 1500);
        return;
      }
      
      uni.navigateTo({
        url
      });
    },
    
    // 显示关于我们
    showAbout() {
      uni.showModal({
        title: '关于我们',
        content: '智能错题本 v1.0.0\n\n一款帮助学生高效管理错题、提升学习效率的应用。',
        showCancel: false
      });
    },
    
    // 显示意见反馈
    showFeedback() {
      uni.showModal({
        title: '意见反馈',
        content: '如有任何问题或建议，请通过以下方式联系我们：\n\n邮箱：feedback@example.com\n电话：400-123-4567',
        showCancel: false
      });
    },
    
    // 分享应用
    shareApp() {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        href: 'https://example.com',
        title: '智能错题本',
        summary: '高效学习，精准提升',
        imageUrl: '/static/images/logo.png',
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          });
        },
        fail: () => {
          // 如果分享失败，可以复制链接
          uni.setClipboardData({
            data: 'https://example.com',
            success: () => {
              uni.showToast({
                title: '链接已复制',
                icon: 'success'
              });
            }
          });
        }
      });
    }
  }
}
</script>

<style>
.profile-page {
  background-color: #f8f8f8;
  min-height: 100vh;
}

/* 用户信息区域 */
.user-info-section {
  background: linear-gradient(135deg, #3c9cff 0%, #5ac725 100%);
  padding: 40rpx 30rpx;
  color: white;
}

.user-avatar {
  display: flex;
  align-items: center;
  margin-bottom: 40rpx;
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  margin-right: 30rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
}

.username {
  font-size: 36rpx;
  font-weight: bold;
}

.user-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.stat-label {
  font-size: 24rpx;
  opacity: 0.8;
}

/* 功能列表 */
.function-list, .other-list {
  margin: 20rpx 30rpx;
  background-color: white;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.function-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1px solid #f0f0f0;
}

.function-item:last-child {
  border-bottom: none;
}

.function-left {
  display: flex;
  align-items: center;
}

.function-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.function-title {
  font-size: 30rpx;
  color: #333;
}

.function-arrow {
  font-size: 30rpx;
  color: #c0c4cc;
}

/* 退出登录区域 */
.logout-section, .login-section {
  margin: 40rpx 30rpx;
}

.logout-btn {
  width: 100%;
  height: 88rpx;
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 32rpx;
  font-weight: bold;
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
}
</style>