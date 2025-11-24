<template>
  <view class="question-detail-page">
    <!-- 加载状态 -->
    <view class="loading-container" v-if="isLoading">
      <u-loading-icon mode="flower" size="40"></u-loading-icon>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 错题详情 -->
    <view class="detail-container" v-else>
      <!-- 题目信息 -->
      <view class="question-card">
        <view class="question-header">
          <view class="question-title">{{ question.title }}</view>
          <view class="question-meta">
            <view class="category-tag">{{ question.categoryName }}</view>
            <view class="difficulty-tag" :class="getDifficultyClass(question.difficulty)">
              {{ getDifficultyText(question.difficulty) }}
            </view>
          </view>
        </view>

        <view class="question-content">
          <text class="content-text">{{ question.content }}</text>
          <!-- 题目图片 -->
          <view class="image-list" v-if="question.images && question.images.length > 0">
            <image 
              class="question-image" 
              v-for="(img, index) in question.images" 
              :key="index"
              :src="img" 
              mode="widthFix"
              @click="previewImage(question.images, index)"
            ></image>
          </view>
        </view>

        <!-- 标签 -->
        <view class="tag-list" v-if="question.tags && question.tags.length > 0">
          <view class="tag-item" v-for="(tag, index) in question.tags" :key="index">
            {{ tag }}
          </view>
        </view>
      </view>

      <!-- 答案区域 -->
      <view class="answer-card">
        <view class="card-title">
          <text class="title-text">正确答案</text>
          <view class="toggle-btn" @click="toggleAnswer">
            <text class="toggle-text">{{ showAnswer ? '隐藏' : '显示' }}答案</text>
            <text class="toggle-icon">{{ showAnswer ? '▲' : '▼' }}</text>
          </view>
        </view>
        <view class="answer-content" v-if="showAnswer">
          <text class="answer-text">{{ question.answer }}</text>
        </view>
      </view>

      <!-- 解题思路 -->
      <view class="solution-card">
        <view class="card-title">
          <text class="title-text">解题思路</text>
          <view class="toggle-btn" @click="toggleSolution">
            <text class="toggle-text">{{ showSolution ? '隐藏' : '显示' }}思路</text>
            <text class="toggle-icon">{{ showSolution ? '▲' : '▼' }}</text>
          </view>
        </view>
        <view class="solution-content" v-if="showSolution">
          <text class="solution-text">{{ question.solution }}</text>
        </view>
      </view>

      <!-- 我的解答 -->
      <view class="my-answer-card" v-if="myAnswer">
        <view class="card-title">
          <text class="title-text">我的解答</text>
          <view class="answer-status" :class="myAnswer.isCorrect ? 'correct' : 'incorrect'">
            {{ myAnswer.isCorrect ? '正确' : '错误' }}
          </view>
        </view>
        <view class="my-answer-content">
          <text class="answer-text">{{ myAnswer.content }}</text>
          <view class="answer-time">答题时间：{{ formatDate(myAnswer.createdAt) }}</view>
        </view>
      </view>

      <!-- 添加解答 -->
      <view class="add-answer-card" v-else>
        <view class="card-title">
          <text class="title-text">添加我的解答</text>
        </view>
        <view class="answer-form">
          <textarea 
            class="answer-input" 
            placeholder="请输入你的解答..." 
            v-model="answerContent"
            maxlength="1000"
          />
          <view class="text-counter">{{ answerContent.length }}/1000</view>
          <button class="submit-btn" @click="submitAnswer" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '提交解答' }}
          </button>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-buttons">
        <button class="action-btn edit-btn" @click="editQuestion">
          <text class="btn-icon">✏️</text>
          <text class="btn-text">编辑</text>
        </button>
        <button class="action-btn delete-btn" @click="deleteQuestion">
          <text class="btn-icon">🗑️</text>
          <text class="btn-text">删除</text>
        </button>
        <button class="action-btn share-btn" @click="shareQuestion">
          <text class="btn-icon">📤</text>
          <text class="btn-text">分享</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

