<template>
  <view class="container">
    <view class="list-container">
      <view class="category-item" v-for="(item, index) in list" :key="index">
        <view class="item-left">
          <view class="color-dot" :style="{ backgroundColor: item.color || '#2979ff' }"></view>
          <text class="name">{{ item.name }}</text>
        </view>
        <view class="item-right">
          <u-icon name="edit-pen" size="20" color="#909399" @click.stop="handleEdit(item)"></u-icon>
          <view class="delete-icon" @click.stop="handleDelete(item)">
             <u-icon name="trash" size="20" color="#fa3534"></u-icon>
          </view>
        </view>
      </view>
    </view>
    
    <view class="add-btn" @click="showAdd = true">
      <u-icon name="plus" color="#fff" size="30"></u-icon>
    </view>
    
    <u-modal :show="showAdd" :title="isEdit ? '编辑学科' : '新增学科'" showCancelButton @confirm="confirmAdd" @cancel="closeModal">
      <view class="modal-content">
        <u--form labelPosition="left" :model="form" :rules="rules" ref="uForm">
           <u-form-item label="名称" prop="name" borderBottom>
             <u--input v-model="form.name" placeholder="请输入学科名称" border="none"></u--input>
           </u-form-item>
           <u-form-item label="颜色" prop="color" borderBottom>
             <view class="color-picker">
                <view 
                  class="color-item" 
                  v-for="color in colors" 
                  :key="color" 
                  :style="{ backgroundColor: color }"
                  :class="{ active: form.color === color }"
                  @click="form.color = color"
                ></view>
             </view>
           </u-form-item>
        </u--form>
      </view>
    </u-modal>
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      list: [],
      showAdd: false,
      isEdit: false,
      form: {
        id: null,
        name: '',
        color: '#2979ff'
      },
      colors: ['#2979ff', '#19be6b', '#ff9900', '#fa3534', '#909399', '#3c9cff', '#5ac725', '#f56c6c'],
      rules: {
        name: [
          { required: true, message: '请输入学科名称', trigger: ['blur', 'change'] }
        ]
      }
    };
  },
  onShow() {
    this.getList();
  },
  methods: {
    async getList() {
      try {
        const res = await request({
          url: 'questions/subjects/',
          method: 'GET'
        });
        this.list = res.results;
      } catch (e) {
        console.error(e);
      }
    },
    handleEdit(item) {
      this.isEdit = true;
      this.form.id = item.id;
      this.form.name = item.name;
      this.form.color = item.color;
      this.showAdd = true;
    },
    handleDelete(item) {
       uni.showModal({
         title: '提示',
         content: `确定要删除学科“${item.name}”吗？`,
         success: async (res) => {
           if (res.confirm) {
             try {
               await request({
                 url: `questions/subjects/${item.id}/`,
                 method: 'DELETE'
               });
               uni.showToast({ title: '删除成功', icon: 'success' });
               this.getList();
             } catch (e) {
               console.error(e);
             }
           }
         }
       });
    },
    closeModal() {
      this.showAdd = false;
      this.isEdit = false;
      this.form = {
        id: null,
        name: '',
        color: '#2979ff'
      };
    },
    confirmAdd() {
      this.$refs.uForm.validate().then(async () => {
        try {
          if (this.isEdit) {
            await request({
              url: `questions/subjects/${this.form.id}/`,
              method: 'PUT',
              data: {
                name: this.form.name,
                color: this.form.color
              }
            });
            uni.showToast({ title: '修改成功', icon: 'success' });
          } else {
            await request({
              url: 'questions/subjects/',
              method: 'POST',
              data: {
                name: this.form.name,
                color: this.form.color
              }
            });
            uni.showToast({ title: '添加成功', icon: 'success' });
          }
          this.closeModal();
          this.getList();
        } catch (e) {
          console.error(e);
        }
      }).catch(errors => {
         uni.showToast({ title: '请完善表单', icon: 'none' });
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #f8f8f8;
  padding: 20rpx;
  padding-bottom: 120rpx;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
  
  .item-left {
    display: flex;
    align-items: center;
    
    .color-dot {
      width: 24rpx;
      height: 24rpx;
      border-radius: 50%;
      margin-right: 20rpx;
    }
    
    .name {
      font-size: 30rpx;
      color: #333;
      font-weight: 500;
    }
  }
  
  .item-right {
     display: flex;
     align-items: center;
     
     .delete-icon {
        margin-left: 30rpx;
     }
  }
}

.add-btn {
  position: fixed;
  right: 40rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background-color: #2979ff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 20rpx rgba(41, 121, 255, 0.3);
  z-index: 99;
  
  &:active {
    transform: scale(0.95);
  }
}

.modal-content {
  padding: 20rpx 0;
  width: 100%;
  
  .color-picker {
    display: flex;
    flex-wrap: wrap;
    gap: 20rpx;
    margin-top: 10rpx;
    
    .color-item {
      width: 40rpx;
      height: 40rpx;
      border-radius: 50%;
      border: 4rpx solid transparent;
      
      &.active {
        border-color: #333;
        transform: scale(1.1);
      }
    }
  }
}
</style>
