<template>
  <view class="search-page">
    <!-- 搜索栏 -->
    <view class="search-header">
      <view class="search-bar">
        <u-search
          v-model="searchKeyword"
          placeholder="搜索错题标题、内容或标签"
          :show-action="false"
          @search="handleSearch"
          @clear="handleClearSearch"
        ></u-search>
      </view>
      <view class="filter-btn" @click="showFilterModal = true">
        <text class="filter-text">筛选</text>
        <text class="filter-icon">⚙️</text>
      </view>
    </view>

    <!-- 搜索历史 -->
    <view class="search-history" v-if="!hasSearched && searchHistory.length > 0">
      <view class="history-header">
        <text class="history-title">搜索历史</text>
        <text class="history-clear" @click="clearHistory">清空</text>
      </view>
      <view class="history-list">
        <view 
          class="history-item" 
          v-for="(item, index) in searchHistory" 
          :key="index"
          @click="searchFromHistory(item)"
        >
          {{ item }}
        </view>
      </view>
    </view>

    <!-- 热门搜索 -->
    <view class="hot-search" v-if="!hasSearched">
      <view class="hot-title">热门搜索</view>
      <view class="hot-list">
        <view 
          class="hot-item" 
          v-for="(item, index) in hotSearchList" 
          :key="index"
          @click="searchFromHistory(item)"
        >
          {{ item }}
        </view>
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="search-results" v-if="hasSearched">
      <!-- 加载状态 -->
      <view class="loading-container" v-if="isLoading">
        <u-loading-icon mode="flower" size="40"></u-loading-icon>
        <text class="loading-text">搜索中...</text>
      </view>

      <!-- 空状态 -->
      <view class="empty-container" v-else-if="searchResults.length === 0">
        <u-empty
          mode="search"
          icon="http://cdn.uviewui.com/uview/empty/search.png"
          text="未找到相关错题"
        ></u-empty>
      </view>

      <!-- 搜索结果列表 -->
      <view class="result-list" v-else>
        <view class="result-header">
          <text class="result-count">找到 {{ totalResults }} 条结果</text>
          <view class="sort-selector" @click="showSortModal = true">
            <text class="sort-text">{{ getSortText() }}</text>
            <text class="sort-arrow">▼</text>
          </view>
        </view>

        <view 
          class="result-item" 
          v-for="item in searchResults" 
          :key="item.id"
          @click="goToDetail(item.id)"
        >
          <view class="result-title">{{ item.title }}</view>
          <view class="result-content">{{ item.content }}</view>
          <view class="result-meta">
            <view class="meta-item category">{{ item.categoryName }}</view>
            <view class="meta-item difficulty" :class="getDifficultyClass(item.difficulty)">
              {{ getDifficultyText(item.difficulty) }}
            </view>
            <view class="meta-item time">{{ formatDate(item.createdAt) }}</view>
          </view>
          <view class="result-tags" v-if="item.tags && item.tags.length > 0">
            <view 
              class="tag-item" 
              v-for="(tag, index) in item.tags" 
              :key="index"
            >
              {{ tag }}
            </view>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="load-more" v-if="hasMore && !isLoading">
          <button class="load-more-btn" @click="loadMore">加载更多</button>
        </view>

        <view class="no-more" v-if="!hasMore && searchResults.length > 0">
          <text class="no-more-text">没有更多了</text>
        </view>
      </view>
    </view>

    <!-- 筛选弹窗 -->
    <u-popup
      :show="showFilterModal"
      mode="bottom"
      round="10"
      closeOnClickOverlay
      @close="showFilterModal = false"
    >
      <view class="filter-modal">
        <view class="modal-header">
          <text class="modal-title">筛选条件</text>
          <text class="modal-reset" @click="resetFilter">重置</text>
        </view>

        <!-- 分类筛选 -->
        <view class="filter-section">
          <view class="section-title">错题分类</view>
          <view class="option-list">
            <view 
              class="option-item" 
              v-for="category in categoryOptions" 
              :key="category.id"
              :class="{ 'active': filterForm.categoryId === category.id }"
              @click="selectCategory(category.id)"
            >
              {{ category.name }}
            </view>
          </view>
        </view>

        <!-- 难度筛选 -->
        <view class="filter-section">
          <view class="section-title">难度等级</view>
          <view class="option-list">
            <view 
              class="option-item" 
              v-for="item in difficultyOptions" 
              :key="item.id"
              :class="{ 'active': filterForm.difficulty === item.id }"
              @click="selectDifficulty(item.id)"
            >
              {{ item.name }}
            </view>
          </view>
        </view>

        <!-- 时间筛选 -->
        <view class="filter-section">
          <view class="section-title">创建时间</view>
          <view class="option-list">
            <view 
              class="option-item" 
              v-for="item in timeOptions" 
              :key="item.id"
              :class="{ 'active': filterForm.timeRange === item.id }"
              @click="selectTimeRange(item.id)"
            >
              {{ item.name }}
            </view>
          </view>
        </view>

        <view class="modal-actions">
          <button class="modal-btn cancel-btn" @click="showFilterModal = false">取消</button>
          <button class="modal-btn confirm-btn" @click="applyFilter">确定</button>
        </view>
      </view>
    </u-popup>

    <!-- 排序弹窗 -->
    <u-popup
      :show="showSortModal"
      mode="bottom"
      round="10"
      closeOnClickOverlay
      @close="showSortModal = false"
    >
      <view class="sort-modal">
        <view class="modal-header">
          <text class="modal-title">排序方式</text>
        </view>
        <view class="option-list">
          <view 
            class="option-item" 
            v-for="item in sortOptions" 
            :key="item.id"
            :class="{ 'active': sortType === item.id }"
            @click="selectSort(item.id)"
          >
            {{ item.name }}
          </view>
        </view>
      </view>
    </u-popup>
  </view>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

