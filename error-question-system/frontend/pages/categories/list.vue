<template>
  <view class="container">
    <!-- 搜索栏 -->
    <view class="search-section">
      <u-search 
        v-model="searchKeyword" 
        placeholder="搜索分类" 
        :show-action="false"
        @search="searchCategories"
        @clear="clearSearch"
      ></u-search>
    </view>

    <!-- 分类统计 -->
    <view class="stats-section">
      <view class="stat-card">
        <text class="stat-number">{{ categories.length }}</text>
        <text class="stat-label">全部分类</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ totalQuestions }}</text>
        <text class="stat-label">错题总数</text>
      </view>
      <view class="stat-card">
        <text class="stat-number">{{ totalAnswers }}</text>
        <text class="stat-label">解答总数</text>
      </view>
    </view>

    <!-- 分类列表 -->
    <view class="categories-section">
      <view class="section-header">
        <text class="section-title">分类列表</text>
        <view class="sort-actions">
          <text 
            class="sort-item" 
            :class="{ active: sortBy === 'name' }"
            @click="setSortBy('name')"
          >
            名称
          </text>
          <text 
            class="sort-item" 
            :class="{ active: sortBy === 'question_count' }"
            @click="setSortBy('question_count')"
          >
            题目数
          </text>
          <text 
            class="sort-item" 
            :class="{ active: sortBy === 'created_at' }"
            @click="setSortBy('created_at')"
          >
            创建时间
          </text>
        </view>
      </view>
      
      <!-- 分类列表 -->
      <view class="category-list" v-if="sortedCategories.length > 0">
        <view 
          class="category-item" 
          v-for="category in sortedCategories" 
          :key="category.id"
          @click="viewCategory(category)"
        >
          <view class="category-header">
            <view class="category-info">
              <view class="category-icon" :style="{ backgroundColor: category.color || '#3cc51f' }">
                <text class="icon-text">{{ category.name.charAt(0) }}</text>
              </view>
              <view class="category-details">
                <text class="category-name">{{ category.name }}</text>
                <text class="category-desc" v-if="category.description">{{ category.description }}</text>
              </view>
            </view>
            <view class="category-actions">
              <u-icon name="arrow-right" color="#999" size="32"></u-icon>
            </view>
          </view>
          <view class="category-stats">
            <view class="stat-item">
              <text class="stat-value">{{ category.question_count || 0 }}</text>
              <text class="stat-name">题目</text>
            </view>
            <view class="stat-item">
              <text class="stat-value">{{ category.answer_count || 0 }}</text>
              <text class="stat-name">解答</text>
            </view>
            <view class="stat-item">
              <text class="stat-value">{{ category.knowledge_point_count || 0 }}</text>
              <text class="stat-name">知识点</text>
            </view>
          </view>
          <view class="category-footer">
            <text class="create-time">创建于 {{ formatDate(category.created_at) }}</text>
            <view class="action-buttons">
              <text class="action-btn edit-btn" @click.stop="editCategory(category)">编辑</text>
              <text class="action-btn delete-btn" @click.stop="confirmDelete(category)">删除</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-else>
        <image src="/static/images/empty-category.png" mode="aspectFit"></image>
        <text class="empty-text">{{ searchKeyword ? '未找到相关分类' : '暂无分类' }}</text>
        <button class="create-btn" v-if="!searchKeyword" @click="showAddModal = true">创建分类</button>
      </view>
    </view>

    <!-- 添加分类按钮 -->
    <view class="add-category-btn" @click="showAddModal = true">
      <u-icon name="plus" color="#fff" size="32"></u-icon>
    </view>

    <!-- 添加/编辑分类弹窗 -->
    <u-popup v-model="showAddModal" mode="center" width="600" border-radius="20">
      <view class="category-modal">
        <view class="modal-header">
          <text class="modal-title">{{ editingCategory ? '编辑分类' : '添加分类' }}</text>
          <u-icon name="close" @click="closeModal"></u-icon>
        </view>
        <view class="modal-content">
          <u-form ref="categoryForm" :model="categoryForm" :rules="categoryRules">
            <u-form-item label="分类名称" prop="name" required>
              <u-input 
                v-model="categoryForm.name" 
                placeholder="请输入分类名称"
                maxlength="20"
              ></u-input>
            </u-form-item>
            <u-form-item label="分类描述" prop="description">
              <u-textarea 
                v-model="categoryForm.description" 
                placeholder="请输入分类描述"
                :maxlength="100"
                height="100"
              ></u-textarea>
            </u-form-item>
            <u-form-item label="分类颜色" prop="color">
              <view class="color-picker">
                <view 
                  class="color-item" 
                  v-for="color in colorOptions" 
                  :key="color"
                  :style="{ backgroundColor: color }"
                  :class="{ active: categoryForm.color === color }"
                  @click="categoryForm.color = color"
                ></view>
              </view>
            </u-form-item>
          </u-form>
        </view>
        <view class="modal-footer">
          <button class="cancel-btn" @click="closeModal">取消</button>
          <button class="submit-btn" @click="submitCategory">{{ editingCategory ? '更新' : '创建' }}</button>
        </view>
      </view>
    </u-popup>

    <!-- 删除确认弹窗 -->
    <u-modal 
      v-model="showDeleteModal" 
      title="删除确认" 
      :content="`确定要删除分类「${deletingCategory ? deletingCategory.name : ''}」吗？删除后该分类下的题目将不再有分类。`"
      :show-cancel-button="true"
      @confirm="deleteCategory"
    ></u-modal>
  </view>
