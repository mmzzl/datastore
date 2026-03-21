<template>
  <view class="container">
    <view class="search-bar">
      <u-search placeholder="搜索错题" v-model="keyword" @search="search" @custom="search"></u-search>
    </view>
    
    <view class="filter-bar">
      <view class="filter-item" @click="showSubject = true">
        <text>{{ currentSubject ? currentSubject.name : '全部学科' }}</text>
        <u-icon name="arrow-down" size="12"></u-icon>
      </view>
      <view class="filter-item" @click="showSort = true">
        <text>{{ currentSort ? currentSort.name : '默认排序' }}</text>
        <u-icon name="arrow-down" size="12"></u-icon>
      </view>
    </view>
    
    <scroll-view scroll-y class="list-container" @scrolltolower="loadMore">
      <view class="question-item" v-for="(item, index) in list" :key="index" @click="toDetail(item.id)">
        <view class="item-header">
          <u-tag :text="getSubjectName(item.subject)" :bgColor="getSubjectColor(item.subject)" borderColor="transparent" size="mini"></u-tag>
          <text class="time">{{ formatTime(item.created_at) }}</text>
        </view>
        <view class="item-title">{{ item.title }}</view>
        <view class="item-footer">
          <view class="difficulty">
            <u-rate :count="5" :value="item.difficulty" readonly size="14"></u-rate>
          </view>
          <view class="status">
            <text v-if="item.is_solved" class="solved">已解决</text>
            <text v-else class="unsolved">未解决</text>
          </view>
        </view>
      </view>
      <u-loadmore :status="status" />
    </scroll-view>
    
    <u-action-sheet :actions="subjectList" :show="showSubject" title="选择学科" @select="subjectSelect" @close="showSubject = false"></u-action-sheet>
    <u-action-sheet :actions="sortList" :show="showSort" title="排序方式" @select="sortSelect" @close="showSort = false"></u-action-sheet>
    
    <view class="add-btn" @click="toAdd">
      <u-icon name="plus" color="#fff" size="30"></u-icon>
    </view>
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      keyword: '',
      list: [],
      page: 1,
      status: 'loadmore',
      showSubject: false,
      subjectList: [{name: '全部学科', id: ''}],
      currentSubject: null,
      showSort: false,
      sortList: [
        {name: '默认排序', value: ''},
        {name: '最新添加', value: '-created_at'},
        {name: '最早添加', value: 'created_at'},
        {name: '难度降序', value: '-difficulty'},
        {name: '难度升序', value: 'difficulty'}
      ],
      currentSort: null
    };
  },
  onShow() {
    this.page = 1;
    this.list = [];
    this.getList();
    this.getSubjects();
  },
  methods: {
    async getSubjects() {
      try {
        const res = await request({
          url: 'questions/subjects/',
          method: 'GET'
        });
        const subjects = res.results.map(item => ({
          name: item.name,
          id: item.id,
          color: item.color
        }));
        this.subjectList = [{name: '全部学科', id: ''}, ...subjects];
      } catch (e) {
        console.error(e);
      }
    },
    async getList() {
      this.status = 'loading';
      try {
        const params = {
          page: this.page,
          search: this.keyword,
          subject: this.currentSubject ? this.currentSubject.id : '',
          ordering: this.currentSort ? this.currentSort.value : ''
        };
        
        const res = await request({
          url: 'questions/questions/',
          method: 'GET',
          data: params
        });
        
        if (res.results.length > 0) {
          this.list = this.list.concat(res.results);
          if (res.next) {
            this.status = 'loadmore';
          } else {
            this.status = 'nomore';
          }
        } else {
          this.status = 'nomore';
        }
      } catch (e) {
        console.error(e);
        this.status = 'loadmore';
      }
    },
    loadMore() {
      if (this.status === 'nomore') return;
      this.page++;
      this.getList();
    },
    search() {
      this.page = 1;
      this.list = [];
      this.getList();
    },
    subjectSelect(e) {
      this.currentSubject = e.id === '' ? null : e;
      this.showSubject = false;
      this.search();
    },
    sortSelect(e) {
      this.currentSort = e.value === '' ? null : e;
      this.showSort = false;
      this.search();
    },
    toDetail(id) {
      uni.navigateTo({
        url: `/pages/question/detail?id=${id}`
      });
    },
    toAdd() {
      uni.navigateTo({
        url: '/pages/question/add'
      });
    },
    formatTime(time) {
        if(!time) return '';
        const date = new Date(time);
        return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
    },
    getSubjectName(subject) {
      if (!subject) return '未分类';
      if (typeof subject === 'object') return subject.name;
      const found = this.subjectList.find(s => s.id === subject);
      return found ? found.name : '未知学科';
    },
    getSubjectColor(subject) {
      if (!subject) return '#999';
      if (typeof subject === 'object') return subject.color || '#2979ff';
      const found = this.subjectList.find(s => s.id === subject);
      return found ? found.color : '#2979ff';
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f8f8;
}

.search-bar {
  padding: 20rpx;
  background-color: #fff;
}

.filter-bar {
  display: flex;
  background-color: #fff;
  padding: 20rpx 0;
  border-top: 1rpx solid #f0f0f0;
  border-bottom: 1rpx solid #f0f0f0;
  
  .filter-item {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 28rpx;
    color: #666;
    
    text {
      margin-right: 10rpx;
    }
  }
}

.list-container {
  flex: 1;
  padding: 20rpx;
  box-sizing: border-box;
}

.question-item {
  background-color: #fff;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    
    .time {
      font-size: 24rpx;
      color: #999;
    }
  }
  
  .item-title {
    font-size: 32rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 20rpx;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }
  
  .item-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .status {
      font-size: 24rpx;
      
      .solved {
        color: #19be6b;
      }
      
      .unsolved {
        color: #ff9900;
      }
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
}
</style>
