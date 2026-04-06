import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('./api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import api from './api'
import { apiQlib } from './api_qlib'

const mockedApi = vi.mocked(api)

describe('apiQlib', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('startTraining', () => {
    it('should POST to /qlib/train', async () => {
      mockedApi.post.mockResolvedValue({ data: { id: 'train-123' } })

      const result = await apiQlib.startTraining({} as any)

      expect(mockedApi.post).toHaveBeenCalledWith('/qlib/train', {})
      expect(result).toEqual({ id: 'train-123' })
    })
  })

  describe('getTrainingStatus', () => {
    it('should GET /qlib/train/:id', async () => {
      mockedApi.get.mockResolvedValue({
        data: { id: 'train-123', status: 'running' },
      })

      const result = await apiQlib.getTrainingStatus('train-123')

      expect(mockedApi.get).toHaveBeenCalledWith('/qlib/train/train-123')
      expect(result.status).toBe('running')
    })
  })

  describe('getModels', () => {
    it('should GET /qlib/models', async () => {
      mockedApi.get.mockResolvedValue({
        data: { items: [{ id: '1', name: 'Model1' }], total: 1 },
      })

      const result = await apiQlib.getModels()

      expect(mockedApi.get).toHaveBeenCalledWith('/qlib/models')
      expect(result.items).toHaveLength(1)
    })
  })

  describe('getModel', () => {
    it('should GET /qlib/models/:id', async () => {
      mockedApi.get.mockResolvedValue({
        data: { id: '1', name: 'Model1' },
      })

      const result = await apiQlib.getModel('1')

      expect(mockedApi.get).toHaveBeenCalledWith('/qlib/models/1')
      expect(result.id).toBe('1')
    })
  })

  describe('getCSI300', () => {
    it('should GET /qlib/instruments/csi300', async () => {
      mockedApi.get.mockResolvedValue({
        data: [{ code: 'SH600000', name: 'Test' }],
      })

      const result = await apiQlib.getCSI300()

      expect(mockedApi.get).toHaveBeenCalledWith('/qlib/instruments/csi300')
      expect(result).toHaveLength(1)
    })
  })
})
