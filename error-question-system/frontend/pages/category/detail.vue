<template>
  <view class="category-detail">
    <view class="header">
      <view class="title">{{ category.name }}</view>
      <view class="stats">
        <text class="count">{{ questionCount }} 道错题</text>
      </view>
    </view>
    
    <view class="content">
      <view class="description" v-if="category.description">
        {{ category.description }}
      </view>
      
      <view class="question-list">
        <view 
          class="question-item" 
          v-for="question in questions" 
          :key="question.id"
          @click="goToQuestionDetail(question.id)"
        >
          <view class="question-title">{{ question.title }}</view>
          <view class="question-meta">
            <text class="difficulty" :style="{ color: getDifficultyColor(question.difficulty) }">
              {{ getDifficultyText(question.difficulty) }}
            </text>
            <text class="date">{{ formatDate(question.createdAt) }}</text>
          </view>
        </view>
        
        <view class="empty" v-if="questions.length === 0">
          该分类下暂无错题
        </view>
      </view>
    </view>
    
    <view class="footer">
      <u-button 
        type="primary" 
        text="添加错题" 
        @click="goToAddQuestion"
      />
    </view>
  </view>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { formatDate, getDifficultyText, getDifficultyColor } from '@/utils'

export default {
  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()
    
    const category = ref({})
    const questions = ref([])
    const questionCount = ref(0)
    const loading = ref(true)
    
    // 加载分类详情
    const loadCategoryDetail = async () => {
      try {
        const categoryId = route.params.id
        const categoryData = await store.dispatch('categories/fetchCategoryById', categoryId)
        category.value = categoryData
        
        // 加载该分类下的错题
        const { questions: questionList, total } = await store.dispatch('questions/fetchQuestions', {
          categoryId,
          page: 1,
          limit: 20
        })
        
        questions.value = questionList
        questionCount.value = total
      } catch (error) {
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      } finally {
        loading.value = false
      }
    }
    
    // 跳转到错题详情
    const goToQuestionDetail = (id) => {
      router.push(`/questions/${id}`)
    }
    
    // 跳转到添加错题页面，并预选分类
    const goToAddQuestion = () => {
      router.push({
        path: '/questions/add',
        query: {
          categoryId: category.value.id,
          categoryName: category.value.name
        }
      })
    }
    
    onMounted(() => {
      loadCategoryDetail()
    })
    
    return {
      category,
      questions,
      questionCount,
      loading,
      formatDate,
      getDifficultyText,
      getDifficultyColor,
      goToQuestionDetail,
      goToAddQuestion
    }
  }
}
</script>

<style lang="scss" scoped>
.category-detail {
  padding: 20rpx;
  min-height: 100vh;
}

.header {
  margin-bottom: 20rpx;
  
  .title {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 10rpx;
  }
  
  .stats {
    .count {
      font-size: 28rpx;
      color: #666;
    }
  }
}

.content {
  .description {
    font-size: 28rpx;
    color: #666;
    line-height: 1.5;
    margin-bottom: 20rpx;
    padding: 20rpx;
    background-color: #f5f5f5;
    border-radius: 10rpx;
  }
  
  .question-list {
    .question-item {
      padding: 20rpx;
      background-color: #fff;
      border-radius: 10rpx;
      margin-bottom: 20rpx;
      box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
      
      .question-title {
        font-size: 30rpx;
        color: #333;
        margin-bottom: 10rpx;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      
      .question-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .difficulty {
          font-size: 24rpx;
        }
        
        .date {
          font-size: 24rpx;
          color: #999;
        }
      }
    }
    
    .empty {
      text-align: center;
      padding: 60rpx 0;
      color: #999;
      font-size: 28rpx;
    }
  }
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx;
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.1);
}
</style>