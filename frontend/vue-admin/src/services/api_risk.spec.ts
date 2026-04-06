import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('./api', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from './api'
import { apiRisk } from './api_risk'

const mockedApi = vi.mocked(api)

describe('apiRisk', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getReports', () => {
    it('should GET /risk/reports with pagination', async () => {
      mockedApi.get.mockResolvedValue({
        data: {
          items: [{ id: '1', type: 'daily' }],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      })

      const result = await apiRisk.getReports(1, 10)

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/reports', {
        params: { page: 1, page_size: 10 },
      })
      expect(result.items).toHaveLength(1)
    })

    it('should include type filter when provided', async () => {
      mockedApi.get.mockResolvedValue({
        data: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
      })

      await apiRisk.getReports(1, 10, 'daily')

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/reports', {
        params: { page: 1, page_size: 10, type: 'daily' },
      })
    })
  })

  describe('getReport', () => {
    it('should GET /risk/reports/:id', async () => {
      mockedApi.get.mockResolvedValue({
        data: { id: '1', type: 'daily' },
      })

      const result = await apiRisk.getReport('1')

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/reports/1')
      expect(result.id).toBe('1')
    })
  })
})
