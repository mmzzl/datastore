<template>
  <view class="about-page">
    <view class="about-header">
      <view class="app-icon">
        <text class="icon-text">错</text>
      </view>
      <view class="app-info">
        <view class="app-name">错题本</view>
        <view class="app-version">版本 {{ version }}</view>
      </view>
    </view>

    <view class="about-content">
      <!-- 应用介绍 -->
      <view class="section">
        <view class="section-title">应用介绍</view>
        <view class="section-content">
          <text class="intro-text">
            错题本是一款专注于错题管理和学习的应用，帮助学生整理、复习和掌握错题，提高学习效率。
          </text>
        </view>
      </view>

      <!-- 主要功能 -->
      <view class="section">
        <view class="section-title">主要功能</view>
        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">📝</view>
            <view class="feature-text">错题录入与分类管理</view>
          </view>
          <view class="feature-item">
            <view class="feature-icon">🔍</view>
            <view class="feature-text">智能搜索与筛选</view>
          </view>
          <view class="feature-item">
            <view class="feature-icon">📊</view>
            <view class="feature-text">学习数据统计与分析</view>
          </view>
          <view class="feature-item">
            <view class="feature-icon">📱</view>
            <view class="feature-text">多平台同步，随时随地学习</view>
          </view>
        </view>
      </view>

      <!-- 联系我们 -->
      <view class="section">
        <view class="section-title">联系我们</view>
        <view class="contact-list">
          <view class="contact-item" @click="handleContact('email')">
            <view class="contact-label">邮箱</view>
            <view class="contact-value">support@errorbook.com</view>
          </view>
          <view class="contact-item" @click="handleContact('phone')">
            <view class="contact-label">电话</view>
            <view class="contact-value">400-123-4567</view>
          </view>
          <view class="contact-item" @click="handleContact('website')">
            <view class="contact-label">官网</view>
            <view class="contact-value">www.errorbook.com</view>
          </view>
        </view>
      </view>

      <!-- 开发团队 -->
      <view class="section">
        <view class="section-title">开发团队</view>
        <view class="team-content">
          <text class="team-text">
            错题本由教育科技团队开发，致力于为学生提供优质的学习工具和服务。
          </text>
        </view>
      </view>

      <!-- 版权信息 -->
      <view class="section">
        <view class="copyright">
          <text class="copyright-text">Copyright © 2023 错题本团队</text>
          <text class="copyright-text">All Rights Reserved</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      version: '1.0.0'
    }
  },
  onLoad() {
    // 获取应用版本号
    this.getAppVersion();
  },
  methods: {
    // 获取应用版本号
    getAppVersion() {
      // #ifdef APP-PLUS
      plus.runtime.getProperty(plus.runtime.appid, (wgtinfo) => {
        this.version = wgtinfo.version;
      });
      // #endif
      
      // #ifndef APP-PLUS
      // 非APP平台使用默认版本号
      // #endif
    },
    
    // 处理联系方式
    handleContact(type) {
      switch (type) {
        case 'email':
          this.copyToClipboard('support@errorbook.com');
          break;
        case 'phone':
          this.makePhoneCall('400-123-4567');
          break;
        case 'website':
          this.openWebsite('https://www.errorbook.com');
          break;
      }
    },
    
    // 复制到剪贴板
    copyToClipboard(text) {
      uni.setClipboardData({
        data: text,
        success: () => {
          uni.showToast({
            title: '已复制到剪贴板',
            icon: 'success'
          });
        },
        fail: () => {
          uni.showToast({
            title: '复制失败',
            icon: 'none'
          });
        }
      });
    },
    
    // 拨打电话
    makePhoneCall(phoneNumber) {
      uni.makePhoneCall({
        phoneNumber: phoneNumber,
        fail: () => {
          uni.showToast({
            title: '拨打电话失败',
            icon: 'none'
          });
        }
      });
    },
    
    // 打开网站
    openWebsite(url) {
      // #ifdef H5
      window.open(url, '_blank');
      // #endif
      
      // #ifndef H5
      uni.showToast({
        title: '请在浏览器中打开',
        icon: 'none'
      });
      // #endif
    }
  }
}
</script>

<style>
.about-page {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding-bottom: 40rpx;
}

.about-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0 40rpx;
  background-color: white;
}

.app-icon {
  width: 160rpx;
  height: 160rpx;
  background-color: #3c9cff;
  border-radius: 30rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(60, 156, 255, 0.3);
}

.icon-text {
  font-size: 80rpx;
  font-weight: bold;
  color: white;
}

.app-info {
  text-align: center;
}

.app-name {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.app-version {
  font-size: 28rpx;
  color: #999;
}

.about-content {
  padding: 0 30rpx;
}

.section {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-top: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  padding-left: 15rpx;
  border-left: 6rpx solid #3c9cff;
}

.section-content {
  padding-left: 15rpx;
}

.intro-text, .team-text {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
}

.feature-list {
  padding-left: 15rpx;
}

.feature-item {
  display: flex;
  align-items: center;
  margin-bottom: 25rpx;
}

.feature-icon {
  font-size: 36rpx;
  margin-right: 20rpx;
}

.feature-text {
  font-size: 28rpx;
  color: #333;
}

.contact-list {
  padding-left: 15rpx;
}

.contact-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1px solid #f0f0f0;
}

.contact-item:last-child {
  border-bottom: none;
}

.contact-label {
  font-size: 28rpx;
  color: #666;
}

.contact-value {
  font-size: 28rpx;
  color: #3c9cff;
}

.copyright {
  text-align: center;
  padding: 20rpx 0;
}

.copyright-text {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 10rpx;
}
</style>