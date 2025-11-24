<template>
  <view class="container" v-if="answerDetail">
    <!-- 题目信息 -->
    <view class="question-section">
      <view class="question-header">
        <text class="question-title">{{ answerDetail.question.title }}</text>
        <view class="question-meta">
          <text class="subject-tag" :style="{ backgroundColor: getSubjectColor(answerDetail.question.subject) }">
            {{ getSubjectName(answerDetail.question.subject) }}
          </text>
          <text class="difficulty-tag" :style="{ color: getDifficultyColor(answerDetail.question.difficulty) }">
            {{ getDifficultyName(answerDetail.question.difficulty) }}
          </text>
        </view>
      </view>
      <view class="question-content">
        <text class="question-text">{{ answerDetail.question.content }}</text>
        <view class="question-images" v-if="answerDetail.question.images && answerDetail.question.images.length > 0">
          <image 
            v-for="(img, index) in answerDetail.question.images" 
            :key="index"
            :src="img.url" 
            mode="widthFix"
            @click="previewImage(answerDetail.question.images, index)"
          ></image>
        </view>
      </view>
    </view>

    <!-- 解答内容 -->
    <view class="answer-section">
      <view class="answer-header">
        <view class="user-info">
          <image :src="answerDetail.user.avatar || '/static/images/default-avatar.png'" mode="aspectFill"></image>
          <view class="user-details">
            <text class="username">{{ answerDetail.user.username }}</text>
            <text class="date">{{ formatDate(answerDetail.created_at) }}</text>
          </view>
        </view>
        <view class="answer-rating" v-if="answerDetail.rating">
          <u-rate 
            v-model="answerDetail.rating" 
            :count="5" 
            :active-color="'#faad14'"
            :inactive-color="'#c8c9cc'"
            size="24"
            readonly
          ></u-rate>
        </view>
      </view>
      <view class="answer-content">
        <text class="answer-text">{{ answerDetail.content }}</text>
        <view class="answer-images" v-if="answerDetail.images && answerDetail.images.length > 0">
          <image 
            v-for="(img, index) in answerDetail.images" 
            :key="index"
            :src="img.url" 
            mode="widthFix"
            @click="previewImage(answerDetail.images, index)"
          ></image>
        </view>
      </view>
      <view class="answer-actions">
        <view class="action-item" @click="likeAnswer">
          <u-icon name="thumb-up" :color="answerDetail.is_liked ? '#3cc51f' : '#999'" size="32"></u-icon>
          <text>{{ answerDetail.like_count || 0 }}</text>
        </view>
        <view class="action-item" @click="showCommentModal = true">
          <u-icon name="chat" color="#999" size="32"></u-icon>
          <text>{{ answerDetail.comment_count || 0 }}</text>
        </view>
        <view class="action-item" @click="shareAnswer">
          <u-icon name="share" color="#999" size="32"></u-icon>
          <text>分享</text>
        </view>
        <view class="action-item" @click="showRateModal = true">
          <u-icon name="star" color="#999" size="32"></u-icon>
          <text>评分</text>
        </view>
      </view>
    </view>

    <!-- 评论列表 -->
    <view class="comments-section">
      <view class="section-header">
        <text class="section-title">评论 ({{ comments.length }})</text>
        <view class="sort-actions">
          <text 
            class="sort-item" 
            :class="{ active: commentSort === 'created_at' }"
            @click="setCommentSort('created_at')"
          >
            最新
          </text>
          <text 
            class="sort-item" 
            :class="{ active: commentSort === 'like_count' }"
            @click="setCommentSort('like_count')"
          >
            最热
          </text>
        </view>
      </view>
      
      <!-- 评论列表 -->
      <view class="comment-list" v-if="sortedComments.length > 0">
        <view 
          class="comment-item" 
          v-for="comment in sortedComments" 
          :key="comment.id"
        >
          <view class="comment-header">
            <image :src="comment.user.avatar || '/static/images/default-avatar.png'" mode="aspectFill"></image>
            <view class="comment-info">
              <text class="username">{{ comment.user.username }}</text>
              <text class="date">{{ formatDate(comment.created_at) }}</text>
            </view>
            <view class="comment-like" @click="likeComment(comment)">
              <u-icon name="thumb-up" :color="comment.is_liked ? '#3cc51f' : '#999'" size="24"></u-icon>
              <text>{{ comment.like_count || 0 }}</text>
            </view>
          </view>
          <text class="comment-content">{{ comment.content }}</text>
          <view class="comment-actions">
            <text class="reply-btn" @click="replyComment(comment)">回复</text>
          </view>
          
          <!-- 回复列表 -->
          <view class="reply-list" v-if="comment.replies && comment.replies.length > 0">
            <view 
              class="reply-item" 
              v-for="reply in comment.replies" 
              :key="reply.id"
            >
              <view class="reply-header">
                <image :src="reply.user.avatar || '/static/images/default-avatar.png'" mode="aspectFill"></image>
                <view class="reply-info">
                  <text class="username">{{ reply.user.username }}</text>
                  <text class="date">{{ formatDate(reply.created_at) }}</text>
                </view>
              </view>
              <text class="reply-content">
                <text class="reply-to">回复@{{ reply.reply_to_user.username }}：</text>
                {{ reply.content }}
              </text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-else>
        <image src="/static/images/empty-comment.png" mode="aspectFit"></image>
        <text class="empty-text">暂无评论</text>
      </view>
    </view>

    <!-- 添加评论按钮 -->
    <view class="add-comment-btn" @click="showCommentModal = true">
      <u-icon name="edit" color="#fff" size="32"></u-icon>
      <text>添加评论</text>
    </view>

    <!-- 评论弹窗 -->
    <u-popup v-model="showCommentModal" mode="bottom" border-radius="20">
      <view class="comment-modal">
        <view class="modal-header">
          <text class="modal-title">{{ replyTo ? '回复评论' : '添加评论' }}</text>
          <u-icon name="close" @click="closeCommentModal"></u-icon>
        </view>
        <view class="modal-content">
          <view class="reply-info" v-if="replyTo">
            <text>回复 @{{ replyTo.user.username }}：</text>
          </view>
          <u-textarea 
            v-model="commentContent" 
            placeholder="请输入评论内容"
            :maxlength="200"
            count
            height="150"
          ></u-textarea>
        </view>
        <view class="modal-footer">
          <button class="cancel-btn" @click="closeCommentModal">取消</button>
          <button class="submit-btn" @click="submitComment">提交</button>
        </view>
      </view>
    </u-popup>

    <!-- 评分弹窗 -->
    <u-popup v-model="showRateModal" mode="center" width="600" border-radius="20">
      <view class="rate-modal">
        <view class="modal-header">
          <text class="modal-title">评分</text>
        </view>
        <view class="modal-content">
          <u-rate 
            v-model="ratingValue" 
            :count="5" 
            :active-color="'#faad14'"
            :inactive-color="'#c8c9cc'"
            size="40"
          ></u-rate>
        </view>
        <view class="modal-footer">
          <button class="cancel-btn" @click="showRateModal = false">取消</button>
          <button class="submit-btn" @click="submitRating">确定</button>
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
      // 解答ID
      answerId: null,
      
      // 解答详情
      answerDetail: null,
      
      // 评论列表
      comments: [],
      
      // 评论排序
      commentSort: 'created_at',
      
      // 评论弹窗
      showCommentModal: false,
      commentContent: '',
      replyTo: null,
      
      // 评分弹窗
      showRateModal: false,
      ratingValue: 0,
      
      // 学科列表
      subjects: []
    }
  },
  computed: {
    // 排序后的评论列表
    sortedComments() {
      const comments = [...this.comments]
      
      if (this.commentSort === 'created_at') {
        return comments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      } else if (this.commentSort === 'like_count') {
        return comments.sort((a, b) => (b.like_count || 0) - (a.like_count || 0))
      }
      
      return comments
    }
  },
  onLoad(options) {
    if (options.id) {
      this.answerId = options.id
      this.loadAnswerDetail()
      this.loadComments()
    }
  },
  onShow() {
    // 每次显示页面时刷新数据
    if (this.answerId) {
      this.loadAnswerDetail()
      this.loadComments()
    }
  },
  onPullDownRefresh() {
    Promise.all([
      this.loadAnswerDetail(),
      this.loadComments()
    ]).finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  methods: {
    // 加载解答详情
    async loadAnswerDetail() {
      try {
        const res = await answerApi.getAnswerDetail(this.answerId)
        if (res.code === 200) {
          this.answerDetail = res.data
          this.ratingValue = this.answerDetail.rating || 0
        }
      } catch (error) {
        console.error('加载解答详情失败:', error)
        this.showToast('加载失败，请重试')
      }
    },
    
    // 加载评论列表
    async loadComments() {
      try {
        const res = await answerApi.getAnswerComments(this.answerId)
        if (res.code === 200) {
          this.comments = res.data || []
        }
      } catch (error) {
        console.error('加载评论列表失败:', error)
      }
    },
    
    // 设置评论排序
    setCommentSort(sort) {
      this.commentSort = sort
    },
    
    // 点赞解答
    async likeAnswer() {
      try {
        const res = await answerApi.likeAnswer(this.answerId)
        if (res.code === 200) {
          this.answerDetail.is_liked = !this.answerDetail.is_liked
          this.answerDetail.like_count = this.answerDetail.is_liked ? 
            (this.answerDetail.like_count || 0) + 1 : 
            Math.max((this.answerDetail.like_count || 0) - 1, 0)
        }
      } catch (error) {
        console.error('点赞失败:', error)
        this.showToast('操作失败，请重试')
      }
    },
    
    // 点赞评论
    async likeComment(comment) {
      try {
        const res = await answerApi.likeComment(comment.id)
        if (res.code === 200) {
          comment.is_liked = !comment.is_liked
          comment.like_count = comment.is_liked ? 
            (comment.like_count || 0) + 1 : 
            Math.max((comment.like_count || 0) - 1, 0)
        }
      } catch (error) {
        console.error('点赞失败:', error)
        this.showToast('操作失败，请重试')
      }
    },
    
    // 回复评论
    replyComment(comment) {
      this.replyTo = comment
      this.commentContent = ''
      this.showCommentModal = true
    },
    
    // 关闭评论弹窗
    closeCommentModal() {
      this.showCommentModal = false
      this.commentContent = ''
      this.replyTo = null
    },
    
    // 提交评论
    async submitComment() {
      if (!this.commentContent.trim()) {
        this.showToast('请输入评论内容')
        return
      }
      
      try {
        this.showLoading('提交中...')
        
        let res
        if (this.replyTo) {
          // 回复评论
          res = await answerApi.replyComment(this.replyTo.id, {
            content: this.commentContent
          })
          
          if (res.code === 200) {
            // 添加回复到评论
            if (!this.replyTo.replies) {
              this.replyTo.replies = []
            }
            this.replyTo.replies.push({
              id: res.data.id,
              content: this.commentContent,
              user: this.$store.state.userInfo,
              reply_to_user: this.replyTo.user,
              created_at: new Date().toISOString()
            })
            
            // 更新评论数
            this.replyTo.reply_count = (this.replyTo.reply_count || 0) + 1
          }
        } else {
          // 添加评论
          res = await answerApi.addComment(this.answerId, {
            content: this.commentContent
          })
          
          if (res.code === 200) {
            // 添加评论到列表
            this.comments.unshift({
              id: res.data.id,
              content: this.commentContent,
              user: this.$store.state.userInfo,
              created_at: new Date().toISOString(),
              like_count: 0,
              is_liked: false,
              replies: []
            })
            
            // 更新解答评论数
            this.answerDetail.comment_count = (this.answerDetail.comment_count || 0) + 1
          }
        }
        
        this.showToast('评论成功')
        this.closeCommentModal()
      } catch (error) {
        console.error('评论失败:', error)
        this.showToast('评论失败，请重试')
      } finally {
        this.hideLoading()
      }
    },
    
    // 提交评分
    async submitRating() {
      try {
        const res = await answerApi.rateAnswer(this.answerId, {
          rating: this.ratingValue
        })
        
        if (res.code === 200) {
          this.answerDetail.rating = this.ratingValue
          this.showToast('评分成功')
          this.showRateModal = false
        }
      } catch (error) {
        console.error('评分失败:', error)
        this.showToast('评分失败，请重试')
      }
    },
    
    // 分享解答
    shareAnswer() {
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
      const subject = this.subjects.find(item => item.id === subjectId)
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
  padding-bottom: 120rpx;
}

.question-section {
  background-color: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .question-header {
    margin-bottom: 20rpx;
    
    .question-title {
      font-size: 36rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 20rpx;
      display: block;
    }
    
    .question-meta {
      display: flex;
      
      .subject-tag {
        font-size: 24rpx;
        color: #fff;
        padding: 6rpx 12rpx;
        border-radius: 20rpx;
        margin-right: 20rpx;
      }
      
      .difficulty-tag {
        font-size: 24rpx;
        font-weight: bold;
      }
    }
  }
  
  .question-content {
    .question-text {
      font-size: 30rpx;
      color: #333;
      line-height: 1.6;
      display: block;
      margin-bottom: 20rpx;
    }
    
    .question-images {
      image {
        width: 100%;
        border-radius: 8rpx;
        margin-bottom: 10rpx;
      }
    }
  }
}

.answer-section {
  background-color: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .answer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    
    .user-info {
      display: flex;
      align-items: center;
      
      image {
        width: 80rpx;
        height: 80rpx;
        border-radius: 50%;
        margin-right: 20rpx;
      }
      
      .user-details {
        .username {
          font-size: 30rpx;
          font-weight: bold;
          color: #333;
          display: block;
          margin-bottom: 10rpx;
        }
        
        .date {
          font-size: 24rpx;
          color: #999;
        }
      }
    }
  }
  
  .answer-content {
    margin-bottom: 30rpx;
    
    .answer-text {
      font-size: 30rpx;
      color: #333;
      line-height: 1.6;
      display: block;
      margin-bottom: 20rpx;
    }
    
    .answer-images {
      image {
        width: 100%;
        border-radius: 8rpx;
        margin-bottom: 10rpx;
      }
    }
  }
  
  .answer-actions {
    display: flex;
    justify-content: space-around;
    padding-top: 20rpx;
    border-top: 1rpx solid #f0f0f0;
    
    .action-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      
      text {
        font-size: 24rpx;
        color: #999;
        margin-top: 10rpx;
      }
    }
  }
}

