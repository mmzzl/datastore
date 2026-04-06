import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: vi.fn(() => ({
    fetchSummary: vi.fn(),
    state: {
      holdingsCount: 5,
      totalCost: 100000,
      marketValue: 120000,
      unrealizedPnL: 20000,
      realizedPnL: 5000,
      profitRate: 0.2,
      signalCount: 10,
      lastUpdated: new Date(),
      loading: false,
      error: null,
      holdings: [],
    },
  })),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    state: { user: { id: 1, username: 'admin' }, token: 'test' },
    hasPermission: vi.fn(() => true),
  })),
}))

import DashboardView from '@/views/DashboardView.vue'

describe('DashboardView', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('should render page', () => {
    wrapper = mount(DashboardView)
    expect(wrapper.find('h1').exists()).toBe(true)
  })

  it('should render stats cards', () => {
    wrapper = mount(DashboardView)
    expect(wrapper.find('.stats-grid').exists()).toBe(true)
  })
})
