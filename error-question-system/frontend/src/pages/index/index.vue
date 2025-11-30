<template>
  <view class="content">
    <view class="header">
      <view class="left-box">
        <text class="title">错题本</text>
      </view>
      <view class="right-box">
        <text class="username">{{ user.nickname || user.username || '同学' }}</text>
        <view class="logout-btn" @click="toLogout">
          <text>退出</text>
        </view>
      </view>
    </view>

    <view class="stats-box">
      <view class="stat-item">
        <text class="count">{{ stats.today_count || 0 }}</text>
        <text class="label">今日错题</text>
      </view>
      <view class="stat-item">
        <text class="count">{{ stats.review_count || 0 }}</text>
        <text class="label">待复习</text>
      </view>
      <view class="stat-item">
        <text class="count">{{ stats.solved_count || 0 }}</text>
        <text class="label">已掌握</text>
      </view>
    </view>

    <view class="action-grid">
      <view class="grid-item" @click="toAddQuestion">
        <u-icon name="camera-fill" size="40" color="#2979ff"></u-icon>
        <text>录入错题</text>
      </view>
      <view class="grid-item" @click="toList">
        <u-icon name="list" size="40" color="#19be6b"></u-icon>
        <text>错题列表</text>
      </view>
      <view class="grid-item" @click="toCategory">
        <u-icon name="grid-fill" size="40" color="#ff9900"></u-icon>
        <text>分类管理</text>
      </view>
      <view class="grid-item" @click="toSearch">
        <u-icon name="search" size="40" color="#909399"></u-icon>
        <text>搜索错题</text>
      </view>
    </view>
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      user: {},
      stats: {
        today_count: 0,
        review_count: 0,
        solved_count: 0
      }
    }
  },
  onShow() {
    const token = uni.getStorageSync('token');
    if (token) {
      const user = uni.getStorageSync('user');
      if(user) {
         this.user = user;
      }
      this.getStats();
    } else {
      // If not logged in, redirect to login
      uni.reLaunch({ url: '/pages/login/login' });
    }
  },
  methods: {
    async getStats() {
      try {
        const res = await request({
            url: 'auth/profile/',
            method: 'GET'
        });
        if (res.profile) {
            this.stats.solved_count = res.profile.solved_questions;
            // Simulated data for now as backend API for daily stats might need specific endpoint
            this.stats.today_count = 0; 
            this.stats.review_count = 0;
        }
      } catch (e) {
        console.error(e);
      }
    },
    toSearch() {
      uni.switchTab({
        url: '/pages/question/list'
      });
    },
    toAddQuestion() {
       uni.navigateTo({
         url: '/pages/question/add'
       });
    },
    toList() {
       uni.switchTab({
         url: '/pages/question/list'
       });
    },
    toCategory() {
       uni.navigateTo({
         url: '/pages/category/list'
       });
    },
    toLogout() {
       uni.showModal({
         title: '提示',
         content: '确定要退出登录吗？',
         success: (res) => {
           if (res.confirm) {
             uni.removeStorageSync('token');
             uni.removeStorageSync('refresh_token');
             uni.removeStorageSync('user');
             uni.reLaunch({ url: '/pages/login/login' });
           }
         }
       });
    }
  }
}
</script>

<style lang="scss" scoped>
.content {
  padding: 30rpx;
  background-color: #f8f8f8;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
  
  .left-box {
    .title {
      font-size: 40rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .right-box {
    display: flex;
    align-items: center;
    
    .username {
      font-size: 28rpx;
      color: #666;
      margin-right: 20rpx;
    }
    
    .logout-btn {
      font-size: 24rpx;
      color: #999;
      padding: 8rpx 20rpx;
      background-color: #e8e8e8;
      border-radius: 30rpx;
      
      &:active {
        background-color: #d8d8d8;
      }
    }
  }
}

.stats-box {
  display: flex;
  justify-content: space-around;
  background-color: #fff;
  padding: 30rpx;
  border-radius: 16rpx;
  margin-bottom: 40rpx;
  box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.05);
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .count {
      font-size: 40rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 10rpx;
    }
    
    .label {
      font-size: 24rpx;
      color: #999;
    }
  }
}

.action-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  
  .grid-item {
    width: 48%;
    background-color: #fff;
    padding: 40rpx 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: 16rpx;
    margin-bottom: 30rpx;
    box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.05);
    
    text {
      margin-top: 20rpx;
      font-size: 28rpx;
      color: #333;
    }
  }
}
</style>
