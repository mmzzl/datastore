<template>
  <view class="container">
    <u--form labelPosition="left" :model="form" :rules="rules" ref="uForm" labelWidth="100">
      
      <u-form-item label="标题" prop="title" borderBottom required>
        <u--input v-model="form.title" placeholder="请输入题目标题" border="none"></u--input>
      </u-form-item>
      
      <u-form-item label="学科" prop="subject" borderBottom required @click="showSubjectSelect">
        <u--input v-model="subjectName" placeholder="请选择学科" disabled disabledColor="#ffffff" border="none" suffixIcon="arrow-right"></u--input>
      </u-form-item>
      
      <u-form-item label="难度" prop="difficulty" borderBottom>
        <u-rate :count="5" v-model="form.difficulty"></u-rate>
      </u-form-item>
      
      <u-form-item label="题目内容" prop="content" borderBottom required>
        <u--textarea v-model="form.content" placeholder="请输入题目内容" height="100"></u--textarea>
      </u-form-item>
      
      <u-form-item label="答案" prop="correct_answer" borderBottom>
        <u--textarea v-model="form.correct_answer" placeholder="请输入参考答案" height="80"></u--textarea>
      </u-form-item>
      
      <u-form-item label="解析" prop="analysis" borderBottom>
        <u--textarea v-model="form.analysis" placeholder="请输入解析" height="80"></u--textarea>
      </u-form-item>
      
      <u-form-item label="附件" prop="attachments" borderBottom>
        <u-upload
          :fileList="fileList"
          @afterRead="afterRead"
          @delete="deletePic"
          name="file"
          multiple
          :maxCount="9"
          width="80"
          height="80"
          accept="file"
        ></u-upload>
      </u-form-item>
      
    </u--form>
    
    <view class="btn-group">
      <u-button type="primary" text="保存" customStyle="margin-top: 40rpx" @click="submit"></u-button>
    </view>
    
    <u-action-sheet :actions="subjectList" :show="showSubject" title="选择学科" @select="subjectSelect" @close="showSubject = false"></u-action-sheet>
    
  </view>
</template>

<script>
import request from '@/utils/request.js';

export default {
  data() {
    return {
      form: {
        title: '',
        subject: '',
        content: '',
        difficulty: 3,
        correct_answer: '',
        analysis: ''
      },
      subjectName: '',
      showSubject: false,
      subjectList: [],
      fileList: [],
      rules: {
        title: [
          { required: true, message: '请输入标题', trigger: ['blur', 'change'] }
        ],
        subject: [
          { required: true, message: '请选择学科', trigger: ['blur', 'change'] }
        ],
        content: [
          { required: true, message: '请输入题目内容', trigger: ['blur', 'change'] }
        ]
      }
    };
  },
  onLoad() {
    this.getSubjects();
  },
  methods: {
    async getSubjects() {
      try {
        const res = await request({
          url: 'questions/subjects/',
          method: 'GET'
        });
        this.subjectList = res.results.map(item => ({
          name: item.name,
          id: item.id,
          color: item.color
        }));
      } catch (e) {
        console.error(e);
      }
    },
    showSubjectSelect() {
      this.showSubject = true;
    },
    subjectSelect(e) {
      this.form.subject = e.id;
      this.subjectName = e.name;
      this.showSubject = false;
      this.$refs.uForm.validateField('subject');
    },
    deletePic(event) {
      this.fileList.splice(event.index, 1)
    },
    async afterRead(event) {
      let lists = [].concat(event.file)
      let fileListLen = this.fileList.length
      lists.map((item) => {
        this.fileList.push({
          ...item,
          status: 'uploading',
          message: '上传中'
        })
      })
      for (let i = 0; i < lists.length; i++) {
        const result = await this.uploadFilePromise(lists[i].url)
        let item = this.fileList[fileListLen]
        this.fileList.splice(fileListLen, 1, Object.assign(item, {
          status: 'success',
          message: '',
          url: result.url,
          name: result.name,
          type: result.type
        }))
        fileListLen++
      }
    },
    uploadFilePromise(url) {
      return new Promise((resolve, reject) => {
        const token = uni.getStorageSync('token');
        uni.uploadFile({
          url: 'http://127.0.0.1:8000/api/questions/upload/', 
          filePath: url,
          name: 'file',
          header: {
            Authorization: `Bearer ${token}`
          },
          success: (res) => {
            if (res.statusCode === 200) {
                const data = JSON.parse(res.data)
                resolve(data)
            } else {
                reject(res)
            }
          },
          fail: (err) => {
              reject(err)
          }
        });
      })
    },
    submit() {
      this.$refs.uForm.validate().then(res => {
        this.createQuestion();
      }).catch(errors => {
        console.log(errors)
      })
    },
    async createQuestion() {
      try {
        const attachments = this.fileList.map(item => ({
          url: item.url,
          name: item.name,
          type: item.type
        }));

        const postData = {
          ...this.form,
          attachments: attachments
        };

        await request({
          url: 'questions/questions/',
          method: 'POST',
          data: postData
        });
        
        uni.showToast({
          title: '添加成功',
          icon: 'success'
        });
        
        setTimeout(() => {
          uni.navigateBack();
        }, 1500);
      } catch (e) {
        console.error(e);
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.container {
  padding: 30rpx;
  background-color: #fff;
  min-height: 100vh;
}
</style>
