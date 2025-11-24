<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  onLaunch() {
    console.log('App Launch')
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  }
}
</script>

<style>
/* 引入iconfont图标字体 */
@import "./styles/iconfont.css";

/* 全局样式 */
page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  background-color: #f8f8f8;
  color: #333;
}

/* 通用样式类 */
.container {
  padding: 20rpx;
}

.flex {
  display: flex;
}

.flex-column {
  display: flex;
  flex-direction: column;
}

.justify-between {
  justify-content: space-between;
}

.justify-center {
  justify-content: center;
}

.align-center {
  align-items: center;
}

.text-center {
  text-align: center;
}

.text-primary {
  color: #007aff;
}

.text-danger {
  color: #ff3b30;
}

.text-success {
  color: #34c759;
}

.text-warning {
  color: #ff9500;
}

.text-muted {
  color: #8e8e93;
}

.bg-primary {
  background-color: #007aff;
}

.bg-danger {
  background-color: #ff3b30;
}

.bg-success {
  background-color: #34c759;
}

.bg-warning {
  background-color: #ff9500;
}

.bg-light {
  background-color: #f2f2f7;
}

.border {
  border: 1px solid #e5e5ea;
}

.border-top {
  border-top: 1px solid #e5e5ea;
}

.border-bottom {
  border-bottom: 1px solid #e5e5ea;
}

.border-left {
  border-left: 1px solid #e5e5ea;
}

.border-right {
  border-right: 1px solid #e5e5ea;
}

.rounded {
  border-radius: 8rpx;
}

.rounded-lg {
  border-radius: 16rpx;
}

.shadow {
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.p-1 {
  padding: 10rpx;
}

.p-2 {
  padding: 20rpx;
}

.p-3 {
  padding: 30rpx;
}

.m-1 {
  margin: 10rpx;
}

.m-2 {
  margin: 20rpx;
}

.m-3 {
  margin: 30rpx;
}

.mt-1 {
  margin-top: 10rpx;
}

.mt-2 {
  margin-top: 20rpx;
}

.mt-3 {
  margin-top: 30rpx;
}

.mb-1 {
  margin-bottom: 10rpx;
}

.mb-2 {
  margin-bottom: 20rpx;
}

.mb-3 {
  margin-bottom: 30rpx;
}

.ml-1 {
  margin-left: 10rpx;
}

.ml-2 {
  margin-left: 20rpx;
}

.ml-3 {
  margin-left: 30rpx;
}

.mr-1 {
  margin-right: 10rpx;
}

.mr-2 {
  margin-right: 20rpx;
}

.mr-3 {
  margin-right: 30rpx;
}

.text-sm {
  font-size: 24rpx;
}

.text-base {
  font-size: 28rpx;
}

.text-lg {
  font-size: 32rpx;
}

.text-xl {
  font-size: 36rpx;
}

.font-bold {
  font-weight: bold;
}
</style>