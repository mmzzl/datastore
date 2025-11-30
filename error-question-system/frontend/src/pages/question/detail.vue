<template>
  <view class="container" v-if="question">
    <view class="header">
      <view class="title">{{ question.title }}</view>
      <view class="info">
        <u-tag :text="question.subject.name" :bgColor="question.subject.color" borderColor="transparent" size="mini"></u-tag>
        <text class="time">{{ formatTime(question.created_at) }}</text>
      </view>
    </view>
    
    <view class="card">
      <view class="card-header">题目内容</view>
      <view class="card-content">
        <text>{{ question.content }}</text>
      </view>
    </view>
    
    <view class="card">
      <view class="card-header">参考答案</view>
      <view class="card-content">
        <text>{{ question.correct_answer || '暂无答案' }}</text>
      </view>
    </view>
    
    <view class="card">
      <view class="card-header">解析</view>
      <view class="card-content">
        <text>{{ question.analysis || '暂无解析' }}</text>
      </view>
    </view>
    
    <view class="footer-btn">
      <u-button type="primary" text="编辑" @click="toEdit"></u-button>
    </view>
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      id: null,
      question: null
    };
  },
  onLoad(options) {
    if (options.id) {
      this.id = options.id;
      this.getDetail();
    }
  },
  methods: {
    async getDetail() {
      try {
        const res = await request({
          url: `questions/questions/${this.id}/`,
          method: 'GET'
        });
        this.question = res;
      } catch (e) {
        console.error(e);
      }
    },
    toEdit() {
       uni.showToast({ title: '编辑功能开发中', icon: 'none' });
    },
    formatTime(time) {
        if(!time) return '';
        const date = new Date(time);
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  padding: 30rpx;
  padding-bottom: 120rpx;
  background-color: #f8f8f8;
  min-height: 100vh;
}

.header {
  background-color: #fff;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  
  .title {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 20rpx;
  }
  
  .info {
    display: flex;
    align-items: center;
    
    .time {
      font-size: 24rpx;
      color: #999;
      margin-left: 20rpx;
    }
  }
}

.card {
  background-color: #fff;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  
  .card-header {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 20rpx;
    border-left: 8rpx solid #2979ff;
    padding-left: 20rpx;
  }
  
  .card-content {
    font-size: 28rpx;
    color: #666;
    line-height: 1.6;
  }
}

.footer-btn {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 20rpx 30rpx;
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.05);
  box-sizing: border-box;
}
</style>
