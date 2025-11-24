<template>
  <view class="questions-list-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrapper">
        <input 
          class="search-input" 
          placeholder="搜索错题..." 
          v-model="searchKeyword"
          @confirm="handleSearch"
        />
        <text class="search-icon" @click="handleSearch">🔍</text>
      </view>
    </view>

    <!-- 筛选栏 -->
    <view class="filter-bar">
      <view class="filter-item" @click="showCategoryPicker">
        <text class="filter-text">{{ selectedCategory.name || '全部分类' }}</text>
        <text class="filter-arrow">▼</text>
      </view>
      <view class="filter-item" @click="showSortPicker">
        <text class="filter-text">{{ sortOptions[currentSort].name }}</text>
        <text class="filter-arrow">▼</text>
      </view>
      <view class="filter-item" @click="showStatusPicker">
        <text class="filter-text">{{ statusOptions[currentStatus].name }}</text>
        <text class="filter-arrow">▼</text>
      </view>
    </view>

    <!-- 错题列表 -->
    <view class="questions-list">
      <view 
        class="question-item" 
        v-for="(item, index) in filteredQuestions" 
        :key="item.id"
        @click="navigateToDetail(item.id)"
      >
        <view class="question-header">
          <text class="question-title">{{ item.title }}</text>
          <view class="question-status" :class="getStatusClass(item.status)">
            {{ getStatusText(item.status) }}
          </view>
        </view>
        <view class="question-content">
          <text class="question-text">{{ item.content }}</text>
        </view>
        <view class="question-footer">
          <text class="question-category">{{ item.category }}</text>
          <text class="question-date">{{ formatDate(item.createTime) }}</text>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-if="filteredQuestions.length === 0">
        <text class="empty-icon">📚</text>
        <text class="empty-text">暂无错题</text>
        <button class="add-btn" @click="navigateToAdd">添加错题</button>
      </view>
    </view>

    <!-- 添加按钮 -->
    <view class="add-button" @click="navigateToAdd">
      <text class="add-icon">+</text>
    </view>

    <!-- 分类选择器 -->
    <picker 
      mode="selector" 
      :range="categoryOptions" 
      range-key="name"
      @change="handleCategoryChange"
      :value="selectedCategoryIndex"
    >
      <view></view>
    </picker>

    <!-- 排序选择器 -->
    <picker 
      mode="selector" 
      :range="sortOptions" 
      range-key="name"
      @change="handleSortChange"
      :value="currentSort"
    >
      <view></view>
    </picker>

    <!-- 状态选择器 -->
    <picker 
      mode="selector" 
      :range="statusOptions" 
      range-key="name"
      @change="handleStatusChange"
      :value="currentStatus"
    >
      <view></view>
    </picker>
  </view>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  data() {
    return {
      searchKeyword: '',
      selectedCategory: { id: '', name: '' },
      selectedCategoryIndex: 0,
      currentSort: 0, // 0: 最新, 1: 最旧, 2: 难度
      currentStatus: 0, // 0: 全部, 1: 未解决, 2: 已解决
      sortOptions: [
        { id: 'newest', name: '最新' },
        { id: 'oldest', name: '最旧' },
        { id: 'difficulty', name: '难度' }
      ],
      statusOptions: [
        { id: 'all', name: '全部状态' },
        { id: 'unsolved', name: '未解决' },
        { id: 'solved', name: '已解决' }
      ],
      categoryOptions: [
        { id: '', name: '全部分类' }
      ]
    }
  },
  computed: {
    ...mapState('questions', ['questions']),
    ...mapState('categories', ['categories']),
    
    // 过滤后的错题列表
    filteredQuestions() {
      let result = [...this.questions];
      
      // 按分类过滤
      if (this.selectedCategory.id) {
        result = result.filter(item => item.categoryId === this.selectedCategory.id);
      }
      
      // 按状态过滤
      if (this.currentStatus === 1) { // 未解决
        result = result.filter(item => item.status !== 'solved');
      } else if (this.currentStatus === 2) { // 已解决
        result = result.filter(item => item.status === 'solved');
      }
      
      // 按关键词搜索
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.toLowerCase();
        result = result.filter(item => 
          item.title.toLowerCase().includes(keyword) || 
          item.content.toLowerCase().includes(keyword)
        );
      }
      
      // 排序
      if (this.currentSort === 0) { // 最新
        result.sort((a, b) => b.createTime - a.createTime);
      } else if (this.currentSort === 1) { // 最旧
        result.sort((a, b) => a.createTime - b.createTime);
      } else if (this.currentSort === 2) { // 难度
        result.sort((a, b) => (b.difficulty || 0) - (a.difficulty || 0));
      }
      
      return result;
    }
  },
  onLoad() {
    this.loadQuestions();
    this.loadCategories();
  },
  onShow() {
    // 每次显示页面时刷新数据
    this.loadQuestions();
  },
  onPullDownRefresh() {
    this.loadQuestions().then(() => {
      uni.stopPullDownRefresh();
    });
  },
  methods: {
    ...mapActions('questions', ['getQuestionList']),
    ...mapActions('categories', ['getCategoryList']),
    
    // 加载错题列表
    async loadQuestions() {
      try {
        await this.getQuestionList();
      } catch (error) {
        console.error('加载错题列表失败:', error);
        uni.showToast({
          title: '加载失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 加载分类列表
    async loadCategories() {
      try {
        await this.getCategoryList();
        // 更新分类选项
        this.categoryOptions = [
          { id: '', name: '全部分类' },
          ...this.categories.map(item => ({
            id: item.id,
            name: item.name
          }))
        ];
      } catch (error) {
        console.error('加载分类列表失败:', error);
      }
    },
    
    // 处理搜索
    handleSearch() {
      // 搜索逻辑已在计算属性中处理
    },
    
    // 显示分类选择器
    showCategoryPicker() {
      // 这里应该触发picker组件
    },
    
    // 显示排序选择器
    showSortPicker() {
      // 这里应该触发picker组件
    },
    
    // 显示状态选择器
    showStatusPicker() {
      // 这里应该触发picker组件
    },
    
    // 处理分类变化
    handleCategoryChange(e) {
      this.selectedCategoryIndex = e.detail.value;
      this.selectedCategory = this.categoryOptions[this.selectedCategoryIndex];
    },
    
    // 处理排序变化
    handleSortChange(e) {
      this.currentSort = e.detail.value;
    },
    
    // 处理状态变化
    handleStatusChange(e) {
      this.currentStatus = e.detail.value;
    },
    
    // 获取状态样式类
    getStatusClass(status) {
      if (status === 'solved') {
        return 'status-solved';
      } else if (status === 'reviewing') {
        return 'status-reviewing';
      } else {
        return 'status-unsolved';
      }
    },
    
    // 获取状态文本
    getStatusText(status) {
      if (status === 'solved') {
        return '已解决';
      } else if (status === 'reviewing') {
        return '复习中';
      } else {
        return '未解决';
      }
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
      } else if (days < 30) {
        return `${Math.floor(days / 7)}周前`;
      } else {
        return `${date.getMonth() + 1}月${date.getDate()}日`;
      }
    },
    
    // 跳转到错题详情
    navigateToDetail(id) {
      uni.navigateTo({
        url: `/pages/questions/detail?id=${id}`
      });
    },
    
    // 跳转到添加错题页面
    navigateToAdd() {
      uni.navigateTo({
        url: '/pages/questions/add'
      });
    }
  }
}
</script>

<style>
.questions-list-page {
  background-color: #f8f8f8;
  min-height: 100vh;
}

/* 搜索栏 */
.search-bar {
  padding: 20rpx 30rpx;
  background-color: white;
  border-bottom: 1px solid #f0f0f0;
}

.search-input-wrapper {
  position: relative;
}

.search-input {
  width: 100%;
  height: 70rpx;
  background-color: #f5f5f5;
  border-radius: 35rpx;
  padding: 0 80rpx 0 30rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.search-icon {
  position: absolute;
  right: 30rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 32rpx;
  color: #999;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  background-color: white;
  border-bottom: 1px solid #f0f0f0;
}

.filter-item {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80rpx;
  position: relative;
}

.filter-item:not(:last-child)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 40rpx;
  width: 1px;
  background-color: #f0f0f0;
}

.filter-text {
  font-size: 28rpx;
  color: #333;
  margin-right: 10rpx;
}

.filter-arrow {
  font-size: 20rpx;
  color: #999;
}

/* 错题列表 */
.questions-list {
  padding: 20rpx 30rpx;
}

.question-item {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.question-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
  margin-right: 20rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.question-status {
  font-size: 24rpx;
  padding: 6rpx 16rpx;
  border-radius: 12rpx;
  color: white;
}

.status-solved {
  background-color: #5ac725;
}

.status-reviewing {
  background-color: #f9ae3d;
}

.status-unsolved {
  background-color: #f56c6c;
}

.question-content {
  margin-bottom: 20rpx;
}

.question-text {
  font-size: 28rpx;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-category {
  font-size: 24rpx;
  color: #3c9cff;
  background-color: rgba(60, 156, 255, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
}

.question-date {
  font-size: 24rpx;
  color: #999;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
}

.empty-icon {
  font-size: 100rpx;
  margin-bottom: 30rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.add-btn {
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 40rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
}

/* 添加按钮 */
.add-button {
  position: fixed;
  right: 40rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background-color: #3c9cff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(60, 156, 255, 0.4);
}

.add-icon {
  font-size: 48rpx;
  color: white;
  font-weight: bold;
}
</style>