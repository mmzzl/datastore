<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NSwitch, NSpin, NAlert, NSpace, NDescriptions, NDescriptionsItem, NTag, NPopconfirm, NDialog } from 'naive-ui'
import { ref } from 'vue'
import { authService } from '../services/api'
import { apiDingtalk, type DingtalkConfig } from '../services/api_dingtalk'

const formValue = ref({
  webhook: '',
  secret: '',
  name: '默认配置',
  user_id: 'admin',
})
const currentConfig = ref<DingtalkConfig | null>(null)
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const configDialogVisible = ref(false)

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
  if (!currentConfig.value?.webhook) return ''
  const url = currentConfig.value.webhook
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
        webhook: '',
        secret: '',
        name: res.items[0].name || '默认配置',
        user_id: res.items[0].user_id || 'admin',
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
    if (currentConfig.value?.id) {
      const updateData: any = {}
      if (formValue.value.webhook) {
        updateData.webhook = formValue.value.webhook
      }
      if (formValue.value.secret) {
        updateData.secret = formValue.value.secret
      }
      updateData.name = formValue.value.name
      await apiDingtalk.updateConfig(currentConfig.value.id, updateData)
    } else {
      await apiDingtalk.createConfig({
        user_id: formValue.value.user_id,
        name: formValue.value.name,
        webhook: formValue.value.webhook,
        secret: formValue.value.secret,
      })
    }
    success.value = '保存成功'
    await loadConfig()
    configDialogVisible.value = false
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
      webhook: '',
      secret: '',
      name: '默认配置',
      user_id: 'admin',
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
    webhook: '',
    secret: '',
    name: '默认配置',
    user_id: 'admin',
  }
}

function openConfigDialog() {
  console.log('点击了配置按钮');
  console.log('currentConfig:', currentConfig.value);
  if (currentConfig.value) {
    formValue.value = {
      webhook: '',
      secret: '',
      name: currentConfig.value.name || '默认配置',
      user_id: currentConfig.value.user_id || 'admin',
    }
  }
  console.log('准备打开模态框');
  configDialogVisible.value = true;
  console.log('configDialogVisible:', configDialogVisible.value);
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
        <div class="actions mb-4">
          <NSpace>
            <NButton type="primary" @click="openConfigDialog">
              配置
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
        </div>

        <div v-if="currentConfig">
          <div class="current-config mb-4">
            <NDescriptions label-placement="left" bordered :column="1">
            <NDescriptionsItem label="状态">
              <NTag :type="currentConfig.is_active ? 'success' : 'default'">
                {{ currentConfig.is_active ? '已启用' : '已禁用' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="配置名称">
              {{ currentConfig.name }}
            </NDescriptionsItem>
            <NDescriptionsItem label="Webhook URL">
              {{ maskedWebhookUrl }}
            </NDescriptionsItem>
            <NDescriptionsItem label="签名密钥">
              {{ maskedSecret }}
            </NDescriptionsItem>
          </NDescriptions>
          </div>
        </div>

        <div v-else class="no-config">
          <p>还没有配置钉钉通知</p>
        </div>
      </NSpin>
    </NCard>

    <!-- 配置弹窗 -->
    <div v-if="configDialogVisible" class="modal-overlay" @click="configDialogVisible = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>钉钉通知配置</h3>
          <button class="close-button" @click="configDialogVisible = false">×</button>
        </div>
        <div class="modal-body">
          <NForm :model="formValue" label-placement="left" label-width="120px">
            <NFormItem label="配置名称">
              <NInput
                v-model:value="formValue.name"
                placeholder="配置名称"
              />
            </NFormItem>
            <NFormItem label="Webhook URL" :rule="webhookUrlRules">
              <NInput
                v-model:value="formValue.webhook"
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
          </NForm>
        </div>
        <div class="modal-footer">
          <NButton @click="configDialogVisible = false">
            取消
          </NButton>
          <NButton type="primary" :loading="saving" @click="saveConfig">
            确定
          </NButton>
        </div>
      </div>
    </div>
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
.actions {
  padding: 12px;
  background-color: var(--n-color-background);
  border-radius: 4px;
  border: 1px solid var(--n-border-color);
}
.no-config {
  padding: 24px;
  text-align: center;
  background-color: var(--n-color-background);
  border-radius: 4px;
  border: 1px dashed var(--n-border-color);
}
.no-config p {
  margin-bottom: 16px;
  color: var(--n-text-color-2);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--n-border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color-1);
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--n-text-color-3);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: var(--n-color-hover);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--n-border-color);
  background-color: var(--n-color-background);
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}
</style>
