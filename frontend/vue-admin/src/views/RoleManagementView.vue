<template>
  <div class="role-management">
    <n-card title="角色管理">
      <template #header-extra>
        <n-button type="primary" @click="openCreateModal">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建角色
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="roles"
        :loading="loading"
        :row-key="(row: Role) => row.id"
      />
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑角色' : '新建角色'" :style="{ width: '600px' }">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="80">
        <n-form-item label="角色ID" path="role_id" v-if="!isEdit">
          <n-input v-model:value="form.role_id" placeholder="请输入角色ID（如 admin, user）" />
        </n-form-item>
        <n-form-item label="角色ID" v-else>
          <n-input :value="form.role_id" disabled />
        </n-form-item>
        <n-form-item label="名称" path="name">
          <n-input v-model:value="form.name" placeholder="请输入角色名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="form.description" type="textarea" placeholder="请输入角色描述" />
        </n-form-item>
        <n-form-item label="权限">
          <div class="permission-panel">
            <div v-for="category in permissionCategories" :key="category" class="permission-category">
              <n-checkbox
                :checked="isCategoryChecked(category)"
                :indeterminate="isCategoryIndeterminate(category)"
                @update:checked="(val: boolean) => toggleCategory(category, val)"
              >
                <span class="category-label">{{ category }}</span>
              </n-checkbox>
              <n-checkbox-group v-model:value="form.permissions" class="permission-items">
                <n-space vertical>
                  <n-checkbox
                    v-for="perm in getPermissionsByCategory(category)"
                    :key="perm.code"
                    :value="perm.code"
                  >
                    {{ perm.name }}
                  </n-checkbox>
                </n-space>
              </n-checkbox-group>
            </div>
          </div>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleSubmit">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { NCard, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSpace, NTag, NIcon, NCheckbox, NCheckboxGroup, useMessage } from 'naive-ui'
import { AddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import { apiRoles, type Role, type Permission } from '../services/api_roles'

const message = useMessage()
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const loading = ref(false)
const submitting = ref(false)

const showModal = ref(false)
const isEdit = ref(false)
const formRef = ref()

const form = ref({
  id: '',
  role_id: '',
  name: '',
  description: '',
  permissions: [] as string[],
})

const rules = {
  role_id: { required: true, message: '请输入角色ID', trigger: 'blur' },
  name: { required: true, message: '请输入角色名称', trigger: 'blur' },
}

const permissionCategories = computed(() => {
  const cats = new Set(permissions.value.map(p => p.category))
  return Array.from(cats)
})

function getPermissionsByCategory(category: string): Permission[] {
  return permissions.value.filter(p => p.category === category)
}

function isCategoryChecked(category: string): boolean {
  const categoryPerms = getPermissionsByCategory(category)
  return categoryPerms.length > 0 && categoryPerms.every(p => form.value.permissions.includes(p.code))
}

function isCategoryIndeterminate(category: string): boolean {
  const categoryPerms = getPermissionsByCategory(category)
  const checkedCount = categoryPerms.filter(p => form.value.permissions.includes(p.code)).length
  return checkedCount > 0 && checkedCount < categoryPerms.length
}

function toggleCategory(category: string, checked: boolean) {
  const categoryPerms = getPermissionsByCategory(category)
  if (checked) {
    const newPerms = new Set(form.value.permissions)
    categoryPerms.forEach(p => newPerms.add(p.code))
    form.value.permissions = Array.from(newPerms)
  } else {
    const catCodes = new Set(categoryPerms.map(p => p.code))
    form.value.permissions = form.value.permissions.filter(p => !catCodes.has(p))
  }
}

const columns = [
  { title: '角色ID', key: 'role_id', width: 120 },
  { title: '名称', key: 'name', width: 150 },
  { title: '描述', key: 'description' },
  {
    title: '权限数',
    key: 'permissions',
    width: 100,
    render: (row: Role) => row.permissions?.length || 0,
  },
  {
    title: '用户数',
    key: 'user_count',
    width: 100,
    render: (row: Role) => row.user_count || 0,
  },
  {
    title: '系统角色',
    key: 'is_system',
    width: 100,
    render: (row: Role) => row.is_system ? h(NTag, { type: 'info', size: 'small' }, () => '是') : h(NTag, { type: 'default', size: 'small' }, () => '否'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Role) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openEditModal(row),
        }, { icon: () => h(NIcon, null, () => h(CreateOutline)), default: () => '编辑' }),
        !row.is_system ? h(NButton, {
          size: 'small',
          quaternary: true,
          type: 'error',
          onClick: () => handleDelete(row),
        }, { icon: () => h(NIcon, null, () => h(TrashOutline)), default: () => '删除' }) : null,
      ].filter(Boolean))
    },
  },
]

async function loadRoles() {
  loading.value = true
  try {
    const res = await apiRoles.getRoles()
    roles.value = res.items
  } catch (e: any) {
    message.error(`加载角色失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loading.value = false
  }
}

async function loadPermissions() {
  try {
    const res = await apiRoles.getPermissions()
    permissions.value = res.items
  } catch (e: any) {
    console.error('加载权限失败:', e)
  }
}

function openCreateModal() {
  isEdit.value = false
  form.value = {
    id: '',
    role_id: '',
    name: '',
    description: '',
    permissions: [],
  }
  showModal.value = true
}

function openEditModal(role: Role) {
  isEdit.value = true
  form.value = {
    id: role.id,
    role_id: role.role_id,
    name: role.name,
    description: role.description,
    permissions: [...(role.permissions || [])],
  }
  showModal.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    submitting.value = true
    if (isEdit.value) {
      await apiRoles.updateRole(form.value.role_id, {
        name: form.value.name,
        description: form.value.description,
        permissions: form.value.permissions,
      })
      message.success('角色更新成功')
    } else {
      await apiRoles.createRole({
        role_id: form.value.role_id,
        name: form.value.name,
        description: form.value.description,
        permissions: form.value.permissions,
      })
      message.success('角色创建成功')
    }
    showModal.value = false
    loadRoles()
  } catch (e: any) {
    if (e.response) {
      message.error(`${isEdit.value ? '更新' : '创建'}失败: ${e.response?.data?.detail || e.message}`)
    }
  } finally {
    submitting.value = false
  }
}

async function handleDelete(role: Role) {
  const confirmed = window.confirm(`确定删除角色 "${role.name}" 吗？`)
  if (!confirmed) return
  try {
    await apiRoles.deleteRole(role.role_id)
    message.success('角色删除成功')
    loadRoles()
  } catch (e: any) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

onMounted(() => {
  loadRoles()
  loadPermissions()
})
</script>

<style scoped>
.role-management {
  padding: 20px;
}
.permission-panel {
  width: 100%;
  max-height: 400px;
  overflow-y: auto;
}
.permission-category {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}
.permission-category:last-child {
  border-bottom: none;
}
.category-label {
  font-weight: 600;
}
.permission-items {
  margin-top: 8px;
  margin-left: 24px;
}
</style>
