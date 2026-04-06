import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/holdings', () => ({
  useHoldingsStore: vi.fn(() => ({
    fetchHoldings: vi.fn(),
    saveHolding: vi.fn(),
    removeHolding: vi.fn(),
    refreshPortfolio: vi.fn(),
    state: {
      holdings: [],
      totalCost: 0,
      marketValue: 0,
      unrealizedPnL: 0,
      profitRate: 0,
      loading: false,
      error: null,
      currentPage: 1,
      pageSize: 10,
      totalPages: 0,
      totalCount: 0,
    },
  })),
}))

vi.mock('@/services/api', () => ({
  authService: {
    getUser: vi.fn(() => 'admin'),
    isAuthenticated: vi.fn(() => true),
  },
}))

import HoldingsView from '@/views/HoldingsView.vue'

describe('HoldingsView', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('should render page header', () => {
    wrapper = mount(HoldingsView, {
      global: {
        provide: {
          authStore: {
            state: { user: { id: 1, username: 'admin' }, token: 'test' }
          }
        }
      }
    })
    expect(wrapper.find('h1').text()).toBe('持仓管理')
  })

  it('should render action buttons', () => {
    wrapper = mount(HoldingsView, {
      global: {
        provide: {
          authStore: {
            state: { user: { id: 1, username: 'admin' }, token: 'test' }
          }
        }
      }
    })
    expect(wrapper.findAll('button').length).toBeGreaterThan(0)
  })

  it('should render add holding form', () => {
    wrapper = mount(HoldingsView, {
      global: {
        provide: {
          authStore: {
            state: { user: { id: 1, username: 'admin' }, token: 'test' }
          }
        }
      }
    })
    expect(wrapper.find('input.input-code').exists()).toBe(true)
    expect(wrapper.find('input.input-quantity').exists()).toBe(true)
    expect(wrapper.find('input.input-cost').exists()).toBe(true)
  })

  it('should not show error banner when no error', () => {
    wrapper = mount(HoldingsView, {
      global: {
        provide: {
          authStore: {
            state: { user: { id: 1, username: 'admin' }, token: 'test' }
          }
        }
      }
    })
    expect(wrapper.find('.error-banner').exists()).toBe(false)
  })
})
