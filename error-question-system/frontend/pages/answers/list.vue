<template>
  <view class="container">
    <!-- 搜索栏 -->
    <view class="search-section">
      <u-search 
        v-model="searchKeyword" 
        placeholder="搜索解答内容"
        @search="handleSearch"
        @clear="handleSearch"
        action-text="筛选"
        @click="showFilterModal = true"
      ></u-search>
    </view>
    
    <!-- 筛选标签 -->
    <view class="filter-tags" v-if="hasActiveFilters">
      <view class="filter-tag" v-if="filterSubject">
        <text>{{ getSubjectName(filterSubject) }}</text>
        <u-icon name="close" @click="clearFilter('subject')"></u-icon>
      </view>
      <view class="filter-tag" v-if="filterDifficulty">
        <text>{{ getDifficultyName(filterDifficulty) }}</text>
        <u-icon name="close" @click="clearFilter('difficulty')"></u-icon>
      </view>
      <view class="filter-tag" v-if="filterRating">
        <text>{{ getRatingName(filterRating) }}</text>
        <u-icon name="close" @click="clearFilter('rating')"></u-icon>
      </view>
      <view class="filter-tag" v-if="filterTime">
        <text>{{ getTimeName(filterTime) }}</text>
        <u-icon name="close" @click="clearFilter('time')"></u-icon>
      </view>
      <view class="clear-all" @click="clearAllFilters">清除全部</view>
    </view>
    
    <!-- 排序栏 -->
    <view class="sort-section">
      <view class="sort-title">排序</view>
      <view class="sort-options">
        <view 
          class="sort-item" 
          :class="{ active: sortType === 'created_at' }"
          @click="setSortType('created_at')"
        >
          <text>最新</text>
        </view>
        <view 
          class="sort-item" 
          :class="{ active: sortType === 'rating' }"
          @click="setSortType('rating')"
        >
          <text>评分最高</text>
        </view>
        <view 
          class="sort-item" 
          :class="{ active: sortType === 'like_count' }"
          @click="setSortType('like_count')"
        >
          <text>点赞最多</text>
        </view>
      </view>
    </view>
    
    <!-- 解答列表 -->
    <view class="answer-list" v-if="answerList.length > 0">
      <view 
        class="answer-item" 
        v-for="answer in answerList" 
        :key="answer.id"
        @click="goToAnswerDetail(answer.id)"
      >
        <!-- 题目信息 -->
        <view class="question-info">
          <text class="question-title">{{ answer.question.title }}</text>
          <view class="question-meta">
            <text class="subject-tag" :style="{ backgroundColor: getSubjectColor(answer.question.subject) }">
              {{ getSubjectName(answer.question.subject) }}
            </text>
            <text class="difficulty-tag" :style="{ color: getDifficultyColor(answer.question.difficulty) }">
              {{ getDifficultyName(answer.question.difficulty) }}
            </text>
          </view>
        </view>
        
        <!-- 解答内容 -->
        <view class="answer-content">
          <text class="answer-text">{{ answer.content }}</text>
          <view class="answer-images" v-if="answer.images && answer.images.length > 0">
            <image 
              v-for="(img, index) in answer.images.slice(0, 3)" 
              :key="index"
              :src="img.url" 
              mode="aspectFill"
              @click.stop="previewImage(answer.images, index)"
            ></image>
            <view class="more-images" v-if="answer.images.length > 3" @click.stop="previewImage(answer.images, 0)">
              <text>+{{ answer.images.length - 3 }}</text>
            </view>
          </view>
        </view>
        
        <!-- 用户信息 -->
        <view class="user-info">
          <view class="user-left">
            <image :src="answer.user.avatar || '/static/images/default-avatar.png'" mode="aspectFill"></image>
            <text class="username">{{ answer.user.username }}</text>
          </view>
          <view class="user-right">
            <view class="rating" v-if="answer.rating">
              <u-icon name="star-fill" color="#faad14" size="24"></u-icon>
              <text>{{ answer.rating }}</text>
            </view>
            <text class="date">{{ formatDate(answer.created_at) }}</text>
          </view>
        </view>
        
        <!-- 互动信息 -->
        <view class="interaction-info">
          <view class="interaction-item">
            <u-icon name="thumb-up" :color="answer.is_liked ? '#3cc51f' : '#999'" size="28"></u-icon>
            <text>{{ answer.like_count || 0 }}</text>
          </view>
          <view class="interaction-item">
            <u-icon name="chat" color="#999" size="28"></u-icon>
            <text>{{ answer.comment_count || 0 }}</text>
          </view>
          <view class="interaction-item" @click.stop="shareAnswer(answer)">
            <u-icon name="share" color="#999" size="28"></u-icon>
            <text>分享</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 空状态 -->
    <view class="empty-state" v-else-if="!loading">
      <image src="/static/images/empty-answer.png" mode="aspectFit"></image>
      <text class="empty-text">暂无解答</text>
      <button class="add-btn" @click="goToAddAnswer">添加解答</button>
    </view>
    
    <!-- 加载状态 -->
    <view class="loading-state" v-if="loading">
      <u-loading mode="flower" size="40"></u-loading>
      <text>加载中...</text>
    </view>
    
    <!-- 加载更多 -->
    <view class="load-more" v-if="hasMore && !loading">
      <u-loadmore 
        :status="loadMoreStatus" 
        @loadmore="loadMore"
      ></u-loadmore>
    </view>
    
    <!-- 筛选弹窗 -->
    <u-popup v-model="showFilterModal" mode="bottom" border-radius="20">
      <view class="filter-modal">
        <view class="modal-header">
          <text class="modal-title">筛选解答</text>
          <u-icon name="close" @click="showFilterModal = false"></u-icon>
        </view>
        <view class="modal-content">
          <!-- 学科筛选 -->
          <view class="filter-group">
            <view class="filter-title">学科</view>
            <view class="filter-options">
              <view 
                class="filter-option" 
                :class="{ active: filterSubject === item.id }"
                v-for="item in subjectOptions" 
                :key="item.id"
                @click="setFilter('subject', item.id)"
              >
                {{ item.name }}
              </view>
            </view>
          </view>
          
          <!-- 难度筛选 -->
          <view class="filter-group">
            <view class="filter-title">难度</view>
            <view class="filter-options">
              <view 
                class="filter-option" 
                :class="{ active: filterDifficulty === item.id }"
                v-for="item in difficultyOptions" 
                :key="item.id"
                @click="setFilter('difficulty', item.id)"
              >
                {{ item.name }}
              </view>
            </view>
          </view>
          
          <!-- 评分筛选 -->
          <view class="filter-group">
            <view class="filter-title">评分</view>
            <view class="filter-options">
              <view 
                class="filter-option" 
                :class="{ active: filterRating === item.value }"
                v-for="item in ratingOptions" 
                :key="item.value"
                @click="setFilter('rating', item.value)"
              >
                {{ item.name }}
              </view>
            </view>
          </view>
          
          <!-- 时间筛选 -->
          <view class="filter-group">
            <view class="filter-title">时间</view>
            <view class="filter-options">
              <view 
                class="filter-option" 
                :class="{ active: filterTime === item.value }"
                v-for="item in timeOptions" 
                :key="item.value"
                @click="setFilter('time', item.value)"
              >
                {{ item.name }}
              </view>
            </view>
          </view>
        </view>
        <view class="modal-footer">
          <button class="reset-btn" @click="resetFilters">重置</button>
          <button class="confirm-btn" @click="applyFilters">确定</button>
        </view>
      </view>
    </u-popup>
  </view>