.comments-section {
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
  
  .comment-list {
    .comment-item {
      margin-bottom: 40rpx;
      padding-bottom: 30rpx;
      border-bottom: 1rpx solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
        margin-bottom: 0;
      }
      
      .comment-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20rpx;
        
        image {
          width: 60rpx;
          height: 60rpx;
          border-radius: 50%;
          margin-right: 20rpx;
        }
        
        .comment-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          
          .username {
            font-size: 28rpx;
            color: #333;
            font-weight: bold;
            margin-bottom: 8rpx;
          }
          
          .date {
            font-size: 24rpx;
            color: #999;
          }
        }
        
        .comment-like {
          display: flex;
          align-items: center;
          
          text {
            font-size: 24rpx;
            color: #999;
            margin-left: 10rpx;
          }
        }
      }
      
      .comment-content {
        font-size: 28rpx;
        color: #333;
        line-height: 1.6;
        margin-bottom: 20rpx;
        padding-left: 80rpx;
      }
      
      .comment-actions {
        padding-left: 80rpx;
        
        .reply-btn {
          font-size: 26rpx;
          color: #1890ff;
        }
      }
      
      .reply-list {
        margin-top: 20rpx;
        padding-left: 80rpx;
        
        .reply-item {
          margin-bottom: 20rpx;
          padding-bottom: 20rpx;
          border-bottom: 1rpx solid #f5f5f5;
          
          &:last-child {
            border-bottom: none;
            margin-bottom: 0;
          }
          
          .reply-header {
            display: flex;
            align-items: center;
            margin-bottom: 15rpx;
            
            image {
              width: 40rpx;
              height: 40rpx;
              border-radius: 50%;
              margin-right: 15rpx;
            }
            
            .reply-info {
              display: flex;
              flex-direction: column;
              
              .username {
                font-size: 24rpx;
                color: #333;
                font-weight: bold;
                margin-bottom: 5rpx;
              }
              
              .date {
                font-size: 22rpx;
                color: #999;
              }
            }
          }
          
          .reply-content {
            font-size: 26rpx;
            color: #666;
            line-height: 1.5;
            
            .reply-to {
              color: #1890ff;
              font-weight: bold;
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
    }
  }
}

.add-comment-btn {
  position: fixed;
  bottom: 40rpx;
  right: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #3cc51f;
  color: #fff;
  width: 160rpx;
  height: 80rpx;
  border-radius: 40rpx;
  box-shadow: 0 4rpx 12rpx rgba(60, 197, 31, 0.3);
  
  text {
    font-size: 28rpx;
    margin-left: 10rpx;
  }
}

.comment-modal, .rate-modal {
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
    
    .reply-info {
      font-size: 28rpx;
      color: #666;
      margin-bottom: 20rpx;
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

.rate-modal {
  .modal-content {
    display: flex;
    justify-content: center;
    padding: 40rpx 0;
  }
}
</style>