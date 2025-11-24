<template>
  <view class="add-question-page">
    <view class="form-container">
      <!-- 题目标题 -->
      <view class="form-section">
        <view class="section-title">题目标题</view>
        <input 
          class="form-input" 
          placeholder="请输入题目标题" 
          v-model="formData.title"
          :class="{ 'error': errors.title }"
        />
        <text class="error-text" v-if="errors.title">{{ errors.title }}</text>
      </view>

      <!-- 错题分类 -->
      <view class="form-section">
        <view class="section-title">错题分类</view>
        <picker 
          mode="selector" 
          :range="categoryOptions" 
          range-key="name"
          @change="handleCategoryChange"
          :value="selectedCategoryIndex"
        >
          <view class="picker-wrapper" :class="{ 'error': errors.categoryId }">
            <text class="picker-text">{{ selectedCategory.name || '请选择分类' }}</text>
            <text class="picker-arrow">▼</text>
          </view>
        </picker>
        <text class="error-text" v-if="errors.categoryId">{{ errors.categoryId }}</text>
      </view>

      <!-- 题目内容 -->
      <view class="form-section">
        <view class="section-title">题目内容</view>
        <textarea 
          class="form-textarea" 
          placeholder="请输入题目内容" 
          v-model="formData.content"
          :class="{ 'error': errors.content }"
          maxlength="1000"
        />
        <view class="text-counter">{{ formData.content.length }}/1000</view>
        <text class="error-text" v-if="errors.content">{{ errors.content }}</text>
      </view>

      <!-- 题目图片 -->
      <view class="form-section">
        <view class="section-title">题目图片</view>
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
              <text class="image-add-text">添加图片</text>
            </view>
          </view>
          <text class="upload-tip">最多可上传3张图片</text>
        </view>
      </view>

      <!-- 题目答案 -->
      <view class="form-section">
        <view class="section-title">题目答案</view>
        <textarea 
          class="form-textarea" 
          placeholder="请输入题目答案" 
          v-model="formData.answer"
          :class="{ 'error': errors.answer }"
          maxlength="1000"
        />
        <view class="text-counter">{{ formData.answer.length }}/1000</view>
        <text class="error-text" v-if="errors.answer">{{ errors.answer }}</text>
      </view>

      <!-- 解题思路 -->
      <view class="form-section">
        <view class="section-title">解题思路</view>
        <textarea 
          class="form-textarea" 
          placeholder="请输入解题思路" 
          v-model="formData.solution"
          :class="{ 'error': errors.solution }"
          maxlength="1000"
        />
        <view class="text-counter">{{ formData.solution.length }}/1000</view>
        <text class="error-text" v-if="errors.solution">{{ errors.solution }}</text>
      </view>

      <!-- 难度等级 -->
      <view class="form-section">
        <view class="section-title">难度等级</view>
        <view class="difficulty-selector">
          <view 
            class="difficulty-item" 
            v-for="(item, index) in difficultyOptions" 
            :key="item.id"
            :class="{ 'active': formData.difficulty === item.id }"
            @click="selectDifficulty(item.id)"
          >
            <text class="difficulty-text">{{ item.name }}</text>
          </view>
        </view>
      </view>

      <!-- 标签 -->
      <view class="form-section">
        <view class="section-title">标签</view>
        <view class="tag-input-wrapper">
          <input 
            class="tag-input" 
            placeholder="输入标签后按回车添加" 
            v-model="tagInput"
            @confirm="addTag"
          />
          <button class="tag-add-btn" @click="addTag">添加</button>
        </view>
        <view class="tag-list">
          <view 
            class="tag-item" 
            v-for="(tag, index) in formData.tags" 
            :key="index"
          >
            <text class="tag-text">{{ tag }}</text>
            <text class="tag-delete" @click="deleteTag(index)">×</text>
          </view>
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="form-section">
        <button class="submit-btn" @click="handleSubmit" :disabled="isLoading">
          {{ isLoading ? '提交中...' : '提交' }}
        </button>
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
        title: '',
        categoryId: '',
        content: '',
        images: [],
        answer: '',
        solution: '',
        difficulty: 2, // 默认中等难度
        tags: []
      },
      errors: {
        title: '',
        categoryId: '',
        content: '',
        answer: '',
        solution: ''
      },
      categoryOptions: [],
      selectedCategory: {},
      selectedCategoryIndex: 0,
      difficultyOptions: [
        { id: 1, name: '简单' },
        { id: 2, name: '中等' },
        { id: 3, name: '困难' }
      ],
      tagInput: '',
      isLoading: false
    }
  },
  onLoad() {
    this.loadCategories();
  },
  methods: {
    ...mapActions('questions', ['addQuestion', 'uploadQuestionImage']),
    ...mapActions('categories', ['getCategoryList']),
    
    // 加载分类列表
    async loadCategories() {
      try {
        await this.getCategoryList();
        // 更新分类选项
        this.categoryOptions = this.categories.map(item => ({
          id: item.id,
          name: item.name
        }));
      } catch (error) {
        console.error('加载分类列表失败:', error);
        uni.showToast({
          title: '加载分类失败',
          icon: 'none'
        });
      }
    },
    
    // 处理分类变化
    handleCategoryChange(e) {
      this.selectedCategoryIndex = e.detail.value;
      this.selectedCategory = this.categoryOptions[this.selectedCategoryIndex];
      this.formData.categoryId = this.selectedCategory.id;
    },
    
    // 选择难度
    selectDifficulty(id) {
      this.formData.difficulty = id;
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
          const result = await this.uploadQuestionImage(filePath);
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
    
    // 添加标签
    addTag() {
      if (!this.tagInput.trim()) {
        return;
      }
      
      if (this.formData.tags.length >= 5) {
        uni.showToast({
          title: '最多添加5个标签',
          icon: 'none'
        });
        return;
      }
      
      if (this.formData.tags.includes(this.tagInput.trim())) {
        uni.showToast({
          title: '标签已存在',
          icon: 'none'
        });
        return;
      }
      
      this.formData.tags.push(this.tagInput.trim());
      this.tagInput = '';
    },
    
    // 删除标签
    deleteTag(index) {
      this.formData.tags.splice(index, 1);
    },
    
    // 表单验证
    validateForm() {
      let isValid = true;
      this.errors = {
        title: '',
        categoryId: '',
        content: '',
        answer: '',
        solution: ''
      };
      
      if (!this.formData.title.trim()) {
        this.errors.title = '请输入题目标题';
        isValid = false;
      }
      
      if (!this.formData.categoryId) {
        this.errors.categoryId = '请选择错题分类';
        isValid = false;
      }
      
      if (!this.formData.content.trim()) {
        this.errors.content = '请输入题目内容';
        isValid = false;
      }
      
      if (!this.formData.answer.trim()) {
        this.errors.answer = '请输入题目答案';
        isValid = false;
      }
      
      if (!this.formData.solution.trim()) {
        this.errors.solution = '请输入解题思路';
        isValid = false;
      }
      
      return isValid;
    },
    
    // 处理提交
    async handleSubmit() {
      if (!this.validateForm()) {
        return;
      }
      
      this.isLoading = true;
      
      try {
        await this.addQuestion(this.formData);
        
        uni.showToast({
          title: '添加成功',
          icon: 'success'
        });
        
        // 添加成功后返回列表页
        setTimeout(() => {
          uni.navigateBack();
        }, 1500);
      } catch (error) {
        console.error('添加错题失败:', error);
        uni.showToast({
          title: error.message || '添加失败，请重试',
          icon: 'none'
        });
      } finally {
        this.isLoading = false;
      }
    }
  }
}
</script>

