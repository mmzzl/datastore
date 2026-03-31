<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NSwitch, NSpin, NAlert, NSpace, NDescriptions, NDescriptionsItem, NTag, NPopconfirm } from 'naive-ui'
import { ref } from 'vue'
import { authService } from '../services/api'
import { apiDingtalk, type DingtalkConfig } from '../services/api_dingtalk'

const formValue = ref({
  webhook_url: '',
  secret: '',
  enabled: false,
  keywords: '',
  at_mobiles: '',
})
const currentConfig = ref<DingtalkConfig | null>(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const webhookUrlRules = {
  required: true,
  validator: (_rule: any, value: string) => {
    if (!value) {
      return new Error('Webhook URL 是必填项')
    }
    if (!value.startsWith('https://oapi.dingtalk.com/robot/msg?access_token=')) {
      return new Error('请输入有效的钉钉 Webhook URL')
    }
    return true
  },
  trigger: ['blur', 'input'] as const
}

const maskedWebhookUrl = computed(() => {
  if (!currentConfig.value?.webhook_url) return ''
  const url = currentConfig.value.webhook_url
  const tokenMatch = url.match(/access_token=([a-fA-F0-9]+)/)
  if (tokenMatch) {
    const token = tokenMatch[1]
    const maskedToken = token.length > 8 
      ? token.slice(0, 4) + '****' + token.slice(-4)
      : '****'
    return url.replace(token, maskedToken)
  }
  return url
})

const maskedSecret = computed(() => {
  if (!currentConfig.value?.secret) return ''
  const secret = currentConfig.value.secret
  return secret.length > 4 ? secret.slice(0, 2) + '****' : '****'
})

onMounted(async () => {
  await loadConfig()
})

async function loadConfig() {
  loading.value = true
  error.value = null
  try {
    const userId = authService.getUser()
    const res = await apiDingtalk.getConfigs(userId)
    if (res.items && res.items.length > 0) {
      currentConfig.value = res.items[0]
      formValue.value = {
        webhook_url: '',
        secret: '',
        enabled: res.items[0].enabled,
        keywords: res.items[0].keywords || '',
        at_mobiles: res.items[0].at_mobiles || '',
      }
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
    const userId = authService.getUser()
    if (currentConfig.value?.id) {
      const updateData: any = {}
      if (formValue.value.webhook_url) {
        updateData.webhook_url = formValue.value.webhook_url
      }
      if (formValue.value.secret) {
        updateData.secret = formValue.value.secret
      }
      updateData.enabled = formValue.value.enabled
      updateData.keywords = formValue.value.keywords
      updateData.at_mobiles = formValue.value.at_mobiles
      await apiDingtalk.updateConfig(currentConfig.value.id, updateData)
    } else {
      await apiDingtalk.createConfig({
        webhook_url: formValue.value.webhook_url,
        secret: formValue.value.secret,
        enabled: formValue.value.enabled,
        keywords: formValue.value.keywords,
        at_mobiles: formValue.value.at_mobiles,
      })
    }
    success.value = '保存成功'
    await loadConfig()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function testNotification() {
  if (!currentConfig.value?.id) {
    error.value = '请先保存配置后再测试'
    return
  }
  testing.value = true
  error.value = null
  success.value = null
  try {
    const res = await apiDingtalk.testNotification(currentConfig.value.id)
    success.value = res.message || '测试消息发送成功'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '测试发送失败'
  } finally {
    testing.value = false
  }
}

async function deleteConfig() {
  if (!currentConfig.value?.id) return
  loading.value = true
  error.value = null
  try {
    await apiDingtalk.deleteConfig(currentConfig.value.id)
    currentConfig.value = null
    formValue.value = {
      webhook_url: '',
      secret: '',
      enabled: false,
      keywords: '',
      at_mobiles: '',
    }
    success.value = '配置已删除'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '删除失败'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formValue.value = {
    webhook_url: '',
    secret: '',
    enabled: currentConfig.value?.enabled || false,
    keywords: currentConfig.value?.keywords || '',
    at_mobiles: currentConfig.value?.at_mobiles || '',
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
        <div v-if="currentConfig" class="current-config mb-4">
          <NDescriptions label-placement="left" bordered :column="1">
            <NDescriptionsItem label="状态">
              <NTag :type="currentConfig.enabled ? 'success' : 'default'">
                {{ currentConfig.enabled ? '已启用' : '已禁用' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="Webhook URL">
              {{ maskedWebhookUrl }}
            </NDescriptionsItem>
            <NDescriptionsItem label="签名密钥">
              {{ maskedSecret }}
            </NDescriptionsItem>
            <NDescriptionsItem v-if="currentConfig.keywords" label="关键词">
              {{ currentConfig.keywords }}
            </NDescriptionsItem>
            <NDescriptionsItem v-if="currentConfig.at_mobiles" label="@手机号">
              {{ currentConfig.at_mobiles }}
            </NDescriptionsItem>
          </NDescriptions>
        </div>

        <NForm :model="formValue" label-placement="left" label-width="120px">
          <NFormItem label="启用通知">
            <NSwitch v-model:value="formValue.enabled" />
          </NFormItem>
          <NFormItem label="Webhook URL" :rule="webhookUrlRules">
            <NInput
              v-model:value="formValue.webhook_url"
              placeholder="https://oapi.dingtalk.com/robot/msg?access_token=xxx"
              :input-props="{ autocomplete: 'off' }"
            />
          </NFormItem>
          <NFormItem label="签名密钥">
            <NInput
              v-model:value="formValue.secret"
              placeholder="加签密钥 (可选)"
              type="password"
              show-password-on="click"
              :input-props="{ autocomplete: 'new-password' }"
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
              <NButton @click="resetForm">
                重置
              </NButton>
              <NButton
                :loading="testing"
                :disabled="!currentConfig?.id"
                @click="testNotification"
              >
                测试通知
              </NButton>
              <NPopconfirm
                v-if="currentConfig?.id"
                @positive-click="deleteConfig"
              >
                <template #trigger>
                  <NButton type="error">
                    删除配置
                  </NButton>
                </template>
                确定要删除此配置吗？
              </NPopconfirm>
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
.current-config {
  padding: 12px;
  background-color: var(--n-color-hover);
  border-radius: 4px;
}
</style>