</template>

<script>
import { answerApi } from '@/api'

export default {
  data() {
    return {
      // 搜索关键词
      searchKeyword: '',
      
      // 筛选条件
      filterSubject: '',
      filterDifficulty: '',
      filterRating: '',
      filterTime: '',
      tempFilterSubject: '',
      tempFilterDifficulty: '',
      tempFilterRating: '',
      tempFilterTime: '',
      
      // 排序类型
      sortType: 'created_at',
      
      // 筛选弹窗
      showFilterModal: false,
      
      // 解答列表
      answerList: [],
      
      // 分页参数
      page: 1,
      pageSize: 10,
      hasMore: true,
      loading: false,
      loadMoreStatus: 'loadmore',
      
      // 选项数据
      subjectOptions: [],
      difficultyOptions: [],
      ratingOptions: [
        { name: '5星', value: 5 },
        { name: '4星及以上', value: 4 },
        { name: '3星及以上', value: 3 },
        { name: '2星及以上', value: 2 },
        { name: '1星及以上', value: 1 }
      ],
      timeOptions: [
        { name: '今天', value: 'today' },
        { name: '本周', value: 'week' },
        { name: '本月', value: 'month' },
        { name: '三个月', value: 'quarter' },
        { name: '半年', value: 'half_year' },
        { name: '一年', value: 'year' }
      ]
    }
  },
  computed: {
    // 是否有激活的筛选条件
    hasActiveFilters() {
      return this.filterSubject || this.filterDifficulty || this.filterRating || this.filterTime
    }
  },
  onLoad() {
    this.loadOptions()
    this.loadAnswerList()
  },
  onPullDownRefresh() {
    this.refreshData()
  },
  onReachBottom() {
    if (this.hasMore && !this.loading) {
      this.loadMore()
    }
  },
  methods: {
    // 加载选项数据
    loadOptions() {
      this.subjectOptions = this.$store.state.subjects || []
      this.difficultyOptions = this.$store.state.difficultyLevels || []
    },
    
    // 加载解答列表
    async loadAnswerList(reset = false) {
      if (this.loading) return
      
      if (reset) {
        this.page = 1
        this.answerList = []
        this.hasMore = true
      }
      
      this.loading = true
      this.loadMoreStatus = 'loading'
      
      try {
        const params = {
          page: this.page,
          page_size: this.pageSize,
          search: this.searchKeyword,
          subject: this.filterSubject,
          difficulty: this.filterDifficulty,
          min_rating: this.filterRating,
          time_range: this.filterTime,
          ordering: this.sortType
        }
        
        const res = await answerApi.getAnswers(params)
        
        if (res.code === 200) {
          const newAnswers = res.data.results || []
          
          if (reset) {
            this.answerList = newAnswers
          } else {
            this.answerList = [...this.answerList, ...newAnswers]
          }
          
          this.hasMore = newAnswers.length === this.pageSize
          this.loadMoreStatus = this.hasMore ? 'loadmore' : 'nomore'
        }
      } catch (error) {
        console.error('加载解答列表失败:', error)
        this.showToast('加载失败，请重试')
        this.loadMoreStatus = 'loadmore'
      } finally {
        this.loading = false
        uni.stopPullDownRefresh()
      }
    },
    
    // 刷新数据
    refreshData() {
      this.loadAnswerList(true)
    },
    
    // 加载更多
    loadMore() {
      if (!this.hasMore || this.loading) return
      
      this.page += 1
      this.loadAnswerList()
    },
    
    // 搜索
    handleSearch() {
      this.loadAnswerList(true)
    },
    
    // 设置排序类型
    setSortType(type) {
      this.sortType = type
      this.loadAnswerList(true)
    },
    
    // 设置筛选条件
    setFilter(type, value) {
      switch (type) {
        case 'subject':
          this.tempFilterSubject = this.tempFilterSubject === value ? '' : value
          break
        case 'difficulty':
          this.tempFilterDifficulty = this.tempFilterDifficulty === value ? '' : value
          break
        case 'rating':
          this.tempFilterRating = this.tempFilterRating === value ? '' : value
          break
        case 'time':
          this.tempFilterTime = this.tempFilterTime === value ? '' : value
          break
      }
    },
    
    // 应用筛选
    applyFilters() {
      this.filterSubject = this.tempFilterSubject
      this.filterDifficulty = this.tempFilterDifficulty
      this.filterRating = this.tempFilterRating
      this.filterTime = this.tempFilterTime
      this.showFilterModal = false
      this.loadAnswerList(true)
    },
    
    // 重置筛选
    resetFilters() {
      this.tempFilterSubject = ''
      this.tempFilterDifficulty = ''
      this.tempFilterRating = ''
      this.tempFilterTime = ''
    },
    
    // 清除单个筛选条件
    clearFilter(type) {
      switch (type) {
        case 'subject':
          this.filterSubject = ''
          break
        case 'difficulty':
          this.filterDifficulty = ''
          break
        case 'rating':
          this.filterRating = ''
          break
        case 'time':
          this.filterTime = ''
          break
      }
      this.loadAnswerList(true)
    },
    
    // 清除所有筛选条件
    clearAllFilters() {
      this.filterSubject = ''
      this.filterDifficulty = ''
      this.filterRating = ''
      this.filterTime = ''
      this.loadAnswerList(true)
    },
    
    // 跳转到解答详情
    goToAnswerDetail(id) {
      uni.navigateTo({
        url: `/pages/answers/detail?id=${id}`
      })
    },
    
    // 跳转到添加解答页面
    goToAddAnswer() {
      uni.navigateTo({
        url: '/pages/answers/add'
      })
    },
    
    // 分享解答
    shareAnswer(answer) {
      // 实现分享功能
      this.showToast('分享功能开发中')
    },
    
    // 预览图片
    previewImage(images, current) {
      const urls = images.map(item => item.url)
      uni.previewImage({
        current,
        urls
      })
    },
    
    // 获取学科名称
    getSubjectName(subjectId) {
      return this.$store.getters.getSubjectNameById(subjectId)
    },
    
    // 获取学科颜色
    getSubjectColor(subjectId) {
      const subject = this.subjectOptions.find(item => item.id === subjectId)
      return subject ? subject.color : '#999'
    },
    
    // 获取难度名称
    getDifficultyName(difficulty) {
      const level = this.$store.getters.getDifficultyLevelById(difficulty)
      return level.name
    },
    
    // 获取难度颜色
    getDifficultyColor(difficulty) {
      const level = this.$store.getters.getDifficultyLevelById(difficulty)
      return level.color
    },
    
    // 获取评分名称
    getRatingName(rating) {
      const option = this.ratingOptions.find(item => item.value === rating)
      return option ? option.name : ''
    },
    
    // 获取时间名称
    getTimeName(time) {
      const option = this.timeOptions.find(item => item.value === time)
      return option ? option.name : ''
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  background-color: #f8f8f8;
  min-height: 100vh;
}

.search-section {
  padding: 20rpx;
  background-color: #fff;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  padding: 20rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #f0f0f0;
  
  .filter-tag {
    display: flex;
    align-items: center;
    background-color: rgba(24, 144, 255, 0.1);
    color: #1890ff;
    font-size: 24rpx;
    padding: 8rpx 16rpx;
    border-radius: 30rpx;
    margin-right: 20rpx;
    margin-bottom: 10rpx;
    
    .u-icon {
      margin-left: 10rpx;
    }
  }
  
  .clear-all {
    font-size: 24rpx;
    color: #999;
    margin-left: 10rpx;
  }
}

.sort-section {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #f0f0f0;
  
  .sort-title {
    font-size: 28rpx;
    color: #666;
    margin-right: 30rpx;
  }
  
  .sort-options {
    display: flex;
    
    .sort-item {
      font-size: 28rpx;
      color: #666;
      margin-right: 30rpx;
      
      &.active {
        color: #3cc51f;
        font-weight: bold;
      }
    }
  }
}

.answer-list {
  padding: 20rpx;
  
  .answer-item {
    background-color: #fff;
    border-radius: 16rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;
    
    .question-info {
      margin-bottom: 20rpx;
      
      .question-title {
        font-size: 32rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 15rpx;
        display: block;
      }
      
      .question-meta {
        display: flex;
        
        .subject-tag {
          font-size: 22rpx;
          color: #fff;
          padding: 4rpx 10rpx;
          border-radius: 20rpx;
          margin-right: 15rpx;
        }
        
        .difficulty-tag {
          font-size: 22rpx;
          font-weight: bold;
        }
      }
    }
    
    .answer-content {
      margin-bottom: 20rpx;
      
      .answer-text {
        font-size: 28rpx;
        color: #333;
        line-height: 1.6;
        display: block;
        margin-bottom: 15rpx;
      }
      
      .answer-images {
        display: flex;
        flex-wrap: wrap;
        
        image {
          width: 200rpx;
          height: 200rpx;
          border-radius: 8rpx;
          margin-right: 15rpx;
          margin-bottom: 15rpx;
        }
        
        .more-images {
          width: 200rpx;
          height: 200rpx;
          background-color: rgba(0, 0, 0, 0.5);
          border-radius: 8rpx;
          display: flex;
          align-items: center;
          justify-content: center;
          
          text {
            font-size: 28rpx;
            color: #fff;
          }
        }
      }
    }
    
    .user-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20rpx;
      
      .user-left {
        display: flex;
        align-items: center;
        
        image {
          width: 50rpx;
          height: 50rpx;
          border-radius: 50%;
          margin-right: 15rpx;
        }
        
        .username {
          font-size: 26rpx;
          color: #333;
        }
      }
      
      .user-right {
        display: flex;
        align-items: center;
        
        .rating {
          display: flex;
          align-items: center;
          margin-right: 20rpx;
          
          text {
            font-size: 24rpx;
            color: #faad14;
            margin-left: 8rpx;
          }
        }
        
        .date {
          font-size: 24rpx;
          color: #999;
        }
      }
    }
    
    .interaction-info {
      display: flex;
      
      .interaction-item {
        display: flex;
        align-items: center;
        margin-right: 40rpx;
        
        text {
          font-size: 24rpx;
          color: #999;
          margin-left: 8rpx;
        }
      }
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 0;
  
  image {
    width: 200rpx;
    height: 200rpx;
    margin-bottom: 30rpx;
  }
  
  .empty-text {
    font-size: 28rpx;
    color: #999;
    margin-bottom: 40rpx;
  }
  
  .add-btn {
    background-color: #3cc51f;
    color: #fff;
    font-size: 28rpx;
    padding: 15rpx 40rpx;
    border-radius: 40rpx;
    border: none;
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 0;
  
  text {
    font-size: 28rpx;
    color: #999;
    margin-top: 20rpx;
  }
}

.load-more {
  padding: 20rpx;
}

.filter-modal {
  padding: 40rpx;
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30rpx;
    
    .modal-title {
      font-size: 36rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .modal-content {
    max-height: 800rpx;
    overflow-y: auto;
    
    .filter-group {
      margin-bottom: 40rpx;
      
      .filter-title {
        font-size: 30rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 20rpx;
      }
      
      .filter-options {
        display: flex;
        flex-wrap: wrap;
        
        .filter-option {
          background-color: #f5f5f5;
          color: #666;
          font-size: 26rpx;
          padding: 15rpx 30rpx;
          border-radius: 30rpx;
          margin-right: 20rpx;
          margin-bottom: 20rpx;
          
          &.active {
            background-color: rgba(60, 197, 31, 0.1);
            color: #3cc51f;
          }
        }
      }
    }
  }
  
  .modal-footer {
    display: flex;
    justify-content: space-between;
    
    .reset-btn, .confirm-btn {
      width: 48%;
      height: 80rpx;
      line-height: 80rpx;
      text-align: center;
      border-radius: 40rpx;
      font-size: 30rpx;
      border: none;
    }
    
    .reset-btn {
      background-color: #f5f5f5;
      color: #666;
    }
    
    .confirm-btn {
      background-color: #3cc51f;
      color: #fff;
    }
  }
}
</style>