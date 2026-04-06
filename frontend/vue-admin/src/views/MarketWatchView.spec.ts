import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    state: { user: { id: 1, username: 'admin' } },
  })),
}))

import MarketWatchView from '@/views/MarketWatchView.vue'

describe('MarketWatchView', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('should render page', () => {
    wrapper = mount(MarketWatchView)
    expect(wrapper.find('h1').text()).toBe('Market Watch')
  })

  it('should show empty message when no signals', () => {
    wrapper = mount(MarketWatchView)
    expect(wrapper.text()).toContain('信号数据尚未就绪')
  })
})
