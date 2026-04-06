import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('./api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import api from './api'
import { apiBacktest, type BacktestRequest } from './api_backtest'

const mockedApi = vi.mocked(api)

describe('apiBacktest', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('startBacktest', () => {
    it('should POST to /backtest/run', async () => {
      mockedApi.post.mockResolvedValue({ data: { id: 'bt-123' } })

      const request: BacktestRequest = {
        strategy: 'test',
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      }
      const result = await apiBacktest.startBacktest(request)

      expect(mockedApi.post).toHaveBeenCalledWith('/backtest/run', request)
      expect(result).toEqual({ id: 'bt-123' })
    })
  })

  describe('getResults', () => {
    it('should GET /backtest/results with pagination', async () => {
      mockedApi.get.mockResolvedValue({
        data: {
          items: [{ id: '1' }],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      })

      const result = await apiBacktest.getResults(1, 10)

      expect(mockedApi.get).toHaveBeenCalledWith('/backtest/results', {
        params: { page: 1, page_size: 10 },
      })
      expect(result.items).toHaveLength(1)
    })
  })

  describe('getResult', () => {
    it('should GET /backtest/results/:id', async () => {
      mockedApi.get.mockResolvedValue({
        data: { id: '1', strategy: 'test' },
      })

      const result = await apiBacktest.getResult('1')

      expect(mockedApi.get).toHaveBeenCalledWith('/backtest/results/1')
      expect(result.id).toBe('1')
    })
  })
})
