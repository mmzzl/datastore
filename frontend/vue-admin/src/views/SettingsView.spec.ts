import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    state: { user: { id: 1, username: 'admin' }, is_superuser: true },
    hasPermission: vi.fn(() => true),
  })),
}))

import SettingsView from '@/views/SettingsView.vue'

describe('SettingsView', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('should render page', () => {
    wrapper = mount(SettingsView)
    expect(wrapper.find('h1').exists()).toBe(true)
  })

  it('should render settings content', () => {
    wrapper = mount(SettingsView)
    expect(wrapper.find('h1').text()).toBe('系统设置')
  })
})
