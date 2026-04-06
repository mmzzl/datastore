import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api_risk', () => ({
  apiRisk: {
    getReports: vi.fn(),
    getReport: vi.fn(),
  },
}))

import { apiRisk } from '@/services/api_risk'
import { useRiskStore } from '@/stores/risk'

describe('Risk Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have initial state', () => {
      const store = useRiskStore()
      expect(store.state.reports).toEqual([])
      expect(store.state.currentReport).toBeNull()
      expect(store.state.loading).toBe(false)
      expect(store.state.error).toBeNull()
    })
  })

  describe('fetchReports', () => {
    it('should fetch reports and update state', async () => {
      vi.mocked(apiRisk.getReports).mockResolvedValue({
        items: [{ id: '1', type: 'daily' }],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })

      const store = useRiskStore()
      await store.fetchReports()

      expect(store.state.reports).toHaveLength(1)
      expect(store.state.loading).toBe(false)
    })

    it('should set error on API failure', async () => {
      vi.mocked(apiRisk.getReports).mockRejectedValue({
        response: { data: { detail: 'API Error' } },
      })

      const store = useRiskStore()
      await store.fetchReports()

      expect(store.state.error).toBe('API Error')
      expect(store.state.loading).toBe(false)
    })
  })

  describe('fetchReport', () => {
    it('should fetch single report', async () => {
      vi.mocked(apiRisk.getReport).mockResolvedValue({ id: '1', type: 'daily' })

      const store = useRiskStore()
      await store.fetchReport('1')

      expect(store.state.currentReport).not.toBeNull()
      expect(store.state.loading).toBe(false)
    })

    it('should handle error on fetchReport', async () => {
      vi.mocked(apiRisk.getReport).mockRejectedValue({
        response: { data: { detail: 'Not found' } },
      })

      const store = useRiskStore()
      await store.fetchReport('1')

      expect(store.state.error).toBe('Not found')
    })
  })

  describe('clearCurrentReport', () => {
    it('should clear current report', () => {
      const store = useRiskStore()
      store.state.currentReport = { id: '1' } as any

      store.clearCurrentReport()

      expect(store.state.currentReport).toBeNull()
    })
  })
})