</template>

<script>
import { categoryApi } from '@/api'

export default {
  data() {
    return {
      // 分类列表
      categories: [],
      
      // 搜索关键词
      searchKeyword: '',
      
      // 排序方式
      sortBy: 'name',
      
      // 统计数据
      totalQuestions: 0,
      totalAnswers: 0,
      
      // 弹窗状态
      showAddModal: false,
      showDeleteModal: false,
      
      // 编辑状态
      editingCategory: null,
      deletingCategory: null,
      
      // 表单数据
      categoryForm: {
        name: '',
        description: '',
        color: '#3cc51f'
      },
      
      // 表单验证规则
      categoryRules: {
        name: [
          { required: true, message: '请输入分类名称', trigger: 'blur' },
          { min: 1, max: 20, message: '分类名称长度在1到20个字符', trigger: 'blur' }
        ]
      },
      
      // 颜色选项
      colorOptions: [
        '#3cc51f', '#1890ff', '#722ed1', '#eb2f96', '#fa541c', 
        '#faad14', '#52c41a', '#13c2c2', '#2f54eb', '#f5222d'
      ]
    }
  },
  computed: {
    // 排序后的分类列表
    sortedCategories() {
      const categories = [...this.categories]
      
      if (this.sortBy === 'name') {
        return categories.sort((a, b) => a.name.localeCompare(b.name))
      } else if (this.sortBy === 'question_count') {
        return categories.sort((a, b) => (b.question_count || 0) - (a.question_count || 0))
      } else if (this.sortBy === 'created_at') {
        return categories.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      }
      
      return categories
    }
  },
  onLoad() {
    this.loadCategories()
    this.loadStats()
  },
  onPullDownRefresh() {
    Promise.all([
      this.loadCategories(),
      this.loadStats()
    ]).finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  methods: {
    // 加载分类列表
    async loadCategories() {
      try {
        this.showLoading('加载中...')
        
        const params = {
          search: this.searchKeyword
        }
        
        const res = await categoryApi.getCategories(params)
        if (res.code === 200) {
          this.categories = res.data || []
        }
      } catch (error) {
        console.error('加载分类列表失败:', error)
        this.showToast('加载失败，请重试')
      } finally {
        this.hideLoading()
      }
    },
    
    // 加载统计数据
    async loadStats() {
      try {
        const res = await categoryApi.getCategoryStats()
        if (res.code === 200) {
          this.totalQuestions = res.data.total_questions || 0
          this.totalAnswers = res.data.total_answers || 0
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    },
    
    // 搜索分类
    searchCategories() {
      this.loadCategories()
    },
    
    // 清除搜索
    clearSearch() {
      this.searchKeyword = ''
      this.loadCategories()
    },
    
    // 设置排序方式
    setSortBy(sortBy) {
      this.sortBy = sortBy
    },
    
    // 查看分类详情
    viewCategory(category) {
      uni.navigateTo({
        url: `/pages/categories/detail?id=${category.id}`
      })
    },
    
    // 编辑分类
    editCategory(category) {
      this.editingCategory = category
      this.categoryForm = {
        name: category.name,
        description: category.description || '',
        color: category.color || '#3cc51f'
      }
      this.showAddModal = true
    },
    
    // 确认删除
    confirmDelete(category) {
      this.deletingCategory = category
      this.showDeleteModal = true
    },
    
    // 删除分类
    async deleteCategory() {
      try {
        this.showLoading('删除中...')
        
        const res = await categoryApi.deleteCategory(this.deletingCategory.id)
        if (res.code === 200) {
          this.showToast('删除成功')
          this.loadCategories()
          this.loadStats()
        }
      } catch (error) {
        console.error('删除分类失败:', error)
        this.showToast('删除失败，请重试')
      } finally {
        this.hideLoading()
        this.deletingCategory = null
      }
    },
    
    // 关闭弹窗
    closeModal() {
      this.showAddModal = false
      this.editingCategory = null
      this.categoryForm = {
        name: '',
        description: '',
        color: '#3cc51f'
      }
    },
    
    // 提交分类
    async submitCategory() {
      try {
        // 表单验证
        await this.$refs.categoryForm.validate()
        
        this.showLoading(this.editingCategory ? '更新中...' : '创建中...')
        
        let res
        if (this.editingCategory) {
          // 更新分类
          res = await categoryApi.updateCategory(this.editingCategory.id, this.categoryForm)
        } else {
          // 创建分类
          res = await categoryApi.createCategory(this.categoryForm)
        }
        
        if (res.code === 200) {
          this.showToast(this.editingCategory ? '更新成功' : '创建成功')
          this.closeModal()
          this.loadCategories()
        }
      } catch (error) {
        console.error('提交分类失败:', error)
        this.showToast('操作失败，请重试')
      } finally {
        this.hideLoading()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding-bottom: 120rpx;
}

.search-section {
  background-color: #fff;
  padding: 20rpx 30rpx;
  margin-bottom: 20rpx;
}

.stats-section {
  background-color: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-between;
  
  .stat-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .stat-number {
      font-size: 48rpx;
      font-weight: bold;
      color: #3cc51f;
      margin-bottom: 10rpx;
    }
    
    .stat-label {
      font-size: 24rpx;
      color: #999;
    }
  }
}

.categories-section {
  background-color: #fff;
  padding: 30rpx;
  
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
    
    .sort-actions {
      display: flex;
      
      .sort-item {
        font-size: 26rpx;
        color: #666;
        margin-left: 30rpx;
        
        &.active {
          color: #3cc51f;
          font-weight: bold;
        }
      }
    }
  }
  
  .category-list {
    .category-item {
      background-color: #fff;
      border-radius: 16rpx;
      padding: 30rpx;
      margin-bottom: 20rpx;
      box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
      
      .category-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20rpx;
        
        .category-info {
          display: flex;
          align-items: center;
          flex: 1;
          
          .category-icon {
            width: 80rpx;
            height: 80rpx;
            border-radius: 16rpx;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 20rpx;
            
            .icon-text {
              font-size: 36rpx;
              font-weight: bold;
              color: #fff;
            }
          }
          
          .category-details {
            flex: 1;
            
            .category-name {
              font-size: 32rpx;
              font-weight: bold;
              color: #333;
              display: block;
              margin-bottom: 10rpx;
            }
            
            .category-desc {
              font-size: 26rpx;
              color: #666;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
              overflow: hidden;
            }
          }
        }
      }
      
      .category-stats {
        display: flex;
        margin-bottom: 20rpx;
        
        .stat-item {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          
          .stat-value {
            font-size: 36rpx;
            font-weight: bold;
            color: #3cc51f;
            margin-bottom: 8rpx;
          }
          
          .stat-name {
            font-size: 24rpx;
            color: #999;
          }
        }
      }
      
      .category-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .create-time {
          font-size: 24rpx;
          color: #999;
        }
        
        .action-buttons {
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

.add-category-btn {
  position: fixed;
  bottom: 40rpx;
  right: 40rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background-color: #3cc51f;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(60, 197, 31, 0.3);
}

.category-modal {
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
    
    .color-picker {
      display: flex;
      flex-wrap: wrap;
      margin-top: 20rpx;
      
      .color-item {
        width: 60rpx;
        height: 60rpx;
        border-radius: 12rpx;
        margin-right: 20rpx;
        margin-bottom: 20rpx;
        position: relative;
        
        &.active {
          &::after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-size: 32rpx;
            font-weight: bold;
          }
        }
      }
    }
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