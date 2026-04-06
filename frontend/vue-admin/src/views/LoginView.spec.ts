import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '@/views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const mockLogin = vi.fn()
const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    login: mockLogin,
    state: {
      error: null,
      loading: false,
    },
  })),
}))

describe('LoginView', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockLogin.mockResolvedValue(true)
    wrapper = mount(LoginView)
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  describe('Template', () => {
    it('should render login form', () => {
      expect(wrapper.find('h1').text()).toBe('登录')
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
    })

    it('should have username input with placeholder', () => {
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('placeholder')).toBe('请输入用户名')
    })

    it('should have password input with placeholder', () => {
      const input = wrapper.find('input[type="password"]')
      expect(input.attributes('placeholder')).toBe('请输入密码')
    })

    it('should not show error message initially', () => {
      expect(wrapper.find('.error-msg').exists()).toBe(false)
    })

    it('should show error message when error exists', async () => {
      wrapper = mount(LoginView, {
        global: {
          provide: {
            error: '测试错误',
          },
        },
      })
      wrapper.vm.error = '测试错误'
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.error-msg').exists()).toBe(true)
    })

    it('should disable button when loading', async () => {
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()
      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('should show loading text when loading', async () => {
      wrapper.vm.loading = true
      await wrapper.vm.$nextTick()
      const button = wrapper.find('button[type="submit"]')
      expect(button.text()).toBe('登录中...')
    })

    it('should enable button when not loading', () => {
      wrapper.vm.loading = false
      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Form Interaction', () => {
    it('should update username on input', async () => {
      const input = wrapper.find('input[type="text"]')
      await input.setValue('admin')
      expect(wrapper.vm.form.username).toBe('admin')
    })

    it('should update password on input', async () => {
      const input = wrapper.find('input[type="password"]')
      await input.setValue('password123')
      expect(wrapper.vm.form.password).toBe('password123')
    })
  })

  describe('Login Flow', () => {
    it('should call authStore.login on form submit', async () => {
      await wrapper.find('input[type="text"]').setValue('admin')
      await wrapper.find('input[type="password"]').setValue('password123')
      await wrapper.find('form').trigger('submit.prevent')
      expect(mockLogin).toHaveBeenCalledWith('admin', 'password123')
    })

    it('should navigate to dashboard on successful login', async () => {
      mockLogin.mockResolvedValue(true)
      await wrapper.find('input[type="text"]').setValue('admin')
      await wrapper.find('input[type="password"]').setValue('password123')
      await wrapper.find('form').trigger('submit.prevent')
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    it('should show error when login fails', async () => {
      mockLogin.mockResolvedValue(false)
      await wrapper.find('input[type="text"]').setValue('admin')
      await wrapper.find('input[type="password"]').setValue('wrongpass')
      await wrapper.find('form').trigger('submit.prevent')
      expect(wrapper.vm.error).toBe('登录失败')
    })
  })
})
