<template>
  <view class="feedback-page">
    <view class="form-container">
      <!-- 反馈类型 -->
      <view class="form-section">
        <view class="section-title">反馈类型</view>
        <view class="type-selector">
          <view 
            class="type-item" 
            v-for="item in feedbackTypes" 
            :key="item.id"
            :class="{ 'active': formData.type === item.id }"
            @click="selectType(item.id)"
          >
            <text class="type-text">{{ item.name }}</text>
          </view>
        </view>
        <text class="error-text" v-if="errors.type">{{ errors.type }}</text>
      </view>

      <!-- 反馈内容 -->
      <view class="form-section">
        <view class="section-title">反馈内容</view>
        <textarea 
          class="form-textarea" 
          placeholder="请详细描述您遇到的问题或建议..." 
          v-model="formData.content"
          :class="{ 'error': errors.content }"
          maxlength="500"
        />
        <view class="text-counter">{{ formData.content.length }}/500</view>
        <text class="error-text" v-if="errors.content">{{ errors.content }}</text>
      </view>

      <!-- 联系方式 -->
      <view class="form-section">
        <view class="section-title">联系方式（选填）</view>
        <input 
          class="form-input" 
          placeholder="手机号或邮箱，方便我们回复您" 
          v-model="formData.contact"
        />
      </view>

      <!-- 图片上传 -->
      <view class="form-section">
        <view class="section-title">相关截图（选填）</view>
        <view class="image-upload">
          <view class="image-list">
            <view 
              class="image-item" 
              v-for="(item, index) in formData.images" 
              :key="index"
            >
              <image class="image" :src="item" mode="aspectFill" @click="previewImage(index)"></image>
              <view class="image-delete" @click="deleteImage(index)">×</view>
            </view>
            <view class="image-add" @click="chooseImage" v-if="formData.images.length < 3">
              <text class="image-add-icon">+</text>
              <text class="image-add-text">添加截图</text>
            </view>
          </view>
          <text class="upload-tip">最多可上传3张图片</text>
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="form-section">
        <button class="submit-btn" @click="handleSubmit" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '提交反馈' }}
        </button>
      </view>

      <!-- 反馈记录 -->
      <view class="feedback-history" v-if="feedbackHistory.length > 0">
        <view class="history-title">我的反馈记录</view>
        <view 
          class="history-item" 
          v-for="item in feedbackHistory" 
          :key="item.id"
          @click="viewFeedbackDetail(item)"
        >
          <view class="history-header">
            <view class="history-type">{{ getFeedbackTypeName(item.type) }}</view>
            <view class="history-status" :class="getStatusClass(item.status)">
              {{ getStatusText(item.status) }}
            </view>
          </view>
          <view class="history-content">{{ item.content }}</view>
          <view class="history-time">{{ formatDate(item.createdAt) }}</view>
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
        type: '',
        content: '',
        contact: '',
        images: []
      },
      errors: {
        type: '',
        content: ''
      },
      feedbackTypes: [
        { id: 'bug', name: '功能异常' },
        { id: 'suggestion', name: '功能建议' },
        { id: 'ui', name: '界面问题' },
        { id: 'performance', name: '性能问题' },
        { id: 'other', name: '其他问题' }
      ],
      isSubmitting: false,
      feedbackHistory: []
    }
  },
  onLoad() {
    this.loadFeedbackHistory();
  },
  methods: {
    ...mapActions('feedback', ['submitFeedback', 'getFeedbackHistory', 'uploadFeedbackImage']),
    
    // 加载反馈历史
    async loadFeedbackHistory() {
      try {
        const result = await this.getFeedbackHistory();
        this.feedbackHistory = result.data || [];
      } catch (error) {
        console.error('加载反馈历史失败:', error);
      }
    },
    
    // 选择反馈类型
    selectType(typeId) {
      this.formData.type = typeId;
      this.errors.type = '';
    },
    
    // 选择图片
    chooseImage() {
      uni.chooseImage({
        count: 3 - this.formData.images.length,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.uploadImages(res.tempFilePaths);
        }
      });
    },
    
    // 上传图片
    async uploadImages(filePaths) {
      uni.showLoading({
        title: '上传中...'
      });
      
      try {
        for (const filePath of filePaths) {
          const result = await this.uploadFeedbackImage(filePath);
          this.formData.images.push(result.url);
        }
        
        uni.hideLoading();
        uni.showToast({
          title: '上传成功',
          icon: 'success'
        });
      } catch (error) {
        uni.hideLoading();
        console.error('上传图片失败:', error);
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        });
      }
    },
    
    // 预览图片
    previewImage(index) {
      uni.previewImage({
        current: index,
        urls: this.formData.images
      });
    },
    
    // 删除图片
    deleteImage(index) {
      this.formData.images.splice(index, 1);
    },
    
    // 表单验证
    validateForm() {
      let isValid = true;
      this.errors = {
        type: '',
        content: ''
      };
      
      if (!this.formData.type) {
        this.errors.type = '请选择反馈类型';
        isValid = false;
      }
      
      if (!this.formData.content.trim()) {
        this.errors.content = '请输入反馈内容';
        isValid = false;
      }
      
      return isValid;
    },
    
    // 处理提交
    async handleSubmit() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isSubmitting = true;
      
      try {
        await this.submitFeedback(this.formData);
        
        uni.showToast({
          title: '提交成功',
          icon: 'success'
        });
        
        // 重置表单
        this.resetForm();
        
        // 重新加载反馈历史
        await this.loadFeedbackHistory();
      } catch (error) {
        console.error('提交反馈失败:', error);
        uni.showToast({
          title: error.message || '提交失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isSubmitting = false;
      }
    },
    
    // 重置表单
    resetForm() {
      this.formData = {
        type: '',
        content: '',
        contact: '',
        images: []
      };
      this.errors = {
        type: '',
        content: ''
      };
    },
    
    // 查看反馈详情
    viewFeedbackDetail(item) {
      // 这里可以跳转到反馈详情页面
      // 目前使用弹窗显示详情
      let detail = `反馈类型：${this.getFeedbackTypeName(item.type)}\n`;
      detail += `反馈内容：${item.content}\n`;
      detail += `提交时间：${this.formatDate(item.createdAt)}\n`;
      detail += `处理状态：${this.getStatusText(item.status)}`;
      
      if (item.reply) {
        detail += `\n\n回复内容：${item.reply}`;
      }
      
      uni.showModal({
        title: '反馈详情',
        content: detail,
        showCancel: false
      });
    },
    
    // 获取反馈类型名称
    getFeedbackTypeName(typeId) {
      const type = this.feedbackTypes.find(item => item.id === typeId);
      return type ? type.name : '未知类型';
    },
    
    // 获取状态文本
    getStatusText(status) {
      const map = {
        'pending': '待处理',
        'processing': '处理中',
        'resolved': '已解决',
        'closed': '已关闭'
      };
      return map[status] || '未知状态';
    },
    
    // 获取状态样式类
    getStatusClass(status) {
      const map = {
        'pending': 'pending',
        'processing': 'processing',
        'resolved': 'resolved',
        'closed': 'closed'
      };
      return map[status] || '';
    },
    
    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      
      return `${year}-${month}-${day} ${hour}:${minute}`;
    }
  }
}
</script>

