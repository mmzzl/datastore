<template>
  <view class="answers-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <u-search
        v-model="searchKeyword"
        placeholder="搜索解答"
        :show-action="false"
        @search="handleSearch"
        @clear="handleClearSearch"
      ></u-search>
    </view>

    <!-- 筛选标签 -->
    <view class="filter-tabs">
      <u-tabs
        :list="filterTabs"
        @click="handleTabChange"
        :current="currentTab"
        line-width="60"
        line-height="6"
        active-color="#3c9cff"
        inactive-color="#606266"
        font-size="28"
      ></u-tabs>
    </view>

    <!-- 解答列表 -->
    <view class="answers-list">
      <!-- 加载状态 -->
      <view class="loading-container" v-if="isLoading">
        <u-loading-icon mode="flower" size="40"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view class="empty-container" v-else-if="filteredAnswers.length === 0">
        <u-empty
          mode="data"
          icon="http://cdn.uviewui.com/uview/empty/data.png"
          text="暂无解答记录"
        ></u-empty>
      </view>

      <!-- 解答项 -->
      <view class="answer-item" v-for="answer in filteredAnswers" :key="answer.id">
        <view class="answer-header">
          <view class="question-title" @click="goToQuestionDetail(answer.questionId)">
            {{ answer.questionTitle }}
          </view>
          <view class="answer-status" :class="getStatusClass(answer.status)">
            {{ getStatusText(answer.status) }}
          </view>
        </view>
        
        <view class="answer-content" @click="goToAnswerDetail(answer.id)">
          <text class="answer-preview">{{ getAnswerPreview(answer.content) }}</text>
        </view>
        
        <view class="answer-footer">
          <view class="answer-meta">
            <text class="meta-item">{{ formatDate(answer.createdAt) }}</text>
            <text class="meta-item">{{ answer.difficulty }}</text>
          </view>
          <view class="answer-actions">
            <button class="action-btn edit-btn" @click="editAnswer(answer)">编辑</button>
            <button class="action-btn delete-btn" @click="confirmDelete(answer)">删除</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import { formatDate } from '@/utils';

export default {
  data() {
    return {
      searchKeyword: '',
      isLoading: true,
      currentTab: 0,
      filterTabs: [
        { name: '全部' },
        { name: '已掌握' },
        { name: '复习中' },
        { name: '待复习' }
      ]
    }
  },
  computed: {
    ...mapGetters('answers', ['answers']),
    filteredAnswers() {
      let result = this.answers;
      
      // 根据标签页筛选
      if (this.currentTab > 0) {
        const statusMap = ['', 'mastered', 'reviewing', 'pending'];
        const status = statusMap[this.currentTab];
        result = result.filter(answer => answer.status === status);
      }
      
      // 根据搜索关键词筛选
      if (this.searchKeyword) {
        result = result.filter(answer => 
          answer.questionTitle.toLowerCase().includes(this.searchKeyword.toLowerCase()) ||
          answer.content.toLowerCase().includes(this.searchKeyword.toLowerCase())
        );
      }
      
      return result;
    }
  },
  onLoad() {
    this.loadAnswers();
  },
  onPullDownRefresh() {
    this.loadAnswers().then(() => {
      uni.stopPullDownRefresh();
    });
  },
  methods: {
    ...mapActions('answers', ['getAnswerList', 'deleteAnswer']),
    
    // 加载解答列表
    async loadAnswers() {
      this.isLoading = true;
      try {
        await this.getAnswerList();
      } catch (error) {
        console.error('加载解答列表失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    // 搜索处理
    handleSearch() {
      // 搜索逻辑已在computed中实现
    },
    
    // 清除搜索
    handleClearSearch() {
      this.searchKeyword = '';
    },
    
    // 标签页切换
    handleTabChange(index) {
      this.currentTab = index;
    },
    
    // 跳转到错题详情
    goToQuestionDetail(questionId) {
      uni.navigateTo({
        url: `/pages/questions/detail?id=${questionId}`
      });
    },
    
    // 跳转到解答详情
    goToAnswerDetail(answerId) {
      uni.navigateTo({
        url: `/pages/answers/detail?id=${answerId}`
      });
    },
    
    // 编辑解答
    editAnswer(answer) {
      uni.navigateTo({
        url: `/pages/answers/edit?id=${answer.id}`
      });
    },
    
    // 确认删除
    confirmDelete(answer) {
      uni.showModal({
        title: '提示',
        content: `确定要删除这条解答吗？`,
        success: (res) => {
          if (res.confirm) {
            this.handleDelete(answer.id);
          }
        }
      });
    },
    
    // 执行删除
    async handleDelete(answerId) {
      try {
        await this.deleteAnswer(answerId);
        uni.showToast({
          title: '删除成功',
          icon: 'success'
        });
      } catch (error) {
        console.error('删除解答失败:', error);
        uni.showToast({
          title: error.message || '删除失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 获取解答预览
    getAnswerPreview(content) {
      if (!content) return '';
      return content.length > 100 ? content.substring(0, 100) + '...' : content;
    },
    
    // 获取状态文本
    getStatusText(status) {
      const statusMap = {
        'mastered': '已掌握',
        'reviewing': '复习中',
        'pending': '待复习'
      };
      return statusMap[status] || '未知';
    },
    
    // 获取状态样式类
    getStatusClass(status) {
      return `status-${status}`;
    },
    
    // 格式化日期
    formatDate(date) {
      return formatDate(date);
    }
  }
}
</script>

<style lang="scss" scoped>
.answers-page {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding-bottom: 40rpx;
}

.search-bar {
  padding: 20rpx 30rpx;
  background-color: white;
}

.filter-tabs {
  background-color: white;
  padding-bottom: 10rpx;
}

.answers-list {
  padding: 0 30rpx;
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

.empty-container {
  padding: 100rpx 0;
}

.answer-item {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20rpx;
}

.question-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
  margin-right: 20rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.answer-status {
  padding: 6rpx 16rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  white-space: nowrap;
  
  &.status-mastered {
    background-color: #e6f7ff;
    color: #1890ff;
  }
  
  &.status-reviewing {
    background-color: #fff7e6;
    color: #fa8c16;
  }
  
  &.status-pending {
    background-color: #fff2f0;
    color: #f5222d;
  }
}

.answer-content {
  margin-bottom: 20rpx;
}

.answer-preview {
  font-size: 28rpx;
  color: #666;
  line-height: 1.5;
}

.answer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.answer-meta {
  display: flex;
  align-items: center;
}

.meta-item {
  font-size: 24rpx;
  color: #999;
  margin-right: 20rpx;
}

.answer-actions {
  display: flex;
  gap: 10rpx;
}

.action-btn {
  padding: 8rpx 16rpx;
  font-size: 24rpx;
  border-radius: 8rpx;
  border: none;
}

.edit-btn {
  background-color: #e6f7ff;
  color: #1890ff;
}

.delete-btn {
  background-color: #fff2f0;
  color: #f5222d;
}
</style>