import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/api_qlib', () => ({
  apiQlib: {
    getModels: vi.fn(),
    getModel: vi.fn(),
    startTraining: vi.fn(),
    getInstruments: vi.fn(),
    startSelection: vi.fn(),
  },
}))

import { apiQlib } from '@/services/api_qlib'
import { useQlibStore } from '@/stores/qlib'

describe('Qlib Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have initial state', () => {
      const store = useQlibStore()
      expect(store.state.models).toEqual([])
      expect(store.state.currentModel).toBeNull()
      expect(store.state.trainingStatus).toBeNull()
      expect(store.state.selectionResults).toBeNull()
      expect(store.state.csi300Instruments).toEqual([])
      expect(store.state.loading).toBe(false)
      expect(store.state.training).toBe(false)
      expect(store.state.selecting).toBe(false)
      expect(store.state.error).toBeNull()
    })
  })

  describe('fetchModels', () => {
    it('should fetch models and update state', async () => {
      vi.mocked(apiQlib.getModels).mockResolvedValue({
        items: [{ id: '1', name: 'Model1' }],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })

      const store = useQlibStore()
      await store.fetchModels()

      expect(store.state.models).toHaveLength(1)
      expect(store.state.loading).toBe(false)
    })

    it('should set error on API failure', async () => {
      vi.mocked(apiQlib.getModels).mockRejectedValue({
        response: { data: { detail: 'API Error' } },
      })

      const store = useQlibStore()
      await store.fetchModels()

      expect(store.state.error).toBe('API Error')
      expect(store.state.loading).toBe(false)
    })
  })

  describe('fetchModel', () => {
    it('should fetch single model', async () => {
      vi.mocked(apiQlib.getModel).mockResolvedValue({ id: '1', name: 'Model1' })

      const store = useQlibStore()
      await store.fetchModel('1')

      expect(store.state.currentModel).not.toBeNull()
      expect(store.state.loading).toBe(false)
    })

    it('should handle error on fetchModel', async () => {
      vi.mocked(apiQlib.getModel).mockRejectedValue({
        response: { data: { detail: 'Not found' } },
      })

      const store = useQlibStore()
      await store.fetchModel('1')

      expect(store.state.error).toBe('Not found')
    })
  })

  describe('startTraining', () => {
    it('should start training and return id', async () => {
      vi.mocked(apiQlib.startTraining).mockResolvedValue({ id: 'train-123' })

      const store = useQlibStore()
      const result = await store.startTraining({} as any)

      expect(store.state.trainingStatus).not.toBeNull()
      expect(result).toBe('train-123')
    })

    it('should handle startTraining error', async () => {
      vi.mocked(apiQlib.startTraining).mockRejectedValue({
        response: { data: { detail: 'Failed' } },
      })

      const store = useQlibStore()
      await expect(store.startTraining({} as any)).rejects.toThrow()

      expect(store.state.error).toBe('Failed')
    })
  })
})