<style>
.feedback-page {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding: 20rpx 0;
}

.form-container {
  background-color: white;
  margin: 0 30rpx;
  border-radius: 16rpx;
  overflow: hidden;
}

.form-section {
  padding: 30rpx;
  border-bottom: 1px solid #f0f0f0;
}

.form-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.type-selector {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 20rpx;
}

.type-item {
  padding: 15rpx 30rpx;
  background-color: #f0f0f0;
  border-radius: 30rpx;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

.type-item.active {
  background-color: #3c9cff;
}

.type-text {
  font-size: 28rpx;
  color: #666;
}

.type-item.active .type-text {
  color: white;
}

.form-textarea {
  width: 100%;
  height: 200rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-textarea.error {
  border-color: #f56c6c;
}

.form-textarea:focus {
  border-color: #3c9cff;
}

.text-counter {
  text-align: right;
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.form-input {
  width: 100%;
  height: 80rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #3c9cff;
}

.error-text {
  color: #f56c6c;
  font-size: 24rpx;
  margin-top: 8rpx;
}

/* 图片上传 */
.image-upload {
  margin-top: 20rpx;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
}

.image-item {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

.image {
  width: 100%;
  height: 100%;
  border-radius: 8rpx;
}

.image-delete {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: #f56c6c;
  color: white;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24rpx;
}

.image-add {
  width: 200rpx;
  height: 200rpx;
  border: 2rpx dashed #ddd;
  border-radius: 8rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.image-add-icon {
  font-size: 60rpx;
  color: #ddd;
  margin-bottom: 10rpx;
}

.image-add-text {
  font-size: 24rpx;
  color: #999;
}

.upload-tip {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 32rpx;
  font-weight: bold;
}

.submit-btn:disabled {
  background-color: #a0cfff;
}

/* 反馈历史 */
.feedback-history {
  background-color: white;
  margin: 30rpx;
  border-radius: 16rpx;
  padding: 30rpx;
}

.history-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  padding-left: 15rpx;
  border-left: 6rpx solid #3c9cff;
}

.history-item {
  padding: 25rpx 0;
  border-bottom: 1px solid #f0f0f0;
}

.history-item:last-child {
  border-bottom: none;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15rpx;
}

.history-type {
  font-size: 28rpx;
  color: #3c9cff;
}

.history-status {
  font-size: 24rpx;
  padding: 6rpx 12rpx;
  border-radius: 30rpx;
}

.history-status.pending {
  background-color: #fff7e6;
  color: #fa8c16;
}

.history-status.processing {
  background-color: #e6f7ff;
  color: #1890ff;
}

.history-status.resolved {
  background-color: #f6ffed;
  color: #52c41a;
}

.history-status.closed {
  background-color: #f0f0f0;
  color: #999;
}

.history-content {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 10rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.history-time {
  font-size: 24rpx;
  color: #999;
}
</style>