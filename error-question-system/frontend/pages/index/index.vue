<template>
  <view class="index-page">
    <!-- 顶部欢迎区域 -->
    <view class="welcome-section">
      <view class="welcome-content">
        <text class="welcome-title">智能错题本</text>
        <text class="welcome-subtitle">高效学习，精准提升</text>
      </view>
    </view>

    <!-- 功能区域 -->
    <view class="function-section">
      <view class="function-grid">
        <view class="function-item" @click="navigateTo('/pages/questions/add')">
          <view class="function-icon add-icon">
            <text class="iconfont icon-add"></text>
          </view>
          <text class="function-title">添加错题</text>
        </view>
        
        <view class="function-item" @click="navigateTo('/pages/questions/list')">
          <view class="function-icon list-icon">
            <text class="iconfont icon-list"></text>
          </view>
          <text class="function-title">错题列表</text>
        </view>
        
        <view class="function-item" @click="navigateTo('/pages/category/index')">
          <view class="function-icon category-icon">
            <text class="iconfont icon-category"></text>
          </view>
          <text class="function-title">错题分类</text>
        </view>
        
        <view class="function-item" @click="navigateTo('/pages/search/index')">
          <view class="function-icon search-icon">
            <text class="iconfont icon-search"></text>
          </view>
          <text class="function-title">搜索错题</text>
        </view>
      </view>
    </view>

    <!-- 统计区域 -->
    <view class="stats-section">
      <view class="stats-title">学习统计</view>
      <view class="stats-grid">
        <view class="stats-item">
          <text class="stats-number">{{ stats.totalQuestions }}</text>
          <text class="stats-label">总错题数</text>
        </view>
        <view class="stats-item">
          <text class="stats-number">{{ stats.solvedQuestions }}</text>
          <text class="stats-label">已解决</text>
        </view>
        <view class="stats-item">
          <text class="stats-number">{{ stats.categories }}</text>
          <text class="stats-label">错题分类</text>
        </view>
      </view>
    </view>

    <!-- 最近错题区域 -->
    <view class="recent-section">
      <view class="section-header">
        <text class="section-title">最近错题</text>
        <text class="section-more" @click="navigateTo('/pages/questions/list')">查看全部</text>
      </view>
      <view class="recent-list">
        <view class="recent-item" v-for="(item, index) in recentQuestions" :key="index" @click="navigateTo('/pages/questions/detail?id=' + item.id)">
          <view class="recent-content">
            <text class="recent-title">{{ item.title }}</text>
            <text class="recent-category">{{ item.category }}</text>
          </view>
          <text class="recent-date">{{ formatDate(item.createTime) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      stats: {
        totalQuestions: 0,
        solvedQuestions: 0,
        categories: 0
      },
      recentQuestions: []
    }
  },
  onLoad() {
    this.loadStats();
    this.loadRecentQuestions();
  },
  onShow() {
    // 每次显示页面时刷新数据
    this.loadStats();
    this.loadRecentQuestions();
  },
  methods: {
    // 加载统计数据
    async loadStats() {
      // 直接使用模拟数据
      this.stats = {
        totalQuestions: 25,
        solvedQuestions: 18,
        categories: 6
      };
    },
    
    // 加载最近错题
    async loadRecentQuestions() {
      // 直接使用模拟数据
      this.recentQuestions = [
        {
          id: 1,
          title: '数学二次函数求最值问题',
          category: '数学',
          createTime: new Date().getTime() - 86400000 // 1天前
        },
        {
          id: 2,
          title: '英语定语从句用法',
          category: '英语',
          createTime: new Date().getTime() - 172800000 // 2天前
        },
        {
          id: 3,
          title: '物理力学平衡问题',
          category: '物理',
          createTime: new Date().getTime() - 259200000 // 3天前
        }
      ];
    },
    
    // 格式化日期
    formatDate(timestamp) {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      
      if (days === 0) {
        return '今天';
      } else if (days === 1) {
        return '昨天';
      } else if (days < 7) {
        return `${days}天前`;
      } else {
        return `${date.getMonth() + 1}月${date.getDate()}日`;
      }
    },
    
    // 页面导航
    navigateTo(url) {
      uni.navigateTo({
        url
      });
    }
  }
}
</script>

<style>
.index-page {
  background-color: #f8f8f8;
  min-height: 100vh;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #3c9cff 0%, #5ac725 100%);
  padding: 60rpx 40rpx 40rpx;
  color: white;
}

.welcome-content {
  display: flex;
  flex-direction: column;
}

.welcome-title {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.welcome-subtitle {
  font-size: 28rpx;
  opacity: 0.8;
}

/* 功能区域 */
.function-section {
  margin: -20rpx 30rpx 30rpx;
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.function-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.function-item {
  width: 45%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30rpx;
}

.function-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16rpx;
}

.add-icon {
  background-color: rgba(60, 156, 255, 0.1);
  color: #3c9cff;
}

.list-icon {
  background-color: rgba(90, 199, 37, 0.1);
  color: #5ac725;
}

.category-icon {
  background-color: rgba(249, 174, 61, 0.1);
  color: #f9ae3d;
}

.search-icon {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.function-title {
  font-size: 28rpx;
  color: #333;
}

/* 统计区域 */
.stats-section {
  margin: 0 30rpx 30rpx;
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.stats-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.stats-grid {
  display: flex;
  justify-content: space-between;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-number {
  font-size: 48rpx;
  font-weight: bold;
  color: #3c9cff;
  margin-bottom: 8rpx;
}

.stats-label {
  font-size: 24rpx;
  color: #666;
}

/* 最近错题区域 */
.recent-section {
  margin: 0 30rpx 30rpx;
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.section-more {
  font-size: 26rpx;
  color: #3c9cff;
}

.recent-list {
  display: flex;
  flex-direction: column;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1px solid #f0f0f0;
}

.recent-item:last-child {
  border-bottom: none;
}

.recent-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.recent-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 8rpx;
  max-width: 400rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-category {
  font-size: 24rpx;
  color: #666;
  background-color: #f0f0f0;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  align-self: flex-start;
}

.recent-date {
  font-size: 24rpx;
  color: #999;
}

/* 图标字体样式 */
.iconfont {
  font-family: "iconfont";
  font-size: 40rpx;
}

.icon-add:before {
  content: "+";
}

.icon-list:before {
  content: "☰";
}

.icon-category:before {
  content: "⊞";
}

.icon-search:before {
  content: "🔍";
}
</style>