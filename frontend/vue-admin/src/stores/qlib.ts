import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { apiQlib, type Model, type TrainingStatus, type SelectionResult, type Instrument } from '../services/api_qlib'

export const useQlibStore = defineStore('qlib', () => {
  const state = reactive({
    models: [] as Model[],
    currentModel: null as Model | null,
    trainingStatus: null as TrainingStatus | null,
    selectionResults: null as SelectionResult | null,
    csi300Instruments: [] as Instrument[],
    loading: false,
    training: false,
    selecting: false,
    error: null as string | null,
  })

  async function fetchModels() {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getModels()
      state.models = res.items || []
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取模型列表失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchModel(id: string) {
    state.loading = true
    state.error = null
    try {
      state.currentModel = await apiQlib.getModel(id)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取模型详情失败'
    } finally {
      state.loading = false
    }
  }

  async function startTraining(request: Parameters<typeof apiQlib.startTraining>[0]) {
    state.training = true
    state.error = null
    try {
      const res = await apiQlib.startTraining(request)
      state.trainingStatus = {
        id: res.id,
        status: 'pending',
        progress: 0
      }
      return res.id
    } catch (e: any) {
      state.error = e.response?.data?.detail || '启动训练失败'
      throw e
    } finally {
      state.training = false
    }
  }

  async function checkTrainingStatus(id: string) {
    try {
      state.trainingStatus = await apiQlib.getTrainingStatus(id)
      return state.trainingStatus
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取训练状态失败'
      throw e
    }
  }

  async function runSelection(request: Parameters<typeof apiQlib.runSelection>[0]) {
    state.selecting = true
    state.error = null
    try {
      state.selectionResults = await apiQlib.runSelection(request)
      return state.selectionResults
    } catch (e: any) {
      state.error = e.response?.data?.detail || '股票筛选失败'
      throw e
    } finally {
      state.selecting = false
    }
  }

  async function fetchCSI300() {
    state.loading = true
    state.error = null
    try {
      state.csi300Instruments = await apiQlib.getCSI300()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取沪深300成分股失败'
    } finally {
      state.loading = false
    }
  }

  function clearSelectionResults() {
    state.selectionResults = null
  }

  function clearTrainingStatus() {
    state.trainingStatus = null
  }

  return {
    state,
    fetchModels,
    fetchModel,
    startTraining,
    checkTrainingStatus,
    runSelection,
    fetchCSI300,
    clearSelectionResults,
    clearTrainingStatus,
  }
})
