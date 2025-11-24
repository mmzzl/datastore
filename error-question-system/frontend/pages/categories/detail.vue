<template>
  <view class="container" v-if="categoryDetail">
    <!-- 分类信息 -->
    <view class="category-info">
      <view class="category-header">
        <view class="category-icon" :style="{ backgroundColor: categoryDetail.color || '#3cc51f' }">
          <text class="icon-text">{{ categoryDetail.name.charAt(0) }}</text>
        </view>
        <view class="category-details">
          <text class="category-name">{{ categoryDetail.name }}</text>
          <text class="category-desc" v-if="categoryDetail.description">{{ categoryDetail.description }}</text>
          <text class="create-time">创建于 {{ formatDate(categoryDetail.created_at) }}</text>
        </view>
      </view>
      <view class="category-stats">
        <view class="stat-item">
          <text class="stat-value">{{ categoryDetail.question_count || 0 }}</text>
          <text class="stat-name">题目</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ categoryDetail.answer_count || 0 }}</text>
          <text class="stat-name">解答</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ categoryDetail.knowledge_point_count || 0 }}</text>
          <text class="stat-name">知识点</text>
        </view>
      </view>
    </view>

    <!-- 知识点列表 -->
    <view class="knowledge-points-section">
      <view class="section-header">
        <text class="section-title">知识点</text>
        <view class="add-btn" @click="showAddKnowledgePointModal = true">
          <u-icon name="plus" color="#3cc51f" size="28"></u-icon>
          <text>添加</text>
        </view>
      </view>
      
      <!-- 知识点列表 -->
      <view class="knowledge-list" v-if="knowledgePoints.length > 0">
        <view 
          class="knowledge-item" 
          v-for="point in knowledgePoints" 
          :key="point.id"
        >
          <view class="knowledge-content">
            <text class="knowledge-name">{{ point.name }}</text>
            <text class="knowledge-desc" v-if="point.description">{{ point.description }}</text>
          </view>
          <view class="knowledge-actions">
            <text class="action-btn edit-btn" @click="editKnowledgePoint(point)">编辑</text>
            <text class="action-btn delete-btn" @click="confirmDeleteKnowledgePoint(point)">删除</text>
          </view>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-else>
        <image src="/static/images/empty-knowledge.png" mode="aspectFit"></image>
        <text class="empty-text">暂无知识点</text>
        <button class="create-btn" @click="showAddKnowledgePointModal = true">添加知识点</button>
      </view>
    </view>

    <!-- 题目列表 -->
    <view class="questions-section">
      <view class="section-header">
        <text class="section-title">错题列表</text>
        <view class="view-all-btn" @click="viewAllQuestions">
          <text>查看全部</text>
          <u-icon name="arrow-right" color="#999" size="24"></u-icon>
        </view>
      </view>
      
      <!-- 题目列表 -->
      <view class="question-list" v-if="questions.length > 0">
        <view 
          class="question-item" 
          v-for="question in questions" 
          :key="question.id"
          @click="viewQuestion(question)"
        >
          <view class="question-header">
            <text class="question-title">{{ question.title }}</text>
            <view class="question-meta">
              <text class="subject-tag" :style="{ backgroundColor: getSubjectColor(question.subject) }">
                {{ getSubjectName(question.subject) }}
              </text>
              <text class="difficulty-tag" :style="{ color: getDifficultyColor(question.difficulty) }">
                {{ getDifficultyName(question.difficulty) }}
              </text>
            </view>
          </view>
          <text class="question-content">{{ question.content }}</text>
          <view class="question-footer">
            <text class="create-time">{{ formatDate(question.created_at) }}</text>
            <view class="question-stats">
              <view class="stat-item">
                <u-icon name="chat" color="#999" size="24"></u-icon>
                <text>{{ question.answer_count || 0 }}</text>
              </view>
              <view class="stat-item">
                <u-icon name="thumb-up" color="#999" size="24"></u-icon>
                <text>{{ question.like_count || 0 }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-else>
        <image src="/static/images/empty-question.png" mode="aspectFit"></image>
        <text class="empty-text">暂无错题</text>
        <button class="create-btn" @click="addQuestion">添加错题</button>
      </view>
    </view>

    <!-- 添加/编辑知识点弹窗 -->
    <u-popup v-model="showAddKnowledgePointModal" mode="center" width="600" border-radius="20">
      <view class="knowledge-modal">
        <view class="modal-header">
          <text class="modal-title">{{ editingKnowledgePoint ? '编辑知识点' : '添加知识点' }}</text>
          <u-icon name="close" @click="closeKnowledgePointModal"></u-icon>
        </view>
        <view class="modal-content">
          <u-form ref="knowledgeForm" :model="knowledgeForm" :rules="knowledgeRules">
            <u-form-item label="知识点名称" prop="name" required>
              <u-input 
                v-model="knowledgeForm.name" 
                placeholder="请输入知识点名称"
                maxlength="50"
              ></u-input>
            </u-form-item>
            <u-form-item label="知识点描述" prop="description">
              <u-textarea 
                v-model="knowledgeForm.description" 
                placeholder="请输入知识点描述"
                :maxlength="200"
                height="120"
              ></u-textarea>
            </u-form-item>
          </u-form>
        </view>
        <view class="modal-footer">
          <button class="cancel-btn" @click="closeKnowledgePointModal">取消</button>
          <button class="submit-btn" @click="submitKnowledgePoint">{{ editingKnowledgePoint ? '更新' : '创建' }}</button>
        </view>
      </view>
    </u-popup>

    <!-- 删除知识点确认弹窗 -->
    <u-modal 
      v-model="showDeleteKnowledgePointModal" 
      title="删除确认" 
      :content="`确定要删除知识点「${deletingKnowledgePoint ? deletingKnowledgePoint.name : ''}」吗？`"
      :show-cancel-button="true"
      @confirm="deleteKnowledgePoint"
    ></u-modal>
  </view>
</template>

<script>
import { categoryApi, questionApi } from '@/api'

export default {
  data() {
    return {
      // 分类ID
      categoryId: null,
      
      // 分类详情
      categoryDetail: null,
      
      // 知识点列表
      knowledgePoints: [],
      
      // 题目列表
      questions: [],
      
      // 弹窗状态
      showAddKnowledgePointModal: false,
      showDeleteKnowledgePointModal: false,
      
      // 编辑状态
      editingKnowledgePoint: null,
      deletingKnowledgePoint: null,
      
      // 表单数据
      knowledgeForm: {
        name: '',
        description: ''
      },
      
      // 表单验证规则
      knowledgeRules: {
        name: [
          { required: true, message: '请输入知识点名称', trigger: 'blur' },
          { min: 1, max: 50, message: '知识点名称长度在1到50个字符', trigger: 'blur' }
        ]
      }
    }
  },
  onLoad(options) {
    if (options.id) {
      this.categoryId = options.id
      this.loadCategoryDetail()
      this.loadKnowledgePoints()
      this.loadQuestions()
    }
  },
  onPullDownRefresh() {
    Promise.all([
      this.loadCategoryDetail(),
      this.loadKnowledgePoints(),
      this.loadQuestions()
    ]).finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  methods: {
    // 加载分类详情
    async loadCategoryDetail() {
      try {
        const res = await categoryApi.getCategoryDetail(this.categoryId)
        if (res.code === 200) {
          this.categoryDetail = res.data
        }
      } catch (error) {
        console.error('加载分类详情失败:', error)
        this.showToast('加载失败，请重试')
      }
    },
    
    // 加载知识点列表
    async loadKnowledgePoints() {
      try {
        const res = await categoryApi.getCategoryKnowledgePoints(this.categoryId)
        if (res.code === 200) {
          this.knowledgePoints = res.data || []
        }
      } catch (error) {
        console.error('加载知识点列表失败:', error)
      }
    },
    
    // 加载题目列表
    async loadQuestions() {
      try {
        const params = {
          category: this.categoryId,
          page_size: 5
        }
        
        const res = await questionApi.getQuestions(params)
        if (res.code === 200) {
          this.questions = res.data.results || []
        }
      } catch (error) {
        console.error('加载题目列表失败:', error)
      }
    },
    
    // 编辑知识点
    editKnowledgePoint(point) {
      this.editingKnowledgePoint = point
      this.knowledgeForm = {
        name: point.name,
        description: point.description || ''
      }
      this.showAddKnowledgePointModal = true
    },
    
    // 确认删除知识点
    confirmDeleteKnowledgePoint(point) {
      this.deletingKnowledgePoint = point
      this.showDeleteKnowledgePointModal = true
    },
    
    // 删除知识点
    async deleteKnowledgePoint() {
      try {
        this.showLoading('删除中...')
        
        const res = await categoryApi.deleteKnowledgePoint(this.deletingKnowledgePoint.id)
        if (res.code === 200) {
          this.showToast('删除成功')
          this.loadKnowledgePoints()
          this.loadCategoryDetail() // 更新知识点数量
        }
      } catch (error) {
        console.error('删除知识点失败:', error)
        this.showToast('删除失败，请重试')
      } finally {
        this.hideLoading()
        this.deletingKnowledgePoint = null
      }
    },
    
    // 关闭知识点弹窗
    closeKnowledgePointModal() {
      this.showAddKnowledgePointModal = false
      this.editingKnowledgePoint = null
      this.knowledgeForm = {
        name: '',
        description: ''
      }
    },
    
    // 提交知识点
    async submitKnowledgePoint() {
      try {
        // 表单验证
        await this.$refs.knowledgeForm.validate()
        
        this.showLoading(this.editingKnowledgePoint ? '更新中...' : '创建中...')
        
        let res
        if (this.editingKnowledgePoint) {
          // 更新知识点
          res = await categoryApi.updateKnowledgePoint(this.editingKnowledgePoint.id, this.knowledgeForm)
        } else {
          // 创建知识点
          res = await categoryApi.createKnowledgePoint(this.categoryId, this.knowledgeForm)
        }
        
        if (res.code === 200) {
          this.showToast(this.editingKnowledgePoint ? '更新成功' : '创建成功')
          this.closeKnowledgePointModal()
          this.loadKnowledgePoints()
          this.loadCategoryDetail() // 更新知识点数量
        }
      } catch (error) {
        console.error('提交知识点失败:', error)
        this.showToast('操作失败，请重试')
      } finally {
        this.hideLoading()
      }
    },
    
    // 查看题目详情
    viewQuestion(question) {
      uni.navigateTo({
        url: `/pages/questions/detail?id=${question.id}`
      })
    },
    
    // 查看所有题目
    viewAllQuestions() {
      uni.navigateTo({
        url: `/pages/questions/list?category=${this.categoryId}`
      })
    },
    
    // 添加题目
    addQuestion() {
      uni.navigateTo({
        url: `/pages/questions/add?category=${this.categoryId}`
      })
    },
    
    // 获取学科名称
    getSubjectName(subjectId) {
      return this.$store.getters.getSubjectNameById(subjectId)
    },
    
    // 获取学科颜色
    getSubjectColor(subjectId) {
      const subject = this.$store.getters.getSubjectById(subjectId)
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
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding-bottom: 40rpx;
}

.category-info {
  background-color: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .category-header {
    display: flex;
    align-items: center;
    margin-bottom: 30rpx;
    
    .category-icon {
      width: 100rpx;
      height: 100rpx;
      border-radius: 20rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 30rpx;
      
      .icon-text {
        font-size: 48rpx;
        font-weight: bold;
        color: #fff;
      }
    }
    
    .category-details {
      flex: 1;
      
      .category-name {
        font-size: 36rpx;
        font-weight: bold;
        color: #333;
        display: block;
        margin-bottom: 10rpx;
      }
      
      .category-desc {
        font-size: 28rpx;
        color: #666;
        display: block;
        margin-bottom: 10rpx;
      }
      
      .create-time {
        font-size: 24rpx;
        color: #999;
      }
    }
  }
  
  .category-stats {
    display: flex;
    padding-top: 20rpx;
    border-top: 1rpx solid #f0f0f0;
    
    .stat-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      
      .stat-value {
        font-size: 40rpx;
        font-weight: bold;
        color: #3cc51f;
        margin-bottom: 10rpx;
      }
      
      .stat-name {
        font-size: 24rpx;
        color: #999;
      }
    }
  }
}

.knowledge-points-section, .questions-section {
  background-color: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30rpx;
    
    .section-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
    
    .add-btn, .view-all-btn {
      display: flex;
      align-items: center;
      
      text {
        font-size: 26rpx;
        color: #3cc51f;
        margin-left: 10rpx;
      }
    }
    
    .view-all-btn {
      text {
        color: #999;
      }
    }
  }
  
  .knowledge-list {
    .knowledge-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20rpx 0;
      border-bottom: 1rpx solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .knowledge-content {
        flex: 1;
        
        .knowledge-name {
          font-size: 30rpx;
          color: #333;
          font-weight: bold;
          display: block;
          margin-bottom: 10rpx;
        }
        
        .knowledge-desc {
          font-size: 26rpx;
          color: #666;
        }
      }
      
      .knowledge-actions {
        display: flex;
        
        .action-btn {
          font-size: 26rpx;
          margin-left: 20rpx;
          
          &.edit-btn {
            color: #1890ff;
          }
          
          &.delete-btn {
            color: #f5222d;
          }
        }
      }
    }
  }
  
  .question-list {
    .question-item {
      padding: 20rpx 0;
      border-bottom: 1rpx solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .question-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15rpx;
        
        .question-title {
          font-size: 30rpx;
          font-weight: bold;
          color: #333;
          flex: 1;
        }
        
        .question-meta {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          
          .subject-tag {
            font-size: 22rpx;
            color: #fff;
            padding: 4rpx 10rpx;
            border-radius: 16rpx;
            margin-bottom: 8rpx;
          }
          
          .difficulty-tag {
            font-size: 22rpx;
            font-weight: bold;
          }
        }
      }
      
      .question-content {
        font-size: 28rpx;
        color: #666;
        margin-bottom: 15rpx;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      
      .question-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .create-time {
          font-size: 24rpx;
          color: #999;
        }
        
        .question-stats {
          display: flex;
          
          .stat-item {
            display: flex;
            align-items: center;
            margin-left: 20rpx;
            
            text {
              font-size: 24rpx;
              color: #999;
              margin-left: 8rpx;
            }
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
    
    .create-btn {
      background-color: #3cc51f;
      color: #fff;
      font-size: 28rpx;
      padding: 20rpx 40rpx;
      border-radius: 40rpx;
      border: none;
    }
  }
}

.knowledge-modal {
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
    margin-bottom: 40rpx;
  }
  
  .modal-footer {
    display: flex;
    justify-content: space-between;
    
    .cancel-btn, .submit-btn {
      width: 48%;
      height: 80rpx;
      line-height: 80rpx;
      text-align: center;
      border-radius: 40rpx;
      font-size: 30rpx;
      border: none;
    }
    
    .cancel-btn {
      background-color: #f5f5f5;
      color: #666;
    }
    
    .submit-btn {
      background-color: #3cc51f;
      color: #fff;
    }
  }
}
</style>