import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api_backtest', () => ({
  apiBacktest: {
    getResults: vi.fn(),
    getResult: vi.fn(),
    startBacktest: vi.fn(),
  },
}))

vi.mock('@/services/websocket', () => ({
  createWebSocket: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  })),
}))

import { apiBacktest } from '@/services/api_backtest'
import { useBacktestStore } from '@/stores/backtest'

describe('Backtest Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have initial state', () => {
      const store = useBacktestStore()
      expect(store.state.results).toEqual([])
      expect(store.state.currentBacktest).toBeNull()
      expect(store.state.progress).toBe(0)
      expect(store.state.status).toBe('idle')
      expect(store.state.wsConnected).toBe(false)
      expect(store.state.loading).toBe(false)
      expect(store.state.error).toBeNull()
    })
  })

  describe('fetchResults', () => {
    it('should fetch results and update state', async () => {
      vi.mocked(apiBacktest.getResults).mockResolvedValue({
        items: [{ id: '1', name: 'Test' }],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })

      const store = useBacktestStore()
      await store.fetchResults()

      expect(store.state.results).toHaveLength(1)
      expect(store.state.loading).toBe(false)
    })

    it('should set error on API failure', async () => {
      vi.mocked(apiBacktest.getResults).mockRejectedValue({
        response: { data: { detail: 'API Error' } },
      })

      const store = useBacktestStore()
      await store.fetchResults()

      expect(store.state.error).toBe('API Error')
      expect(store.state.loading).toBe(false)
    })
  })

  describe('fetchResult', () => {
    it('should fetch single result', async () => {
      vi.mocked(apiBacktest.getResult).mockResolvedValue({ id: '1', name: 'Test' })

      const store = useBacktestStore()
      await store.fetchResult('1')

      expect(store.state.currentBacktest).not.toBeNull()
      expect(store.state.loading).toBe(false)
    })

    it('should handle error on fetchResult', async () => {
      vi.mocked(apiBacktest.getResult).mockRejectedValue({
        response: { data: { detail: 'Not found' } },
      })

      const store = useBacktestStore()
      await store.fetchResult('1')

      expect(store.state.error).toBe('Not found')
    })
  })

  describe('startBacktest', () => {
    it('should start backtest and return id', async () => {
      vi.mocked(apiBacktest.startBacktest).mockResolvedValue({ id: 'bt-123' })

      const store = useBacktestStore()
      const result = await store.startBacktest({} as any)

      expect(store.state.status).toBe('running')
      expect(result).toBe('bt-123')
    })

    it('should handle startBacktest error', async () => {
      vi.mocked(apiBacktest.startBacktest).mockRejectedValue({
        response: { data: { detail: 'Failed' } },
      })

      const store = useBacktestStore()
      await expect(store.startBacktest({} as any)).rejects.toThrow()

      expect(store.state.status).toBe('failed')
    })
  })

  describe('reset', () => {
    it('should reset state', () => {
      const store = useBacktestStore()
      store.state.status = 'running'
      store.state.progress = 50
      store.state.currentBacktest = { id: '1' } as any
      store.state.error = 'error'

      store.reset()

      expect(store.state.status).toBe('idle')
      expect(store.state.progress).toBe(0)
      expect(store.state.currentBacktest).toBeNull()
      expect(store.state.error).toBeNull()
    })
  })
})
