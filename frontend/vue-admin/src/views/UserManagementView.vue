<template>
  <div class="user-management">
    <n-card title="用户管理">
      <template #header-extra>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建用户
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="users"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row: User) => row.id"
        @update:page="handlePageChange"
      />
    </n-card>

    <n-modal v-model:show="showCreateModal" preset="card" title="新建用户" :style="{ width: '500px' }">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="left" label-width="80">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="createForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="createForm.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-form-item label="显示名" path="display_name">
          <n-input v-model:value="createForm.display_name" placeholder="请输入显示名" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="createForm.email" placeholder="请输入邮箱（可选）" />
        </n-form-item>
        <n-form-item label="角色" path="role_id">
          <n-select v-model:value="createForm.role_id" :options="roleOptions" placeholder="请选择角色" />
        </n-form-item>
        <n-form-item label="超级用户" path="is_superuser">
          <n-switch v-model:value="createForm.is_superuser" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleCreate">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showEditModal" preset="card" title="编辑用户" :style="{ width: '500px' }">
      <n-form ref="editFormRef" :model="editForm" :rules="editRules" label-placement="left" label-width="80">
        <n-form-item label="用户名">
          <n-input :value="editForm.username" disabled />
        </n-form-item>
        <n-form-item label="显示名" path="display_name">
          <n-input v-model:value="editForm.display_name" placeholder="请输入显示名" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="editForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="角色" path="role_id">
          <n-select v-model:value="editForm.role_id" :options="roleOptions" placeholder="请选择角色" />
        </n-form-item>
        <n-form-item label="状态" path="status">
          <n-select v-model:value="editForm.status" :options="statusOptions" placeholder="请选择状态" />
        </n-form-item>
        <n-form-item label="超级用户" path="is_superuser">
          <n-switch v-model:value="editForm.is_superuser" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleEdit">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showResetPasswordModal" preset="card" title="重置密码" :style="{ width: '400px' }">
      <n-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-placement="left" label-width="80">
        <n-form-item label="用户名">
          <n-input :value="resetForm.username" disabled />
        </n-form-item>
        <n-form-item label="新密码" path="new_password">
          <n-input v-model:value="resetForm.new_password" type="password" placeholder="请输入新密码" />
        </n-form-item>
        <n-form-item label="确认密码" path="confirm_password">
          <n-input v-model:value="resetForm.confirm_password" type="password" placeholder="请确认新密码" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showResetPasswordModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleResetPassword">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { NCard, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NSpace, NTag, NIcon, useMessage } from 'naive-ui'
import { AddOutline, CreateOutline, TrashOutline, KeyOutline, LockOpenOutline } from '@vicons/ionicons5'
import { apiUsers, type User } from '../services/api_users'
import { apiRoles, type Role } from '../services/api_roles'

const message = useMessage()
const users = ref<User[]>([])
const roles = ref<Role[]>([])
const loading = ref(false)
const submitting = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showResetPasswordModal = ref(false)

const createFormRef = ref()
const editFormRef = ref()
const resetFormRef = ref()

const createForm = ref({
  username: '',
  password: '',
  display_name: '',
  email: '',
  role_id: '',
  is_superuser: false,
})

const editForm = ref({
  id: '',
  username: '',
  display_name: '',
  email: '',
  role_id: '',
  status: 'active' as 'active' | 'disabled' | 'locked',
  is_superuser: false,
})

const resetForm = ref({
  id: '',
  username: '',
  new_password: '',
  confirm_password: '',
})

const createRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  display_name: { required: true, message: '请输入显示名', trigger: 'blur' },
  role_id: { required: true, message: '请选择角色', trigger: 'change' },
}

const editRules = {
  display_name: { required: true, message: '请输入显示名', trigger: 'blur' },
  role_id: { required: true, message: '请选择角色', trigger: 'change' },
}

const resetRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string) => {
        return value === resetForm.value.new_password
      },
      message: '两次密码不一致',
      trigger: 'blur',
    },
  ],
}

const statusOptions = [
  { label: '正常', value: 'active' },
  { label: '禁用', value: 'disabled' },
  { label: '锁定', value: 'locked' },
]

const roleOptions = computed(() => {
  return roles.value.map(r => ({
    label: r.name,
    value: r.role_id,
  }))
})

const pagination = computed(() => ({
  page: currentPage.value,
  pageSize: pageSize.value,
  itemCount: total.value,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    currentPage.value = page
    loadUsers()
  },
  onUpdatePageSize: (size: number) => {
    pageSize.value = size
    currentPage.value = 1
    loadUsers()
  },
}))