export default {
  data() {
    return {
      questionId: '',
      question: {},
      myAnswer: null,
      isLoading: true,
      showAnswer: false,
      showSolution: false,
      answerContent: '',
      isSubmitting: false
    }
  },
  computed: {
    ...mapGetters('questions', ['getQuestionById', 'getMyAnswerByQuestionId'])
  },
  onLoad(options) {
    if (options.id) {
      this.questionId = options.id;
      this.loadQuestionDetail();
    } else {
      uni.showToast({
        title: '参数错误',
        icon: 'none'
      });
      setTimeout(() => {
        uni.navigateBack();
      }, 1500);
    }
  },
  methods: {
    ...mapActions('questions', [
      'getQuestionDetail', 
      'submitMyAnswer', 
      'deleteQuestion',
      'shareQuestion'
    ]),
    
    // 加载错题详情
    async loadQuestionDetail() {
      try {
        await this.getQuestionDetail(this.questionId);
        this.question = this.getQuestionById(this.questionId);
        this.myAnswer = this.getMyAnswerByQuestionId(this.questionId);
      } catch (error) {
        console.error('加载错题详情失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        });
        setTimeout(() => {
          uni.navigateBack();
        }, 1500);
      } finally {
        this.isLoading = false;
      }
    },
    
    // 切换答案显示
    toggleAnswer() {
      this.showAnswer = !this.showAnswer;
    },
    
    // 切换解题思路显示
    toggleSolution() {
      this.showSolution = !this.showSolution;
    },
    
    // 提交解答
    async submitAnswer() {
      if (!this.answerContent.trim()) {
        uni.showToast({
          title: '请输入解答内容',
          icon: 'none'
        });
        return;
      }
      
      this.isSubmitting = true;
      
      try {
        await this.submitMyAnswer({
          questionId: this.questionId,
          content: this.answerContent.trim()
        });
        
        uni.showToast({
          title: '提交成功',
          icon: 'success'
        });
        
        // 重新加载详情
        await this.loadQuestionDetail();
      } catch (error) {
        console.error('提交解答失败:', error);
        uni.showToast({
          title: error.message || '提交失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isSubmitting = false;
      }
    },
    
    // 编辑错题
    editQuestion() {
      uni.navigateTo({
        url: `/pages/questions/edit?id=${this.questionId}`
      });
    },
    
    // 删除错题
    confirmDelete() {
      uni.showModal({
        title: '提示',
        content: '确定要删除这道错题吗？',
        success: async (res) => {
          if (res.confirm) {
            this.deleteQuestion();
          }
        }
      });
    },
    
    // 执行删除
    async deleteQuestion() {
      try {
        await this.deleteQuestion(this.questionId);
        
        uni.showToast({
          title: '删除成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          uni.navigateBack();
        }, 1500);
      } catch (error) {
        console.error('删除错题失败:', error);
        uni.showToast({
          title: error.message || '删除失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 分享错题
    shareQuestion() {
      try {
        this.shareQuestion(this.questionId);
        
        uni.showToast({
          title: '分享成功',
          icon: 'success'
        });
      } catch (error) {
        console.error('分享错题失败:', error);
        uni.showToast({
          title: error.message || '分享失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 预览图片
    previewImage(images, current) {
      uni.previewImage({
        current: current,
        urls: images
      });
    },
    
    // 获取难度文本
    getDifficultyText(difficulty) {
      const map = {
        1: '简单',
        2: '中等',
        3: '困难'
      };
      return map[difficulty] || '未知';
    },
    
    // 获取难度样式类
    getDifficultyClass(difficulty) {
      const map = {
        1: 'easy',
        2: 'medium',
        3: 'hard'
      };
      return map[difficulty] || '';
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
.question-detail-page {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding: 20rpx 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 400rpx;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
  margin-top: 20rpx;
}

.detail-container {
  padding: 0 30rpx;
}

.question-card {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.question-header {
  margin-bottom: 20rpx;
}

.question-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  line-height: 1.5;
  margin-bottom: 20rpx;
}

.question-meta {
  display: flex;
  align-items: center;
}

.category-tag, .difficulty-tag {
  padding: 8rpx 16rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  margin-right: 20rpx;
}

.category-tag {
  background-color: #e6f7ff;
  color: #1890ff;
}

.difficulty-tag.easy {
  background-color: #f6ffed;
  color: #52c41a;
}

.difficulty-tag.medium {
  background-color: #fff7e6;
  color: #fa8c16;
}

.difficulty-tag.hard {
  background-color: #fff2f0;
  color: #f5222d;
}

.question-content {
  margin-bottom: 20rpx;
}

.content-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.6;
}

.image-list {
  margin-top: 20rpx;
}

.question-image {
  width: 100%;
  border-radius: 8rpx;
  margin-bottom: 20rpx;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
}

.tag-item {
  background-color: #f0f0f0;
  color: #666;
  font-size: 24rpx;
  padding: 8rpx 16rpx;
  border-radius: 30rpx;
  margin-right: 20rpx;
  margin-bottom: 10rpx;
}

.answer-card, .solution-card, .my-answer-card, .add-answer-card {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.title-text {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.toggle-btn {
  display: flex;
  align-items: center;
}

.toggle-text {
  font-size: 28rpx;
  color: #3c9cff;
  margin-right: 8rpx;
}

.toggle-icon {
  font-size: 20rpx;
  color: #3c9cff;
}

.answer-status {
  padding: 8rpx 16rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
}

.answer-status.correct {
  background-color: #f6ffed;
  color: #52c41a;
}

.answer-status.incorrect {
  background-color: #fff2f0;
  color: #f5222d;
}

.answer-content, .solution-content, .my-answer-content {
  padding: 20rpx;
  background-color: #f8f8f8;
  border-radius: 8rpx;
}

.answer-text, .solution-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.6;
}

.answer-time {
  font-size: 24rpx;
  color: #999;
  margin-top: 20rpx;
  text-align: right;
}

.answer-form {
  padding: 20rpx;
  background-color: #f8f8f8;
  border-radius: 8rpx;
}

.answer-input {
  width: 100%;
  height: 200rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.text-counter {
  text-align: right;
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.submit-btn {
  width: 100%;
  height: 80rpx;
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 30rpx;
  font-weight: bold;
  margin-top: 20rpx;
}

.submit-btn:disabled {
  background-color: #a0cfff;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
  margin-bottom: 40rpx;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 200rpx;
  height: 120rpx;
  background-color: white;
  border-radius: 16rpx;
  padding: 20rpx 0;
}

.btn-icon {
  font-size: 40rpx;
  margin-bottom: 10rpx;
}

.btn-text {
  font-size: 28rpx;
  color: #333;
}

.edit-btn {
  border: 1px solid #3c9cff;
}

.delete-btn {
  border: 1px solid #f56c6c;
}

.share-btn {
  border: 1px solid #67c23a;
}
</style>