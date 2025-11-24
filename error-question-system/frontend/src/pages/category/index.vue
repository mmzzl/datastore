<template>
  <view class="category-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <u-search
        v-model="searchKeyword"
        placeholder="搜索错题分类"
        :show-action="false"
        @search="handleSearch"
        @clear="handleClearSearch"
      ></u-search>
    </view>

    <!-- 分类列表 -->
    <view class="category-list">
      <!-- 加载状态 -->
      <view class="loading-container" v-if="isLoading">
        <u-loading-icon mode="flower" size="40"></u-loading-icon>
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view class="empty-container" v-else-if="filteredCategories.length === 0">
        <u-empty
          mode="data"
          icon="http://cdn.uviewui.com/uview/empty/data.png"
          text="暂无分类数据"
        ></u-empty>
      </view>

      <!-- 分类项 -->
      <view class="category-item" v-for="category in filteredCategories" :key="category.id">
        <view class="category-info" @click="goToQuestionList(category)">
          <view class="category-icon">
            <text class="icon-text">{{ category.name.charAt(0) }}</text>
          </view>
          <view class="category-details">
            <view class="category-name">{{ category.name }}</view>
            <view class="category-desc" v-if="category.description">{{ category.description }}</view>
            <view class="category-stats">
              <text class="stats-item">{{ category.questionCount || 0 }} 道错题</text>
            </view>
          </view>
        </view>
        <view class="category-actions">
          <button class="action-btn edit-btn" @click="editCategory(category)">编辑</button>
          <button class="action-btn delete-btn" @click="confirmDelete(category)">删除</button>
        </view>
      </view>
    </view>

    <!-- 添加按钮 -->
    <view class="add-btn" @click="showAddModal = true">
      <text class="add-icon">+</text>
    </view>

    <!-- 添加/编辑分类弹窗 -->
    <u-popup
      :show="showAddModal || showEditModal"
      mode="center"
      round="10"
      closeOnClickOverlay
      @close="closeModal"
    >
      <view class="modal-content">
        <view class="modal-title">{{ isEditing ? '编辑分类' : '添加分类' }}</view>
        <view class="form-item">
          <view class="form-label">分类名称</view>
          <input
            class="form-input"
            v-model="categoryForm.name"
            placeholder="请输入分类名称"
            :class="{ 'error': errors.name }"
          />
          <text class="error-text" v-if="errors.name">{{ errors.name }}</text>
        </view>
        <view class="form-item">
          <view class="form-label">分类描述</view>
          <textarea
            class="form-textarea"
            v-model="categoryForm.description"
            placeholder="请输入分类描述（选填）"
            maxlength="200"
          />
          <view class="text-counter">{{ categoryForm.description.length }}/200</view>
        </view>
        <view class="form-item">
          <view class="form-label">图标颜色</view>
          <view class="color-picker">
            <view
              class="color-item"
              v-for="color in colorOptions"
              :key="color"
              :style="{ backgroundColor: color }"
              :class="{ 'active': categoryForm.color === color }"
              @click="selectColor(color)"
            ></view>
          </view>
        </view>
        <view class="modal-actions">
          <button class="modal-btn cancel-btn" @click="closeModal">取消</button>
          <button class="modal-btn confirm-btn" @click="handleSubmit" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '确定' }}
          </button>
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
      isLoading: true,
      showAddModal: false,
      showEditModal: false,
      isEditing: false,
      isSubmitting: false,
      categoryForm: {
        id: '',
        name: '',
        description: '',
        color: '#3c9cff'
      },
      errors: {
        name: ''
      },
      colorOptions: [
        '#3c9cff', '#5ac725', '#f9ae3d', '#f56c6c', 
        '#909399', '#722ed1', '#13c2c2', '#eb2f96'
      ]
    }
  },
  computed: {
    ...mapGetters('categories', ['categories']),
    filteredCategories() {
      if (!this.searchKeyword) {
        return this.categories;
      }
      return this.categories.filter(category => 
        category.name.toLowerCase().includes(this.searchKeyword.toLowerCase()) ||
        (category.description && category.description.toLowerCase().includes(this.searchKeyword.toLowerCase()))
      );
    }
  },
  onLoad() {
    this.loadCategories();
  },
  onPullDownRefresh() {
    this.loadCategories().then(() => {
      uni.stopPullDownRefresh();
    });
  },
  methods: {
    ...mapActions('categories', ['getCategoryList', 'addCategory', 'updateCategory', 'deleteCategory']),
    
    // 加载分类列表
    async loadCategories() {
      this.isLoading = true;
      try {
        await this.getCategoryList();
      } catch (error) {
        console.error('加载分类列表失败:', error);
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
    
    // 跳转到错题列表
    goToQuestionList(category) {
      uni.navigateTo({
        url: `/pages/questions/list?categoryId=${category.id}&categoryName=${category.name}`
      });
    },
    
    // 编辑分类
    editCategory(category) {
      this.isEditing = true;
      this.categoryForm = {
        id: category.id,
        name: category.name,
        description: category.description || '',
        color: category.color || '#3c9cff'
      };
      this.showEditModal = true;
    },
    
    // 确认删除
    confirmDelete(category) {
      uni.showModal({
        title: '提示',
        content: `确定要删除"${category.name}"分类吗？删除后该分类下的错题将移至"未分类"。`,
        success: (res) => {
          if (res.confirm) {
            this.handleDelete(category.id);
          }
        }
      });
    },
    
    // 执行删除
    async handleDelete(categoryId) {
      try {
        await this.deleteCategory(categoryId);
        uni.showToast({
          title: '删除成功',
          icon: 'success'
        });
      } catch (error) {
        console.error('删除分类失败:', error);
        uni.showToast({
          title: error.message || '删除失败，请重试',
          icon: 'none'
        });
      }
    },
    
    // 选择颜色
    selectColor(color) {
      this.categoryForm.color = color;
    },
    
    // 关闭弹窗
    closeModal() {
      this.showAddModal = false;
      this.showEditModal = false;
      this.isEditing = false;
      this.resetForm();
    },
    
    // 重置表单
    resetForm() {
      this.categoryForm = {
        id: '',
        name: '',
        description: '',
        color: '#3c9cff'
      };
      this.errors = {
        name: ''
      };
    },
    
    // 表单验证
    validateForm() {
      let isValid = true;
      this.errors = {
        name: ''
      };
      
      if (!this.categoryForm.name.trim()) {
        this.errors.name = '请输入分类名称';
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
        if (this.isEditing) {
          // 编辑分类
          await this.updateCategory(this.categoryForm);
          uni.showToast({
            title: '修改成功',
            icon: 'success'
          });
        } else {
          // 添加分类
          await this.addCategory(this.categoryForm);
          uni.showToast({
            title: '添加成功',
            icon: 'success'
          });
        }
        
        this.closeModal();
      } catch (error) {
        console.error('提交分类失败:', error);
        uni.showToast({
          title: error.message || '操作失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isSubmitting = false;
      }
    }
  }
}
</script>

<style>
.category-page {
  background-color: #f8f8f8;
  min-height: 100vh;
  padding-bottom: 40rpx;
}

.search-bar {
  padding: 20rpx 30rpx;
  background-color: white;
}

.category-list {
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

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.category-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.category-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background-color: #3c9cff;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 30rpx;
}

.icon-text {
  font-size: 40rpx;
  font-weight: bold;
  color: white;
}

.category-details {
  flex: 1;
}

.category-name {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.category-desc {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 10rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.category-stats {
  font-size: 24rpx;
  color: #999;
}

.stats-item {
  margin-right: 20rpx;
}

.category-actions {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.action-btn {
  padding: 10rpx 20rpx;
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

.add-btn {
  position: fixed;
  bottom: 40rpx;
  right: 30rpx;
  width: 120rpx;
  height: 120rpx;
  background-color: #3c9cff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(60, 156, 255, 0.4);
}

.add-icon {
  font-size: 60rpx;
  color: white;
  font-weight: bold;
}

/* 弹窗样式 */
.modal-content {
  width: 600rpx;
  padding: 40rpx;
}

.modal-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  text-align: center;
  margin-bottom: 40rpx;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 20rpx;
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

.form-input.error {
  border-color: #f56c6c;
}

.form-textarea {
  width: 100%;
  height: 150rpx;
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

.error-text {
  color: #f56c6c;
  font-size: 24rpx;
  margin-top: 8rpx;
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.color-item {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  border: 4rpx solid transparent;
}

.color-item.active {
  border-color: #333;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
}

.modal-btn {
  width: 240rpx;
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

.confirm-btn:disabled {
  background-color: #a0cfff;
}
</style>