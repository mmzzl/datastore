<script setup lang="ts">
import { onMounted } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NSwitch, NSpin, NAlert, NSpace } from 'naive-ui'
import { ref } from 'vue'
import api from '../services/api'

interface DingtalkConfig {
  webhook_url: string
  secret: string
  enabled: boolean
  keywords?: string
  at_mobiles?: string
}

const formValue = ref<DingtalkConfig>({
  webhook_url: '',
  secret: '',
  enabled: false,
  keywords: '',
  at_mobiles: '',
})
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

onMounted(async () => {
  await loadConfig()
})

async function loadConfig() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/dingtalk/config')
    if (res.data) {
      formValue.value = res.data
    }
  } catch (e: any) {
    if (e.response?.status !== 404) {
      error.value = e.response?.data?.detail || '加载配置失败'
    }
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  error.value = null
  success.value = null
  try {
    await api.post('/dingtalk/config', formValue.value)
    success.value = '保存成功'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  error.value = null
  success.value = null
  try {
    await api.post('/dingtalk/test', formValue.value)
    success.value = '测试消息发送成功'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '测试发送失败'
  }
}
</script>

<template>
  <div class="dingtalk-config-view">
    <NCard title="钉钉通知配置">
      <NAlert v-if="error" type="error" class="mb-4">
        {{ error }}
      </NAlert>
      <NAlert v-if="success" type="success" class="mb-4">
        {{ success }}
      </NAlert>

      <NSpin :show="loading">
        <NForm :model="formValue" label-placement="left" label-width="120px">
          <NFormItem label="启用通知">
            <NSwitch v-model:value="formValue.enabled" />
          </NFormItem>
          <NFormItem label="Webhook URL">
            <NInput
              v-model:value="formValue.webhook_url"
              placeholder="钉钉机器人 Webhook 地址"
            />
          </NFormItem>
          <NFormItem label="签名密钥">
            <NInput
              v-model:value="formValue.secret"
              placeholder="加签密钥 (可选)"
              type="password"
              show-password-on="click"
            />
          </NFormItem>
          <NFormItem label="关键词">
            <NInput
              v-model:value="formValue.keywords"
              placeholder="消息关键词 (可选, 多个用逗号分隔)"
            />
          </NFormItem>
          <NFormItem label="@手机号">
            <NInput
              v-model:value="formValue.at_mobiles"
              placeholder="@人员手机号 (可选, 多个用逗号分隔)"
            />
          </NFormItem>
          <NFormItem>
            <NSpace>
              <NButton type="primary" :loading="saving" @click="saveConfig">
                保存配置
              </NButton>
              <NButton @click="testConnection">
                测试发送
              </NButton>
            </NSpace>
          </NFormItem>
        </NForm>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.dingtalk-config-view {
  padding: 20px;
}
.mb-4 {
  margin-bottom: 16px;
}
</style>