<style>
.add-question-page {
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

.form-input:focus {
  border-color: #3c9cff;
}

.picker-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 80rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx;
  padding: 0 20rpx;
  box-sizing: border-box;
}

.picker-wrapper.error {
  border-color: #f56c6c;
}

.picker-text {
  font-size: 28rpx;
  color: #333;
}

.picker-arrow {
  font-size: 20rpx;
  color: #999;
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

/* 难度选择 */
.difficulty-selector {
  display: flex;
  margin-top: 20rpx;
}

.difficulty-item {
  flex: 1;
  height: 80rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #e5e5ea;
  margin-right: 20rpx;
  border-radius: 8rpx;
}

.difficulty-item:last-child {
  margin-right: 0;
}

.difficulty-item.active {
  background-color: #3c9cff;
  border-color: #3c9cff;
}

.difficulty-item.active .difficulty-text {
  color: white;
}

.difficulty-text {
  font-size: 28rpx;
  color: #333;
}

/* 标签 */
.tag-input-wrapper {
  display: flex;
  margin-top: 20rpx;
}

.tag-input {
  flex: 1;
  height: 70rpx;
  border: 1px solid #e5e5ea;
  border-radius: 8rpx 0 0 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.tag-add-btn {
  width: 120rpx;
  height: 70rpx;
  background-color: #3c9cff;
  color: white;
  border: none;
  border-radius: 0 8rpx 8rpx 0;
  font-size: 28rpx;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.tag-item {
  display: flex;
  align-items: center;
  background-color: #f0f0f0;
  padding: 10rpx 20rpx;
  border-radius: 30rpx;
  margin-right: 20rpx;
  margin-bottom: 20rpx;
}

.tag-text {
  font-size: 24rpx;
  color: #333;
  margin-right: 10rpx;
}

.tag-delete {
  font-size: 24rpx;
  color: #999;
}

/* 提交按钮 */
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
</style>