export default {
  data() {
    return {
      searchKeyword: '',
      hasSearched: false,
      isLoading: false,
      searchResults: [],
      totalResults: 0,
      currentPage: 1,
      pageSize: 10,
      hasMore: true,
      searchHistory: [],
      hotSearchList: [
        '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'
      ],
      showFilterModal: false,
      showSortModal: false,
      sortType: 'time_desc', // 默认按时间倒序
      filterForm: {
        categoryId: '',
        difficulty: '',
        timeRange: ''
      },
      tempFilterForm: {
        categoryId: '',
        difficulty: '',
        timeRange: ''
      },
      categoryOptions: [],
      difficultyOptions: [
        { id: 1, name: '简单' },
        { id: 2, name: '中等' },
        { id: 3, name: '困难' }
      ],
      timeOptions: [
        { id: '7', name: '最近7天' },
        { id: '30', name: '最近30天' },
        { id: '90', name: '最近90天' },
        { id: '365', name: '最近一年' }
      ],
      sortOptions: [
        { id: 'time_desc', name: '最新创建' },
        { id: 'time_asc', name: '最早创建' },
        { id: 'difficulty_desc', name: '难度从高到低' },
        { id: 'difficulty_asc', name: '难度从低到高' }
      ]
    }
  },
  computed: {
    ...mapGetters('categories', ['categories'])
  },
  onLoad() {
    this.loadSearchHistory();
    this.loadCategories();
  },
  methods: {
    ...mapActions('questions', ['searchQuestions']),
    ...mapActions('categories', ['getCategoryList']),
    
    // 加载搜索历史
    loadSearchHistory() {
      try {
        const history = uni.getStorageSync('searchHistory') || [];
        this.searchHistory = history.slice(0, 10); // 最多保存10条
      } catch (error) {
        console.error('加载搜索历史失败:', error);
      }
    },
    
    // 保存搜索历史
    saveSearchHistory(keyword) {
      try {
        // 移除重复项
        const index = this.searchHistory.indexOf(keyword);
        if (index > -1) {
          this.searchHistory.splice(index, 1);
        }
        
        // 添加到开头
        this.searchHistory.unshift(keyword);
        
        // 最多保存10条
        this.searchHistory = this.searchHistory.slice(0, 10);
        
        // 保存到本地存储
        uni.setStorageSync('searchHistory', this.searchHistory);
      } catch (error) {
        console.error('保存搜索历史失败:', error);
      }
    },
    
    // 清空搜索历史
    clearHistory() {
      uni.showModal({
        title: '提示',
        content: '确定要清空搜索历史吗？',
        success: (res) => {
          if (res.confirm) {
            this.searchHistory = [];
            try {
              uni.removeStorageSync('searchHistory');
            } catch (error) {
              console.error('清空搜索历史失败:', error);
            }
          }
        }
      });
    },
    
    // 从历史记录搜索
    searchFromHistory(keyword) {
      this.searchKeyword = keyword;
      this.handleSearch();
    },
    
    // 加载分类列表
    async loadCategories() {
      try {
        await this.getCategoryList();
        this.categoryOptions = this.categories.map(item => ({
          id: item.id,
          name: item.name
        }));
      } catch (error) {
        console.error('加载分类列表失败:', error);
      }
    },
    
    // 处理搜索
    handleSearch() {
      if (!this.searchKeyword.trim()) {
        uni.showToast({
          title: '请输入搜索关键词',
          icon: 'none'
        });
        return;
      }
      
      this.hasSearched = true;
      this.currentPage = 1;
      this.hasMore = true;
      this.searchResults = [];
      
      // 保存搜索历史
      this.saveSearchHistory(this.searchKeyword.trim());
      
      this.performSearch();
    },
    
    // 执行搜索
    async performSearch() {
      this.isLoading = true;
      
      try {
        const params = {
          keyword: this.searchKeyword.trim(),
          page: this.currentPage,
          pageSize: this.pageSize,
          sort: this.sortType,
          categoryId: this.filterForm.categoryId,
          difficulty: this.filterForm.difficulty,
          timeRange: this.filterForm.timeRange
        };
        
        const result = await this.searchQuestions(params);
        
        if (this.currentPage === 1) {
          this.searchResults = result.data;
        } else {
          this.searchResults = [...this.searchResults, ...result.data];
        }
        
        this.totalResults = result.total;
        this.hasMore = result.data.length === this.pageSize;
      } catch (error) {
        console.error('搜索错题失败:', error);
        uni.showToast({
          title: error.message || '搜索失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    // 加载更多
    loadMore() {
      if (this.hasMore && !this.isLoading) {
        this.currentPage++;
        this.performSearch();
      }
    },
    
    // 清除搜索
    handleClearSearch() {
      this.searchKeyword = '';
      this.hasSearched = false;
      this.searchResults = [];
      this.totalResults = 0;
      this.currentPage = 1;
      this.hasMore = true;
    },
    
    // 选择分类
    selectCategory(id) {
      this.tempFilterForm.categoryId = this.tempFilterForm.categoryId === id ? '' : id;
    },
    
    // 选择难度
    selectDifficulty(id) {
      this.tempFilterForm.difficulty = this.tempFilterForm.difficulty === id ? '' : id;
    },
    
    // 选择时间范围
    selectTimeRange(id) {
      this.tempFilterForm.timeRange = this.tempFilterForm.timeRange === id ? '' : id;
    },
    
    // 重置筛选
    resetFilter() {
      this.tempFilterForm = {
        categoryId: '',
        difficulty: '',
        timeRange: ''
      };
    },
    
    // 应用筛选
    applyFilter() {
      this.filterForm = { ...this.tempFilterForm };
      this.showFilterModal = false;
      
      if (this.hasSearched) {
        this.currentPage = 1;
        this.hasMore = true;
        this.searchResults = [];
        this.performSearch();
      }
    },
    
    // 选择排序
    selectSort(id) {
      this.sortType = id;
      this.showSortModal = false;
      
      if (this.hasSearched) {
        this.currentPage = 1;
        this.hasMore = true;
        this.searchResults = [];
        this.performSearch();
      }
    },
    
    // 获取排序文本
    getSortText() {
      const option = this.sortOptions.find(item => item.id === this.sortType);
      return option ? option.name : '最新创建';
    },
    
    // 跳转到详情页
    goToDetail(id) {
      uni.navigateTo({
        url: `/pages/questions/detail?id=${id}`
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
      
      return `${year}-${month}-${day}`;
    }
  }
}
</script>

<style>
.search-page {
  background-color: #f8f8f8;
  min-height: 100vh;
}

.search-header {
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  background-color: white;
}

.search-bar {
  flex: 1;
  margin-right: 20rpx;
}

.filter-btn {
  display: flex;
  align-items: center;
  padding: 10rpx 20rpx;
  background-color: #f0f0f0;
  border-radius: 30rpx;
}

.filter-text {
  font-size: 28rpx;
  color: #666;
  margin-right: 8rpx;
}

.filter-icon {
  font-size: 28rpx;
}

/* 搜索历史 */
.search-history {
  padding: 30rpx;
  background-color: white;
  margin-bottom: 20rpx;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.history-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
}

.history-clear {
  font-size: 28rpx;
  color: #999;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
}

.history-item {
  padding: 10rpx 20rpx;
  background-color: #f0f0f0;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

/* 热门搜索 */
.hot-search {
  padding: 30rpx;
  background-color: white;
}

.hot-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.hot-list {
  display: flex;
  flex-wrap: wrap;
}

.hot-item {
  padding: 10rpx 20rpx;
  background-color: #fff7e6;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #fa8c16;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

/* 搜索结果 */
.search-results {
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

.result-list {
  padding-bottom: 40rpx;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.result-count {
  font-size: 28rpx;
  color: #666;
}

.sort-selector {
  display: flex;
  align-items: center;
}

.sort-text {
  font-size: 28rpx;
  color: #3c9cff;
  margin-right: 8rpx;
}

.sort-arrow {
  font-size: 20rpx;
  color: #3c9cff;
}

.result-item {
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 15rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.result-content {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 15rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

.result-meta {
  display: flex;
  align-items: center;
  margin-bottom: 15rpx;
}

.meta-item {
  font-size: 24rpx;
  margin-right: 20rpx;
}

.meta-item.category {
  color: #1890ff;
}

.meta-item.difficulty.easy {
  color: #52c41a;
}

.meta-item.difficulty.medium {
  color: #fa8c16;
}

.meta-item.difficulty.hard {
  color: #f5222d;
}

.meta-item.time {
  color: #999;
}

.result-tags {
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

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 40rpx;
}

.load-more-btn {
  background-color: #f0f0f0;
  color: #666;
  border: none;
  border-radius: 30rpx;
  padding: 10rpx 40rpx;
  font-size: 28rpx;
}

.no-more {
  text-align: center;
  margin-top: 40rpx;
}

.no-more-text {
  font-size: 28rpx;
  color: #999;
}

/* 筛选弹窗 */
.filter-modal {
  padding: 40rpx 30rpx;
}

.sort-modal {
  padding: 40rpx 30rpx;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.modal-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.modal-reset {
  font-size: 28rpx;
  color: #3c9cff;
}

.filter-section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.option-list {
  display: flex;
  flex-wrap: wrap;
}

.option-item {
  padding: 15rpx 30rpx;
  background-color: #f0f0f0;
  border-radius: 30rpx;
  font-size: 28rpx;
  color: #666;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

.option-item.active {
  background-color: #3c9cff;
  color: white;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
}

.modal-btn {
  width: 300rpx;
  height: 80rpx;
  border-radius: 8rpx;
  font-size: 30rpx;
  font-weight: bold;
  border: none;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #666;
}

.confirm-btn {
  background-color: #3c9cff;
  color: white;
}
</style>