const columns = [
  { title: '用户名', key: 'username' },
  { title: '显示名', key: 'display_name' },
  { title: '邮箱', key: 'email' },
  { title: '角色', key: 'role_name' },
  {
    title: '状态',
    key: 'status',
    render: (row: User) => {
      const statusMap: Record<string, { type: 'success' | 'warning' | 'error' | 'info', text: string }> = {
        active: { type: 'success', text: '正常' },
        disabled: { type: 'warning', text: '禁用' },
        locked: { type: 'error', text: '锁定' },
      }
      const s = statusMap[row.status] || { type: 'info', text: row.status }
      return h(NTag, { type: s.type, size: 'small' }, () => s.text)
    },
  },
  {
    title: '超级用户',
    key: 'is_superuser',
    render: (row: User) => row.is_superuser ? h(NTag, { type: 'success', size: 'small' }, () => '是') : h(NTag, { type: 'default', size: 'small' }, () => '否'),
  },
  {
    title: '最后登录',
    key: 'last_login',
    render: (row: User) => row.last_login ? new Date(row.last_login).toLocaleString('zh-CN') : '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row: User) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openEditModal(row),
        }, { icon: () => h(NIcon, null, () => h(CreateOutline)), default: () => '编辑' }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openResetPasswordModal(row),
        }, { icon: () => h(NIcon, null, () => h(KeyOutline)), default: () => '重置密码' }),
        row.status === 'locked' ? h(NButton, {
          size: 'small',
          quaternary: true,
          type: 'success',
          onClick: () => handleUnlock(row),
        }, { icon: () => h(NIcon, null, () => h(LockOpenOutline)), default: () => '解锁' }) : null,
        h(NButton, {
          size: 'small',
          quaternary: true,
          type: 'error',
          onClick: () => handleDelete(row),
        }, { icon: () => h(NIcon, null, () => h(TrashOutline)), default: () => '删除' }),
      ].filter(Boolean))
    },
  },
]

async function loadUsers() {
  loading.value = true
  try {
    const res = await apiUsers.getUsers(currentPage.value, pageSize.value)
    users.value = res.items
    total.value = res.total
  } catch (e: any) {
    message.error(`加载用户失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

async function loadRoles() {
  try {
    const res = await apiRoles.getRoles()
    roles.value = res.items
  } catch (e: any) {
    console.error('加载角色失败:', e)
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadUsers()
}

function openEditModal(user: User) {
  editForm.value = {
    id: user.id,
    username: user.username,
    display_name: user.display_name,
    email: user.email || '',
    role_id: user.role_id,
    status: user.status,
    is_superuser: user.is_superuser,
  }
  showEditModal.value = true
}

function openResetPasswordModal(user: User) {
  resetForm.value = {
    id: user.id,
    username: user.username,
    new_password: '',
    confirm_password: '',
  }
  showResetPasswordModal.value = true
}

async function handleCreate() {
  try {
    await createFormRef.value?.validate()
    submitting.value = true
    await apiUsers.createUser({
      username: createForm.value.username,
      password: createForm.value.password,
      display_name: createForm.value.display_name,
      email: createForm.value.email || undefined,
      role_id: createForm.value.role_id,
      is_superuser: createForm.value.is_superuser,
    })
    message.success('用户创建成功')
    showCreateModal.value = false
    createForm.value = {
      username: '',
      password: '',
      display_name: '',
      email: '',
      role_id: '',
      is_superuser: false,
    }
    loadUsers()
  } catch (e: any) {
    if (e.response) {
      message.error(`创建失败: ${e.response?.data?.detail || e.message}`)
    }
  } finally {
    submitting.value = false
  }
}

async function handleEdit() {
  try {
    await editFormRef.value?.validate()
    submitting.value = true
    await apiUsers.updateUser(editForm.value.id, {
      display_name: editForm.value.display_name,
      email: editForm.value.email || undefined,
      role_id: editForm.value.role_id,
      status: editForm.value.status,
      is_superuser: editForm.value.is_superuser,
    })
    message.success('用户更新成功')
    showEditModal.value = false
    loadUsers()
  } catch (e: any) {
    if (e.response) {
      message.error(`更新失败: ${e.response?.data?.detail || e.message}`)
    }
  } finally {
    submitting.value = false
  }
}

async function handleResetPassword() {
  try {
    await resetFormRef.value?.validate()
    submitting.value = true
    await apiUsers.resetPassword(resetForm.value.id, {
      new_password: resetForm.value.new_password,
    })
    message.success('密码重置成功')
    showResetPasswordModal.value = false
  } catch (e: any) {
    if (e.response) {
      message.error(`重置失败: ${e.response?.data?.detail || e.message}`)
    }
  } finally {
    submitting.value = false
  }
}

async function handleUnlock(user: User) {
  try {
    await apiUsers.unlockUser(user.id)
    message.success('用户解锁成功')
    loadUsers()
  } catch (e: any) {
    message.error(`解锁失败: ${e.response?.data?.detail || e.message}`)
  }
}

async function handleDelete(user: User) {
  const confirmed = window.confirm(`确定删除用户 "${user.username}" 吗？`)
  if (!confirmed) return
  try {
    await apiUsers.deleteUser(user.id)
    message.success('用户删除成功')
    loadUsers()
  } catch (e: any) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}
</style>
